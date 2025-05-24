"""
Unit tests for StrategyManager
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock

from src.core.strategy_manager import StrategyManager, BaseStrategy, StrategyType
from src.core.config import get_settings


class MockStrategy(BaseStrategy):
    """Mock strategy for testing"""
    
    async def initialize(self) -> None:
        """Initialize mock strategy"""
        pass
    
    async def analyze_market(self, market_data) -> dict:
        """Mock market analysis"""
        return {
            "action": "buy",
            "symbol": "BTCUSDT",
            "price": 50000.0,
            "quantity": 1.0
        }
    
    async def cleanup(self) -> None:
        """Cleanup mock strategy"""
        pass


@pytest.fixture
def settings():
    """Get test settings"""
    return get_settings()


@pytest.fixture
def strategy_manager(settings):
    """Create strategy manager instance"""
    return StrategyManager(settings)


@pytest.mark.asyncio
async def test_strategy_manager_initialization(strategy_manager):
    """Test strategy manager initialization"""
    assert strategy_manager.strategies == {}
    assert strategy_manager.active_strategies == []
    assert strategy_manager.strategy_classes == {}


@pytest.mark.asyncio
async def test_register_strategy_class(strategy_manager):
    """Test strategy class registration"""
    strategy_manager.register_strategy_class(StrategyType.ICT, MockStrategy)
    
    assert StrategyType.ICT in strategy_manager.strategy_classes
    assert strategy_manager.strategy_classes[StrategyType.ICT] == MockStrategy


@pytest.mark.asyncio
async def test_create_strategy(strategy_manager):
    """Test strategy creation"""
    strategy_manager.register_strategy_class(StrategyType.ICT, MockStrategy)
    
    strategy = await strategy_manager.create_strategy(StrategyType.ICT, "test_strategy")
    
    assert strategy.name == "test_strategy"
    assert "test_strategy" in strategy_manager.strategies
    assert isinstance(strategy, MockStrategy)


@pytest.mark.asyncio
async def test_start_stop_strategy(strategy_manager):
    """Test strategy start and stop"""
    strategy_manager.register_strategy_class(StrategyType.ICT, MockStrategy)
    
    strategy = await strategy_manager.create_strategy(StrategyType.ICT, "test_strategy")
    
    # Start strategy
    await strategy_manager.start_strategy("test_strategy")
    assert "test_strategy" in strategy_manager.active_strategies
    
    # Stop strategy
    await strategy_manager.stop_strategy("test_strategy")
    assert "test_strategy" not in strategy_manager.active_strategies


@pytest.mark.asyncio
async def test_process_market_data(strategy_manager):
    """Test market data processing"""
    strategy_manager.register_strategy_class(StrategyType.ICT, MockStrategy)
    
    strategy = await strategy_manager.create_strategy(StrategyType.ICT, "test_strategy")
    await strategy_manager.start_strategy("test_strategy")
    
    market_data = {
        "symbol": "BTCUSDT",
        "price": 50000.0,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    signals = await strategy_manager.process_market_data(market_data)
    
    assert len(signals) == 1
    assert signals[0]["action"] == "buy"
    assert signals[0]["strategy"] == "test_strategy"


@pytest.mark.asyncio
async def test_get_strategy_status(strategy_manager):
    """Test getting strategy status"""
    strategy_manager.register_strategy_class(StrategyType.ICT, MockStrategy)
    
    strategy = await strategy_manager.create_strategy(StrategyType.ICT, "test_strategy")
    
    status = strategy_manager.get_strategy_status("test_strategy")
    
    assert status is not None
    assert status["name"] == "test_strategy"
    assert "performance" in status


@pytest.mark.asyncio
async def test_get_all_strategies_status(strategy_manager):
    """Test getting all strategies status"""
    strategy_manager.register_strategy_class(StrategyType.ICT, MockStrategy)
    
    await strategy_manager.create_strategy(StrategyType.ICT, "strategy1")
    await strategy_manager.create_strategy(StrategyType.ICT, "strategy2")
    
    all_status = strategy_manager.get_all_strategies_status()
    
    assert len(all_status) == 2
    assert all_status[0]["name"] in ["strategy1", "strategy2"]
    assert all_status[1]["name"] in ["strategy1", "strategy2"]
