import sys
print("Python executable:", sys.executable)
print("\nPython version:", sys.version)
print("\nSys path:")
for p in sys.path:
    print(p)
    
print("\n\nTrying to import matplotlib...")
try:
    import matplotlib
    import matplotlib.pyplot as plt
    print("Success! matplotlib version:", matplotlib.__version__)
except ImportError as e:
    print(f"Error: {e}")
