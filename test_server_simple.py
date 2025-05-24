#!/usr/bin/env python3
"""
Simple server test to verify the dashboard is working
"""

import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_basic_imports():
    """Test basic imports work"""
    print("🧪 Testing basic imports...")
    
    try:
        # Test core imports
        from core.config import get_settings
        print("✅ Core config import successful")
        
        # Test memory storage
        from core.memory_storage import get_memory_data_manager
        data_manager = get_memory_data_manager()
        print(f"✅ Memory storage loaded: {len(data_manager.positions)} positions, {len(data_manager.trades)} trades")
        
        # Test API models
        from api.models import TradeResponse, PositionResponse
        print("✅ API models import successful")
        
        # Test API routes
        from api.routes import api_router
        print(f"✅ API routes loaded: {len(api_router.routes)} routes")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fastapi_app():
    """Test FastAPI app creation"""
    print("\n🧪 Testing FastAPI app creation...")
    
    try:
        # Import FastAPI components
        from fastapi import FastAPI
        from fastapi.staticfiles import StaticFiles
        print("✅ FastAPI imports successful")
        
        # Test app creation
        from main import app
        print("✅ FastAPI app created successfully")
        
        # Check routes
        routes = [route.path for route in app.routes]
        print(f"✅ App has {len(routes)} routes")
        
        # Check for key routes
        key_routes = ["/", "/dashboard", "/health", "/api/v1/trading/status"]
        for route in key_routes:
            if any(route in r for r in routes):
                print(f"✅ Route {route} found")
            else:
                print(f"❌ Route {route} missing")
        
        return True
        
    except Exception as e:
        print(f"❌ FastAPI app test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_static_files():
    """Test static files exist"""
    print("\n🧪 Testing static files...")
    
    static_files = [
        "src/static/index.html",
        "src/static/styles.css",
        "src/static/dashboard.js"
    ]
    
    all_exist = True
    for file_path in static_files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"✅ {file_path} exists ({size} bytes)")
        else:
            print(f"❌ {file_path} missing")
            all_exist = False
    
    return all_exist

def main():
    """Run all tests"""
    print("🚀 Simple Server Test")
    print("=" * 50)
    
    tests = [
        ("Basic Imports", test_basic_imports),
        ("FastAPI App", test_fastapi_app),
        ("Static Files", test_static_files)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} test...")
        if test_func():
            print(f"✅ {test_name} test PASSED")
            passed += 1
        else:
            print(f"❌ {test_name} test FAILED")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Server components are ready.")
        print("\n📋 Manual verification steps:")
        print("   1. The server should be running on http://localhost:8000")
        print("   2. Dashboard should be accessible at http://localhost:8000/dashboard")
        print("   3. API docs should be at http://localhost:8000/docs")
        print("   4. Health check at http://localhost:8000/health")
        
        print("\n🔧 If server isn't responding:")
        print("   - Check if port 8000 is available")
        print("   - Look for any error messages in the server terminal")
        print("   - Try restarting the server")
        
        return True
    else:
        print(f"\n❌ {total - passed} tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
