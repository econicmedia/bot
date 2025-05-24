"""
Exchange Integrations Module

This module provides integrations with various cryptocurrency exchanges
and trading platforms including:
- Binance (Spot & Futures)
- Coinbase Pro
- TradingView webhooks
- Fusion Trading platform
"""

from .base import BaseExchange, ExchangeError, ConnectionError, AuthenticationError
from .binance.client import BinanceExchange
# from .coinbase import CoinbaseExchange  # TODO: Implement Coinbase integration

__all__ = [
    "BaseExchange",
    "ExchangeError",
    "ConnectionError",
    "AuthenticationError",
    "BinanceExchange",
    # "CoinbaseExchange"  # TODO: Implement Coinbase integration
]
