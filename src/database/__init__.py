"""
Database Integration Module

This module provides database connectivity and data persistence for the trading bot.
Includes models, connection management, and data access layers.
"""

from .connection import DatabaseManager, get_database_manager
from .models import (
    Base, User, Strategy, Order, Trade, Position, Portfolio, 
    PerformanceMetric, TradingSession
)
from .repositories import (
    OrderRepository, TradeRepository, PositionRepository,
    PortfolioRepository, PerformanceRepository
)

__all__ = [
    "DatabaseManager",
    "get_database_manager",
    "Base",
    "User",
    "Strategy", 
    "Order",
    "Trade",
    "Position",
    "Portfolio",
    "PerformanceMetric",
    "TradingSession",
    "OrderRepository",
    "TradeRepository", 
    "PositionRepository",
    "PortfolioRepository",
    "PerformanceRepository"
]
