"""
Core Trading Engine - Main trading system orchestrator
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from enum import Enum

from .config import Settings
from .logger import get_trading_logger
from .strategy_manager import StrategyManager
from .risk_manager import RiskManager
from .order_manager import OrderManager
from .data_manager import DataManager
from .portfolio_manager import PortfolioManager


class EngineStatus(str, Enum):
    """Trading engine status enumeration"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


class TradingEngine:
    """Main trading engine that orchestrates all trading operations"""

    def __init__(self, settings: Settings):
        """Initialize the trading engine"""
        self.settings = settings
        self.logger = get_trading_logger("TradingEngine")
        self.status = EngineStatus.STOPPED

        # Core components (will be initialized later)
        self.strategy_manager = None
        self.risk_manager = None
        self.order_manager = None
        self.data_manager = None
        self.portfolio_manager = None

        # Runtime state
        self.start_time: Optional[datetime] = None
        self.last_heartbeat: Optional[datetime] = None
        self.active_strategies: List[str] = []
        self.performance_metrics: Dict[str, Any] = {}

        self.logger.logger.info("Trading engine initialized", mode=settings.trading.mode)

    async def initialize(self) -> None:
        """Initialize all engine components"""
        try:
            self.status = EngineStatus.STARTING
            self.logger.logger.info("Initializing trading engine components...")

            # Initialize core components
            self.strategy_manager = StrategyManager(self.settings)
            self.risk_manager = RiskManager(self.settings)
            self.order_manager = OrderManager(self.settings)
            self.data_manager = DataManager(self.settings)
            self.portfolio_manager = PortfolioManager(self.settings)

            # Initialize each component
            await self.strategy_manager.initialize() if hasattr(self.strategy_manager, 'initialize') else None
            await self.risk_manager.initialize()
            await self.order_manager.initialize()
            await self.data_manager.initialize()
            await self.portfolio_manager.initialize()

            self.logger.logger.info("Trading engine components initialized successfully")

            # Reset status to STOPPED after successful initialization
            self.status = EngineStatus.STOPPED

        except Exception as e:
            self.status = EngineStatus.ERROR
            self.logger.error("Failed to initialize trading engine", e)
            raise

    async def start(self) -> None:
        """Start the trading engine"""
        try:
            if self.status != EngineStatus.STOPPED:
                raise RuntimeError(f"Cannot start engine in {self.status} state")

            self.logger.logger.info("Starting trading engine...")
            self.status = EngineStatus.STARTING

            # Start data manager for market data
            if self.data_manager:
                await self.data_manager.start()
                self.logger.logger.info("Data manager started")

            # Start order manager
            if self.order_manager:
                await self.order_manager.start()
                self.logger.logger.info("Order manager started")

            # Start portfolio manager
            if self.portfolio_manager:
                await self.portfolio_manager.start()
                self.logger.logger.info("Portfolio manager started")

            # Start strategy manager
            if self.strategy_manager:
                await self.strategy_manager.start()
                self.logger.logger.info("Strategy manager started")

            # Start the main trading loop
            self._start_trading_loop()

            self.status = EngineStatus.RUNNING
            self.start_time = datetime.now(timezone.utc)
            self.last_heartbeat = datetime.now(timezone.utc)

            self.logger.logger.info("Trading engine started successfully")

        except Exception as e:
            self.status = EngineStatus.ERROR
            self.logger.error("Failed to start trading engine", e)
            raise

    async def stop(self) -> None:
        """Stop the trading engine"""
        try:
            if self.status == EngineStatus.STOPPED:
                return

            self.logger.logger.info("Stopping trading engine...")
            self.status = EngineStatus.STOPPING

            # Stop all components gracefully
            # TODO: Stop actual components when implemented

            self.status = EngineStatus.STOPPED
            self.logger.logger.info("Trading engine stopped successfully")

        except Exception as e:
            self.status = EngineStatus.ERROR
            self.logger.error("Failed to stop trading engine", e)
            raise

    async def get_status(self) -> Dict[str, Any]:
        """Get current engine status"""
        uptime = 0
        if self.start_time:
            uptime = (datetime.now(timezone.utc) - self.start_time).total_seconds()

        return {
            "status": self.status.value,
            "mode": self.settings.trading.mode,
            "uptime": uptime,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "active_strategies": self.active_strategies,
            "components": {
                "strategy_manager": "initialized" if self.strategy_manager else "not_initialized",
                "risk_manager": "initialized" if self.risk_manager else "not_initialized",
                "order_manager": "initialized" if self.order_manager else "not_initialized",
                "data_manager": "initialized" if self.data_manager else "not_initialized",
                "portfolio_manager": "initialized" if self.portfolio_manager else "not_initialized"
            }
        }

    async def heartbeat(self) -> None:
        """Update heartbeat timestamp"""
        self.last_heartbeat = datetime.now(timezone.utc)

    def is_running(self) -> bool:
        """Check if engine is running"""
        return self.status == EngineStatus.RUNNING

    def is_healthy(self) -> bool:
        """Check if engine is healthy"""
        if not self.is_running():
            return False

        # Check if heartbeat is recent (within last 60 seconds)
        if self.last_heartbeat:
            time_since_heartbeat = (datetime.now(timezone.utc) - self.last_heartbeat).total_seconds()
            return time_since_heartbeat < 60

        return False

    def _start_trading_loop(self) -> None:
        """Start the main trading loop as a background task"""
        asyncio.create_task(self._trading_loop())

    async def _trading_loop(self) -> None:
        """Main trading loop - processes market data and executes strategies"""
        self.logger.logger.info("Starting main trading loop...")

        while self.status == EngineStatus.RUNNING:
            try:
                # Update heartbeat
                await self.heartbeat()

                # Get latest market data
                if self.data_manager:
                    market_data = await self.data_manager.get_latest_market_data()

                    if market_data:
                        # Process through strategies
                        if self.strategy_manager:
                            signals = await self.strategy_manager.process_market_data(market_data)

                            # Execute signals
                            for signal in signals:
                                await self._execute_signal(signal)

                # Sleep for a short interval before next iteration
                await asyncio.sleep(1)  # 1 second interval

            except Exception as e:
                self.logger.error(f"Error in trading loop: {e}")
                await asyncio.sleep(5)  # Wait longer on error

        self.logger.logger.info("Trading loop stopped")

    async def _execute_signal(self, signal: Dict[str, Any]) -> None:
        """Execute a trading signal"""
        try:
            if not signal or signal.get("action") != "enter":
                return

            # Validate signal
            if not self._validate_signal(signal):
                self.logger.logger.warning(f"Invalid signal rejected: {signal}")
                return

            # Check risk management
            if self.risk_manager and not await self.risk_manager.validate_trade(signal):
                self.logger.logger.warning(f"Signal rejected by risk manager: {signal}")
                return

            # Create and submit order
            if self.order_manager:
                order = await self._create_order_from_signal(signal)
                if order:
                    await self.order_manager.submit_order(order)
                    self.logger.logger.info(f"Order submitted: {order.id}")

        except Exception as e:
            self.logger.error(f"Error executing signal: {e}")

    def _validate_signal(self, signal: Dict[str, Any]) -> bool:
        """Validate a trading signal"""
        required_fields = ["action", "direction", "price", "strategy"]
        return all(field in signal for field in required_fields)

    async def _create_order_from_signal(self, signal: Dict[str, Any]) -> Optional[Any]:
        """Create an order from a trading signal"""
        try:
            from .order_manager import Order, OrderType, OrderSide

            # Determine order parameters
            symbol = signal.get("symbol", "BTCUSDT")
            side = OrderSide.BUY if signal["direction"] == "long" else OrderSide.SELL
            quantity = signal.get("quantity", 0.001)  # Default small quantity
            price = signal.get("price")

            # Create order
            order = Order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                order_type=OrderType.LIMIT if price else OrderType.MARKET,
                price=price,
                strategy=signal.get("strategy")
            )

            return order

        except Exception as e:
            self.logger.error(f"Error creating order from signal: {e}")
            return None