"""
Oscillator Indicators

Implements oscillator-type technical indicators including:
- Relative Strength Index (RSI)
- Stochastic Oscillator
- Williams %R
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
import numpy as np

from .base import IndicatorBase, IndicatorResult, IndicatorType
from src.core.data_manager import Candle


class RSIIndicator(IndicatorBase):
    """Relative Strength Index (RSI) oscillator"""
    
    def __init__(
        self,
        period: int = 14,
        overbought: float = 70.0,
        oversold: float = 30.0,
        timeframe: str = "1m",
        **kwargs
    ):
        """
        Initialize RSI indicator
        
        Args:
            period: Number of periods for calculation
            overbought: Overbought threshold (default 70)
            oversold: Oversold threshold (default 30)
            timeframe: Data timeframe
        """
        super().__init__(
            name=f"RSI_{period}",
            indicator_type=IndicatorType.OSCILLATOR,
            period=period,
            timeframe=timeframe,
            **kwargs
        )
        
        self.overbought = overbought
        self.oversold = oversold
        
        # For EMA-based RSI calculation
        self.alpha = 1.0 / period
        self.avg_gain = None
        self.avg_loss = None
        
        self.logger.logger.info(f"Initialized RSI indicator (period={period})")
    
    def calculate(self, candles: List[Candle]) -> Optional[IndicatorResult]:
        """Calculate RSI value"""
        try:
            if not self.validate_candles(candles, self.min_periods + 1):  # Need +1 for price changes
                return None
            
            prices = self.extract_prices(candles, "close")
            current_candle = candles[-1]
            
            rsi_value = self._calculate_rsi(prices)
            if rsi_value is None:
                return None
            
            # Generate signal based on RSI levels
            signal = self._generate_signal(rsi_value)
            
            # Calculate confidence based on distance from extreme levels
            confidence = self._calculate_confidence(rsi_value)
            
            return IndicatorResult(
                timestamp=current_candle.timestamp,
                value=rsi_value,
                signal=signal,
                confidence=confidence,
                metadata={
                    "overbought": self.overbought,
                    "oversold": self.oversold,
                    "period": self.period
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating RSI", e)
            return None
    
    def _calculate_rsi(self, prices: np.ndarray) -> Optional[float]:
        """Calculate RSI using Wilder's smoothing method"""
        if len(prices) < self.period + 1:
            return None
        
        # Calculate price changes
        price_changes = np.diff(prices)
        
        # Separate gains and losses
        gains = np.where(price_changes > 0, price_changes, 0)
        losses = np.where(price_changes < 0, -price_changes, 0)
        
        # Initialize average gain/loss if first calculation
        if self.avg_gain is None or self.avg_loss is None:
            self.avg_gain = np.mean(gains[-self.period:])
            self.avg_loss = np.mean(losses[-self.period:])
        else:
            # Use Wilder's smoothing (EMA with alpha = 1/period)
            current_gain = gains[-1]
            current_loss = losses[-1]
            
            self.avg_gain = (self.avg_gain * (self.period - 1) + current_gain) / self.period
            self.avg_loss = (self.avg_loss * (self.period - 1) + current_loss) / self.period
        
        # Avoid division by zero
        if self.avg_loss == 0:
            return 100.0
        
        # Calculate RSI
        rs = self.avg_gain / self.avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return float(rsi)
    
    def _generate_signal(self, rsi_value: float) -> Optional[str]:
        """Generate trading signal based on RSI levels"""
        if rsi_value >= self.overbought:
            return "sell"  # Overbought condition
        elif rsi_value <= self.oversold:
            return "buy"   # Oversold condition
        else:
            return "hold"
    
    def _calculate_confidence(self, rsi_value: float) -> float:
        """Calculate confidence based on distance from extreme levels"""
        if rsi_value >= self.overbought:
            # More overbought = higher confidence for sell signal
            return min((rsi_value - self.overbought) / (100 - self.overbought), 1.0)
        elif rsi_value <= self.oversold:
            # More oversold = higher confidence for buy signal
            return min((self.oversold - rsi_value) / self.oversold, 1.0)
        else:
            # Neutral zone = low confidence
            return 0.1


class StochasticIndicator(IndicatorBase):
    """Stochastic Oscillator (%K and %D)"""
    
    def __init__(
        self,
        k_period: int = 14,
        d_period: int = 3,
        smooth_k: int = 3,
        overbought: float = 80.0,
        oversold: float = 20.0,
        timeframe: str = "1m",
        **kwargs
    ):
        """
        Initialize Stochastic indicator
        
        Args:
            k_period: Period for %K calculation
            d_period: Period for %D smoothing
            smooth_k: Period for %K smoothing
            overbought: Overbought threshold
            oversold: Oversold threshold
            timeframe: Data timeframe
        """
        super().__init__(
            name=f"STOCH_{k_period}_{d_period}",
            indicator_type=IndicatorType.OSCILLATOR,
            period=k_period,
            timeframe=timeframe,
            **kwargs
        )
        
        self.k_period = k_period
        self.d_period = d_period
        self.smooth_k = smooth_k
        self.overbought = overbought
        self.oversold = oversold
        
        # Storage for %K values for %D calculation
        self.k_values = []
        
        self.logger.logger.info(f"Initialized Stochastic indicator (K={k_period}, D={d_period})")
    
    def calculate(self, candles: List[Candle]) -> Optional[IndicatorResult]:
        """Calculate Stochastic %K and %D values"""
        try:
            if not self.validate_candles(candles, self.k_period):
                return None
            
            current_candle = candles[-1]
            
            # Calculate %K
            k_value = self._calculate_k(candles)
            if k_value is None:
                return None
            
            # Store %K value for %D calculation
            self.k_values.append(k_value)
            if len(self.k_values) > 100:  # Maintain reasonable history
                self.k_values = self.k_values[-100:]
            
            # Calculate %D (smoothed %K)
            d_value = self._calculate_d()
            
            # Generate signal based on %K and %D
            signal = self._generate_signal(k_value, d_value)
            
            # Calculate confidence
            confidence = self._calculate_confidence(k_value, d_value)
            
            return IndicatorResult(
                timestamp=current_candle.timestamp,
                value={"k": k_value, "d": d_value},
                signal=signal,
                confidence=confidence,
                metadata={
                    "k_period": self.k_period,
                    "d_period": self.d_period,
                    "overbought": self.overbought,
                    "oversold": self.oversold
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating Stochastic", e)
            return None
    
    def _calculate_k(self, candles: List[Candle]) -> Optional[float]:
        """Calculate %K value"""
        if len(candles) < self.k_period:
            return None
        
        # Get recent candles for calculation
        recent_candles = candles[-self.k_period:]
        
        # Find highest high and lowest low
        highest_high = max(c.high for c in recent_candles)
        lowest_low = min(c.low for c in recent_candles)
        current_close = candles[-1].close
        
        # Avoid division by zero
        if highest_high == lowest_low:
            return 50.0
        
        # Calculate %K
        k_value = ((current_close - lowest_low) / (highest_high - lowest_low)) * 100
        
        return float(k_value)
    
    def _calculate_d(self) -> Optional[float]:
        """Calculate %D value (smoothed %K)"""
        if len(self.k_values) < self.d_period:
            return None
        
        # %D is the moving average of %K
        recent_k_values = self.k_values[-self.d_period:]
        d_value = sum(recent_k_values) / len(recent_k_values)
        
        return float(d_value)
    
    def _generate_signal(self, k_value: float, d_value: Optional[float]) -> Optional[str]:
        """Generate trading signal based on Stochastic levels and crossovers"""
        if d_value is None:
            return None
        
        # Overbought/Oversold signals
        if k_value >= self.overbought and d_value >= self.overbought:
            return "sell"
        elif k_value <= self.oversold and d_value <= self.oversold:
            return "buy"
        
        # Crossover signals (if we have previous values)
        if len(self.results) >= 1:
            prev_result = self.results[-1]
            if isinstance(prev_result.value, dict):
                prev_k = prev_result.value.get("k")
                prev_d = prev_result.value.get("d")
                
                if prev_k is not None and prev_d is not None:
                    # %K crosses above %D = bullish
                    if prev_k <= prev_d and k_value > d_value:
                        return "buy"
                    # %K crosses below %D = bearish
                    elif prev_k >= prev_d and k_value < d_value:
                        return "sell"
        
        return "hold"
    
    def _calculate_confidence(self, k_value: float, d_value: Optional[float]) -> float:
        """Calculate confidence based on extreme levels and divergence"""
        if d_value is None:
            return 0.1
        
        # Higher confidence for extreme levels
        if k_value >= self.overbought or k_value <= self.oversold:
            extreme_confidence = min(abs(k_value - 50) / 50, 1.0)
        else:
            extreme_confidence = 0.1
        
        # Higher confidence when %K and %D are aligned
        alignment_confidence = 1.0 - abs(k_value - d_value) / 100
        
        return (extreme_confidence + alignment_confidence) / 2


class WilliamsRIndicator(IndicatorBase):
    """Williams %R oscillator"""
    
    def __init__(
        self,
        period: int = 14,
        overbought: float = -20.0,
        oversold: float = -80.0,
        timeframe: str = "1m",
        **kwargs
    ):
        """
        Initialize Williams %R indicator
        
        Args:
            period: Number of periods for calculation
            overbought: Overbought threshold (default -20)
            oversold: Oversold threshold (default -80)
            timeframe: Data timeframe
        """
        super().__init__(
            name=f"WILLR_{period}",
            indicator_type=IndicatorType.OSCILLATOR,
            period=period,
            timeframe=timeframe,
            **kwargs
        )
        
        self.overbought = overbought
        self.oversold = oversold
        
        self.logger.logger.info(f"Initialized Williams %R indicator (period={period})")
    
    def calculate(self, candles: List[Candle]) -> Optional[IndicatorResult]:
        """Calculate Williams %R value"""
        try:
            if not self.validate_candles(candles, self.period):
                return None
            
            current_candle = candles[-1]
            
            willr_value = self._calculate_willr(candles)
            if willr_value is None:
                return None
            
            # Generate signal
            signal = self._generate_signal(willr_value)
            
            # Calculate confidence
            confidence = self._calculate_confidence(willr_value)
            
            return IndicatorResult(
                timestamp=current_candle.timestamp,
                value=willr_value,
                signal=signal,
                confidence=confidence,
                metadata={
                    "period": self.period,
                    "overbought": self.overbought,
                    "oversold": self.oversold
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating Williams %R", e)
            return None
    
    def _calculate_willr(self, candles: List[Candle]) -> Optional[float]:
        """Calculate Williams %R value"""
        if len(candles) < self.period:
            return None
        
        # Get recent candles
        recent_candles = candles[-self.period:]
        
        # Find highest high and lowest low
        highest_high = max(c.high for c in recent_candles)
        lowest_low = min(c.low for c in recent_candles)
        current_close = candles[-1].close
        
        # Avoid division by zero
        if highest_high == lowest_low:
            return -50.0
        
        # Calculate Williams %R
        willr = ((highest_high - current_close) / (highest_high - lowest_low)) * -100
        
        return float(willr)
    
    def _generate_signal(self, willr_value: float) -> Optional[str]:
        """Generate trading signal based on Williams %R levels"""
        if willr_value >= self.overbought:
            return "sell"  # Overbought
        elif willr_value <= self.oversold:
            return "buy"   # Oversold
        else:
            return "hold"
    
    def _calculate_confidence(self, willr_value: float) -> float:
        """Calculate confidence based on distance from extreme levels"""
        if willr_value >= self.overbought:
            return min((willr_value - self.overbought) / (0 - self.overbought), 1.0)
        elif willr_value <= self.oversold:
            return min((self.oversold - willr_value) / (self.oversold - (-100)), 1.0)
        else:
            return 0.1
