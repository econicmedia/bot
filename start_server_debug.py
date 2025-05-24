#!/usr/bin/env python3
"""
Start Server with Debug Output
"""

import sys
import os
import asyncio
import logging

# Add src to path
sys.path.append('src')

async def test_server_startup():
    """Test server startup with detailed logging"""
    print("🚀 Starting AI Trading Bot Server with Debug Output")
    print("=" * 60)
    
    try:
        # Import required modules
        print("📦 Importing modules...")
        from core.config import get_settings
        from core.engine import TradingEngine
        from core.logger import setup_logging
        
        # Setup logging
        setup_logging()
        logger = logging.getLogger(__name__)
        
        print("✅ Modules imported successfully")
        
        # Get settings
        print("⚙️ Loading configuration...")
        settings = get_settings()
        print(f"   - Host: {settings.api.host}")
        print(f"   - Port: {settings.api.port}")
        print(f"   - Debug: {settings.app.debug}")
        
        # Test trading engine initialization
        print("🔧 Testing trading engine initialization...")
        trading_engine = TradingEngine(settings)
        await trading_engine.initialize()
        print("✅ Trading engine initialized successfully")
        
        # Test memory storage
        print("💾 Testing memory storage...")
        from core.memory_storage import get_memory_data_manager
        data_manager = get_memory_data_manager()
        print("✅ Memory storage initialized")
        
        print("\n🎉 All components initialized successfully!")
        print("🌐 Server should be ready to start on http://localhost:8000")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Server startup test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def start_server():
    """Start the actual server"""
    print("\n🚀 Starting FastAPI server...")
    
    try:
        import uvicorn
        from main import app
        
        # Start server
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info",
            reload=False
        )
        
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Main function"""
    # Test startup first
    success = await test_server_startup()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ VALIDATION COMPLETE - Starting server...")
        print("📋 Dashboard will be available at: http://localhost:8000/dashboard")
        print("📋 API docs will be available at: http://localhost:8000/docs")
        print("📋 Health check: http://localhost:8000/health")
        print("=" * 60)
        
        # Start the server
        start_server()
    else:
        print("\n❌ Validation failed - cannot start server")
        return False

if __name__ == "__main__":
    asyncio.run(main())
