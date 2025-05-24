#!/usr/bin/env python3
"""
Test Database Integration

This script tests the database integration components to ensure they work correctly
with the trading bot's data persistence layer.
"""

import asyncio
import sys
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

# Add src to path
sys.path.append('src')

from core.config import get_settings


async def test_database_connection():
    """Test basic database connection"""
    print("🔗 Testing Database Connection...")
    
    try:
        from database.connection import DatabaseManager
        
        settings = get_settings()
        db_manager = DatabaseManager(settings)
        
        # Test initialization
        await db_manager.initialize()
        
        print("✅ Database connection initialized")
        
        # Test health check
        health = await db_manager.health_check()
        print(f"   - Status: {health['status']}")
        print(f"   - Connected: {health['connected']}")
        print(f"   - Database: {health['database']}")
        
        # Test session
        async with db_manager.get_session() as session:
            result = await session.execute("SELECT 1 as test")
            row = result.fetchone()
            print(f"   - Test query result: {row}")
        
        await db_manager.close()
        return True
        
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_database_models():
    """Test database models and schema creation"""
    print("\n📊 Testing Database Models...")
    
    try:
        from database.connection import DatabaseManager
        from database.models import Base
        
        settings = get_settings()
        db_manager = DatabaseManager(settings)
        await db_manager.initialize()
        
        # Create tables
        await db_manager.create_tables()
        print("✅ Database tables created successfully")
        
        # Test table creation was successful
        async with db_manager.get_session() as session:
            # Check if tables exist by querying them
            tables_to_check = [
                "trading.users",
                "trading.strategies", 
                "trading.orders",
                "trading.trades",
                "trading.positions",
                "trading.portfolios"
            ]
            
            for table in tables_to_check:
                try:
                    result = await session.execute(f"SELECT COUNT(*) FROM {table}")
                    count = result.scalar()
                    print(f"   - Table {table}: {count} records")
                except Exception as e:
                    print(f"   - Table {table}: Error - {e}")
        
        await db_manager.close()
        return True
        
    except Exception as e:
        print(f"❌ Database models test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_repositories():
    """Test database repositories"""
    print("\n📚 Testing Database Repositories...")
    
    try:
        from database.connection import get_database_manager
        from database.repositories import OrderRepository, TradeRepository, PositionRepository
        
        db_manager = await get_database_manager()
        user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
        
        async with db_manager.get_session() as session:
            order_repo = OrderRepository(session)
            
            # Test order creation
            order_data = {
                "user_id": user_id,
                "symbol": "BTCUSDT",
                "side": "buy",
                "order_type": "limit",
                "quantity": Decimal("0.001"),
                "price": Decimal("50000.0"),
                "time_in_force": "GTC",
                "status": "pending",
                "filled_quantity": Decimal("0"),
                "remaining_quantity": Decimal("0.001"),
                "average_fill_price": Decimal("0"),
                "commission": Decimal("0"),
                "created_at": datetime.utcnow(),
                "submitted_at": datetime.utcnow()
            }
            
            order = await order_repo.create_order(order_data)
            print(f"✅ Created test order: {order.id}")
            
            # Test order retrieval
            retrieved_order = await order_repo.get_order_by_id(order.id)
            if retrieved_order:
                print(f"✅ Retrieved order: {retrieved_order.symbol}")
            
            # Test order update
            success = await order_repo.update_order_status(
                order.id, 
                "filled",
                Decimal("0.001"),
                Decimal("50000.0"),
                Decimal("50.0")
            )
            print(f"✅ Updated order status: {success}")
            
            # Test order statistics
            stats = await order_repo.get_order_statistics(user_id, 30)
            print(f"✅ Order statistics: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Repository test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_portfolio_manager_integration():
    """Test database portfolio manager"""
    print("\n💼 Testing Database Portfolio Manager...")
    
    try:
        from core.database_portfolio_manager import DatabasePortfolioManager
        from core.config import get_settings
        
        settings = get_settings()
        user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
        
        # Create portfolio manager
        portfolio_manager = DatabasePortfolioManager(settings, user_id)
        await portfolio_manager.initialize()
        
        print("✅ Database portfolio manager initialized")
        
        # Test opening a position
        position = await portfolio_manager.open_position(
            symbol="BTCUSDT",
            side="long",
            quantity=0.001,
            entry_price=50000.0,
            strategy="test_strategy",
            commission=50.0
        )
        
        print(f"✅ Opened position: {position.symbol} {position.side}")
        
        # Test updating position price
        await portfolio_manager.update_position_prices({"BTCUSDT": 51000.0})
        print("✅ Updated position price")
        
        # Test portfolio summary
        summary = await portfolio_manager.get_portfolio_summary()
        print(f"✅ Portfolio summary:")
        print(f"   - Total value: ${summary['total_value']:.2f}")
        print(f"   - Cash balance: ${summary['cash_balance']:.2f}")
        print(f"   - Positions: {summary['positions_count']}")
        print(f"   - Unrealized P&L: ${summary['unrealized_pnl']:.2f}")
        
        # Test closing position
        trade = await portfolio_manager.close_position("BTCUSDT", 51000.0, 50.0)
        if trade:
            print(f"✅ Closed position: P&L ${trade.pnl:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Portfolio manager integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_order_manager_integration():
    """Test database-integrated order manager"""
    print("\n📋 Testing Database Order Manager Integration...")
    
    try:
        from core.order_manager import OrderManager, Order, OrderSide, OrderType
        from core.config import get_settings
        
        settings = get_settings()
        user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
        
        # Create order manager
        order_manager = OrderManager(settings, user_id)
        await order_manager.initialize()
        
        print("✅ Database order manager initialized")
        print(f"   - Database enabled: {order_manager.enable_database}")
        print(f"   - Paper trading: {order_manager.paper_trading}")
        
        # Test creating and submitting an order
        order = Order(
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=0.001,
            price=50000.0,
            strategy="test_strategy"
        )
        
        order_id = await order_manager.submit_order(order)
        print(f"✅ Submitted order: {order_id}")
        
        # Test order retrieval
        retrieved_order = order_manager.get_order(order_id)
        if retrieved_order:
            print(f"✅ Retrieved order: {retrieved_order.status.value}")
        
        # Test order status
        status = order_manager.get_order_status()
        print(f"✅ Order manager status: {status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Order manager integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_performance_metrics():
    """Test performance metrics calculation"""
    print("\n📈 Testing Performance Metrics...")
    
    try:
        from database.connection import get_database_manager
        from database.repositories import PerformanceRepository
        
        db_manager = await get_database_manager()
        user_id = uuid.UUID("00000000-0000-0000-000000000001")
        
        async with db_manager.get_session() as session:
            perf_repo = PerformanceRepository(session)
            
            # Test creating performance metrics
            metric_data = {
                "user_id": user_id,
                "date": datetime.utcnow(),
                "total_trades": 10,
                "winning_trades": 6,
                "losing_trades": 4,
                "win_rate": Decimal("0.6"),
                "gross_profit": Decimal("1000.0"),
                "gross_loss": Decimal("-400.0"),
                "net_profit": Decimal("600.0"),
                "total_volume": Decimal("50000.0"),
                "total_commission": Decimal("50.0")
            }
            
            metric = await perf_repo.create_performance_metric(metric_data)
            print(f"✅ Created performance metric: {metric.id}")
            
            # Test retrieving metrics
            metrics = await perf_repo.get_performance_history(user_id, limit=10)
            print(f"✅ Retrieved {len(metrics)} performance records")
            
            # Test updating daily performance
            success = await perf_repo.update_daily_performance(
                user_id,
                datetime.utcnow(),
                {"total_trades": 12, "net_profit": Decimal("700.0")}
            )
            print(f"✅ Updated daily performance: {success}")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance metrics test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all database integration tests"""
    print("🚀 Starting Database Integration Tests")
    print("=" * 60)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Database Models", test_database_models),
        ("Database Repositories", test_repositories),
        ("Portfolio Manager Integration", test_portfolio_manager_integration),
        ("Order Manager Integration", test_order_manager_integration),
        ("Performance Metrics", test_performance_metrics),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All database integration tests passed! Database layer is ready.")
        print("\n📋 Next Steps:")
        print("   1. Set up PostgreSQL database")
        print("   2. Configure database credentials in .env")
        print("   3. Run database migrations")
        print("   4. Test with live trading bot")
    else:
        print("⚠️ Some tests failed. Please check the database configuration and implementation.")
    
    return passed == total


if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
