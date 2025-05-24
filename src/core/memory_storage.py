"""
In-Memory Data Storage for Immediate Dashboard Functionality

This module provides in-memory storage for trading data when PostgreSQL is not available.
Perfect for immediate testing and demonstration of the web dashboard.
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from decimal import Decimal
import random
import json

from .logger import get_trading_logger


@dataclass
class MemoryPosition:
    """In-memory position representation"""
    symbol: str
    side: str  # "long" or "short"
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    margin_used: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class MemoryTrade:
    """In-memory trade representation"""
    trade_id: str
    order_id: str
    symbol: str
    side: str
    quantity: float
    price: float
    commission: float
    timestamp: datetime
    strategy: Optional[str] = None
    pnl: float = 0.0


@dataclass
class MemoryOrder:
    """In-memory order representation"""
    order_id: str
    symbol: str
    side: str
    quantity: float
    price: Optional[float]
    order_type: str
    status: str
    created_at: datetime
    updated_at: datetime
    filled_quantity: float = 0.0


@dataclass
class PortfolioSnapshot:
    """Portfolio state snapshot"""
    timestamp: datetime
    total_value: float
    cash_balance: float
    positions_value: float
    unrealized_pnl: float
    realized_pnl: float
    daily_pnl: float


class MemoryDataManager:
    """
    In-memory data manager for immediate dashboard functionality

    Provides all trading data storage without requiring external databases.
    Perfect for demonstration and immediate testing.
    """

    def __init__(self):
        self.logger = get_trading_logger("MemoryDataManager")

        # Core data storage
        self.positions: Dict[str, MemoryPosition] = {}
        self.trades: List[MemoryTrade] = []
        self.orders: Dict[str, MemoryOrder] = {}
        self.portfolio_history: List[PortfolioSnapshot] = []

        # Portfolio state
        self.cash_balance = 8500.0  # Starting with $8,500 cash (some invested)
        self.initial_balance = 10000.0

        # Strategy performance tracking
        self.strategy_metrics: Dict[str, Dict[str, Any]] = {
            "ICT": {
                "total_trades": 45,
                "winning_trades": 29,
                "losing_trades": 16,
                "total_return": 0.156,
                "sharpe_ratio": 1.23,
                "max_drawdown": 0.087,
                "win_rate": 0.644,
                "avg_win": 125.50,
                "avg_loss": -78.30,
                "profit_factor": 2.34,
                "enabled": True
            },
            "SMC": {
                "total_trades": 38,
                "winning_trades": 24,
                "losing_trades": 14,
                "total_return": 0.134,
                "sharpe_ratio": 1.15,
                "max_drawdown": 0.092,
                "win_rate": 0.632,
                "avg_win": 110.75,
                "avg_loss": -82.15,
                "profit_factor": 2.12,
                "enabled": True
            },
            "Scalping": {
                "total_trades": 127,
                "winning_trades": 78,
                "losing_trades": 49,
                "total_return": 0.089,
                "sharpe_ratio": 0.98,
                "max_drawdown": 0.045,
                "win_rate": 0.614,
                "avg_win": 45.20,
                "avg_loss": -38.90,
                "profit_factor": 1.87,
                "enabled": False
            }
        }

        # Market data simulation
        self.market_prices: Dict[str, float] = {
            "BTCUSDT": 43250.50,
            "ETHUSDT": 2580.75,
            "ADAUSDT": 0.485,
            "SOLUSDT": 98.45,
            "DOTUSDT": 7.23
        }

        # Initialize with some demo data
        self._initialize_demo_data()

        # Background tasks will be started when needed
        self._background_tasks_started = False

    def _initialize_demo_data(self):
        """Initialize with demonstration data"""
        self.logger.info("Initializing demo trading data...")

        # Clear existing data
        self.positions.clear()
        self.trades.clear()

        # Reset portfolio state
        self.cash_balance = 8500.0

        # Create some demo positions with current market prices
        self._create_demo_position("BTCUSDT", "long", 0.25, 42800.0)
        self._create_demo_position("ETHUSDT", "long", 2.5, 2520.0)
        self._create_demo_position("SOLUSDT", "short", 10.0, 102.30)

        # Create some demo trades
        self._create_demo_trades()

        # Create portfolio history
        self._create_portfolio_history()

        self.logger.info(f"Demo data initialized: {len(self.positions)} positions, {len(self.trades)} trades")

    def _create_demo_position(self, symbol: str, side: str, quantity: float, entry_price: float):
        """Create a demo position"""
        current_price = self.market_prices.get(symbol, entry_price)

        if side == "long":
            unrealized_pnl = (current_price - entry_price) * quantity
        else:
            unrealized_pnl = (entry_price - current_price) * quantity

        position = MemoryPosition(
            symbol=symbol,
            side=side,
            quantity=quantity,
            entry_price=entry_price,
            current_price=current_price,
            unrealized_pnl=unrealized_pnl,
            margin_used=entry_price * quantity * 0.1,  # 10x leverage
            created_at=datetime.utcnow() - timedelta(hours=random.randint(1, 48))
        )

        self.positions[symbol] = position

    def _create_demo_trades(self):
        """Create demo trade history"""
        symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "SOLUSDT", "DOTUSDT"]
        strategies = ["ICT", "SMC", "Scalping"]

        for i in range(50):
            symbol = random.choice(symbols)
            strategy = random.choice(strategies)
            side = random.choice(["buy", "sell"])
            quantity = round(random.uniform(0.1, 5.0), 3)
            price = self.market_prices[symbol] * random.uniform(0.95, 1.05)

            # Calculate PnL (simplified)
            pnl = random.uniform(-200, 300) if random.random() > 0.35 else random.uniform(-100, 50)

            trade = MemoryTrade(
                trade_id=str(uuid.uuid4()),
                order_id=str(uuid.uuid4()),
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                commission=price * quantity * 0.001,  # 0.1% commission
                timestamp=datetime.utcnow() - timedelta(hours=random.randint(1, 168)),  # Last week
                strategy=strategy,
                pnl=pnl
            )

            self.trades.append(trade)

        # Sort trades by timestamp (newest first)
        self.trades.sort(key=lambda x: x.timestamp, reverse=True)

    def _create_portfolio_history(self):
        """Create portfolio performance history"""
        base_time = datetime.utcnow() - timedelta(days=30)

        for i in range(30):
            timestamp = base_time + timedelta(days=i)

            # Simulate portfolio growth with some volatility
            days_passed = i
            base_growth = 1 + (days_passed * 0.005)  # 0.5% daily average growth
            volatility = random.uniform(0.98, 1.02)  # ±2% daily volatility

            total_value = self.initial_balance * base_growth * volatility
            positions_value = total_value * 0.7  # 70% in positions
            cash_balance = total_value * 0.3  # 30% cash

            daily_pnl = (total_value - self.initial_balance) * 0.1 if i > 0 else 0

            snapshot = PortfolioSnapshot(
                timestamp=timestamp,
                total_value=total_value,
                cash_balance=cash_balance,
                positions_value=positions_value,
                unrealized_pnl=positions_value - (self.initial_balance * 0.7),
                realized_pnl=sum(trade.pnl for trade in self.trades if trade.timestamp.date() <= timestamp.date()),
                daily_pnl=daily_pnl
            )

            self.portfolio_history.append(snapshot)

    def start_background_tasks(self):
        """Start background tasks for real-time updates (call from async context)"""
        if not self._background_tasks_started:
            try:
                asyncio.create_task(self._price_update_task())
                asyncio.create_task(self._portfolio_update_task())
                self._background_tasks_started = True
                self.logger.info("Background tasks started successfully")
            except RuntimeError:
                # No event loop running, tasks will be started later
                self.logger.info("No event loop running, background tasks will start later")
                pass

    async def _price_update_task(self):
        """Simulate real-time price updates"""
        while True:
            try:
                for symbol in self.market_prices:
                    # Simulate price movement (±0.5% every 5 seconds)
                    change = random.uniform(-0.005, 0.005)
                    self.market_prices[symbol] *= (1 + change)

                    # Update position current prices and PnL
                    if symbol in self.positions:
                        position = self.positions[symbol]
                        position.current_price = self.market_prices[symbol]

                        if position.side == "long":
                            position.unrealized_pnl = (position.current_price - position.entry_price) * position.quantity
                        else:
                            position.unrealized_pnl = (position.entry_price - position.current_price) * position.quantity

                        position.updated_at = datetime.utcnow()

                await asyncio.sleep(5)  # Update every 5 seconds

            except Exception as e:
                self.logger.error("Error in price update task", e)
                await asyncio.sleep(10)

    async def _portfolio_update_task(self):
        """Update portfolio snapshots periodically"""
        while True:
            try:
                # Create new portfolio snapshot every hour
                total_positions_value = sum(
                    pos.current_price * pos.quantity for pos in self.positions.values()
                )
                total_unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
                total_realized_pnl = sum(trade.pnl for trade in self.trades)

                snapshot = PortfolioSnapshot(
                    timestamp=datetime.utcnow(),
                    total_value=self.cash_balance + total_positions_value,
                    cash_balance=self.cash_balance,
                    positions_value=total_positions_value,
                    unrealized_pnl=total_unrealized_pnl,
                    realized_pnl=total_realized_pnl,
                    daily_pnl=total_unrealized_pnl + total_realized_pnl
                )

                self.portfolio_history.append(snapshot)

                # Keep only last 100 snapshots
                if len(self.portfolio_history) > 100:
                    self.portfolio_history = self.portfolio_history[-100:]

                await asyncio.sleep(3600)  # Update every hour

            except Exception as e:
                self.logger.error("Error in portfolio update task", e)
                await asyncio.sleep(600)  # Retry in 10 minutes


# Global instance for immediate use (will be initialized when needed)
memory_data_manager = None

def get_memory_data_manager():
    """Get or create the global memory data manager"""
    global memory_data_manager
    if memory_data_manager is None:
        memory_data_manager = MemoryDataManager()
    return memory_data_manager
