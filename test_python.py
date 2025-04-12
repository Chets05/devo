import sys
import os

print("Python version:")
print(sys.version)
print("\nPython executable:")
print(sys.executable)
print("\nPython path:")
for path in sys.path:
    print(f"  {path}")
print("\nCurrent working directory:")
print(os.getcwd())
print("\nEnvironment variables:")
for key, value in os.environ.items():
    if "PYTHON" in key or "PATH" in key:
        print(f"  {key}={value}")

print("\nTest completed successfully!") 