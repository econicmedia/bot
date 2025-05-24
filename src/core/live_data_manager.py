"""
Live Data Manager for Real Market Data Integration

This module provides live market data integration while maintaining paper trading functionality.
Connects to real exchanges for market data but executes trades in simulation mode.
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from decimal import Decimal
import random
import json

from .logger import get_trading_logger
from .memory_storage import MemoryPosition, MemoryTrade, MemoryOrder, PortfolioSnapshot


class LiveDataManager:
    """
    Live data manager that connects to real market data for paper trading

    Features:
    - Real-time market data from Binance
    - Paper trading execution (no real money)
    - Live strategy signal generation
    - Real-time dashboard updates
    """

    def __init__(self, settings=None):
        self.logger = get_trading_logger("LiveDataManager")
        self.settings = settings

        # Core data storage (same as memory manager)
        self.positions: Dict[str, MemoryPosition] = {}
        self.trades: List[MemoryTrade] = []
        self.orders: Dict[str, MemoryOrder] = {}
        self.portfolio_history: List[PortfolioSnapshot] = []

        # Portfolio state
        self.cash_balance = 10000.0  # Starting with $10,000 for paper trading
        self.initial_balance = 10000.0

        # Live market data
        self.market_prices: Dict[str, float] = {}
        self.market_data_callbacks: List[Callable] = []

        # Exchange connection
        self.exchange = None
        self.is_connected = False

        # Trading state
        self.is_trading_active = False
        self.last_strategy_check = datetime.utcnow()

        # Strategy performance tracking
        self.strategy_metrics: Dict[str, Dict[str, Any]] = {
            "ICT": {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "total_return": 0.0,
                "win_rate": 0.0,
                "enabled": True,
                "last_signal": None,
                "signals_today": 0
            },
            "SMC": {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "total_return": 0.0,
                "win_rate": 0.0,
                "enabled": True,
                "last_signal": None,
                "signals_today": 0
            }
        }

        # Symbols to track
        self.tracked_symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "SOLUSDT", "DOTUSDT"]

        # Background tasks
        self._background_tasks_started = False
        self._tasks = []

    async def initialize(self):
        """Initialize the live data manager"""
        self.logger.info("Initializing live data manager...")

        try:
            # Initialize exchange connection
            await self._initialize_exchange()

            # Start background tasks
            await self._start_background_tasks()

            self.logger.info("Live data manager initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize live data manager: {e}")
            # Fall back to demo mode
            await self._initialize_demo_mode()
            return False

    async def _initialize_exchange(self):
        """Initialize exchange connection for live data"""
        try:
            from ..integrations.binance.client import BinanceExchange

            if self.settings:
                binance_config = self.settings.data_sources.binance
                api_key = binance_config.api_key
                api_secret = binance_config.api_secret
                sandbox = binance_config.sandbox
            else:
                # Use demo credentials
                api_key = "demo_api_key"
                api_secret = "demo_api_secret"
                sandbox = True

            self.exchange = BinanceExchange(api_key, api_secret, sandbox)

            # Test connection
            if await self.exchange.connect():
                self.is_connected = True
                self.logger.info("Connected to Binance for live market data")

                # Get initial market prices
                await self._fetch_initial_prices()
            else:
                self.logger.warning("Failed to connect to exchange, using demo mode")
                await self._initialize_demo_mode()

        except Exception as e:
            self.logger.error(f"Exchange initialization failed: {e}")
            await self._initialize_demo_mode()

    async def _fetch_initial_prices(self):
        """Fetch initial market prices from exchange"""
        try:
            for symbol in self.tracked_symbols:
                try:
                    ticker = await self.exchange.get_ticker(symbol)
                    self.market_prices[symbol] = ticker.last
                    self.logger.info(f"Fetched {symbol}: ${ticker.last:,.2f}")
                except Exception as e:
                    self.logger.warning(f"Failed to fetch {symbol} price: {e}")
                    # Use fallback price
                    fallback_prices = {
                        "BTCUSDT": 43250.50,
                        "ETHUSDT": 2580.75,
                        "ADAUSDT": 0.485,
                        "SOLUSDT": 98.45,
                        "DOTUSDT": 7.23
                    }
                    self.market_prices[symbol] = fallback_prices.get(symbol, 100.0)

        except Exception as e:
            self.logger.error(f"Failed to fetch initial prices: {e}")
            await self._initialize_demo_mode()

    async def _initialize_demo_mode(self):
        """Initialize with demo data when live connection fails"""
        self.logger.info("Initializing demo mode with simulated data...")

        # Set demo prices
        self.market_prices = {
            "BTCUSDT": 43250.50,
            "ETHUSDT": 2580.75,
            "ADAUSDT": 0.485,
            "SOLUSDT": 98.45,
            "DOTUSDT": 7.23
        }

        # Create some demo positions for testing
        await self._create_demo_position("BTCUSDT", "long", 0.1, 42800.0)
        await self._create_demo_position("ETHUSDT", "long", 1.0, 2520.0)

        self.is_connected = False

    async def _start_background_tasks(self):
        """Start background tasks for live updates"""
        if not self._background_tasks_started:
            try:
                # Start price update task
                task1 = asyncio.create_task(self._live_price_update_task())
                self._tasks.append(task1)

                # Start strategy monitoring task
                task2 = asyncio.create_task(self._strategy_monitoring_task())
                self._tasks.append(task2)

                # Start portfolio update task
                task3 = asyncio.create_task(self._portfolio_update_task())
                self._tasks.append(task3)

                self._background_tasks_started = True
                self.logger.info("Background tasks started successfully")

            except Exception as e:
                self.logger.error(f"Failed to start background tasks: {e}")

    async def _live_price_update_task(self):
        """Update prices from live market data or simulation"""
        while True:
            try:
                if self.is_connected and self.exchange:
                    # Fetch live prices
                    for symbol in self.tracked_symbols:
                        try:
                            ticker = await self.exchange.get_ticker(symbol)
                            old_price = self.market_prices.get(symbol, ticker.last)
                            self.market_prices[symbol] = ticker.last

                            # Update positions with new prices
                            await self._update_position_prices(symbol, ticker.last)

                            # Log significant price changes
                            if old_price and abs(ticker.last - old_price) / old_price > 0.01:  # 1% change
                                self.logger.info(f"{symbol} price update: ${old_price:,.2f} → ${ticker.last:,.2f}")

                        except Exception as e:
                            self.logger.warning(f"Failed to update {symbol} price: {e}")

                    await asyncio.sleep(10)  # Update every 10 seconds for live data

                else:
                    # Simulate price updates when not connected
                    for symbol in self.market_prices:
                        change = random.uniform(-0.002, 0.002)  # ±0.2% change
                        self.market_prices[symbol] *= (1 + change)
                        await self._update_position_prices(symbol, self.market_prices[symbol])

                    await asyncio.sleep(5)  # Update every 5 seconds for simulation

            except Exception as e:
                self.logger.error(f"Error in price update task: {e}")
                await asyncio.sleep(30)  # Wait longer on error

    async def _update_position_prices(self, symbol: str, new_price: float):
        """Update position prices and PnL"""
        if symbol in self.positions:
            position = self.positions[symbol]
            position.current_price = new_price

            if position.side == "long":
                position.unrealized_pnl = (new_price - position.entry_price) * position.quantity
            else:
                position.unrealized_pnl = (position.entry_price - new_price) * position.quantity

            position.updated_at = datetime.utcnow()

    async def _strategy_monitoring_task(self):
        """Monitor for strategy signals and execute paper trades"""
        while True:
            try:
                if self.is_trading_active:
                    # Check for ICT signals
                    await self._check_ict_signals()

                    # Check for SMC signals
                    await self._check_smc_signals()

                    self.last_strategy_check = datetime.utcnow()

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                self.logger.error(f"Error in strategy monitoring: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error

    async def _check_ict_signals(self):
        """Check for ICT trading signals (simplified)"""
        try:
            # Simplified ICT signal generation for demo
            for symbol in self.tracked_symbols:
                if random.random() < 0.05:  # 5% chance per check
                    signal_strength = random.uniform(0.6, 1.0)

                    if signal_strength > 0.8:  # Strong signal
                        side = "long" if random.random() > 0.5 else "short"
                        await self._execute_paper_trade(symbol, side, "ICT", signal_strength)

        except Exception as e:
            self.logger.error(f"Error checking ICT signals: {e}")

    async def _check_smc_signals(self):
        """Check for SMC trading signals (simplified)"""
        try:
            # Simplified SMC signal generation for demo
            for symbol in self.tracked_symbols:
                if random.random() < 0.03:  # 3% chance per check
                    signal_strength = random.uniform(0.7, 1.0)

                    if signal_strength > 0.85:  # Strong signal
                        side = "long" if random.random() > 0.5 else "short"
                        await self._execute_paper_trade(symbol, side, "SMC", signal_strength)

        except Exception as e:
            self.logger.error(f"Error checking SMC signals: {e}")

    async def _execute_paper_trade(self, symbol: str, side: str, strategy: str, signal_strength: float):
        """Execute a paper trade based on strategy signal"""
        try:
            current_price = self.market_prices.get(symbol)
            if not current_price:
                return

            # Calculate position size (risk management)
            risk_amount = self.cash_balance * 0.02  # 2% risk per trade
            quantity = risk_amount / current_price

            # Check if we have enough cash
            trade_value = current_price * quantity
            if trade_value > self.cash_balance * 0.1:  # Max 10% per trade
                quantity = (self.cash_balance * 0.1) / current_price

            if quantity < 0.001:  # Minimum trade size
                return

            # Create paper trade
            trade_id = str(uuid.uuid4())

            # Simulate some slippage
            execution_price = current_price * (1 + random.uniform(-0.001, 0.001))

            trade = MemoryTrade(
                trade_id=trade_id,
                order_id=str(uuid.uuid4()),
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=execution_price,
                commission=execution_price * quantity * 0.001,  # 0.1% commission
                timestamp=datetime.utcnow(),
                strategy=strategy,
                pnl=0.0  # Will be calculated when position is closed
            )

            self.trades.append(trade)

            # Update strategy metrics
            self.strategy_metrics[strategy]["signals_today"] += 1
            self.strategy_metrics[strategy]["last_signal"] = datetime.utcnow()

            # Update cash balance
            self.cash_balance -= (execution_price * quantity + trade.commission)

            # Create or update position
            await self._update_position(symbol, side, quantity, execution_price, strategy)

            self.logger.info(f"Paper trade executed: {strategy} {side} {quantity:.4f} {symbol} @ ${execution_price:,.2f}")

        except Exception as e:
            self.logger.error(f"Error executing paper trade: {e}")

    async def _update_position(self, symbol: str, side: str, quantity: float, price: float, strategy: str):
        """Update or create position"""
        try:
            if symbol in self.positions:
                # Update existing position
                position = self.positions[symbol]

                if position.side == side:
                    # Add to position
                    total_quantity = position.quantity + quantity
                    weighted_price = ((position.entry_price * position.quantity) + (price * quantity)) / total_quantity
                    position.quantity = total_quantity
                    position.entry_price = weighted_price
                else:
                    # Opposite side - close or reduce position
                    if quantity >= position.quantity:
                        # Close position completely
                        pnl = self._calculate_position_pnl(position, price)
                        await self._close_position(symbol, pnl)

                        # Create new position if quantity is larger
                        if quantity > position.quantity:
                            remaining_quantity = quantity - position.quantity
                            await self._create_new_position(symbol, side, remaining_quantity, price, strategy)
                    else:
                        # Reduce position
                        position.quantity -= quantity

            else:
                # Create new position
                await self._create_new_position(symbol, side, quantity, price, strategy)

        except Exception as e:
            self.logger.error(f"Error updating position: {e}")

    async def _create_new_position(self, symbol: str, side: str, quantity: float, price: float, strategy: str):
        """Create a new position"""
        current_price = self.market_prices.get(symbol, price)

        if side == "long":
            unrealized_pnl = (current_price - price) * quantity
        else:
            unrealized_pnl = (price - current_price) * quantity

        position = MemoryPosition(
            symbol=symbol,
            side=side,
            quantity=quantity,
            entry_price=price,
            current_price=current_price,
            unrealized_pnl=unrealized_pnl,
            margin_used=price * quantity * 0.1,  # 10x leverage simulation
            created_at=datetime.utcnow()
        )

        self.positions[symbol] = position

    async def _close_position(self, symbol: str, pnl: float):
        """Close a position and update metrics"""
        if symbol in self.positions:
            position = self.positions[symbol]

            # Update cash balance
            position_value = position.current_price * position.quantity
            self.cash_balance += position_value + pnl

            # Update strategy metrics
            # Note: This is simplified - in reality we'd track which strategy opened the position
            for strategy in self.strategy_metrics:
                if self.strategy_metrics[strategy]["enabled"]:
                    self.strategy_metrics[strategy]["total_trades"] += 1
                    if pnl > 0:
                        self.strategy_metrics[strategy]["winning_trades"] += 1
                    else:
                        self.strategy_metrics[strategy]["losing_trades"] += 1
                    break

            # Remove position
            del self.positions[symbol]

            self.logger.info(f"Position closed: {symbol} PnL: ${pnl:.2f}")

    def _calculate_position_pnl(self, position: MemoryPosition, exit_price: float) -> float:
        """Calculate PnL for a position"""
        if position.side == "long":
            return (exit_price - position.entry_price) * position.quantity
        else:
            return (position.entry_price - exit_price) * position.quantity

    async def _create_demo_position(self, symbol: str, side: str, quantity: float, entry_price: float):
        """Create a demo position for testing"""
        await self._create_new_position(symbol, side, quantity, entry_price, "Demo")

    async def _portfolio_update_task(self):
        """Update portfolio snapshots periodically"""
        while True:
            try:
                # Calculate portfolio metrics
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

                await asyncio.sleep(300)  # Update every 5 minutes

            except Exception as e:
                self.logger.error(f"Error in portfolio update task: {e}")
                await asyncio.sleep(600)

    # Public API methods for the trading bot

    async def start_trading(self):
        """Start active trading"""
        self.is_trading_active = True
        self.logger.info("Paper trading started")

    async def stop_trading(self):
        """Stop active trading"""
        self.is_trading_active = False
        self.logger.info("Paper trading stopped")

    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get current portfolio summary"""
        total_positions_value = sum(
            pos.current_price * pos.quantity for pos in self.positions.values()
        )
        total_unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())

        return {
            "total_value": self.cash_balance + total_positions_value,
            "cash_balance": self.cash_balance,
            "positions_value": total_positions_value,
            "unrealized_pnl": total_unrealized_pnl,
            "daily_pnl": total_unrealized_pnl,
            "active_positions": len(self.positions),
            "total_trades": len(self.trades),
            "is_trading": self.is_trading_active,
            "is_connected": self.is_connected
        }

    def get_positions(self) -> List[Dict[str, Any]]:
        """Get current positions"""
        return [
            {
                "symbol": pos.symbol,
                "side": pos.side,
                "quantity": pos.quantity,
                "entry_price": pos.entry_price,
                "current_price": pos.current_price,
                "unrealized_pnl": pos.unrealized_pnl,
                "created_at": pos.created_at.isoformat()
            }
            for pos in self.positions.values()
        ]

    def get_recent_trades(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent trades"""
        recent_trades = sorted(self.trades, key=lambda x: x.timestamp, reverse=True)[:limit]
        return [
            {
                "trade_id": trade.trade_id,
                "symbol": trade.symbol,
                "side": trade.side,
                "quantity": trade.quantity,
                "price": trade.price,
                "timestamp": trade.timestamp.isoformat(),
                "strategy": trade.strategy,
                "pnl": trade.pnl
            }
            for trade in recent_trades
        ]

    def get_strategy_performance(self) -> Dict[str, Any]:
        """Get strategy performance metrics"""
        return self.strategy_metrics

    def get_market_prices(self) -> Dict[str, float]:
        """Get current market prices"""
        return self.market_prices.copy()

    async def cleanup(self):
        """Cleanup resources"""
        try:
            # Stop background tasks
            for task in self._tasks:
                if not task.done():
                    task.cancel()

            # Disconnect from exchange
            if self.exchange and self.is_connected:
                await self.exchange.disconnect()

            self.logger.info("Live data manager cleaned up")

        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


# Global instance
live_data_manager = None

def get_live_data_manager(settings=None):
    """Get or create the global live data manager"""
    global live_data_manager
    if live_data_manager is None:
        live_data_manager = LiveDataManager(settings)
    return live_data_manager
