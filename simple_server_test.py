#!/usr/bin/env python3
"""
Simple server test to diagnose startup issues
"""

import sys
import os
from pathlib import Path

print("🔍 AI Trading Bot - Server Diagnostic Test")
print("=" * 50)

# Test 1: Python environment
print("1. Testing Python environment...")
print(f"   Python version: {sys.version}")
print(f"   Working directory: {os.getcwd()}")
print(f"   Python path: {sys.executable}")

# Test 2: Add src to path
print("\n2. Setting up Python path...")
src_path = os.path.join(os.getcwd(), 'src')
sys.path.insert(0, src_path)
print(f"   Added to path: {src_path}")
print(f"   Path exists: {os.path.exists(src_path)}")

# Test 3: Import basic modules
print("\n3. Testing basic imports...")
try:
    import fastapi
    print(f"   ✅ FastAPI version: {fastapi.__version__}")
except ImportError as e:
    print(f"   ❌ FastAPI import failed: {e}")
    sys.exit(1)

try:
    import uvicorn
    print(f"   ✅ Uvicorn imported successfully")
except ImportError as e:
    print(f"   ❌ Uvicorn import failed: {e}")
    sys.exit(1)

# Test 4: Test core imports
print("\n4. Testing core module imports...")
try:
    from core.config import get_settings
    print("   ✅ Config module imported")
    
    settings = get_settings()
    print(f"   ✅ Settings loaded (mode: {settings.trading.mode})")
except Exception as e:
    print(f"   ❌ Core config import failed: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Test static files
print("\n5. Testing static files...")
static_dir = Path("src/static")
if static_dir.exists():
    print(f"   ✅ Static directory exists: {static_dir}")
    index_file = static_dir / "index.html"
    if index_file.exists():
        print(f"   ✅ index.html exists")
    else:
        print(f"   ❌ index.html missing")
else:
    print(f"   ❌ Static directory missing: {static_dir}")

# Test 6: Create minimal FastAPI app
print("\n6. Testing minimal FastAPI app creation...")
try:
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    
    app = FastAPI(title="Test App")
    
    @app.get("/")
    async def root():
        return {"message": "Test server working"}
    
    @app.get("/health")
    async def health():
        return {"status": "healthy"}
    
    print("   ✅ FastAPI app created successfully")
    
    # Test 7: Try to start server
    print("\n7. Testing server startup...")
    print("   Attempting to start server on port 8080...")
    
    try:
        import uvicorn
        uvicorn.run(app, host="127.0.0.1", port=8080, log_level="info")
    except Exception as e:
        print(f"   ❌ Server startup failed: {e}")
        print("   Trying alternative port 8081...")
        try:
            uvicorn.run(app, host="127.0.0.1", port=8081, log_level="info")
        except Exception as e2:
            print(f"   ❌ Alternative port failed: {e2}")
            print("   Trying port 8000...")
            try:
                uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
            except Exception as e3:
                print(f"   ❌ All ports failed: {e3}")
                
except Exception as e:
    print(f"   ❌ FastAPI app creation failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("Diagnostic test completed.")
