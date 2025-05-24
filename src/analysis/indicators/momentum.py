"""
Momentum Indicators

Implements momentum-based technical indicators including:
- MACD (Moving Average Convergence Divergence)
- CCI (Commodity Channel Index)
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
import numpy as np

from .base import IndicatorBase, IndicatorResult, IndicatorType
from .moving_averages import MovingAverageIndicator
from src.core.data_manager import Candle


class MACDIndicator(IndicatorBase):
    """MACD (Moving Average Convergence Divergence) indicator"""
    
    def __init__(
        self,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
        timeframe: str = "1m",
        **kwargs
    ):
        """
        Initialize MACD indicator
        
        Args:
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line EMA period
            timeframe: Data timeframe
        """
        super().__init__(
            name=f"MACD_{fast_period}_{slow_period}_{signal_period}",
            indicator_type=IndicatorType.MOMENTUM,
            period=slow_period,  # Use slow period as minimum required
            timeframe=timeframe,
            **kwargs
        )
        
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        
        # Create EMA indicators for MACD calculation
        self.fast_ema = MovingAverageIndicator(
            period=fast_period,
            ma_type="ema",
            timeframe=timeframe
        )
        self.slow_ema = MovingAverageIndicator(
            period=slow_period,
            ma_type="ema",
            timeframe=timeframe
        )
        
        # Storage for MACD line values to calculate signal line
        self.macd_values = []
        self.signal_ema = MovingAverageIndicator(
            period=signal_period,
            ma_type="ema",
            timeframe=timeframe
        )
        
        self.logger.logger.info(f"Initialized MACD indicator ({fast_period}, {slow_period}, {signal_period})")
    
    def calculate(self, candles: List[Candle]) -> Optional[IndicatorResult]:
        """Calculate MACD, Signal, and Histogram values"""
        try:
            if not self.validate_candles(candles, self.slow_period):
                return None
            
            current_candle = candles[-1]
            
            # Update EMAs with current candle
            fast_result = self.fast_ema.update(current_candle)
            slow_result = self.slow_ema.update(current_candle)
            
            if not fast_result or not slow_result:
                return None
            
            # Calculate MACD line
            macd_line = fast_result.value - slow_result.value
            
            # Store MACD value for signal line calculation
            self.macd_values.append(macd_line)
            if len(self.macd_values) > 100:  # Maintain reasonable history
                self.macd_values = self.macd_values[-100:]
            
            # Calculate signal line (EMA of MACD line)
            signal_line = self._calculate_signal_line()
            
            # Calculate histogram
            histogram = macd_line - (signal_line if signal_line is not None else 0)
            
            # Generate signal
            signal = self._generate_signal(macd_line, signal_line, histogram)
            
            # Calculate confidence
            confidence = self._calculate_confidence(macd_line, signal_line, histogram)
            
            return IndicatorResult(
                timestamp=current_candle.timestamp,
                value={
                    "macd": macd_line,
                    "signal": signal_line,
                    "histogram": histogram
                },
                signal=signal,
                confidence=confidence,
                metadata={
                    "fast_period": self.fast_period,
                    "slow_period": self.slow_period,
                    "signal_period": self.signal_period
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating MACD", e)
            return None
    
    def _calculate_signal_line(self) -> Optional[float]:
        """Calculate signal line (EMA of MACD values)"""
        if len(self.macd_values) < self.signal_period:
            return None
        
        # Calculate EMA of MACD values
        recent_macd = self.macd_values[-self.signal_period:]
        
        # Simple EMA calculation for signal line
        alpha = 2.0 / (self.signal_period + 1)
        signal_line = recent_macd[0]
        
        for macd_val in recent_macd[1:]:
            signal_line = (macd_val * alpha) + (signal_line * (1 - alpha))
        
        return signal_line
    
    def _generate_signal(self, macd_line: float, signal_line: Optional[float], histogram: float) -> Optional[str]:
        """Generate trading signal based on MACD crossovers and histogram"""
        if signal_line is None or len(self.results) < 1:
            return None
        
        # Get previous values for crossover detection
        prev_result = self.results[-1]
        if not isinstance(prev_result.value, dict):
            return None
        
        prev_macd = prev_result.value.get("macd")
        prev_signal = prev_result.value.get("signal")
        prev_histogram = prev_result.value.get("histogram")
        
        if prev_macd is None or prev_signal is None or prev_histogram is None:
            return None
        
        # MACD line crosses above signal line = bullish
        if prev_macd <= prev_signal and macd_line > signal_line:
            return "buy"
        
        # MACD line crosses below signal line = bearish
        elif prev_macd >= prev_signal and macd_line < signal_line:
            return "sell"
        
        # Histogram momentum signals
        elif histogram > 0 and prev_histogram <= 0:
            return "buy"  # Histogram turns positive
        elif histogram < 0 and prev_histogram >= 0:
            return "sell"  # Histogram turns negative
        
        return "hold"
    
    def _calculate_confidence(self, macd_line: float, signal_line: Optional[float], histogram: float) -> float:
        """Calculate confidence based on MACD strength and divergence"""
        if signal_line is None:
            return 0.1
        
        # Higher confidence for stronger MACD signals
        macd_strength = abs(macd_line - signal_line)
        strength_confidence = min(macd_strength / 0.01, 1.0)  # Normalize based on typical MACD values
        
        # Higher confidence for strong histogram
        histogram_confidence = min(abs(histogram) / 0.01, 1.0)
        
        return (strength_confidence + histogram_confidence) / 2


class CCIIndicator(IndicatorBase):
    """Commodity Channel Index (CCI) indicator"""
    
    def __init__(
        self,
        period: int = 20,
        constant: float = 0.015,
        overbought: float = 100.0,
        oversold: float = -100.0,
        timeframe: str = "1m",
        **kwargs
    ):
        """
        Initialize CCI indicator
        
        Args:
            period: Number of periods for calculation
            constant: CCI constant (typically 0.015)
            overbought: Overbought threshold
            oversold: Oversold threshold
            timeframe: Data timeframe
        """
        super().__init__(
            name=f"CCI_{period}",
            indicator_type=IndicatorType.MOMENTUM,
            period=period,
            timeframe=timeframe,
            **kwargs
        )
        
        self.constant = constant
        self.overbought = overbought
        self.oversold = oversold
        
        self.logger.logger.info(f"Initialized CCI indicator (period={period})")
    
    def calculate(self, candles: List[Candle]) -> Optional[IndicatorResult]:
        """Calculate CCI value"""
        try:
            if not self.validate_candles(candles, self.period):
                return None
            
            current_candle = candles[-1]
            
            cci_value = self._calculate_cci(candles)
            if cci_value is None:
                return None
            
            # Generate signal
            signal = self._generate_signal(cci_value)
            
            # Calculate confidence
            confidence = self._calculate_confidence(cci_value)
            
            return IndicatorResult(
                timestamp=current_candle.timestamp,
                value=cci_value,
                signal=signal,
                confidence=confidence,
                metadata={
                    "period": self.period,
                    "constant": self.constant,
                    "overbought": self.overbought,
                    "oversold": self.oversold
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating CCI", e)
            return None
    
    def _calculate_cci(self, candles: List[Candle]) -> Optional[float]:
        """Calculate CCI value"""
        if len(candles) < self.period:
            return None
        
        # Get recent candles
        recent_candles = candles[-self.period:]
        
        # Calculate typical prices (HLC/3)
        typical_prices = [(c.high + c.low + c.close) / 3 for c in recent_candles]
        
        # Calculate simple moving average of typical prices
        sma_tp = sum(typical_prices) / len(typical_prices)
        
        # Calculate mean deviation
        mean_deviation = sum(abs(tp - sma_tp) for tp in typical_prices) / len(typical_prices)
        
        # Avoid division by zero
        if mean_deviation == 0:
            return 0.0
        
        # Calculate CCI
        current_tp = typical_prices[-1]
        cci = (current_tp - sma_tp) / (self.constant * mean_deviation)
        
        return float(cci)
    
    def _generate_signal(self, cci_value: float) -> Optional[str]:
        """Generate trading signal based on CCI levels"""
        if cci_value >= self.overbought:
            return "sell"  # Overbought
        elif cci_value <= self.oversold:
            return "buy"   # Oversold
        elif cci_value > 0:
            return "hold"  # Bullish territory
        else:
            return "hold"  # Bearish territory
    
    def _calculate_confidence(self, cci_value: float) -> float:
        """Calculate confidence based on distance from extreme levels"""
        # Higher confidence for more extreme values
        if abs(cci_value) >= 100:
            return min(abs(cci_value) / 200, 1.0)  # Scale extreme values
        else:
            return 0.1  # Low confidence in neutral zone
