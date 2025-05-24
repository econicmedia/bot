"""
Unit tests for configuration module
"""

import pytest
from src.core.config import get_settings, Settings


def test_get_settings():
    """Test settings loading"""
    settings = get_settings()
    assert isinstance(settings, Settings)
    assert settings.app.name == "AI Trading Bot"
    assert settings.app.version == "1.0.0"


def test_trading_config():
    """Test trading configuration"""
    settings = get_settings()
    assert settings.trading.mode in ["paper", "live"]
    assert settings.trading.max_positions > 0
    assert settings.trading.risk.max_position_size > 0
    assert settings.trading.risk.max_daily_loss > 0


def test_database_config():
    """Test database configuration"""
    settings = get_settings()
    assert settings.database.host
    assert settings.database.port > 0
    assert settings.database.database
    assert settings.database.username


def test_api_config():
    """Test API configuration"""
    settings = get_settings()
    assert settings.api.host
    assert settings.api.port > 0
    assert isinstance(settings.api.cors_origins, list)
