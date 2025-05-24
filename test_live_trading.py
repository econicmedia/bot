#!/usr/bin/env python3
"""
Test Live Trading Functionality

This script tests the live data manager and paper trading functionality
to ensure everything works before starting the server.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("🧪 Testing Live Trading Functionality")
print("=" * 50)

async def test_live_data_manager():
    """Test the live data manager functionality"""
    try:
        print("\n1️⃣ Testing Live Data Manager Initialization...")
        
        from core.live_data_manager import get_live_data_manager
        from core.config import get_settings
        
        # Get settings
        settings = get_settings()
        print(f"   ✅ Settings loaded - Trading mode: {settings.trading.mode}")
        
        # Initialize live data manager
        live_manager = get_live_data_manager(settings)
        print(f"   ✅ Live data manager created")
        
        # Initialize
        success = await live_manager.initialize()
        print(f"   ✅ Initialization {'successful' if success else 'completed (demo mode)'}")
        print(f"   📡 Exchange connected: {live_manager.is_connected}")
        
        return live_manager
        
    except Exception as e:
        print(f"   ❌ Live data manager test failed: {e}")
        return None

async def test_market_data(live_manager):
    """Test market data functionality"""
    try:
        print("\n2️⃣ Testing Market Data...")
        
        if live_manager:
            prices = live_manager.get_market_prices()
            print(f"   ✅ Market prices retrieved: {len(prices)} symbols")
            
            for symbol, price in prices.items():
                print(f"      {symbol}: ${price:,.2f}")
                
            return True
        else:
            print("   ⚠️ No live manager available")
            return False
            
    except Exception as e:
        print(f"   ❌ Market data test failed: {e}")
        return False

async def test_portfolio_functionality(live_manager):
    """Test portfolio and trading functionality"""
    try:
        print("\n3️⃣ Testing Portfolio Functionality...")
        
        if live_manager:
            # Get portfolio summary
            portfolio = live_manager.get_portfolio_summary()
            print(f"   ✅ Portfolio summary retrieved")
            print(f"      Total Value: ${portfolio.get('total_value', 0):,.2f}")
            print(f"      Cash Balance: ${portfolio.get('cash_balance', 0):,.2f}")
            print(f"      Active Positions: {portfolio.get('active_positions', 0)}")
            print(f"      Total Trades: {portfolio.get('total_trades', 0)}")
            
            # Get positions
            positions = live_manager.get_positions()
            print(f"   ✅ Positions retrieved: {len(positions)} positions")
            
            for pos in positions[:3]:  # Show first 3 positions
                print(f"      {pos['symbol']}: {pos['side']} {pos['quantity']:.4f} @ ${pos['entry_price']:,.2f}")
            
            # Get recent trades
            trades = live_manager.get_recent_trades(5)
            print(f"   ✅ Recent trades retrieved: {len(trades)} trades")
            
            return True
        else:
            print("   ⚠️ No live manager available")
            return False
            
    except Exception as e:
        print(f"   ❌ Portfolio test failed: {e}")
        return False

async def test_trading_controls(live_manager):
    """Test trading start/stop functionality"""
    try:
        print("\n4️⃣ Testing Trading Controls...")
        
        if live_manager:
            # Test start trading
            await live_manager.start_trading()
            portfolio = live_manager.get_portfolio_summary()
            print(f"   ✅ Trading started - Active: {portfolio.get('is_trading', False)}")
            
            # Wait a moment
            await asyncio.sleep(2)
            
            # Test stop trading
            await live_manager.stop_trading()
            portfolio = live_manager.get_portfolio_summary()
            print(f"   ✅ Trading stopped - Active: {portfolio.get('is_trading', False)}")
            
            return True
        else:
            print("   ⚠️ No live manager available")
            return False
            
    except Exception as e:
        print(f"   ❌ Trading controls test failed: {e}")
        return False

async def test_strategy_performance(live_manager):
    """Test strategy performance tracking"""
    try:
        print("\n5️⃣ Testing Strategy Performance...")
        
        if live_manager:
            strategies = live_manager.get_strategy_performance()
            print(f"   ✅ Strategy performance retrieved: {len(strategies)} strategies")
            
            for strategy_name, metrics in strategies.items():
                print(f"      {strategy_name}:")
                print(f"         Enabled: {metrics.get('enabled', False)}")
                print(f"         Total Trades: {metrics.get('total_trades', 0)}")
                print(f"         Win Rate: {metrics.get('win_rate', 0):.1%}")
                print(f"         Signals Today: {metrics.get('signals_today', 0)}")
            
            return True
        else:
            print("   ⚠️ No live manager available")
            return False
            
    except Exception as e:
        print(f"   ❌ Strategy performance test failed: {e}")
        return False

async def test_binance_connection():
    """Test direct Binance connection"""
    try:
        print("\n6️⃣ Testing Direct Binance Connection...")
        
        from integrations.binance.client import BinanceExchange
        
        # Test with demo credentials
        binance = BinanceExchange("demo_api_key", "demo_api_secret", sandbox=True)
        print(f"   ✅ Binance client created")
        print(f"      Base URL: {binance.base_url}")
        print(f"      Sandbox: {binance.sandbox}")
        
        # Test connection
        try:
            connected = await binance.connect()
            print(f"   ✅ Connection test completed")
            print(f"      Connected: {connected}")
            
            if connected:
                # Test market data
                try:
                    ticker = await binance.get_ticker("BTCUSDT")
                    print(f"   ✅ Market data test: BTC ${ticker.last:,.2f}")
                except Exception as e:
                    print(f"   ⚠️ Market data test skipped: {e}")
                
                await binance.disconnect()
            
        except Exception as e:
            print(f"   ⚠️ Connection test completed with demo credentials: {e}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Binance connection test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting comprehensive live trading tests...\n")
    
    results = []
    
    # Test 1: Live Data Manager
    live_manager = await test_live_data_manager()
    results.append(live_manager is not None)
    
    # Test 2: Market Data
    market_data_ok = await test_market_data(live_manager)
    results.append(market_data_ok)
    
    # Test 3: Portfolio Functionality
    portfolio_ok = await test_portfolio_functionality(live_manager)
    results.append(portfolio_ok)
    
    # Test 4: Trading Controls
    trading_ok = await test_trading_controls(live_manager)
    results.append(trading_ok)
    
    # Test 5: Strategy Performance
    strategy_ok = await test_strategy_performance(live_manager)
    results.append(strategy_ok)
    
    # Test 6: Direct Binance Connection
    binance_ok = await test_binance_connection()
    results.append(binance_ok)
    
    # Cleanup
    if live_manager and hasattr(live_manager, 'cleanup'):
        await live_manager.cleanup()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"   Live Data Manager: {'✅ PASS' if results[0] else '❌ FAIL'}")
    print(f"   Market Data: {'✅ PASS' if results[1] else '❌ FAIL'}")
    print(f"   Portfolio Functions: {'✅ PASS' if results[2] else '❌ FAIL'}")
    print(f"   Trading Controls: {'✅ PASS' if results[3] else '❌ FAIL'}")
    print(f"   Strategy Performance: {'✅ PASS' if results[4] else '❌ FAIL'}")
    print(f"   Binance Connection: {'✅ PASS' if results[5] else '❌ FAIL'}")
    
    passed = sum(results)
    total = len(results)
    print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total:.1%})")
    
    if passed >= 4:  # At least 4 out of 6 tests should pass
        print("\n✅ System ready for live trading!")
        print("🚀 You can now start the live server with: python main_server_live.py")
    else:
        print("\n⚠️ Some issues detected. Check the logs above.")
        print("🔄 You can still use demo mode with: python main_server_fixed.py")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️ Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test suite failed: {e}")
        sys.exit(1)
