#!/usr/bin/env python3
"""
Simple test script to verify core components work
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.config import get_settings
from src.core.strategy_manager import StrategyManager
from src.core.risk_manager import RiskManager
from src.core.order_manager import OrderManager
from src.core.data_manager import DataManager
from src.core.portfolio_manager import PortfolioManager


async def test_core_components():
    """Test core components initialization"""
    print("Testing AI Trading Bot Core Components...")
    
    try:
        # Get settings
        print("1. Loading settings...")
        settings = get_settings()
        print(f"   ✓ Settings loaded (mode: {settings.trading.mode})")
        
        # Test StrategyManager
        print("2. Testing StrategyManager...")
        strategy_manager = StrategyManager(settings)
        print("   ✓ StrategyManager created")
        
        # Test RiskManager
        print("3. Testing RiskManager...")
        risk_manager = RiskManager(settings)
        await risk_manager.initialize()
        print("   ✓ RiskManager initialized")
        
        # Test OrderManager
        print("4. Testing OrderManager...")
        order_manager = OrderManager(settings)
        await order_manager.initialize()
        print("   ✓ OrderManager initialized")
        
        # Test DataManager
        print("5. Testing DataManager...")
        data_manager = DataManager(settings)
        await data_manager.initialize()
        print("   ✓ DataManager initialized")
        
        # Test PortfolioManager
        print("6. Testing PortfolioManager...")
        portfolio_manager = PortfolioManager(settings)
        await portfolio_manager.initialize()
        print("   ✓ PortfolioManager initialized")
        
        # Test basic functionality
        print("7. Testing basic functionality...")
        
        # Test risk calculation
        position_size, details = risk_manager.calculate_position_size(
            symbol="BTCUSDT",
            entry_price=50000.0,
            stop_loss_price=49000.0
        )
        print(f"   ✓ Position size calculated: {position_size:.2f}")
        
        # Test portfolio status
        portfolio_status = portfolio_manager.get_performance_summary()
        print(f"   ✓ Portfolio value: ${portfolio_status['current_value']:,.2f}")
        
        # Test order manager status
        order_status = order_manager.get_order_status()
        print(f"   ✓ Order manager status: {order_status['paper_trading']}")
        
        # Test data manager status
        data_status = data_manager.get_data_status()
        print(f"   ✓ Data manager running: {data_status['is_running']}")
        
        print("\n🎉 All core components working correctly!")
        print("\nNext steps:")
        print("- Install remaining dependencies from requirements.txt")
        print("- Run the full application with: python -m src.main")
        print("- Access the API at: http://localhost:8000")
        
        # Cleanup
        await data_manager.stop()
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing components: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_core_components())
    sys.exit(0 if success else 1)
