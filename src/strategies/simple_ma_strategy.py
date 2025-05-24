"""
Simple Moving Average Strategy - Basic implementation for testing
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import deque

from src.core.strategy_manager import BaseStrategy
from src.core.config import Settings
from src.core.data_manager import Candle


class SimpleMAStrategy(BaseStrategy):
    """Simple Moving Average crossover strategy for testing"""

    def __init__(self, name: str, settings: Settings):
        """Initialize strategy"""
        super().__init__(name, settings)

        # Strategy parameters
        self.fast_period = 10
        self.slow_period = 20
        self.symbol = "BTCUSDT"
        self.timeframe = "1m"

        # Data storage
        self.candles: deque = deque(maxlen=self.slow_period + 10)
        self.fast_ma_values: deque = deque(maxlen=100)
        self.slow_ma_values: deque = deque(maxlen=100)

        # State tracking
        self.last_signal = None
        self.last_signal_time = None

        self.logger.logger.info(f"SimpleMA strategy initialized: {self.fast_period}/{self.slow_period}")

    async def initialize(self) -> None:
        """Initialize strategy components"""
        try:
            # Strategy-specific initialization
            self.logger.logger.info("SimpleMA strategy components initialized")
        except Exception as e:
            self.logger.error("Failed to initialize SimpleMA strategy", e)
            raise

    async def analyze_market(self, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze market data and generate signals"""
        try:
            # Check if we have data for our symbol
            if self.symbol not in market_data:
                return None

            symbol_data = market_data[self.symbol]
            candle_data = symbol_data.get("candle", {})

            if not candle_data:
                return None

            # Create candle object from the data
            candle = Candle(
                symbol=candle_data["symbol"],
                timeframe=candle_data["timeframe"],
                timestamp=datetime.fromisoformat(candle_data["timestamp"]),
                open_price=candle_data["open_price"],
                high_price=candle_data["high_price"],
                low_price=candle_data["low_price"],
                close_price=candle_data["close_price"],
                volume=candle_data["volume"]
            )

            # Add candle to our data
            self.candles.append(candle)

            # Need enough data for calculation
            if len(self.candles) < self.slow_period:
                return None

            # Calculate moving averages
            fast_ma = self._calculate_ma(self.fast_period)
            slow_ma = self._calculate_ma(self.slow_period)

            if fast_ma is None or slow_ma is None:
                return None

            # Store MA values
            self.fast_ma_values.append(fast_ma)
            self.slow_ma_values.append(slow_ma)

            # Generate signal
            signal = self._generate_signal(fast_ma, slow_ma)

            if signal:
                self.last_signal = signal["action"]
                self.last_signal_time = datetime.utcnow()

                self.logger.logger.info(
                    f"Signal generated: {signal['action']} at {candle.close:.2f} "
                    f"(Fast MA: {fast_ma:.2f}, Slow MA: {slow_ma:.2f})"
                )

                return signal

            return None

        except Exception as e:
            self.logger.error("Error analyzing market data in SimpleMA strategy", e)
            return None

    def _calculate_ma(self, period: int) -> Optional[float]:
        """Calculate moving average for given period"""
        if len(self.candles) < period:
            return None

        # Get last 'period' candles
        recent_candles = list(self.candles)[-period:]

        # Calculate average of close prices
        total = sum(candle.close for candle in recent_candles)
        return total / period

    def _generate_signal(self, fast_ma: float, slow_ma: float) -> Optional[Dict[str, Any]]:
        """Generate trading signal based on MA crossover"""
        # Need at least 2 MA values to detect crossover
        if len(self.fast_ma_values) < 2 or len(self.slow_ma_values) < 2:
            return None

        # Get previous MA values
        prev_fast_ma = self.fast_ma_values[-2]
        prev_slow_ma = self.slow_ma_values[-2]

        current_candle = self.candles[-1]

        # Detect crossovers
        # Bullish crossover: fast MA crosses above slow MA
        if (prev_fast_ma <= prev_slow_ma and fast_ma > slow_ma and
            self.last_signal != "enter"):

            return {
                "action": "enter",
                "direction": "long",
                "symbol": self.symbol,
                "price": current_candle.close_price,
                "quantity": 0.001,  # Small quantity for testing
                "stop_loss": current_candle.close_price * 0.98,  # 2% stop loss
                "take_profit": current_candle.close_price * 1.04,  # 4% take profit
                "strategy": self.name,
                "reason": f"MA crossover: Fast({fast_ma:.2f}) > Slow({slow_ma:.2f})",
                "confidence": 0.7,
                "metadata": {
                    "fast_ma": fast_ma,
                    "slow_ma": slow_ma,
                    "timeframe": self.timeframe
                }
            }

        # Bearish crossover: fast MA crosses below slow MA
        elif (prev_fast_ma >= prev_slow_ma and fast_ma < slow_ma and
              self.last_signal != "enter"):

            return {
                "action": "enter",
                "direction": "short",
                "symbol": self.symbol,
                "price": current_candle.close_price,
                "quantity": 0.001,  # Small quantity for testing
                "stop_loss": current_candle.close_price * 1.02,  # 2% stop loss
                "take_profit": current_candle.close_price * 0.96,  # 4% take profit
                "strategy": self.name,
                "reason": f"MA crossover: Fast({fast_ma:.2f}) < Slow({slow_ma:.2f})",
                "confidence": 0.7,
                "metadata": {
                    "fast_ma": fast_ma,
                    "slow_ma": slow_ma,
                    "timeframe": self.timeframe
                }
            }

        return None

    async def cleanup(self) -> None:
        """Cleanup strategy resources"""
        try:
            # Clear data structures
            self.candles.clear()
            self.fast_ma_values.clear()
            self.slow_ma_values.clear()

            self.logger.logger.info("SimpleMA strategy cleaned up")
        except Exception as e:
            self.logger.error("Error cleaning up SimpleMA strategy", e)

    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information"""
        return {
            "name": self.name,
            "type": "simple_ma",
            "parameters": {
                "fast_period": self.fast_period,
                "slow_period": self.slow_period,
                "symbol": self.symbol,
                "timeframe": self.timeframe
            },
            "state": {
                "candles_count": len(self.candles),
                "last_signal": self.last_signal,
                "last_signal_time": self.last_signal_time.isoformat() if self.last_signal_time else None,
                "current_fast_ma": self.fast_ma_values[-1] if self.fast_ma_values else None,
                "current_slow_ma": self.slow_ma_values[-1] if self.slow_ma_values else None
            }
        }
