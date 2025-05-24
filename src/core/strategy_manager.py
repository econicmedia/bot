"""
Strategy Manager - Manages trading strategies and their execution
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any, Type
from enum import Enum

from .config import Settings
from .logger import get_trading_logger


class StrategyStatus(str, Enum):
    """Strategy status enumeration"""
    INACTIVE = "inactive"
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"


class StrategyType(str, Enum):
    """Strategy type enumeration"""
    ICT = "ict"
    SMC = "smc"
    SCALPING = "scalping"
    SWING = "swing"


class BaseStrategy(ABC):
    """Base class for all trading strategies"""

    def __init__(self, name: str, settings: Settings):
        """Initialize strategy"""
        self.name = name
        self.settings = settings
        self.logger = get_trading_logger(f"Strategy.{name}")
        self.status = StrategyStatus.INACTIVE
        self.created_at = datetime.utcnow()
        self.last_signal_time: Optional[datetime] = None
        self.performance_metrics: Dict[str, Any] = {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "total_pnl": 0.0,
            "win_rate": 0.0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0
        }

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize strategy components"""
        pass

    @abstractmethod
    async def analyze_market(self, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze market data and generate signals"""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup strategy resources"""
        pass

    async def start(self) -> None:
        """Start the strategy"""
        try:
            await self.initialize()
            self.status = StrategyStatus.ACTIVE
            self.logger.logger.info(f"Strategy {self.name} started successfully")
        except Exception as e:
            self.status = StrategyStatus.ERROR
            self.logger.error(f"Failed to start strategy {self.name}", e)
            raise

    async def stop(self) -> None:
        """Stop the strategy"""
        try:
            await self.cleanup()
            self.status = StrategyStatus.INACTIVE
            self.logger.logger.info(f"Strategy {self.name} stopped successfully")
        except Exception as e:
            self.status = StrategyStatus.ERROR
            self.logger.error(f"Failed to stop strategy {self.name}", e)
            raise

    def pause(self) -> None:
        """Pause the strategy"""
        if self.status == StrategyStatus.ACTIVE:
            self.status = StrategyStatus.PAUSED
            self.logger.logger.info(f"Strategy {self.name} paused")

    def resume(self) -> None:
        """Resume the strategy"""
        if self.status == StrategyStatus.PAUSED:
            self.status = StrategyStatus.ACTIVE
            self.logger.logger.info(f"Strategy {self.name} resumed")

    def update_performance(self, trade_result: Dict[str, Any]) -> None:
        """Update strategy performance metrics"""
        self.performance_metrics["total_trades"] += 1

        pnl = trade_result.get("pnl", 0.0)
        self.performance_metrics["total_pnl"] += pnl

        if pnl > 0:
            self.performance_metrics["winning_trades"] += 1
            self.performance_metrics["avg_win"] = (
                (self.performance_metrics["avg_win"] * (self.performance_metrics["winning_trades"] - 1) + pnl) /
                self.performance_metrics["winning_trades"]
            )
        else:
            self.performance_metrics["losing_trades"] += 1
            self.performance_metrics["avg_loss"] = (
                (self.performance_metrics["avg_loss"] * (self.performance_metrics["losing_trades"] - 1) + abs(pnl)) /
                self.performance_metrics["losing_trades"]
            )

        # Calculate win rate
        if self.performance_metrics["total_trades"] > 0:
            self.performance_metrics["win_rate"] = (
                self.performance_metrics["winning_trades"] / self.performance_metrics["total_trades"]
            )

    def get_status(self) -> Dict[str, Any]:
        """Get strategy status and metrics"""
        return {
            "name": self.name,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "last_signal_time": self.last_signal_time.isoformat() if self.last_signal_time else None,
            "performance": self.performance_metrics
        }


class StrategyManager:
    """Manages all trading strategies"""

    def __init__(self, settings: Settings):
        """Initialize strategy manager"""
        self.settings = settings
        self.logger = get_trading_logger("StrategyManager")
        self.strategies: Dict[str, BaseStrategy] = {}
        self.strategy_classes: Dict[StrategyType, Type[BaseStrategy]] = {}
        self.active_strategies: List[str] = []

        self.logger.logger.info("Strategy manager initialized")

    async def start(self) -> None:
        """Start the strategy manager"""
        self.logger.logger.info("Starting strategy manager...")

        # Auto-start enabled strategies
        await self._start_enabled_strategies()

        self.logger.logger.info("Strategy manager started")

    async def _start_enabled_strategies(self) -> None:
        """Start strategies that are enabled in configuration"""
        try:
            # Create and start simple MA strategy for testing
            from ..strategies.simple_ma_strategy import SimpleMAStrategy
            self.register_strategy_class(StrategyType.TECHNICAL, SimpleMAStrategy)
            await self.create_strategy(StrategyType.TECHNICAL, "simple_ma")
            await self.start_strategy("simple_ma")

        except Exception as e:
            self.logger.error(f"Error starting enabled strategies: {e}")

    def register_strategy_class(self, strategy_type: StrategyType, strategy_class: Type[BaseStrategy]) -> None:
        """Register a strategy class"""
        self.strategy_classes[strategy_type] = strategy_class
        self.logger.logger.info(f"Registered strategy class: {strategy_type.value}")

    async def create_strategy(self, strategy_type: StrategyType, name: str) -> BaseStrategy:
        """Create a new strategy instance"""
        if strategy_type not in self.strategy_classes:
            raise ValueError(f"Strategy type {strategy_type.value} not registered")

        if name in self.strategies:
            raise ValueError(f"Strategy {name} already exists")

        strategy_class = self.strategy_classes[strategy_type]
        strategy = strategy_class(name, self.settings)

        self.strategies[name] = strategy
        self.logger.logger.info(f"Created strategy: {name} ({strategy_type.value})")

        return strategy

    async def start_strategy(self, name: str) -> None:
        """Start a specific strategy"""
        if name not in self.strategies:
            raise ValueError(f"Strategy {name} not found")

        strategy = self.strategies[name]
        await strategy.start()

        if name not in self.active_strategies:
            self.active_strategies.append(name)

        self.logger.logger.info(f"Started strategy: {name}")

    async def stop_strategy(self, name: str) -> None:
        """Stop a specific strategy"""
        if name not in self.strategies:
            raise ValueError(f"Strategy {name} not found")

        strategy = self.strategies[name]
        await strategy.stop()

        if name in self.active_strategies:
            self.active_strategies.remove(name)

        self.logger.logger.info(f"Stopped strategy: {name}")

    async def start_all_strategies(self) -> None:
        """Start all registered strategies"""
        for name, strategy in self.strategies.items():
            try:
                await self.start_strategy(name)
            except Exception as e:
                self.logger.error(f"Failed to start strategy {name}", e)

    async def stop_all_strategies(self) -> None:
        """Stop all active strategies"""
        for name in self.active_strategies.copy():
            try:
                await self.stop_strategy(name)
            except Exception as e:
                self.logger.error(f"Failed to stop strategy {name}", e)

    async def process_market_data(self, market_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process market data through all active strategies"""
        signals = []

        for name in self.active_strategies:
            strategy = self.strategies[name]
            if strategy.status == StrategyStatus.ACTIVE:
                try:
                    signal = await strategy.analyze_market(market_data)
                    if signal:
                        signal["strategy"] = name
                        signal["timestamp"] = datetime.utcnow().isoformat()
                        signals.append(signal)
                        strategy.last_signal_time = datetime.utcnow()
                except Exception as e:
                    self.logger.error(f"Error processing market data in strategy {name}", e)

        return signals

    def get_strategy_status(self, name: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific strategy"""
        if name not in self.strategies:
            return None

        return self.strategies[name].get_status()

    def get_all_strategies_status(self) -> List[Dict[str, Any]]:
        """Get status of all strategies"""
        return [strategy.get_status() for strategy in self.strategies.values()]

    def get_active_strategies(self) -> List[str]:
        """Get list of active strategy names"""
        return self.active_strategies.copy()
