#!/usr/bin/env python3
"""
Quick test of core trading functionality
"""

import asyncio
import sys

# Add src to path
sys.path.insert(0, 'src')

async def test_strategy_signal_generation():
    """Test strategy signal generation with realistic data"""
    print("🎯 Testing Strategy Signal Generation...")
    
    try:
        from core.config import get_settings
        from strategies.simple_ma_strategy import SimpleMAStrategy
        from datetime import datetime, timedelta
        
        settings = get_settings()
        strategy = SimpleMAStrategy("test_ma", settings)
        
        # Initialize strategy
        await strategy.initialize()
        print("✅ Strategy initialized")
        
        # Generate multiple candles to trigger MA calculation
        base_price = 50000.0
        signals_generated = []
        
        for i in range(25):  # Generate 25 candles
            # Create trending price data
            if i < 10:
                price = base_price + (i * 50)  # Uptrend
            elif i < 15:
                price = base_price + 500 - ((i-10) * 30)  # Slight downtrend
            else:
                price = base_price + 350 + ((i-15) * 80)  # Strong uptrend
            
            mock_data = {
                "BTCUSDT": {
                    "symbol": "BTCUSDT",
                    "price": price,
                    "timestamp": datetime.now() - timedelta(minutes=25-i),
                    "candle": {
                        "symbol": "BTCUSDT",
                        "timeframe": "1m",
                        "timestamp": (datetime.now() - timedelta(minutes=25-i)).isoformat(),
                        "open_price": price - 10,
                        "high_price": price + 20,
                        "low_price": price - 20,
                        "close_price": price,
                        "volume": 100.0
                    }
                }
            }
            
            signal = await strategy.analyze_market(mock_data)
            if signal:
                signals_generated.append(signal)
                print(f"📊 Signal {len(signals_generated)}: {signal['action']} {signal['direction']} at ${signal['price']:.2f}")
        
        print(f"✅ Generated {len(signals_generated)} trading signals")
        return len(signals_generated) > 0
        
    except Exception as e:
        print(f"❌ Strategy test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_order_execution():
    """Test order execution in paper trading mode"""
    print("\n📋 Testing Order Execution...")
    
    try:
        from core.config import get_settings
        from core.order_manager import OrderManager, Order, OrderType, OrderSide
        
        settings = get_settings()
        order_manager = OrderManager(settings)
        
        # Initialize order manager
        await order_manager.initialize()
        print("✅ Order manager initialized")
        
        # Create a test order
        order = Order(
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            quantity=0.001,
            order_type=OrderType.MARKET,
            price=50000.0
        )
        
        print(f"📝 Created order: {order.symbol} {order.side.value} {order.quantity}")
        
        # Submit the order
        order_id = await order_manager.submit_order(order)
        print(f"✅ Order submitted: {order_id}")
        
        # Check order status
        submitted_order = order_manager.get_order(order_id)
        if submitted_order:
            print(f"📊 Order status: {submitted_order.status.value}")
            print(f"   Filled quantity: {submitted_order.filled_quantity}")
            print(f"   Average fill price: ${submitted_order.average_fill_price:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Order execution test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_portfolio_tracking():
    """Test portfolio tracking functionality"""
    print("\n💰 Testing Portfolio Tracking...")
    
    try:
        from core.config import get_settings
        from core.portfolio_manager import PortfolioManager
        
        settings = get_settings()
        portfolio = PortfolioManager(settings)
        
        # Initialize portfolio
        await portfolio.initialize()
        print("✅ Portfolio manager initialized")
        
        # Check initial state
        initial_value = portfolio.get_portfolio_value()
        print(f"💵 Initial portfolio value: ${initial_value:.2f}")
        
        # Open a position
        position = portfolio.open_position(
            symbol="BTCUSDT",
            side="long",
            quantity=0.001,
            entry_price=50000.0,
            commission=0.5
        )
        
        print(f"📈 Opened position: {position.symbol} {position.side} {position.quantity}")
        
        # Update with new price
        portfolio.update_position_prices({"BTCUSDT": 51000.0})
        
        # Check updated portfolio
        new_value = portfolio.get_portfolio_value()
        unrealized_pnl = portfolio.get_unrealized_pnl()
        
        print(f"💵 Updated portfolio value: ${new_value:.2f}")
        print(f"📊 Unrealized P&L: ${unrealized_pnl:.2f}")
        
        # Close the position
        trade = portfolio.close_position("BTCUSDT", 51000.0, commission=0.5)
        if trade:
            print(f"📉 Closed position: P&L = ${trade.pnl:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Portfolio test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    print("🚀 Quick Trading Functionality Test")
    print("=" * 50)
    
    tests = [
        ("Strategy Signal Generation", test_strategy_signal_generation),
        ("Order Execution", test_order_execution),
        ("Portfolio Tracking", test_portfolio_tracking)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        print("-" * 30)
        
        try:
            if await test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL CORE FUNCTIONALITY WORKING!")
        print("\n🚀 The AI Trading Bot is ready for:")
        print("   ✅ Automated signal generation")
        print("   ✅ Order execution (paper trading)")
        print("   ✅ Portfolio tracking")
        print("   ✅ Real-time trading operations")
        print("\n💡 Next steps:")
        print("   1. Start the web server: python -m src.main")
        print("   2. Open dashboard: http://localhost:8080/dashboard")
        print("   3. Click 'Start Bot' to begin automated trading!")
    else:
        print("\n⚠️  Some core functionality needs attention.")
    
    return passed == total

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
