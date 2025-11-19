# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

"""Constraint-Aware Chain-of-Thought Statement Model.

ADAPTED FROM: habermas_machine.statement_model.cot_model
CHANGES: Injects constraints into generation prompts
WHY: Standard CRM generates arbitrary statements; we need to guide the LLM
     to generate ONLY constraint-satisfying statements from the start.

ARCHITECTURAL DIFFERENCE:
Standard CRM: Generate statements → Filter violations (wasteful, may get no valid options)
This system: Inject constraints → Generate only valid statements (efficient, guaranteed feasible)
"""

from collections.abc import Sequence
import re
from typing import List

from sacred_values_architecture.llm_client import base_client
from sacred_values_architecture.statement_model import base_model
from sacred_values_architecture.types import Constraint
from sacred_values_architecture.core import constraint_compiler


def _generate_opinion_critique_prompt(
    question: str,
    opinions: Sequence[str],
    previous_winner: str,
    critiques: Sequence[str],
    constraints: List[Constraint] | None = None,
) -> str:
    """Generates a constraint-aware prompt using opinions, winner, and critiques.

    ADAPTED FROM: habermas_machine.statement_model.cot_model._generate_opinion_critique_prompt
    CHANGES: Added constraint injection
    WHY: LLM needs to know about constraints BEFORE generation, not after
    """

    prompt = f"""You are assisting a citizens' jury in forming a consensus opinion on an important question. The jury members have provided their individual opinions, a first draft of a consensus statement was created, and critiques of that draft were gathered. Your role is to generate a revised consensus statement that incorporates the feedback and aims to better represent the collective view of the jury.  Ensure the revised statement does not conflict with the individual opinions.

Please think through this task step-by-step:

1. Carefully analyze the individual opinions, noting key themes, points of agreement, and areas of disagreement.
2. Review the previous draft consensus statement and identify its strengths and weaknesses.
3. Analyze the critiques of the previous draft, paying attention to specific suggestions and concerns raised by the jury members.
4. Based on the opinions, the previous draft, and the critiques, synthesize a revised consensus statement that addresses the concerns raised and better reflects the collective view of the jury. Ensure the statement is clear, concise, addresses the core issue posed in the question, and *does not conflict* with any of the individual opinions.  Refer to specific opinion and critique numbers when making your revisions.

Provide your answer in the following format:
<answer>
[Your step-by-step reasoning and explanation for the revised statement]
<sep>
[Revised consensus statement]
</answer>

Example:
<answer>
1. Opinions generally agree on the need for more green spaces (Opinions 1, 2, 3), but disagree on the specific location (Opinions 2 and 3 prefer the riverfront) and funding (Opinion 1 suggests a tax levy, Opinion 3 suggests private donations).
2. The previous draft suggested converting the old factory site into a park, but didn't address funding, which was a key concern in Critique 1.
3. Critiques highlighted the lack of funding details (Critique 1) and some preferred a different location (Critique 2 suggested the riverfront, echoing Opinion 2).
4. The revised statement proposes converting the old factory site into a park, funded by a combination of city funds and private donations (addressing Opinion 3 and Critique 1), and includes a plan for community input on park design and amenities. The factory site is chosen as a compromise location, as it avoids the higher costs associated with the riverfront development suggested in Opinion 2 and Critique 2.
<sep>
We propose converting the old factory site into a park, funded by a combination of city funds and private donations. We will actively seek community input on the park's design and amenities to ensure it meets the needs of our residents.
</answer>


Below you will find the question, the individual opinions, the previous draft consensus statement, and the critiques provided by the jury members.


Question: {question}

Individual Opinions:
"""
    for i, opinion in enumerate(opinions):
        prompt += f'Opinion Person {i+1}: {opinion}\n'

    prompt += f"""
Previous Draft Consensus Statement: {previous_winner}

Critiques of the Previous Draft:
"""

    for i, critique in enumerate(critiques):
        prompt += f'Critique Person {i+1}: {critique}\n'

    # CRITICAL ADDITION: Inject constraints into prompt
    # This guides the LLM to generate only constraint-satisfying statements
    if constraints:
        constraint_text = constraint_compiler.get_constraint_injection_prompt(constraints)
        prompt += "\n" + constraint_text

    return prompt.strip()


def _generate_opinion_only_prompt(
    question: str,
    opinions: Sequence[str],
    constraints: List[Constraint] | None = None,
) -> str:
    """Generates a constraint-aware prompt for the LLM using only the opinions.

    ADAPTED FROM: habermas_machine.statement_model.cot_model._generate_opinion_only_prompt
    CHANGES: Added constraint injection
    WHY: First round of deliberation also needs to respect constraints
    """
    prompt = f"""
You are assisting a citizens' jury in forming an initial consensus opinion on an important question. The jury members have provided their individual opinions. Your role is to generate a draft consensus statement that captures the main points of agreement and represents the collective view of the jury.  The draft statement must not conflict with any of the individual opinions.

Please think through this task step-by-step:

1. Carefully analyze the individual opinions, noting key themes, points of agreement, and areas of disagreement.
2. Based on the analysis, synthesize a concise and clear consensus statement that represents the shared perspective of the jury members.  Address the core issue posed in the question, and ensure the statement *does not conflict* with any of the individual opinions.  Refer to specific opinion numbers to demonstrate how the draft reflects the collective view.

Provide your answer in the following format:
<answer>
[Your step-by-step reasoning and explanation for the statement]
<sep>
[Draft consensus statement]
</answer>

Example:
<answer>
1. Most opinions emphasize the importance of public transportation (Opinions 1, 3, 4) and reducing car dependency (Opinions 2, 4). Some also mention cycling and walking as important additions (Opinions 2, 3).
2. The draft statement prioritizes investment in public transport and encourages cycling and walking, reflecting the shared views expressed in the majority of opinions.
<sep>
We believe that investing in public transport, along with promoting cycling and walking, are crucial steps towards creating a more sustainable and livable city.
</answer>


Below you will find the question and the individual opinions of the jury members.

Question: {question}

Individual Opinions:
"""

    for i, opinion in enumerate(opinions):
        prompt += f'Opinion Person {i+1}: {opinion}\n'

    # CRITICAL ADDITION: Inject constraints into prompt
    # This is THE key innovation: tell the LLM about constraints upfront
    if constraints:
        constraint_text = constraint_compiler.get_constraint_injection_prompt(constraints)
        prompt += "\n" + constraint_text

    return prompt.strip()


def _generate_prompt(
    question: str,
    opinions: Sequence[str],
    previous_winner: str | None = None,
    critiques: Sequence[str] | None = None,
    constraints: List[Constraint] | None = None,
) -> str:
    """Generates a constraint-aware prompt for the LLM.

    ADAPTED FROM: habermas_machine.statement_model.cot_model._generate_prompt
    CHANGES: Passes constraints to sub-functions
    WHY: Route constraints to appropriate prompt builder
    """
    if previous_winner is None:
        return _generate_opinion_only_prompt(question, opinions, constraints)
    else:
        return _generate_opinion_critique_prompt(
            question, opinions, previous_winner, critiques, constraints
        )


def _process_model_response(response: str) -> tuple[str, str]:
    """Processes the model's response, extracting the statement and explanation.

    COPIED FROM: habermas_machine.statement_model.cot_model._process_model_response
    No changes needed - response parsing is the same.

    Args:
        response: The raw model response.

    Returns:
        A tuple of (statement, explanation).  If the response format is
        incorrect, returns ("", "INCORRECT_TEMPLATE").
    """
    match = re.search(
        r'<answer>\s*(.*?)\s*<sep>\s*(.*?)\s*</answer>', response, re.DOTALL
    )
    if match:
        explanation = match.group(1).strip()
        statement = match.group(2).strip()
        return statement, explanation
    else:
        return '', 'INCORRECT_TEMPLATE'


class ConstrainedCOTModel(base_model.BaseStatementModel):
    """Constraint-aware statement model using chain-of-thought reasoning.

    ADAPTED FROM: habermas_machine.statement_model.cot_model.COTModel
    CHANGES: Accepts constraints and injects them into prompts
    WHY: Generate only constraint-satisfying statements from the start

    This is a KEY ARCHITECTURAL COMPONENT:
    Instead of generating arbitrary statements and filtering, we guide the LLM
    to generate only statements in the feasible set (constraint-satisfying region).
    """

    def generate_statement(
        self,
        llm_client: base_client.LLMClient,
        question: str,
        opinions: Sequence[str],
        previous_winner: str | None = None,
        critiques: Sequence[str] | None = None,
        seed: int | None = None,
        override_prompt: str | None = None,
        num_retries_on_error: int = 1,
        constraints: List[Constraint] | None = None,  # NEW PARAMETER
    ) -> base_model.StatementResult:
        """Generates a constraint-satisfying statement.

        ADAPTED FROM: COTModel.generate_statement
        CHANGES: Added constraints parameter, passes to prompt generation
        WHY: Enable constraint-aware generation

        Args:
            llm_client: The LLM client to use
            question: The deliberation question
            opinions: List of citizen opinions
            previous_winner: Previous winning statement (if any)
            critiques: Critiques of previous winner (if any)
            seed: Random seed (if supported by client)
            override_prompt: Override the default prompt (advanced)
            num_retries_on_error: Number of retries if generation fails
            constraints: List of constraints to satisfy (NEW)

        Returns:
            StatementResult(statement, explanation)
        """
        if num_retries_on_error is None:
            num_retries_on_error = 0
        else:
            if num_retries_on_error < 0:
                raise ValueError('num_retries_on_error must be None or at least 0.')

        # Generate constraint-aware prompt
        prompt = _generate_prompt(
            question, opinions, previous_winner, critiques, constraints
        )

        statement, explanation = '', ''  # Dummy result.
        for _ in range(num_retries_on_error):
            response = llm_client.sample_text(
                prompt, terminators=['</answer>'], seed=seed)

            statement, explanation = _process_model_response(response)
            if len(statement) > 5 and 'INCORRECT' not in explanation:
                return base_model.StatementResult(statement, explanation)
            else:
                if seed is not None:
                    seed += 1
                    print(f'Retrying with new seed. Explanation: {explanation}')

        # If we reach here, all retries failed. Return the last result.
        return base_model.StatementResult(statement, explanation)
