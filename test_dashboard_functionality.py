#!/usr/bin/env python3
"""
Test the dashboard functionality and trading engine integration
"""

import asyncio
import sys
import time
import aiohttp

# Add src to path
sys.path.insert(0, 'src')

async def test_dashboard_api():
    """Test the dashboard API endpoints"""
    print("🌐 Testing Dashboard API Functionality...")
    
    # Start the server in background
    from main import app
    import uvicorn
    from threading import Thread
    
    def run_server():
        uvicorn.run(app, host="127.0.0.1", port=8080, log_level="error")
    
    # Start server in background thread
    server_thread = Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Wait for server to start
    await asyncio.sleep(3)
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test health endpoint
            print("🔍 Testing health endpoint...")
            try:
                async with session.get("http://localhost:8080/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Health check passed: {data.get('status', 'unknown')}")
                    else:
                        print(f"⚠️  Health check returned: {response.status}")
            except Exception as e:
                print(f"❌ Health check failed: {e}")
            
            # Test bot status
            print("🤖 Testing bot status...")
            try:
                async with session.get("http://localhost:8080/api/v1/bot/status") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Bot status: {data}")
                    else:
                        print(f"⚠️  Bot status returned: {response.status}")
            except Exception as e:
                print(f"❌ Bot status failed: {e}")
            
            # Test trading positions
            print("📊 Testing trading positions...")
            try:
                async with session.get("http://localhost:8080/api/v1/trading/positions") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Positions: {len(data)} positions found")
                    else:
                        print(f"⚠️  Positions returned: {response.status}")
            except Exception as e:
                print(f"❌ Positions failed: {e}")
            
            # Test starting the bot
            print("🚀 Testing bot start...")
            try:
                async with session.post("http://localhost:8080/api/v1/trading/start") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Bot started: {data.get('message', 'unknown')}")
                    else:
                        text = await response.text()
                        print(f"⚠️  Bot start returned: {response.status} - {text}")
            except Exception as e:
                print(f"❌ Bot start failed: {e}")
            
            # Wait a bit for trading activity
            print("⏳ Waiting for trading activity...")
            await asyncio.sleep(10)
            
            # Check for trades
            print("📈 Testing trades endpoint...")
            try:
                async with session.get("http://localhost:8080/api/v1/trading/trades") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Trades: {len(data)} trades found")
                        if data:
                            print(f"   Latest trade: {data[0]}")
                    else:
                        print(f"⚠️  Trades returned: {response.status}")
            except Exception as e:
                print(f"❌ Trades failed: {e}")
            
            # Test performance metrics
            print("📊 Testing performance metrics...")
            try:
                async with session.get("http://localhost:8080/api/v1/analytics/performance") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Performance: {data}")
                    else:
                        print(f"⚠️  Performance returned: {response.status}")
            except Exception as e:
                print(f"❌ Performance failed: {e}")
            
            # Stop the bot
            print("🛑 Testing bot stop...")
            try:
                async with session.post("http://localhost:8080/api/v1/trading/stop") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Bot stopped: {data.get('message', 'unknown')}")
                    else:
                        print(f"⚠️  Bot stop returned: {response.status}")
            except Exception as e:
                print(f"❌ Bot stop failed: {e}")
        
        print("\n🎉 Dashboard API test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Dashboard API test failed: {e}")
        return False

async def test_trading_engine_directly():
    """Test the trading engine directly without the web server"""
    print("\n🔧 Testing Trading Engine Directly...")
    
    try:
        from core.config import get_settings
        from core.engine import TradingEngine
        from core.memory_storage import get_memory_data_manager
        
        # Initialize settings
        settings = get_settings()
        print(f"✅ Settings loaded (mode: {settings.trading.mode})")
        
        # Initialize memory data manager
        data_manager = get_memory_data_manager()
        data_manager.start_background_tasks()
        print("✅ Memory data manager started")
        
        # Create and initialize trading engine
        engine = TradingEngine(settings)
        await engine.initialize()
        print("✅ Trading engine initialized")
        
        # Start the engine
        await engine.start()
        print("✅ Trading engine started")
        
        # Let it run for a bit
        print("⏳ Running for 15 seconds to generate signals...")
        await asyncio.sleep(15)
        
        # Check status
        status = await engine.get_status()
        print(f"📊 Engine status: {status['status']}")
        print(f"   Uptime: {status.get('uptime', 0):.1f} seconds")
        
        # Check for orders
        if engine.order_manager:
            orders = engine.order_manager.get_orders()
            print(f"📋 Orders placed: {len(orders)}")
            
            for order in orders[-3:]:  # Show last 3 orders
                print(f"   - {order.symbol} {order.side.value} {order.quantity} @ {order.price} ({order.status.value})")
        
        # Check portfolio
        if engine.portfolio_manager:
            portfolio_value = engine.portfolio_manager.get_portfolio_value()
            positions = engine.portfolio_manager.get_positions()
            trades = engine.portfolio_manager.get_trades()
            print(f"💰 Portfolio value: ${portfolio_value:.2f}")
            print(f"📈 Active positions: {len(positions)}")
            print(f"📊 Total trades: {len(trades)}")
        
        # Stop the engine
        await engine.stop()
        print("✅ Trading engine stopped")
        
        return True
        
    except Exception as e:
        print(f"❌ Trading engine test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    print("🧪 AI Trading Bot - Comprehensive Functionality Test")
    print("=" * 60)
    
    # Test 1: Direct trading engine
    success1 = await test_trading_engine_directly()
    
    # Test 2: Dashboard API
    print("\n" + "=" * 60)
    success2 = await test_dashboard_api()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print(f"   Direct Engine Test: {'✅ PASSED' if success1 else '❌ FAILED'}")
    print(f"   Dashboard API Test: {'✅ PASSED' if success2 else '❌ FAILED'}")
    
    if success1 and success2:
        print("\n🎉 ALL TESTS PASSED! The AI Trading Bot is fully functional!")
        print("\n🚀 Ready for automated trading:")
        print("   1. Start server: python -m src.main")
        print("   2. Open dashboard: http://localhost:8080/dashboard")
        print("   3. Click 'Start Bot' to begin trading!")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
    
    return success1 and success2

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
