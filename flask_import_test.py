import sys
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")

print("\nTrying to import Flask...")
try:
    import flask
    print(f"SUCCESS! Flask imported. Version: {flask.__version__}")
except ImportError as e:
    print(f"FAILED to import Flask: {e}")
    
    print("\nChecking sys.path:")
    for path in sys.path:
        print(f"  {path}")
        
    print("\nTrying to import other packages:")
    for package in ['os', 'json', 'requests', 'numpy']:
        try:
            __import__(package)
            print(f"  ✓ {package} imported successfully")
        except ImportError:
            print(f"  ✗ {package} failed to import") 