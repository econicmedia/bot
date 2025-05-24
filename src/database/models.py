"""
Database Models

SQLAlchemy models for the trading bot's data persistence layer.
Defines tables for trades, orders, positions, portfolio state, and performance metrics.
"""

import uuid
from datetime import datetime
from typing import Optional
from decimal import Decimal

from sqlalchemy import (
    Column, String, Integer, Numeric, Boolean, DateTime, Text, 
    ForeignKey, UniqueConstraint, Index, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# Base class for all models
Base = declarative_base()


class User(Base):
    """User model for multi-user support"""
    __tablename__ = "users"
    __table_args__ = {"schema": "trading"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    orders = relationship("Order", back_populates="user")
    trades = relationship("Trade", back_populates="user")
    positions = relationship("Position", back_populates="user")
    portfolios = relationship("Portfolio", back_populates="user")


class Strategy(Base):
    """Strategy configuration model"""
    __tablename__ = "strategies"
    __table_args__ = {"schema": "trading"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    strategy_type = Column(String(50), nullable=False)  # ICT, technical_analysis, etc.
    parameters = Column(JSON)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    orders = relationship("Order", back_populates="strategy")
    trades = relationship("Trade", back_populates="strategy")


class Order(Base):
    """Order model for tracking all order lifecycle"""
    __tablename__ = "orders"
    __table_args__ = (
        Index("idx_orders_user_symbol", "user_id", "symbol"),
        Index("idx_orders_status", "status"),
        Index("idx_orders_created_at", "created_at"),
        {"schema": "trading"}
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("trading.users.id"), nullable=False)
    strategy_id = Column(UUID(as_uuid=True), ForeignKey("trading.strategies.id"))
    
    # Order details
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)  # buy, sell
    order_type = Column(String(20), nullable=False)  # market, limit, stop, stop_limit
    quantity = Column(Numeric(20, 8), nullable=False)
    price = Column(Numeric(20, 8))
    stop_price = Column(Numeric(20, 8))
    time_in_force = Column(String(10), default="GTC")
    
    # Order state
    status = Column(String(20), nullable=False, default="pending")
    filled_quantity = Column(Numeric(20, 8), default=0)
    remaining_quantity = Column(Numeric(20, 8))
    average_fill_price = Column(Numeric(20, 8), default=0)
    commission = Column(Numeric(20, 8), default=0)
    
    # Exchange information
    exchange = Column(String(50))
    exchange_order_id = Column(String(100))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    submitted_at = Column(DateTime(timezone=True))
    filled_at = Column(DateTime(timezone=True))
    cancelled_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Error information
    error_message = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="orders")
    strategy = relationship("Strategy", back_populates="orders")
    trades = relationship("Trade", back_populates="order")


class Trade(Base):
    """Trade model for executed trades"""
    __tablename__ = "trades"
    __table_args__ = (
        Index("idx_trades_user_symbol", "user_id", "symbol"),
        Index("idx_trades_executed_at", "executed_at"),
        {"schema": "trading"}
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("trading.users.id"), nullable=False)
    strategy_id = Column(UUID(as_uuid=True), ForeignKey("trading.strategies.id"))
    order_id = Column(UUID(as_uuid=True), ForeignKey("trading.orders.id"))
    
    # Trade details
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)  # buy, sell
    quantity = Column(Numeric(20, 8), nullable=False)
    price = Column(Numeric(20, 8), nullable=False)
    commission = Column(Numeric(20, 8), default=0)
    
    # Exchange information
    exchange = Column(String(50))
    exchange_trade_id = Column(String(100))
    
    # Timestamps
    executed_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="trades")
    strategy = relationship("Strategy", back_populates="trades")
    order = relationship("Order", back_populates="trades")


class Position(Base):
    """Position model for tracking open positions"""
    __tablename__ = "positions"
    __table_args__ = (
        UniqueConstraint("user_id", "symbol", name="uq_user_symbol_position"),
        Index("idx_positions_user", "user_id"),
        {"schema": "trading"}
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("trading.users.id"), nullable=False)
    
    # Position details
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)  # long, short
    quantity = Column(Numeric(20, 8), nullable=False)
    entry_price = Column(Numeric(20, 8), nullable=False)
    current_price = Column(Numeric(20, 8))
    
    # P&L tracking
    unrealized_pnl = Column(Numeric(20, 8), default=0)
    realized_pnl = Column(Numeric(20, 8), default=0)
    commission_paid = Column(Numeric(20, 8), default=0)
    
    # Risk management
    stop_loss = Column(Numeric(20, 8))
    take_profit = Column(Numeric(20, 8))
    
    # Timestamps
    entry_time = Column(DateTime(timezone=True), nullable=False)
    exit_time = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Status
    is_open = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="positions")


class Portfolio(Base):
    """Portfolio model for tracking portfolio state snapshots"""
    __tablename__ = "portfolios"
    __table_args__ = (
        Index("idx_portfolios_user_timestamp", "user_id", "timestamp"),
        {"schema": "trading"}
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("trading.users.id"), nullable=False)
    
    # Portfolio values
    total_value = Column(Numeric(20, 8), nullable=False)
    cash_balance = Column(Numeric(20, 8), nullable=False)
    positions_value = Column(Numeric(20, 8), default=0)
    unrealized_pnl = Column(Numeric(20, 8), default=0)
    realized_pnl = Column(Numeric(20, 8), default=0)
    
    # Performance metrics
    total_return = Column(Numeric(10, 4), default=0)  # Percentage
    daily_return = Column(Numeric(10, 4), default=0)  # Percentage
    max_drawdown = Column(Numeric(10, 4), default=0)  # Percentage
    
    # Timestamp
    timestamp = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="portfolios")


class PerformanceMetric(Base):
    """Performance metrics model for detailed analytics"""
    __tablename__ = "performance_metrics"
    __table_args__ = (
        Index("idx_performance_user_date", "user_id", "date"),
        {"schema": "analytics"}
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("trading.users.id"), nullable=False)
    
    # Date for daily metrics
    date = Column(DateTime(timezone=True), nullable=False)
    
    # Trading metrics
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate = Column(Numeric(5, 4), default=0)  # Percentage as decimal
    
    # P&L metrics
    gross_profit = Column(Numeric(20, 8), default=0)
    gross_loss = Column(Numeric(20, 8), default=0)
    net_profit = Column(Numeric(20, 8), default=0)
    profit_factor = Column(Numeric(10, 4), default=0)
    
    # Risk metrics
    max_drawdown = Column(Numeric(10, 4), default=0)
    sharpe_ratio = Column(Numeric(10, 4), default=0)
    sortino_ratio = Column(Numeric(10, 4), default=0)
    
    # Volume metrics
    total_volume = Column(Numeric(20, 8), default=0)
    total_commission = Column(Numeric(20, 8), default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class TradingSession(Base):
    """Trading session model for tracking bot sessions"""
    __tablename__ = "trading_sessions"
    __table_args__ = (
        Index("idx_sessions_start_time", "start_time"),
        {"schema": "logs"}
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Session details
    session_name = Column(String(100))
    trading_mode = Column(String(20), nullable=False)  # paper, live
    strategies_used = Column(JSON)  # List of strategy names
    
    # Session metrics
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)
    
    # Performance summary
    starting_balance = Column(Numeric(20, 8))
    ending_balance = Column(Numeric(20, 8))
    total_trades = Column(Integer, default=0)
    total_pnl = Column(Numeric(20, 8), default=0)
    
    # Status
    status = Column(String(20), default="active")  # active, completed, error
    error_message = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
