"""
Risk Manager - Handles risk management and position sizing
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import math

from .config import Settings
from .logger import get_trading_logger


class RiskLevel(str, Enum):
    """Risk level enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PositionSizeMethod(str, Enum):
    """Position sizing method enumeration"""
    FIXED = "fixed"
    PERCENTAGE = "percentage"
    VOLATILITY = "volatility"
    KELLY = "kelly"


class RiskMetrics:
    """Risk metrics container"""

    def __init__(self):
        self.var_1d: float = 0.0  # 1-day Value at Risk
        self.var_5d: float = 0.0  # 5-day Value at Risk
        self.current_drawdown: float = 0.0
        self.max_drawdown: float = 0.0
        self.sharpe_ratio: float = 0.0
        self.sortino_ratio: float = 0.0
        self.beta: float = 0.0
        self.correlation: float = 0.0
        self.volatility: float = 0.0
        self.last_updated: datetime = datetime.utcnow()


class RiskManager:
    """Manages risk and position sizing for the trading system"""

    def __init__(self, settings: Settings):
        """Initialize risk manager"""
        self.settings = settings
        self.logger = get_trading_logger("RiskManager")
        self.risk_config = settings.trading.risk

        # Risk state
        self.current_positions: Dict[str, Dict[str, Any]] = {}
        self.daily_pnl: float = 0.0
        self.daily_trades: int = 0
        self.portfolio_value: float = 100000.0  # Default starting value
        self.peak_portfolio_value: float = 100000.0
        self.risk_metrics = RiskMetrics()

        # Risk limits
        self.max_position_size = self.risk_config.max_position_size
        self.max_daily_loss = self.risk_config.max_daily_loss
        self.max_drawdown = self.risk_config.max_drawdown
        self.stop_loss_pct = self.risk_config.stop_loss_pct
        self.take_profit_pct = self.risk_config.take_profit_pct

        # Daily reset tracking
        self.last_reset_date = datetime.utcnow().date()

        self.logger.logger.info("Risk manager initialized")

    async def initialize(self) -> None:
        """Initialize risk manager components"""
        try:
            # Load historical data for risk calculations if available
            await self._load_historical_data()
            self.logger.logger.info("Risk manager initialized successfully")
        except Exception as e:
            self.logger.error("Failed to initialize risk manager", e)
            raise

    async def _load_historical_data(self) -> None:
        """Load historical data for risk calculations"""
        # TODO: Implement historical data loading from database
        # For now, use default values
        pass

    def _reset_daily_metrics(self) -> None:
        """Reset daily metrics if new day"""
        current_date = datetime.utcnow().date()
        if current_date > self.last_reset_date:
            self.daily_pnl = 0.0
            self.daily_trades = 0
            self.last_reset_date = current_date
            self.logger.logger.info("Daily metrics reset")

    def calculate_position_size(
        self,
        symbol: str,
        entry_price: float,
        stop_loss_price: float,
        method: PositionSizeMethod = PositionSizeMethod.PERCENTAGE,
        confidence: float = 1.0
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate position size based on risk parameters

        Args:
            symbol: Trading symbol
            entry_price: Entry price for the position
            stop_loss_price: Stop loss price
            method: Position sizing method
            confidence: Confidence level (0.0 to 1.0)

        Returns:
            Tuple of (position_size, calculation_details)
        """
        self._reset_daily_metrics()

        # Calculate risk per share
        risk_per_share = abs(entry_price - stop_loss_price)
        if risk_per_share == 0:
            return 0.0, {"error": "Invalid stop loss price"}

        # Calculate maximum risk amount
        max_risk_amount = self.portfolio_value * self.max_position_size

        # Adjust for confidence level
        adjusted_risk_amount = max_risk_amount * confidence

        # Calculate base position size
        base_position_size = adjusted_risk_amount / risk_per_share

        # Apply position sizing method
        if method == PositionSizeMethod.FIXED:
            position_size = min(base_position_size, 1000)  # Fixed max 1000 shares
        elif method == PositionSizeMethod.PERCENTAGE:
            position_size = base_position_size
        elif method == PositionSizeMethod.VOLATILITY:
            # Adjust based on volatility (simplified)
            volatility_factor = max(0.5, min(2.0, 1.0 / (self.risk_metrics.volatility + 0.01)))
            position_size = base_position_size * volatility_factor
        elif method == PositionSizeMethod.KELLY:
            # Simplified Kelly criterion
            win_rate = 0.6  # Default assumption
            avg_win_loss_ratio = 1.5  # Default assumption
            kelly_fraction = (win_rate * avg_win_loss_ratio - (1 - win_rate)) / avg_win_loss_ratio
            kelly_fraction = max(0, min(0.25, kelly_fraction))  # Cap at 25%
            position_size = (self.portfolio_value * kelly_fraction) / entry_price
        else:
            position_size = base_position_size

        # Apply additional constraints
        position_size = self._apply_position_constraints(symbol, position_size, entry_price)

        calculation_details = {
            "method": method.value,
            "risk_per_share": risk_per_share,
            "max_risk_amount": max_risk_amount,
            "adjusted_risk_amount": adjusted_risk_amount,
            "base_position_size": base_position_size,
            "final_position_size": position_size,
            "confidence": confidence,
            "portfolio_value": self.portfolio_value
        }

        return position_size, calculation_details

    def _apply_position_constraints(self, symbol: str, position_size: float, entry_price: float) -> float:
        """Apply additional position constraints"""
        # Maximum position value constraint
        max_position_value = self.portfolio_value * 0.2  # Max 20% of portfolio per position
        max_size_by_value = max_position_value / entry_price
        position_size = min(position_size, max_size_by_value)

        # Minimum position size
        min_position_size = 1.0
        if position_size < min_position_size:
            return 0.0

        # Round to appropriate precision
        return math.floor(position_size)

    def validate_trade(self, trade_request: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate if a trade request meets risk criteria

        Args:
            trade_request: Dictionary containing trade details

        Returns:
            Tuple of (is_valid, reason)
        """
        self._reset_daily_metrics()

        symbol = trade_request.get("symbol")
        side = trade_request.get("side")  # "buy" or "sell"
        quantity = trade_request.get("quantity", 0)
        price = trade_request.get("price", 0)

        # Check daily trade limit
        if self.daily_trades >= self.settings.trading.max_daily_trades:
            return False, "Daily trade limit exceeded"

        # Check daily loss limit
        if self.daily_pnl <= -self.portfolio_value * self.max_daily_loss:
            return False, "Daily loss limit exceeded"

        # Check maximum drawdown
        current_drawdown = (self.peak_portfolio_value - self.portfolio_value) / self.peak_portfolio_value
        if current_drawdown >= self.max_drawdown:
            return False, "Maximum drawdown limit exceeded"

        # Check position concentration
        position_value = quantity * price
        if position_value > self.portfolio_value * 0.2:
            return False, "Position size exceeds concentration limit"

        # Check if we already have a position in this symbol
        if symbol in self.current_positions:
            existing_position = self.current_positions[symbol]
            if (existing_position["side"] == side and
                existing_position["quantity"] + quantity > existing_position["max_quantity"]):
                return False, "Position size limit exceeded for symbol"

        return True, "Trade validated"

    def add_position(self, position: Dict[str, Any]) -> None:
        """Add a new position to tracking"""
        symbol = position["symbol"]
        self.current_positions[symbol] = position
        self.daily_trades += 1
        self.logger.logger.info(f"Added position: {symbol}")

    def update_position(self, symbol: str, updates: Dict[str, Any]) -> None:
        """Update an existing position"""
        if symbol in self.current_positions:
            self.current_positions[symbol].update(updates)
            self.logger.logger.info(f"Updated position: {symbol}")

    def close_position(self, symbol: str, close_price: float, close_time: datetime) -> Dict[str, Any]:
        """Close a position and calculate P&L"""
        if symbol not in self.current_positions:
            return {"error": "Position not found"}

        position = self.current_positions[symbol]
        entry_price = position["entry_price"]
        quantity = position["quantity"]
        side = position["side"]

        # Calculate P&L
        if side == "buy":
            pnl = (close_price - entry_price) * quantity
        else:
            pnl = (entry_price - close_price) * quantity

        # Update daily P&L
        self.daily_pnl += pnl

        # Update portfolio value
        self.portfolio_value += pnl

        # Update peak portfolio value
        if self.portfolio_value > self.peak_portfolio_value:
            self.peak_portfolio_value = self.portfolio_value

        # Remove position
        del self.current_positions[symbol]

        trade_result = {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "entry_price": entry_price,
            "close_price": close_price,
            "pnl": pnl,
            "close_time": close_time.isoformat()
        }

        self.logger.logger.info(f"Closed position: {symbol}, P&L: {pnl:.2f}")
        return trade_result

    def calculate_stop_loss(self, entry_price: float, side: str) -> float:
        """Calculate stop loss price"""
        if side == "buy":
            return entry_price * (1 - self.stop_loss_pct)
        else:
            return entry_price * (1 + self.stop_loss_pct)

    def calculate_take_profit(self, entry_price: float, side: str) -> float:
        """Calculate take profit price"""
        if side == "buy":
            return entry_price * (1 + self.take_profit_pct)
        else:
            return entry_price * (1 - self.take_profit_pct)

    def get_risk_status(self) -> Dict[str, Any]:
        """Get current risk status"""
        self._reset_daily_metrics()

        current_drawdown = (self.peak_portfolio_value - self.portfolio_value) / self.peak_portfolio_value

        # Determine risk level
        if current_drawdown >= self.max_drawdown * 0.8:
            risk_level = RiskLevel.CRITICAL
        elif current_drawdown >= self.max_drawdown * 0.6:
            risk_level = RiskLevel.HIGH
        elif current_drawdown >= self.max_drawdown * 0.3:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        return {
            "risk_level": risk_level.value,
            "portfolio_value": self.portfolio_value,
            "peak_portfolio_value": self.peak_portfolio_value,
            "current_drawdown": current_drawdown,
            "daily_pnl": self.daily_pnl,
            "daily_trades": self.daily_trades,
            "active_positions": len(self.current_positions),
            "risk_metrics": {
                "var_1d": self.risk_metrics.var_1d,
                "var_5d": self.risk_metrics.var_5d,
                "max_drawdown": self.risk_metrics.max_drawdown,
                "sharpe_ratio": self.risk_metrics.sharpe_ratio,
                "volatility": self.risk_metrics.volatility
            }
        }
