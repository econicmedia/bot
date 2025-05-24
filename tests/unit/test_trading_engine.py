"""
Unit tests for TradingEngine
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from src.core.engine import TradingEngine, EngineStatus
from src.core.config import get_settings


@pytest.fixture
def settings():
    """Get test settings"""
    return get_settings()


@pytest.fixture
def trading_engine(settings):
    """Create trading engine instance"""
    return TradingEngine(settings)


@pytest.mark.asyncio
async def test_trading_engine_initialization(trading_engine):
    """Test trading engine initialization"""
    assert trading_engine.status == EngineStatus.STOPPED
    assert trading_engine.strategy_manager is None
    assert trading_engine.risk_manager is None
    assert trading_engine.order_manager is None
    assert trading_engine.data_manager is None
    assert trading_engine.portfolio_manager is None


@pytest.mark.asyncio
async def test_trading_engine_initialize_components(trading_engine):
    """Test trading engine component initialization"""
    await trading_engine.initialize()
    
    # Check that all components are initialized
    assert trading_engine.strategy_manager is not None
    assert trading_engine.risk_manager is not None
    assert trading_engine.order_manager is not None
    assert trading_engine.data_manager is not None
    assert trading_engine.portfolio_manager is not None


@pytest.mark.asyncio
async def test_trading_engine_start_stop(trading_engine):
    """Test trading engine start and stop"""
    # Initialize first
    await trading_engine.initialize()
    
    # Start engine
    await trading_engine.start()
    assert trading_engine.status == EngineStatus.RUNNING
    assert trading_engine.is_running()
    assert trading_engine.start_time is not None
    
    # Stop engine
    await trading_engine.stop()
    assert trading_engine.status == EngineStatus.STOPPED
    assert not trading_engine.is_running()


@pytest.mark.asyncio
async def test_trading_engine_get_status(trading_engine):
    """Test getting trading engine status"""
    await trading_engine.initialize()
    await trading_engine.start()
    
    status = await trading_engine.get_status()
    
    assert status["status"] == EngineStatus.RUNNING.value
    assert status["mode"] == trading_engine.settings.trading.mode
    assert status["uptime"] >= 0
    assert status["start_time"] is not None
    assert "components" in status
    
    # Check component status
    components = status["components"]
    assert components["strategy_manager"] == "initialized"
    assert components["risk_manager"] == "initialized"
    assert components["order_manager"] == "initialized"
    assert components["data_manager"] == "initialized"
    assert components["portfolio_manager"] == "initialized"


@pytest.mark.asyncio
async def test_trading_engine_heartbeat(trading_engine):
    """Test trading engine heartbeat"""
    await trading_engine.initialize()
    
    initial_heartbeat = trading_engine.last_heartbeat
    await trading_engine.heartbeat()
    
    assert trading_engine.last_heartbeat > initial_heartbeat


@pytest.mark.asyncio
async def test_trading_engine_health_check(trading_engine):
    """Test trading engine health check"""
    await trading_engine.initialize()
    
    # Engine not running - should not be healthy
    assert not trading_engine.is_healthy()
    
    # Start engine
    await trading_engine.start()
    await trading_engine.heartbeat()
    
    # Should be healthy now
    assert trading_engine.is_healthy()


@pytest.mark.asyncio
async def test_trading_engine_error_handling(settings):
    """Test trading engine error handling"""
    # Mock a component that fails to initialize
    with patch('src.core.engine.RiskManager') as mock_risk_manager:
        mock_risk_manager.return_value.initialize = AsyncMock(side_effect=Exception("Test error"))
        
        engine = TradingEngine(settings)
        
        with pytest.raises(Exception):
            await engine.initialize()
        
        assert engine.status == EngineStatus.ERROR


@pytest.mark.asyncio
async def test_trading_engine_paper_mode(settings):
    """Test trading engine in paper trading mode"""
    # Ensure we're in paper mode
    settings.trading.mode = "paper"
    
    engine = TradingEngine(settings)
    await engine.initialize()
    
    # In paper mode, engine should initialize but not auto-start
    assert engine.status == EngineStatus.STOPPED
    
    # Manual start should work
    await engine.start()
    assert engine.status == EngineStatus.RUNNING
