"""
Binance Exchange Integration

This module provides integration with Binance exchange including:
- Spot trading
- Futures trading (planned)
- Real-time market data via WebSocket
- Order management
- Account information
"""

from .client import BinanceExchange
from .websocket import BinanceWebSocket

__all__ = [
    "BinanceExchange",
    "BinanceWebSocket"
]
