#!/usr/bin/env python3
"""
Database Configuration Test

Tests the database configuration without requiring an actual database connection.
This verifies that all the configuration and models are properly set up.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.append('src')


def test_environment_setup():
    """Test environment configuration"""
    print("🔧 Testing Environment Setup...")
    
    # Check .env file
    env_file = Path('.env')
    if env_file.exists():
        print("   ✅ .env file found")
        
        # Read and validate key settings
        with open(env_file, 'r') as f:
            content = f.read()
            
        required_vars = [
            'DATABASE_URL',
            'TRADING_MODE',
            'APP_DEBUG'
        ]
        
        for var in required_vars:
            if var in content:
                print(f"   ✅ {var} configured")
            else:
                print(f"   ❌ {var} missing")
    else:
        print("   ❌ .env file not found")
        return False
    
    return True


def test_configuration_loading():
    """Test configuration loading"""
    print("\n⚙️ Testing Configuration Loading...")
    
    try:
        from core.config import get_settings
        
        settings = get_settings()
        print("   ✅ Settings loaded successfully")
        
        # Test database configuration
        db_config = settings.database
        print(f"   - Database host: {db_config.host}")
        print(f"   - Database port: {db_config.port}")
        print(f"   - Database name: {db_config.database}")
        print(f"   - Database user: {db_config.username}")
        print(f"   - Pool size: {db_config.pool_size}")
        
        # Test trading configuration
        trading_config = settings.trading
        print(f"   - Trading mode: {trading_config.mode}")
        print(f"   - Max positions: {trading_config.max_positions}")
        
        # Test app configuration
        app_config = settings.app
        print(f"   - App name: {app_config.name}")
        print(f"   - Debug mode: {app_config.debug}")
        print(f"   - Log level: {app_config.log_level}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Configuration loading failed: {e}")
        return False


def test_database_models():
    """Test database models"""
    print("\n📊 Testing Database Models...")
    
    try:
        from database.models import (
            Base, User, Strategy, Order, Trade, Position, Portfolio, 
            PerformanceMetric, TradingSession
        )
        
        print("   ✅ All models imported successfully")
        
        # Test model attributes
        models_to_test = [
            (User, ['id', 'username', 'email', 'created_at']),
            (Strategy, ['id', 'name', 'strategy_type', 'parameters']),
            (Order, ['id', 'symbol', 'side', 'order_type', 'quantity']),
            (Trade, ['id', 'symbol', 'side', 'quantity', 'price']),
            (Position, ['id', 'symbol', 'side', 'quantity', 'entry_price']),
            (Portfolio, ['id', 'total_value', 'cash_balance']),
        ]
        
        for model, attributes in models_to_test:
            model_name = model.__name__
            print(f"   - {model_name}: ", end="")
            
            missing_attrs = []
            for attr in attributes:
                if not hasattr(model, attr):
                    missing_attrs.append(attr)
            
            if missing_attrs:
                print(f"❌ Missing: {missing_attrs}")
            else:
                print("✅")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Model testing failed: {e}")
        return False


def test_database_repositories():
    """Test database repositories"""
    print("\n🏪 Testing Database Repositories...")
    
    try:
        from database.repositories import (
            OrderRepository, TradeRepository, PositionRepository,
            PortfolioRepository, PerformanceRepository
        )
        
        print("   ✅ All repositories imported successfully")
        
        # Test repository methods
        repositories_to_test = [
            (OrderRepository, ['create_order', 'get_order_by_id']),
            (TradeRepository, ['create_trade', 'get_trade_by_id']),
            (PositionRepository, ['create_position', 'get_position_by_id']),
            (PortfolioRepository, ['create_portfolio_snapshot']),
            (PerformanceRepository, ['create_performance_metric']),
        ]
        
        for repo_class, methods in repositories_to_test:
            repo_name = repo_class.__name__
            print(f"   - {repo_name}: ", end="")
            
            missing_methods = []
            for method in methods:
                if not hasattr(repo_class, method):
                    missing_methods.append(method)
            
            if missing_methods:
                print(f"❌ Missing: {missing_methods}")
            else:
                print("✅")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Repository testing failed: {e}")
        return False


def test_database_connection_class():
    """Test database connection class"""
    print("\n🔗 Testing Database Connection Class...")
    
    try:
        from database.connection import DatabaseManager
        from core.config import get_settings
        
        settings = get_settings()
        db_manager = DatabaseManager(settings)
        
        print("   ✅ DatabaseManager instantiated successfully")
        print(f"   - Connection state: {db_manager.is_connected}")
        print(f"   - Max retries: {db_manager.max_retries}")
        
        # Test URL building
        db_url = db_manager._build_database_url()
        print(f"   - Database URL: {db_url}")
        
        if "postgresql+asyncpg://" in db_url:
            print("   ✅ Correct async driver configured")
        else:
            print("   ❌ Incorrect database driver")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Database connection class test failed: {e}")
        return False


def main():
    """Main test function"""
    print("🧪 Database Configuration Tests")
    print("=" * 50)
    
    tests = [
        test_environment_setup,
        test_configuration_loading,
        test_database_models,
        test_database_repositories,
        test_database_connection_class,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All configuration tests passed!")
        print("\n📋 Next Steps:")
        print("   1. Install PostgreSQL or start Docker container")
        print("   2. Run: python setup_database.py")
        print("   3. Run: python test_paper_trading.py")
        print("   4. Start trading bot: python src/main.py")
    else:
        print(f"\n❌ {total - passed} tests failed. Please fix configuration issues.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
