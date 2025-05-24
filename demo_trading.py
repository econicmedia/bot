#!/usr/bin/env python3
"""
Demo script to show the trading system in action
"""

import asyncio
import sys
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.config import get_settings
from src.core.engine import TradingEngine
from src.core.strategy_manager import StrategyType
from src.strategies.simple_ma_strategy import SimpleMAStrategy


async def demo_trading_system():
    """Demonstrate the trading system with a simple strategy"""
    print("🚀 AI Trading Bot Demo")
    print("=" * 50)
    
    try:
        # Initialize the trading engine
        print("1. Initializing Trading Engine...")
        settings = get_settings()
        engine = TradingEngine(settings)
        await engine.initialize()
        print("   ✓ Trading engine initialized")
        
        # Register and create a strategy
        print("\n2. Setting up Trading Strategy...")
        engine.strategy_manager.register_strategy_class(StrategyType.ICT, SimpleMAStrategy)
        strategy = await engine.strategy_manager.create_strategy(StrategyType.ICT, "demo_ma_strategy")
        await engine.strategy_manager.start_strategy("demo_ma_strategy")
        print("   ✓ Simple MA strategy created and started")
        
        # Simulate some market data
        print("\n3. Simulating Market Data...")
        
        # Generate some sample candle data
        base_price = 50000.0
        for i in range(25):  # Generate 25 candles to trigger MA calculations
            price_change = (-1 if i % 3 == 0 else 1) * (i * 10)  # Create some price movement
            current_price = base_price + price_change
            
            market_data = {
                "symbol": "BTCUSDT",
                "data_type": "candle",
                "timestamp": datetime.utcnow().isoformat(),
                "data": {
                    "symbol": "BTCUSDT",
                    "timeframe": "1m",
                    "timestamp": datetime.utcnow().isoformat(),
                    "open": current_price - 5,
                    "high": current_price + 10,
                    "low": current_price - 10,
                    "close": current_price,
                    "volume": 100.0 + i * 5
                }
            }
            
            # Process market data through strategies
            signals = await engine.strategy_manager.process_market_data(market_data)
            
            if signals:
                for signal in signals:
                    print(f"   📊 Signal: {signal['action']} {signal['symbol']} at ${signal['price']:.2f}")
                    print(f"      Reason: {signal['reason']}")
                    
                    # Simulate order execution
                    if signal['action'] in ['buy', 'sell']:
                        # Calculate position size using risk manager
                        position_size, details = engine.risk_manager.calculate_position_size(
                            symbol=signal['symbol'],
                            entry_price=signal['price'],
                            stop_loss_price=signal['price'] * 0.98 if signal['action'] == 'buy' else signal['price'] * 1.02
                        )
                        
                        if position_size > 0:
                            print(f"      💰 Position size: {position_size:.2f} shares")
                            
                            # Create and submit order
                            from src.core.order_manager import Order, OrderType, OrderSide
                            order = Order(
                                symbol=signal['symbol'],
                                side=OrderSide.BUY if signal['action'] == 'buy' else OrderSide.SELL,
                                order_type=OrderType.MARKET,
                                quantity=position_size,
                                strategy=signal['strategy']
                            )
                            
                            order_id = await engine.order_manager.submit_order(order)
                            print(f"      📋 Order submitted: {order_id}")
                            
                            # Update portfolio (simulate fill)
                            if signal['action'] == 'buy':
                                position = engine.portfolio_manager.open_position(
                                    symbol=signal['symbol'],
                                    side='long',
                                    quantity=position_size,
                                    entry_price=signal['price'],
                                    strategy=signal['strategy']
                                )
                                print(f"      📈 Opened long position: {signal['symbol']}")
                            
            # Small delay to make it more realistic
            await asyncio.sleep(0.1)
        
        # Show final status
        print("\n4. Final Status:")
        
        # Portfolio summary
        portfolio_summary = engine.portfolio_manager.get_performance_summary()
        print(f"   💼 Portfolio Value: ${portfolio_summary['current_value']:,.2f}")
        print(f"   💰 Cash Balance: ${portfolio_summary['cash_balance']:,.2f}")
        print(f"   📊 Total P&L: ${portfolio_summary['total_pnl']:,.2f}")
        print(f"   📈 Active Positions: {portfolio_summary['active_positions']}")
        
        # Strategy performance
        strategy_status = engine.strategy_manager.get_strategy_status("demo_ma_strategy")
        if strategy_status:
            perf = strategy_status['performance']
            print(f"   🎯 Strategy Trades: {perf['total_trades']}")
            print(f"   🏆 Win Rate: {perf['win_rate']:.1%}")
        
        # Risk status
        risk_status = engine.risk_manager.get_risk_status()
        print(f"   ⚠️  Risk Level: {risk_status['risk_level']}")
        print(f"   📉 Current Drawdown: {risk_status['current_drawdown']:.1%}")
        
        # Order status
        order_status = engine.order_manager.get_order_status()
        print(f"   📋 Total Orders: {order_status['total_orders']}")
        print(f"   🔄 Active Orders: {order_status['active_orders']}")
        
        print("\n✅ Demo completed successfully!")
        print("\n🎉 Key Features Demonstrated:")
        print("   • Core trading engine initialization")
        print("   • Strategy management and execution")
        print("   • Risk management and position sizing")
        print("   • Order management and execution")
        print("   • Portfolio tracking and performance")
        print("   • Real-time market data processing")
        
        # Cleanup
        await engine.strategy_manager.stop_all_strategies()
        await engine.data_manager.stop()
        
        return True
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(demo_trading_system())
    print(f"\n{'🎉 Demo successful!' if success else '❌ Demo failed!'}")
    sys.exit(0 if success else 1)
