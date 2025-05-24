"""
Pytest configuration and fixtures
"""

import pytest
import asyncio
from typing import AsyncGenerator
from fastapi.testclient import TestClient

from src.main import app
from src.core.config import get_settings


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings():
    """Test settings fixture"""
    settings = get_settings()
    settings.trading.mode = "paper"
    settings.database.database = "test_trading_db"
    return settings


@pytest.fixture
def client():
    """Test client fixture"""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
async def async_client():
    """Async test client fixture"""
    from httpx import AsyncClient
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_market_data():
    """Sample market data for testing"""
    return {
        "symbol": "BTCUSDT",
        "timestamp": "2024-01-01T00:00:00Z",
        "open": 50000.0,
        "high": 51000.0,
        "low": 49000.0,
        "close": 50500.0,
        "volume": 1000.0
    }


@pytest.fixture
def sample_order():
    """Sample order data for testing"""
    return {
        "symbol": "BTCUSDT",
        "side": "buy",
        "quantity": 0.001,
        "order_type": "market"
    }
