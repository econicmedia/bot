"""
Portfolio Manager - Tracks portfolio state and performance
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict
import math

from .config import Settings
from .logger import get_trading_logger


class Position:
    """Represents a trading position"""

    def __init__(
        self,
        symbol: str,
        side: str,
        quantity: float,
        entry_price: float,
        entry_time: datetime,
        strategy: Optional[str] = None
    ):
        self.symbol = symbol
        self.side = side  # "long" or "short"
        self.quantity = quantity
        self.entry_price = entry_price
        self.entry_time = entry_time
        self.strategy = strategy

        # Current state
        self.current_price = entry_price
        self.unrealized_pnl = 0.0
        self.realized_pnl = 0.0
        self.commission_paid = 0.0

        # Risk management
        self.stop_loss: Optional[float] = None
        self.take_profit: Optional[float] = None

        # Tracking
        self.last_updated = entry_time
        self.max_unrealized_pnl = 0.0
        self.min_unrealized_pnl = 0.0

    def update_price(self, new_price: float, timestamp: datetime) -> None:
        """Update position with new market price"""
        self.current_price = new_price
        self.last_updated = timestamp

        # Calculate unrealized P&L
        if self.side == "long":
            self.unrealized_pnl = (new_price - self.entry_price) * self.quantity
        else:  # short
            self.unrealized_pnl = (self.entry_price - new_price) * self.quantity

        # Track max/min unrealized P&L
        self.max_unrealized_pnl = max(self.max_unrealized_pnl, self.unrealized_pnl)
        self.min_unrealized_pnl = min(self.min_unrealized_pnl, self.unrealized_pnl)

    def get_market_value(self) -> float:
        """Get current market value of position"""
        return self.current_price * self.quantity

    def get_total_pnl(self) -> float:
        """Get total P&L (realized + unrealized)"""
        return self.realized_pnl + self.unrealized_pnl

    def to_dict(self) -> Dict[str, Any]:
        """Convert position to dictionary"""
        return {
            "symbol": self.symbol,
            "side": self.side,
            "quantity": self.quantity,
            "entry_price": self.entry_price,
            "current_price": self.current_price,
            "entry_time": self.entry_time.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "strategy": self.strategy,
            "unrealized_pnl": self.unrealized_pnl,
            "realized_pnl": self.realized_pnl,
            "total_pnl": self.get_total_pnl(),
            "market_value": self.get_market_value(),
            "commission_paid": self.commission_paid,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "max_unrealized_pnl": self.max_unrealized_pnl,
            "min_unrealized_pnl": self.min_unrealized_pnl
        }


class Trade:
    """Represents a completed trade"""

    def __init__(
        self,
        symbol: str,
        side: str,
        quantity: float,
        entry_price: float,
        exit_price: float,
        entry_time: datetime,
        exit_time: datetime,
        strategy: Optional[str] = None,
        commission: float = 0.0
    ):
        self.symbol = symbol
        self.side = side
        self.quantity = quantity
        self.entry_price = entry_price
        self.exit_price = exit_price
        self.entry_time = entry_time
        self.exit_time = exit_time
        self.strategy = strategy
        self.commission = commission

        # Calculate P&L
        if side == "long":
            self.pnl = (exit_price - entry_price) * quantity - commission
        else:  # short
            self.pnl = (entry_price - exit_price) * quantity - commission

        self.duration = exit_time - entry_time
        self.return_pct = (self.pnl / (entry_price * quantity)) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert trade to dictionary"""
        return {
            "symbol": self.symbol,
            "side": self.side,
            "quantity": self.quantity,
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "entry_time": self.entry_time.isoformat(),
            "exit_time": self.exit_time.isoformat(),
            "strategy": self.strategy,
            "pnl": self.pnl,
            "commission": self.commission,
            "duration_seconds": self.duration.total_seconds(),
            "return_pct": self.return_pct
        }


class PortfolioManager:
    """Manages portfolio state and performance tracking"""

    def __init__(self, settings: Settings):
        """Initialize portfolio manager"""
        self.settings = settings
        self.logger = get_trading_logger("PortfolioManager")

        # Portfolio state
        self.initial_capital = 100000.0  # Default starting capital
        self.cash_balance = self.initial_capital
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []

        # Performance tracking
        self.total_pnl = 0.0
        self.total_commission = 0.0
        self.peak_portfolio_value = self.initial_capital
        self.max_drawdown = 0.0
        self.daily_pnl_history: List[Dict[str, Any]] = []

        # Statistics
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.largest_win = 0.0
        self.largest_loss = 0.0

        # Risk metrics
        self.var_95 = 0.0  # 95% Value at Risk
        self.sharpe_ratio = 0.0
        self.sortino_ratio = 0.0

        self.logger.logger.info("Portfolio manager initialized")

    async def start(self) -> None:
        """Start the portfolio manager"""
        await self.initialize()

        # Start background tasks
        asyncio.create_task(self._daily_performance_task())

        self.logger.logger.info("Portfolio manager started")

    async def initialize(self) -> None:
        """Initialize portfolio manager"""
        try:
            # Load historical data if available
            await self._load_portfolio_state()

            # Start performance tracking task
            asyncio.create_task(self._daily_performance_task())

            self.logger.logger.info("Portfolio manager initialized successfully")

        except Exception as e:
            self.logger.error("Failed to initialize portfolio manager", e)
            raise

    async def _load_portfolio_state(self) -> None:
        """Load portfolio state from database"""
        # TODO: Load from database
        # For now, use default values
        pass

    async def _daily_performance_task(self) -> None:
        """Daily performance tracking task"""
        last_date = datetime.utcnow().date()

        while True:
            current_date = datetime.utcnow().date()

            if current_date > last_date:
                # New day - record daily performance
                daily_pnl = self._calculate_daily_pnl()
                portfolio_value = self.get_portfolio_value()

                daily_record = {
                    "date": last_date.isoformat(),
                    "portfolio_value": portfolio_value,
                    "daily_pnl": daily_pnl,
                    "cash_balance": self.cash_balance,
                    "positions_count": len(self.positions),
                    "total_trades": self.total_trades
                }

                self.daily_pnl_history.append(daily_record)

                # Keep only last 365 days
                if len(self.daily_pnl_history) > 365:
                    self.daily_pnl_history.pop(0)

                # Update performance metrics
                self._update_performance_metrics()

                last_date = current_date

            await asyncio.sleep(3600)  # Check every hour

    def _calculate_daily_pnl(self) -> float:
        """Calculate daily P&L"""
        # TODO: Implement proper daily P&L calculation
        # For now, return current unrealized P&L
        return sum(pos.unrealized_pnl for pos in self.positions.values())

    def open_position(
        self,
        symbol: str,
        side: str,
        quantity: float,
        entry_price: float,
        strategy: Optional[str] = None,
        commission: float = 0.0
    ) -> Position:
        """Open a new position"""
        if symbol in self.positions:
            raise ValueError(f"Position already exists for {symbol}")

        position = Position(
            symbol=symbol,
            side=side,
            quantity=quantity,
            entry_price=entry_price,
            entry_time=datetime.utcnow(),
            strategy=strategy
        )

        position.commission_paid = commission
        self.positions[symbol] = position

        # Update cash balance
        position_value = entry_price * quantity
        if side == "long":
            self.cash_balance -= position_value + commission
        else:  # short
            self.cash_balance += position_value - commission

        self.total_commission += commission

        self.logger.logger.info(f"Opened {side} position: {symbol} {quantity}@{entry_price}")
        return position

    def close_position(
        self,
        symbol: str,
        exit_price: float,
        commission: float = 0.0
    ) -> Optional[Trade]:
        """Close an existing position"""
        if symbol not in self.positions:
            self.logger.logger.warning(f"No position found for {symbol}")
            return None

        position = self.positions[symbol]
        exit_time = datetime.utcnow()

        # Create trade record
        trade = Trade(
            symbol=symbol,
            side=position.side,
            quantity=position.quantity,
            entry_price=position.entry_price,
            exit_price=exit_price,
            entry_time=position.entry_time,
            exit_time=exit_time,
            strategy=position.strategy,
            commission=position.commission_paid + commission
        )

        self.trades.append(trade)

        # Update portfolio metrics
        self.total_pnl += trade.pnl
        self.total_commission += commission
        self.total_trades += 1

        if trade.pnl > 0:
            self.winning_trades += 1
            self.largest_win = max(self.largest_win, trade.pnl)
        else:
            self.losing_trades += 1
            self.largest_loss = min(self.largest_loss, trade.pnl)

        # Update cash balance
        position_value = exit_price * position.quantity
        if position.side == "long":
            self.cash_balance += position_value - commission
        else:  # short
            self.cash_balance -= position_value + commission

        # Remove position
        del self.positions[symbol]

        self.logger.logger.info(f"Closed position: {symbol} P&L: {trade.pnl:.2f}")
        return trade

    def update_position_prices(self, price_updates: Dict[str, float]) -> None:
        """Update positions with new market prices"""
        timestamp = datetime.utcnow()

        for symbol, price in price_updates.items():
            if symbol in self.positions:
                self.positions[symbol].update_price(price, timestamp)

    def get_portfolio_value(self) -> float:
        """Get total portfolio value"""
        positions_value = sum(pos.get_market_value() for pos in self.positions.values())
        return self.cash_balance + positions_value

    def get_unrealized_pnl(self) -> float:
        """Get total unrealized P&L"""
        return sum(pos.unrealized_pnl for pos in self.positions.values())

    def get_total_pnl(self) -> float:
        """Get total P&L (realized + unrealized)"""
        return self.total_pnl + self.get_unrealized_pnl()

    def _update_performance_metrics(self) -> None:
        """Update performance metrics"""
        portfolio_value = self.get_portfolio_value()

        # Update peak value and drawdown
        if portfolio_value > self.peak_portfolio_value:
            self.peak_portfolio_value = portfolio_value

        current_drawdown = (self.peak_portfolio_value - portfolio_value) / self.peak_portfolio_value
        self.max_drawdown = max(self.max_drawdown, current_drawdown)

        # Calculate Sharpe ratio (simplified)
        if len(self.daily_pnl_history) > 30:
            returns = [d["daily_pnl"] / d["portfolio_value"] for d in self.daily_pnl_history[-30:]]
            avg_return = sum(returns) / len(returns)
            return_std = math.sqrt(sum((r - avg_return) ** 2 for r in returns) / len(returns))

            if return_std > 0:
                self.sharpe_ratio = (avg_return * 252) / (return_std * math.sqrt(252))  # Annualized

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get portfolio performance summary"""
        portfolio_value = self.get_portfolio_value()
        total_return = (portfolio_value - self.initial_capital) / self.initial_capital

        win_rate = self.winning_trades / self.total_trades if self.total_trades > 0 else 0
        avg_win = self.largest_win / self.winning_trades if self.winning_trades > 0 else 0
        avg_loss = abs(self.largest_loss) / self.losing_trades if self.losing_trades > 0 else 0

        return {
            "initial_capital": self.initial_capital,
            "current_value": portfolio_value,
            "cash_balance": self.cash_balance,
            "total_return": total_return,
            "total_return_pct": total_return * 100,
            "total_pnl": self.get_total_pnl(),
            "realized_pnl": self.total_pnl,
            "unrealized_pnl": self.get_unrealized_pnl(),
            "total_commission": self.total_commission,
            "max_drawdown": self.max_drawdown,
            "peak_value": self.peak_portfolio_value,
            "sharpe_ratio": self.sharpe_ratio,
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "win_rate": win_rate,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "largest_win": self.largest_win,
            "largest_loss": self.largest_loss,
            "active_positions": len(self.positions)
        }

    def get_positions(self) -> List[Dict[str, Any]]:
        """Get all current positions"""
        return [pos.to_dict() for pos in self.positions.values()]

    def get_trades(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get trade history"""
        trades = [trade.to_dict() for trade in self.trades]
        if limit:
            trades = trades[-limit:]
        return trades

    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get specific position"""
        if symbol in self.positions:
            return self.positions[symbol].to_dict()
        return None
