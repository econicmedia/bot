"""
Unit tests for trading engine
"""

import pytest
from src.core.engine import TradingEngine, EngineStatus
from src.core.config import get_settings


@pytest.fixture
def trading_engine():
    """Trading engine fixture"""
    settings = get_settings()
    return TradingEngine(settings)


@pytest.mark.asyncio
async def test_engine_initialization(trading_engine):
    """Test engine initialization"""
    assert trading_engine.status == EngineStatus.STOPPED
    
    await trading_engine.initialize()
    assert trading_engine.status == EngineStatus.STOPPED  # Still stopped until started


@pytest.mark.asyncio
async def test_engine_start_stop(trading_engine):
    """Test engine start and stop"""
    await trading_engine.initialize()
    
    # Test start
    await trading_engine.start()
    assert trading_engine.status == EngineStatus.RUNNING
    assert trading_engine.is_running()
    assert trading_engine.start_time is not None
    
    # Test stop
    await trading_engine.stop()
    assert trading_engine.status == EngineStatus.STOPPED
    assert not trading_engine.is_running()


@pytest.mark.asyncio
async def test_engine_status(trading_engine):
    """Test engine status reporting"""
    await trading_engine.initialize()
    
    status = await trading_engine.get_status()
    assert isinstance(status, dict)
    assert "status" in status
    assert "mode" in status
    assert "uptime" in status
    assert "components" in status


@pytest.mark.asyncio
async def test_engine_heartbeat(trading_engine):
    """Test engine heartbeat"""
    await trading_engine.initialize()
    await trading_engine.start()
    
    initial_heartbeat = trading_engine.last_heartbeat
    await trading_engine.heartbeat()
    
    assert trading_engine.last_heartbeat > initial_heartbeat
    
    await trading_engine.stop()
