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

"""Sacred Values Architecture for Habermas Machine.

This package implements a modified version of the Habermas Machine that properly
handles sacred values as lexicographic constraints rather than weighted preferences.

ARCHITECTURAL INNOVATION:
The standard Collective Rational Model (CRM) treats all values as weighted
preferences subject to democratic compromise. This creates a critical flaw:
sacred values (religious beliefs, moral absolutes) CANNOT be traded off against
other preferences, but CRM forces them into utilitarian calculations.

This architecture fixes that by:
1. Detecting sacred values in citizen opinions (non-negotiable language)
2. Compiling them into hard constraints (not weights)
3. Generating only constraint-satisfying candidate statements
4. Filtering out constraint-violating options before voting
5. Providing transparency about which constraints were respected

This ensures sacred values are treated as LEXICOGRAPHIC CONSTRAINTS:
constraints that must be satisfied FIRST, before any other optimization.
"""

__version__ = "0.1.0"
