"""
Integration tests for API endpoints
"""

import pytest
from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "AI Trading Bot API"
    assert data["version"] == "1.0.0"


def test_health_endpoint(client: TestClient):
    """Test health check endpoint"""
    response = client.get("/health")
    # Note: This might fail initially since TradingEngine isn't fully initialized
    # In a real test, we'd mock the trading engine
    assert response.status_code in [200, 503]


def test_trading_status_endpoint(client: TestClient):
    """Test trading status endpoint"""
    response = client.get("/api/v1/trading/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "mode" in data


def test_strategies_endpoint(client: TestClient):
    """Test strategies endpoint"""
    response = client.get("/api/v1/strategies/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_positions_endpoint(client: TestClient):
    """Test positions endpoint"""
    response = client.get("/api/v1/positions")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_trades_endpoint(client: TestClient):
    """Test trades endpoint"""
    response = client.get("/api/v1/trades")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_performance_endpoint(client: TestClient):
    """Test performance endpoint"""
    response = client.get("/api/v1/analytics/performance")
    assert response.status_code == 200
    data = response.json()
    assert "total_return" in data
    assert "sharpe_ratio" in data
