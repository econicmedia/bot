#!/usr/bin/env python3
"""
Synchronous test to verify basic functionality
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test basic imports"""
    try:
        print("🧪 Testing imports...")
        
        # Test config
        from core.config import get_settings
        settings = get_settings()
        print(f"✅ Settings loaded - Trading mode: {settings.trading.mode}")
        
        # Test memory storage
        from core.memory_storage import get_memory_data_manager
        memory_manager = get_memory_data_manager()
        print("✅ Memory data manager created")
        
        # Test Binance client
        from integrations.binance.client import BinanceExchange
        binance = BinanceExchange("demo_api_key", "demo_api_secret", sandbox=True)
        print("✅ Binance client created")
        
        # Test live data manager
        from core.live_data_manager import get_live_data_manager
        live_manager = get_live_data_manager(settings)
        print("✅ Live data manager created")
        
        print("\n🎯 All imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_basic_functionality():
    """Test basic functionality without async"""
    try:
        print("\n🧪 Testing basic functionality...")
        
        from core.memory_storage import get_memory_data_manager
        memory_manager = get_memory_data_manager()
        
        # Test portfolio data
        positions = list(memory_manager.positions.values())
        print(f"✅ Positions: {len(positions)}")
        
        trades = memory_manager.trades
        print(f"✅ Trades: {len(trades)}")
        
        prices = memory_manager.market_prices
        print(f"✅ Market prices: {len(prices)} symbols")
        
        for symbol, price in list(prices.items())[:3]:
            print(f"   {symbol}: ${price:,.2f}")
        
        print("\n🎯 Basic functionality working!")
        return True
        
    except Exception as e:
        print(f"❌ Functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Running synchronous tests...")
    
    # Test imports
    import_success = test_imports()
    
    # Test functionality
    func_success = test_basic_functionality()
    
    if import_success and func_success:
        print("\n✅ SUCCESS: Basic system is functional!")
        print("🚀 You can now try starting the server:")
        print("   venv\\Scripts\\python.exe main_server_live.py")
    else:
        print("\n❌ FAILED: Check errors above")
