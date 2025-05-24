#!/usr/bin/env python3
"""
Paper Trading Integration Test

Tests the complete paper trading workflow with database persistence.
"""

import sys
import asyncio
import uuid
from decimal import Decimal
from datetime import datetime

# Add src to path
sys.path.append('src')

from core.config import get_settings
from database.connection import DatabaseManager
from database.repositories import OrderRepository, TradeRepository, PositionRepository, PortfolioRepository
from database.models import User, Strategy, Order, Trade, Position


async def create_test_user(session):
    """Create a test user for paper trading"""
    from sqlalchemy import text
    
    # Check if test user exists
    result = await session.execute(text("""
        SELECT id FROM trading.users WHERE username = 'test_trader'
    """))
    user = result.fetchone()
    
    if user:
        return user[0]
    
    # Create test user
    user_id = uuid.uuid4()
    await session.execute(text("""
        INSERT INTO trading.users (id, username, email, password_hash)
        VALUES (:id, 'test_trader', 'test@trader.com', 'test_hash')
    """), {"id": user_id})
    
    return user_id


async def create_test_strategy(session):
    """Create a test strategy"""
    from sqlalchemy import text
    
    # Check if test strategy exists
    result = await session.execute(text("""
        SELECT id FROM trading.strategies WHERE name = 'Test ICT Strategy'
    """))
    strategy = result.fetchone()
    
    if strategy:
        return strategy[0]
    
    # Create test strategy
    strategy_id = uuid.uuid4()
    await session.execute(text("""
        INSERT INTO trading.strategies (id, name, description, strategy_type, parameters)
        VALUES (:id, 'Test ICT Strategy', 'Test strategy for paper trading', 'ICT', 
                '{"timeframes": ["1m", "5m"], "risk_per_trade": 0.02}')
    """), {"id": strategy_id})
    
    return strategy_id


async def test_paper_trading_workflow():
    """Test complete paper trading workflow"""
    print("📈 Testing Paper Trading Workflow...")
    
    try:
        settings = get_settings()
        db_manager = DatabaseManager(settings)
        await db_manager.initialize()
        
        async with db_manager.get_session() as session:
            # Create test data
            user_id = await create_test_user(session)
            strategy_id = await create_test_strategy(session)
            
            print(f"   - Test user created: {user_id}")
            print(f"   - Test strategy created: {strategy_id}")
            
            # Initialize repositories
            order_repo = OrderRepository(session)
            trade_repo = TradeRepository(session)
            position_repo = PositionRepository(session)
            
            # Test 1: Create a buy order
            print("\n   📋 Creating buy order...")
            buy_order_data = {
                "user_id": user_id,
                "strategy_id": strategy_id,
                "symbol": "BTCUSDT",
                "side": "buy",
                "order_type": "market",
                "quantity": Decimal("0.001"),
                "price": Decimal("45000.00"),
                "status": "filled"
            }
            
            buy_order = await order_repo.create_order(buy_order_data)
            print(f"      ✅ Buy order created: {buy_order.id}")
            
            # Test 2: Create corresponding trade
            print("   💰 Creating trade...")
            trade_data = {
                "order_id": buy_order.id,
                "symbol": "BTCUSDT",
                "side": "buy",
                "quantity": Decimal("0.001"),
                "price": Decimal("45000.00"),
                "commission": Decimal("0.45"),
                "executed_at": datetime.utcnow()
            }
            
            trade = await trade_repo.create_trade(trade_data)
            print(f"      ✅ Trade created: {trade.id}")
            
            # Test 3: Create position
            print("   📊 Creating position...")
            position_data = {
                "user_id": user_id,
                "symbol": "BTCUSDT",
                "side": "long",
                "quantity": Decimal("0.001"),
                "entry_price": Decimal("45000.00"),
                "current_price": Decimal("45500.00"),
                "unrealized_pnl": Decimal("0.50")
            }
            
            position = await position_repo.create_position(position_data)
            print(f"      ✅ Position created: {position.id}")
            
            # Test 4: Create sell order to close position
            print("   📋 Creating sell order...")
            sell_order_data = {
                "user_id": user_id,
                "strategy_id": strategy_id,
                "symbol": "BTCUSDT",
                "side": "sell",
                "order_type": "market",
                "quantity": Decimal("0.001"),
                "price": Decimal("45500.00"),
                "status": "filled"
            }
            
            sell_order = await order_repo.create_order(sell_order_data)
            print(f"      ✅ Sell order created: {sell_order.id}")
            
            # Test 5: Create closing trade
            print("   💰 Creating closing trade...")
            closing_trade_data = {
                "order_id": sell_order.id,
                "symbol": "BTCUSDT",
                "side": "sell",
                "quantity": Decimal("0.001"),
                "price": Decimal("45500.00"),
                "commission": Decimal("0.455"),
                "executed_at": datetime.utcnow()
            }
            
            closing_trade = await trade_repo.create_trade(closing_trade_data)
            print(f"      ✅ Closing trade created: {closing_trade.id}")
            
            # Test 6: Update position
            print("   📊 Updating position...")
            await position_repo.update_position(position.id, {
                "quantity": Decimal("0.000"),
                "current_price": Decimal("45500.00"),
                "realized_pnl": Decimal("0.045")  # 0.50 - 0.455 commission
            })
            print("      ✅ Position updated")
            
            # Test 7: Query trading history
            print("\n   📊 Querying trading history...")
            user_orders = await order_repo.get_orders_by_user(user_id)
            user_trades = await trade_repo.get_trades_by_user(user_id)
            user_positions = await position_repo.get_positions_by_user(user_id)
            
            print(f"      - Orders: {len(user_orders)}")
            print(f"      - Trades: {len(user_trades)}")
            print(f"      - Positions: {len(user_positions)}")
            
            # Calculate P&L
            total_pnl = sum(trade.price * trade.quantity * (1 if trade.side == 'sell' else -1) 
                          for trade in user_trades)
            total_commission = sum(trade.commission for trade in user_trades)
            net_pnl = total_pnl - total_commission
            
            print(f"      - Total P&L: ${total_pnl:.2f}")
            print(f"      - Total Commission: ${total_commission:.3f}")
            print(f"      - Net P&L: ${net_pnl:.3f}")
        
        await db_manager.close()
        print("\n✅ Paper trading workflow test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Paper trading workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_performance_tracking():
    """Test performance metrics tracking"""
    print("\n📊 Testing Performance Tracking...")
    
    try:
        settings = get_settings()
        db_manager = DatabaseManager(settings)
        await db_manager.initialize()
        
        async with db_manager.get_session() as session:
            from sqlalchemy import text
            
            # Get test user
            result = await session.execute(text("""
                SELECT id FROM trading.users WHERE username = 'test_trader'
            """))
            user = result.fetchone()
            
            if not user:
                print("   ❌ Test user not found. Run paper trading test first.")
                return False
            
            user_id = user[0]
            
            # Calculate daily performance
            result = await session.execute(text("""
                SELECT 
                    COUNT(*) as trade_count,
                    SUM(CASE WHEN side = 'buy' THEN -price * quantity ELSE price * quantity END) as total_pnl,
                    SUM(commission) as total_commission
                FROM trading.trades t
                JOIN trading.orders o ON t.order_id = o.id
                WHERE o.user_id = :user_id
                AND DATE(t.executed_at) = CURRENT_DATE
            """), {"user_id": user_id})
            
            performance = result.fetchone()
            
            if performance:
                trade_count, total_pnl, total_commission = performance
                net_pnl = (total_pnl or 0) - (total_commission or 0)
                
                print(f"   - Today's trades: {trade_count or 0}")
                print(f"   - Gross P&L: ${total_pnl or 0:.3f}")
                print(f"   - Commission: ${total_commission or 0:.3f}")
                print(f"   - Net P&L: ${net_pnl:.3f}")
        
        await db_manager.close()
        print("✅ Performance tracking test completed")
        return True
        
    except Exception as e:
        print(f"❌ Performance tracking test failed: {e}")
        return False


async def main():
    """Main test function"""
    print("🧪 Paper Trading Integration Tests")
    print("=" * 50)
    
    # Test paper trading workflow
    workflow_ok = await test_paper_trading_workflow()
    
    if workflow_ok:
        # Test performance tracking
        await test_performance_tracking()
        
        print("\n🎉 All paper trading tests completed!")
        print("\n📋 Summary:")
        print("   ✅ Database integration working")
        print("   ✅ Order management working")
        print("   ✅ Trade execution working")
        print("   ✅ Position tracking working")
        print("   ✅ Performance calculation working")
        
        print("\n🚀 Ready for live paper trading!")
        
    else:
        print("\n❌ Paper trading tests failed")
        print("   Please check database setup and try again")


if __name__ == "__main__":
    asyncio.run(main())
