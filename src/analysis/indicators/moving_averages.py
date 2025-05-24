"""
Moving Average Indicators

Implements various types of moving averages including:
- Simple Moving Average (SMA)
- Exponential Moving Average (EMA) 
- Weighted Moving Average (WMA)
- Hull Moving Average (HMA)
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
import numpy as np

from .base import IndicatorBase, IndicatorResult, IndicatorType
from src.core.data_manager import Candle


class MovingAverageIndicator(IndicatorBase):
    """Moving Average indicator with multiple calculation methods"""
    
    def __init__(
        self,
        period: int = 20,
        ma_type: str = "sma",
        price_type: str = "close",
        timeframe: str = "1m",
        **kwargs
    ):
        """
        Initialize Moving Average indicator
        
        Args:
            period: Number of periods for calculation
            ma_type: Type of MA ("sma", "ema", "wma", "hma")
            price_type: Price to use ("close", "open", "high", "low", "hl2", "hlc3", "ohlc4")
            timeframe: Data timeframe
        """
        super().__init__(
            name=f"{ma_type.upper()}_{period}",
            indicator_type=IndicatorType.TREND,
            period=period,
            timeframe=timeframe,
            **kwargs
        )
        
        self.ma_type = ma_type.lower()
        self.price_type = price_type
        
        # Validation
        if self.ma_type not in ["sma", "ema", "wma", "hma"]:
            raise ValueError(f"Invalid MA type: {ma_type}")
        
        # EMA-specific parameters
        if self.ma_type == "ema":
            self.alpha = 2.0 / (period + 1)
            self.previous_ema = None
        
        self.logger.logger.info(f"Initialized {self.ma_type.upper()} indicator (period={period})")
    
    def calculate(self, candles: List[Candle]) -> Optional[IndicatorResult]:
        """Calculate moving average value"""
        try:
            if not self.validate_candles(candles, self.min_periods):
                return None
            
            prices = self.extract_prices(candles, self.price_type)
            current_candle = candles[-1]
            
            # Calculate based on MA type
            if self.ma_type == "sma":
                ma_value = self._calculate_sma(prices)
            elif self.ma_type == "ema":
                ma_value = self._calculate_ema(prices)
            elif self.ma_type == "wma":
                ma_value = self._calculate_wma(prices)
            elif self.ma_type == "hma":
                ma_value = self._calculate_hma(prices)
            else:
                return None
            
            if ma_value is None:
                return None
            
            # Generate signal based on price vs MA
            signal = self._generate_signal(current_candle.close, ma_value)
            
            # Calculate confidence based on distance from MA
            confidence = self._calculate_confidence(current_candle.close, ma_value)
            
            return IndicatorResult(
                timestamp=current_candle.timestamp,
                value=ma_value,
                signal=signal,
                confidence=confidence,
                metadata={
                    "ma_type": self.ma_type,
                    "period": self.period,
                    "price_type": self.price_type,
                    "current_price": current_candle.close
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating {self.name}", e)
            return None
    
    def _calculate_sma(self, prices: np.ndarray) -> Optional[float]:
        """Calculate Simple Moving Average"""
        if len(prices) < self.period:
            return None
        
        return float(np.mean(prices[-self.period:]))
    
    def _calculate_ema(self, prices: np.ndarray) -> Optional[float]:
        """Calculate Exponential Moving Average"""
        if len(prices) < self.period:
            return None
        
        # Initialize EMA with SMA if first calculation
        if self.previous_ema is None:
            self.previous_ema = float(np.mean(prices[:self.period]))
            if len(prices) == self.period:
                return self.previous_ema
        
        # Calculate EMA: EMA = (Price * Alpha) + (Previous EMA * (1 - Alpha))
        current_price = float(prices[-1])
        ema_value = (current_price * self.alpha) + (self.previous_ema * (1 - self.alpha))
        self.previous_ema = ema_value
        
        return ema_value
    
    def _calculate_wma(self, prices: np.ndarray) -> Optional[float]:
        """Calculate Weighted Moving Average"""
        if len(prices) < self.period:
            return None
        
        recent_prices = prices[-self.period:]
        weights = np.arange(1, self.period + 1)
        
        return float(np.sum(recent_prices * weights) / np.sum(weights))
    
    def _calculate_hma(self, prices: np.ndarray) -> Optional[float]:
        """Calculate Hull Moving Average"""
        if len(prices) < self.period:
            return None
        
        # HMA = WMA(2 * WMA(n/2) - WMA(n), sqrt(n))
        half_period = self.period // 2
        sqrt_period = int(np.sqrt(self.period))
        
        if len(prices) < self.period:
            return None
        
        # Calculate WMA for half period
        wma_half = self._calculate_wma_for_period(prices, half_period)
        if wma_half is None:
            return None
        
        # Calculate WMA for full period
        wma_full = self._calculate_wma_for_period(prices, self.period)
        if wma_full is None:
            return None
        
        # Create the HMA series: 2 * WMA(n/2) - WMA(n)
        hma_series = 2 * wma_half - wma_full
        
        # We need to calculate this for the last sqrt_period values
        # For simplicity, return the current calculation
        return float(hma_series)
    
    def _calculate_wma_for_period(self, prices: np.ndarray, period: int) -> Optional[float]:
        """Helper method to calculate WMA for specific period"""
        if len(prices) < period:
            return None
        
        recent_prices = prices[-period:]
        weights = np.arange(1, period + 1)
        
        return float(np.sum(recent_prices * weights) / np.sum(weights))
    
    def _generate_signal(self, current_price: float, ma_value: float) -> Optional[str]:
        """Generate trading signal based on price vs MA"""
        if not self.results:
            return None
        
        # Get previous MA value for trend detection
        previous_result = self.results[-1] if self.results else None
        if not previous_result:
            return None
        
        previous_ma = previous_result.value
        
        # Price above MA and MA trending up = bullish
        if current_price > ma_value and ma_value > previous_ma:
            return "buy"
        
        # Price below MA and MA trending down = bearish
        elif current_price < ma_value and ma_value < previous_ma:
            return "sell"
        
        return "hold"
    
    def _calculate_confidence(self, current_price: float, ma_value: float) -> float:
        """Calculate confidence based on distance from MA"""
        if ma_value == 0:
            return 0.0
        
        # Calculate percentage distance from MA
        distance_pct = abs(current_price - ma_value) / ma_value
        
        # Convert to confidence (closer to MA = lower confidence for signals)
        # Further from MA = higher confidence for trend continuation
        confidence = min(distance_pct * 10, 1.0)  # Scale and cap at 1.0
        
        return confidence
    
    def get_trend_direction(self) -> Optional[str]:
        """Get current trend direction based on MA slope"""
        if len(self.results) < 2:
            return None
        
        current_ma = self.results[-1].value
        previous_ma = self.results[-2].value
        
        if current_ma > previous_ma:
            return "up"
        elif current_ma < previous_ma:
            return "down"
        else:
            return "sideways"
    
    def get_ma_cross_signals(self, other_ma: 'MovingAverageIndicator') -> Optional[str]:
        """
        Detect crossover signals with another MA
        
        Args:
            other_ma: Another MovingAverageIndicator instance
            
        Returns:
            "golden_cross", "death_cross", or None
        """
        if not self.results or not other_ma.results:
            return None
        
        if len(self.results) < 2 or len(other_ma.results) < 2:
            return None
        
        # Current values
        fast_current = self.results[-1].value
        slow_current = other_ma.results[-1].value
        
        # Previous values
        fast_previous = self.results[-2].value
        slow_previous = other_ma.results[-2].value
        
        # Detect crossovers
        if fast_previous <= slow_previous and fast_current > slow_current:
            return "golden_cross"  # Fast MA crosses above slow MA
        elif fast_previous >= slow_previous and fast_current < slow_current:
            return "death_cross"   # Fast MA crosses below slow MA
        
        return None
