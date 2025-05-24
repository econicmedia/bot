#!/usr/bin/env python3
"""
Simple Dashboard Test - Verify core functionality works
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test that all imports work"""
    print("🧪 Testing imports...")
    
    try:
        from core.config import get_settings
        print("✅ Config import successful")
        
        settings = get_settings()
        print(f"✅ Settings loaded: {settings.app.name}")
        
        from api.models import TradeResponse, PositionResponse
        print("✅ API models import successful")
        
        # Test memory storage without background tasks
        print("🧪 Testing memory storage...")
        from core.memory_storage import MemoryDataManager
        
        # Create instance without starting background tasks
        data_manager = MemoryDataManager()
        print(f"✅ Memory storage created with {len(data_manager.positions)} positions")
        print(f"✅ Memory storage has {len(data_manager.trades)} trades")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_routes():
    """Test API route imports"""
    print("\n🧪 Testing API routes...")
    
    try:
        from api.routes import api_router
        print("✅ API router import successful")
        
        # Test that we can access the router
        print(f"✅ API router has {len(api_router.routes)} routes")
        
        return True
        
    except Exception as e:
        print(f"❌ API routes test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_static_files():
    """Test that static files exist"""
    print("\n🧪 Testing static files...")
    
    static_files = [
        "src/static/index.html",
        "src/static/styles.css", 
        "src/static/dashboard.js"
    ]
    
    all_exist = True
    for file_path in static_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
            all_exist = False
    
    return all_exist

def main():
    """Run all tests"""
    print("🚀 Simple Dashboard Test")
    print("=" * 50)
    
    tests = [
        ("Core Imports", test_imports),
        ("API Routes", test_api_routes), 
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
        print("\n🎉 All tests passed! Dashboard components are ready.")
        print("\n📋 Next steps:")
        print("   1. Start the server: cd src && python main.py")
        print("   2. Open browser: http://localhost:8000/dashboard")
        return True
    else:
        print(f"\n❌ {total - passed} tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
