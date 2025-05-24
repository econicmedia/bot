#!/usr/bin/env python3
"""
Test Server Startup
Quick test to validate server can start
"""

import sys
import os

# Add src to path
sys.path.append('src')

def test_imports():
    """Test critical imports"""
    print("🧪 Testing critical imports...")
    
    try:
        import fastapi
        print("   ✅ FastAPI imported")
    except ImportError as e:
        print(f"   ❌ FastAPI import failed: {e}")
        return False
    
    try:
        import uvicorn
        print("   ✅ Uvicorn imported")
    except ImportError as e:
        print(f"   ❌ Uvicorn import failed: {e}")
        return False
    
    try:
        from core.config import get_settings
        print("   ✅ Config imported")
    except ImportError as e:
        print(f"   ❌ Config import failed: {e}")
        return False
    
    try:
        from core.engine import TradingEngine
        print("   ✅ Trading engine imported")
    except ImportError as e:
        print(f"   ❌ Trading engine import failed: {e}")
        return False
    
    return True

def test_static_files():
    """Test static files exist"""
    print("\n📁 Testing static files...")
    
    static_files = [
        'src/static/index.html',
        'src/static/styles.css',
        'src/static/dashboard.js'
    ]
    
    all_exist = True
    for file_path in static_files:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} missing")
            all_exist = False
    
    return all_exist

def test_config():
    """Test configuration"""
    print("\n⚙️ Testing configuration...")
    
    try:
        from core.config import get_settings
        settings = get_settings()
        print(f"   ✅ API host: {settings.api.host}")
        print(f"   ✅ API port: {settings.api.port}")
        print(f"   ✅ Debug mode: {settings.app.debug}")
        return True
    except Exception as e:
        print(f"   ❌ Config test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 AI Trading Bot - Server Startup Test")
    print("=" * 50)
    
    # Run tests
    tests = [
        ("Import Test", test_imports),
        ("Static Files Test", test_static_files),
        ("Configuration Test", test_config)
    ]
    
    all_passed = True
    for test_name, test_func in tests:
        result = test_func()
        if not result:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL TESTS PASSED - Server should start successfully!")
        print("\n📋 Next step: Start the server with:")
        print("   cd src && ..\\venv\\Scripts\\python.exe main.py")
    else:
        print("❌ SOME TESTS FAILED - Please fix issues before starting server")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
