#!/usr/bin/env python3
"""
Debug Server Startup Issues
"""

import sys
import os
import traceback

# Add src to path
sys.path.append('src')

def test_imports():
    """Test all critical imports"""
    print("🔍 Testing imports...")
    
    try:
        import fastapi
        print("✅ FastAPI imported")
    except Exception as e:
        print(f"❌ FastAPI import failed: {e}")
        return False
    
    try:
        import uvicorn
        print("✅ Uvicorn imported")
    except Exception as e:
        print(f"❌ Uvicorn import failed: {e}")
        return False
    
    try:
        from core.config import get_settings
        settings = get_settings()
        print("✅ Config loaded")
    except Exception as e:
        print(f"❌ Config import failed: {e}")
        traceback.print_exc()
        return False
    
    try:
        from core.memory_storage import get_memory_data_manager
        data_manager = get_memory_data_manager()
        print("✅ Memory storage imported")
    except Exception as e:
        print(f"❌ Memory storage import failed: {e}")
        traceback.print_exc()
        return False
    
    try:
        from api.routes import api_router
        print("✅ API routes imported")
    except Exception as e:
        print(f"❌ API routes import failed: {e}")
        traceback.print_exc()
        return False
    
    return True

def test_simple_server():
    """Test a minimal FastAPI server"""
    print("\n🚀 Testing minimal server...")
    
    try:
        from fastapi import FastAPI
        import uvicorn
        
        app = FastAPI()
        
        @app.get("/")
        def root():
            return {"message": "Server is working!"}
        
        @app.get("/test")
        def test():
            return {"status": "ok", "message": "Test endpoint working"}
        
        print("✅ Minimal FastAPI app created")
        print("🚀 Starting server on port 8001...")
        
        # Start on different port to avoid conflicts
        uvicorn.run(app, host="127.0.0.1", port=8001, log_level="debug")
        
    except Exception as e:
        print(f"❌ Minimal server failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Main diagnostic function"""
    print("🔧 AI Trading Bot - Server Diagnostic")
    print("=" * 50)
    
    # Test imports first
    if not test_imports():
        print("\n❌ Import tests failed - cannot start server")
        return False
    
    print("\n✅ All imports successful!")
    print("🔄 Starting minimal test server...")
    
    # Start minimal server
    test_simple_server()

if __name__ == "__main__":
    main()
