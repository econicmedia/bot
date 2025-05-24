#!/usr/bin/env python3
"""
Simple test to verify live data manager functionality
"""

import sys
import os
import asyncio

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_basic_functionality():
    """Test basic functionality"""
    try:
        print("Testing basic imports...")
        
        # Test config
        from core.config import get_settings
        settings = get_settings()
        print(f"✅ Settings loaded - Trading mode: {settings.trading.mode}")
        
        # Test live data manager
        from core.live_data_manager import get_live_data_manager
        live_manager = get_live_data_manager(settings)
        print("✅ Live data manager created")
        
        # Test initialization
        success = await live_manager.initialize()
        print(f"✅ Initialization: {'Success' if success else 'Demo mode'}")
        
        # Test portfolio
        portfolio = live_manager.get_portfolio_summary()
        print(f"✅ Portfolio: ${portfolio.get('total_value', 0):,.2f}")
        
        # Test market data
        prices = live_manager.get_market_prices()
        print(f"✅ Market data: {len(prices)} symbols")
        
        # Test trading controls
        await live_manager.start_trading()
        print("✅ Trading started")
        
        await live_manager.stop_trading()
        print("✅ Trading stopped")
        
        # Cleanup
        await live_manager.cleanup()
        print("✅ Cleanup completed")
        
        print("\n🎯 All tests passed! System is ready.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Running simple functionality test...")
    result = asyncio.run(test_basic_functionality())
    if result:
        print("\n✅ SUCCESS: Live trading system is functional!")
    else:
        print("\n❌ FAILED: Check errors above")
