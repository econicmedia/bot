#!/usr/bin/env python3
"""
Simple Binance Integration Test
"""

import sys
sys.path.append('src')

def test_imports():
    """Test if all imports work"""
    try:
        print("Testing imports...")
        
        # Test core imports
        from core.config import get_settings
        print("✅ Core config imported")
        
        # Test integration imports
        from integrations.base import BaseExchange, OrderSide, OrderType
        print("✅ Base exchange imported")
        
        from integrations.binance.client import BinanceExchange
        print("✅ Binance client imported")
        
        # Test order manager
        from core.order_manager import OrderManager, Order
        print("✅ Order manager imported")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_basic_functionality():
    """Test basic functionality"""
    try:
        print("\nTesting basic functionality...")
        
        # Test settings
        from core.config import get_settings
        settings = get_settings()
        print(f"✅ Settings loaded - Trading mode: {settings.trading.mode}")
        
        # Test Binance client creation
        from integrations.binance.client import BinanceExchange
        binance = BinanceExchange("test_key", "test_secret", sandbox=True)
        print(f"✅ Binance client created - Sandbox: {binance.sandbox}")
        
        # Test order creation
        from core.order_manager import Order, OrderSide, OrderType
        order = Order(
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=0.001,
            price=50000.0
        )
        print(f"✅ Order created - ID: {order.id[:8]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Simple Binance Integration Test")
    print("=" * 40)
    
    success = True
    
    if not test_imports():
        success = False
    
    if not test_basic_functionality():
        success = False
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 All basic tests passed!")
    else:
        print("❌ Some tests failed!")
    
    print("Test completed.")
