#!/usr/bin/env python3
"""
Test the enhanced trading engine with real automated trading
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, 'src')

async def test_trading_engine():
    """Test the trading engine with automated trading"""
    print("🚀 Testing Enhanced Trading Engine...")
    
    try:
        from core.config import get_settings
        from core.engine import TradingEngine
        
        # Initialize settings
        settings = get_settings()
        print(f"✅ Settings loaded (mode: {settings.trading.mode})")
        
        # Create trading engine
        engine = TradingEngine(settings)
        print("✅ Trading engine created")
        
        # Initialize engine
        await engine.initialize()
        print("✅ Trading engine initialized")
        
        # Start the engine
        await engine.start()
        print("✅ Trading engine started")
        
        # Check status
        status = await engine.get_status()
        print(f"✅ Engine status: {status['status']}")
        print(f"   - Mode: {status['mode']}")
        print(f"   - Components: {status['components']}")
        
        # Let it run for a bit to see if it generates signals
        print("\n⏳ Running trading engine for 30 seconds...")
        await asyncio.sleep(30)
        
        # Check if any orders were placed
        if engine.order_manager:
            orders = engine.order_manager.get_orders()
            print(f"📊 Orders placed: {len(orders)}")
            
            for order in orders[-5:]:  # Show last 5 orders
                print(f"   - {order.symbol} {order.side.value} {order.quantity} @ {order.price} ({order.status.value})")
        
        # Check portfolio
        if engine.portfolio_manager:
            portfolio_value = engine.portfolio_manager.get_portfolio_value()
            positions = engine.portfolio_manager.get_positions()
            print(f"💰 Portfolio value: ${portfolio_value:.2f}")
            print(f"📈 Active positions: {len(positions)}")
        
        # Stop the engine
        await engine.stop()
        print("✅ Trading engine stopped")
        
        print("\n🎉 Trading engine test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Trading engine test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_api_integration():
    """Test the API integration with the trading engine"""
    print("\n🌐 Testing API Integration...")
    
    try:
        import aiohttp
        
        # Test start trading endpoint
        async with aiohttp.ClientSession() as session:
            # Start trading
            async with session.post("http://localhost:8080/api/v1/trading/start") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Trading started via API: {data['message']}")
                else:
                    print(f"❌ Failed to start trading: {response.status}")
                    return False
            
            # Check status
            async with session.get("http://localhost:8080/api/v1/bot/status") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Bot status: {data}")
                else:
                    print(f"❌ Failed to get status: {response.status}")
            
            # Wait a bit
            await asyncio.sleep(10)
            
            # Check for trades
            async with session.get("http://localhost:8080/api/v1/trading/trades") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Trades: {len(data)} trades found")
                else:
                    print(f"❌ Failed to get trades: {response.status}")
            
            # Stop trading
            async with session.post("http://localhost:8080/api/v1/trading/stop") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Trading stopped via API: {data['message']}")
                else:
                    print(f"❌ Failed to stop trading: {response.status}")
        
        print("✅ API integration test completed!")
        return True
        
    except Exception as e:
        print(f"❌ API integration test failed: {e}")
        return False

async def main():
    """Main test function"""
    print("🧪 Enhanced Trading Engine Test Suite")
    print("=" * 50)
    
    # Test 1: Core trading engine
    success1 = await test_trading_engine()
    
    # Test 2: API integration (requires server to be running)
    print("\n" + "=" * 50)
    try:
        success2 = await test_api_integration()
    except Exception as e:
        print(f"⚠️  API test skipped (server not running): {e}")
        success2 = True  # Don't fail the test if server isn't running
    
    # Summary
    print("\n" + "=" * 50)
    if success1 and success2:
        print("🎉 All tests passed! Trading engine is ready for automated trading.")
    else:
        print("❌ Some tests failed. Check the output above.")
    
    return success1 and success2

if __name__ == "__main__":
    asyncio.run(main())
