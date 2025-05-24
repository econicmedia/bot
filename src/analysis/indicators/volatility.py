"""
Volatility Indicators

Implements volatility-based technical indicators including:
- Bollinger Bands
- Average True Range (ATR)
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
import numpy as np

from .base import IndicatorBase, IndicatorResult, IndicatorType
from .moving_averages import MovingAverageIndicator
from src.core.data_manager import Candle


class BollingerBandsIndicator(IndicatorBase):
    """Bollinger Bands indicator"""
    
    def __init__(
        self,
        period: int = 20,
        std_dev: float = 2.0,
        ma_type: str = "sma",
        timeframe: str = "1m",
        **kwargs
    ):
        """
        Initialize Bollinger Bands indicator
        
        Args:
            period: Number of periods for calculation
            std_dev: Standard deviation multiplier
            ma_type: Moving average type for middle band
            timeframe: Data timeframe
        """
        super().__init__(
            name=f"BB_{period}_{std_dev}",
            indicator_type=IndicatorType.VOLATILITY,
            period=period,
            timeframe=timeframe,
            **kwargs
        )
        
        self.std_dev = std_dev
        self.ma_type = ma_type
        
        # Create MA indicator for middle band
        self.ma_indicator = MovingAverageIndicator(
            period=period,
            ma_type=ma_type,
            timeframe=timeframe
        )
        
        self.logger.logger.info(f"Initialized Bollinger Bands indicator (period={period}, std={std_dev})")
    
    def calculate(self, candles: List[Candle]) -> Optional[IndicatorResult]:
        """Calculate Bollinger Bands values"""
        try:
            if not self.validate_candles(candles, self.period):
                return None
            
            current_candle = candles[-1]
            
            # Update MA indicator
            ma_result = self.ma_indicator.update(current_candle)
            if not ma_result:
                return None
            
            middle_band = ma_result.value
            
            # Calculate standard deviation
            prices = self.extract_prices(candles[-self.period:], "close")
            std_deviation = float(np.std(prices))
            
            # Calculate upper and lower bands
            upper_band = middle_band + (self.std_dev * std_deviation)
            lower_band = middle_band - (self.std_dev * std_deviation)
            
            # Calculate band width and %B
            band_width = (upper_band - lower_band) / middle_band * 100
            percent_b = (current_candle.close - lower_band) / (upper_band - lower_band)
            
            # Generate signal
            signal = self._generate_signal(current_candle.close, upper_band, lower_band, percent_b)
            
            # Calculate confidence
            confidence = self._calculate_confidence(current_candle.close, upper_band, lower_band, percent_b)
            
            return IndicatorResult(
                timestamp=current_candle.timestamp,
                value={
                    "upper": upper_band,
                    "middle": middle_band,
                    "lower": lower_band,
                    "width": band_width,
                    "percent_b": percent_b
                },
                signal=signal,
                confidence=confidence,
                metadata={
                    "period": self.period,
                    "std_dev": self.std_dev,
                    "ma_type": self.ma_type
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating Bollinger Bands", e)
            return None
    
    def _generate_signal(self, price: float, upper_band: float, lower_band: float, percent_b: float) -> Optional[str]:
        """Generate trading signal based on Bollinger Bands"""
        # Price touches or exceeds upper band = potential sell signal
        if price >= upper_band or percent_b >= 1.0:
            return "sell"
        
        # Price touches or falls below lower band = potential buy signal
        elif price <= lower_band or percent_b <= 0.0:
            return "buy"
        
        # Price near middle band = neutral
        else:
            return "hold"
    
    def _calculate_confidence(self, price: float, upper_band: float, lower_band: float, percent_b: float) -> float:
        """Calculate confidence based on position within bands"""
        # Higher confidence when price is at extreme positions
        if percent_b >= 1.0:  # Above upper band
            return min((percent_b - 1.0) * 10, 1.0)
        elif percent_b <= 0.0:  # Below lower band
            return min(abs(percent_b) * 10, 1.0)
        elif percent_b >= 0.8:  # Near upper band
            return (percent_b - 0.8) / 0.2
        elif percent_b <= 0.2:  # Near lower band
            return (0.2 - percent_b) / 0.2
        else:  # Middle area
            return 0.1
    
    def get_squeeze_status(self) -> Optional[str]:
        """Detect Bollinger Band squeeze (low volatility)"""
        if len(self.results) < 20:
            return None
        
        # Get recent band widths
        recent_widths = []
        for result in self.results[-20:]:
            if isinstance(result.value, dict) and "width" in result.value:
                recent_widths.append(result.value["width"])
        
        if len(recent_widths) < 20:
            return None
        
        current_width = recent_widths[-1]
        avg_width = sum(recent_widths) / len(recent_widths)
        
        # Squeeze when current width is significantly below average
        if current_width < avg_width * 0.7:
            return "squeeze"
        elif current_width > avg_width * 1.3:
            return "expansion"
        else:
            return "normal"


class ATRIndicator(IndicatorBase):
    """Average True Range (ATR) indicator"""
    
    def __init__(
        self,
        period: int = 14,
        ma_type: str = "ema",
        timeframe: str = "1m",
        **kwargs
    ):
        """
        Initialize ATR indicator
        
        Args:
            period: Number of periods for calculation
            ma_type: Moving average type for smoothing
            timeframe: Data timeframe
        """
        super().__init__(
            name=f"ATR_{period}",
            indicator_type=IndicatorType.VOLATILITY,
            period=period,
            timeframe=timeframe,
            **kwargs
        )
        
        self.ma_type = ma_type
        
        # Storage for True Range values
        self.tr_values = []
        
        # For EMA calculation
        if ma_type == "ema":
            self.alpha = 2.0 / (period + 1)
            self.previous_atr = None
        
        self.logger.logger.info(f"Initialized ATR indicator (period={period})")
    
    def calculate(self, candles: List[Candle]) -> Optional[IndicatorResult]:
        """Calculate ATR value"""
        try:
            if not self.validate_candles(candles, 2):  # Need at least 2 candles for TR
                return None
            
            current_candle = candles[-1]
            
            # Calculate True Range
            tr_value = self._calculate_true_range(candles)
            if tr_value is None:
                return None
            
            # Store TR value
            self.tr_values.append(tr_value)
            if len(self.tr_values) > self.max_history:
                self.tr_values = self.tr_values[-self.max_history:]
            
            # Calculate ATR
            atr_value = self._calculate_atr()
            if atr_value is None:
                return None
            
            # Generate signal (ATR is primarily used for volatility measurement)
            signal = self._generate_signal(atr_value)
            
            # Calculate confidence (higher ATR = higher volatility = potentially higher confidence)
            confidence = self._calculate_confidence(atr_value)
            
            return IndicatorResult(
                timestamp=current_candle.timestamp,
                value=atr_value,
                signal=signal,
                confidence=confidence,
                metadata={
                    "period": self.period,
                    "ma_type": self.ma_type,
                    "true_range": tr_value
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating ATR", e)
            return None
    
    def _calculate_true_range(self, candles: List[Candle]) -> Optional[float]:
        """Calculate True Range for current candle"""
        if len(candles) < 2:
            return None
        
        current = candles[-1]
        previous = candles[-2]
        
        # True Range is the maximum of:
        # 1. Current High - Current Low
        # 2. |Current High - Previous Close|
        # 3. |Current Low - Previous Close|
        tr1 = current.high - current.low
        tr2 = abs(current.high - previous.close)
        tr3 = abs(current.low - previous.close)
        
        return max(tr1, tr2, tr3)
    
    def _calculate_atr(self) -> Optional[float]:
        """Calculate ATR using specified moving average method"""
        if len(self.tr_values) < self.period:
            return None
        
        if self.ma_type == "sma":
            # Simple Moving Average of True Range
            recent_tr = self.tr_values[-self.period:]
            return sum(recent_tr) / len(recent_tr)
        
        elif self.ma_type == "ema":
            # Exponential Moving Average of True Range
            if self.previous_atr is None:
                # Initialize with SMA
                recent_tr = self.tr_values[-self.period:]
                self.previous_atr = sum(recent_tr) / len(recent_tr)
                return self.previous_atr
            else:
                # EMA calculation
                current_tr = self.tr_values[-1]
                atr_value = (current_tr * self.alpha) + (self.previous_atr * (1 - self.alpha))
                self.previous_atr = atr_value
                return atr_value
        
        else:
            # Default to SMA
            recent_tr = self.tr_values[-self.period:]
            return sum(recent_tr) / len(recent_tr)
    
    def _generate_signal(self, atr_value: float) -> Optional[str]:
        """Generate signal based on ATR (primarily for volatility assessment)"""
        if len(self.results) < 10:
            return None
        
        # Get recent ATR values for comparison
        recent_atr_values = [r.value for r in self.results[-10:] if isinstance(r.value, (int, float))]
        
        if len(recent_atr_values) < 5:
            return None
        
        avg_atr = sum(recent_atr_values) / len(recent_atr_values)
        
        # High volatility might indicate trend change or continuation
        if atr_value > avg_atr * 1.5:
            return "high_volatility"
        elif atr_value < avg_atr * 0.5:
            return "low_volatility"
        else:
            return "normal_volatility"
    
    def _calculate_confidence(self, atr_value: float) -> float:
        """Calculate confidence based on ATR level"""
        if len(self.results) < 5:
            return 0.5
        
        # Get recent ATR values
        recent_atr_values = [r.value for r in self.results[-5:] if isinstance(r.value, (int, float))]
        
        if len(recent_atr_values) < 3:
            return 0.5
        
        avg_atr = sum(recent_atr_values) / len(recent_atr_values)
        
        # Higher confidence for more extreme ATR values
        if avg_atr > 0:
            volatility_ratio = atr_value / avg_atr
            if volatility_ratio > 1.5 or volatility_ratio < 0.5:
                return min(abs(volatility_ratio - 1.0), 1.0)
        
        return 0.5
    
    def get_volatility_level(self) -> Optional[str]:
        """Get current volatility level classification"""
        if len(self.results) < 20:
            return None
        
        # Get recent ATR values
        recent_atr_values = [r.value for r in self.results[-20:] if isinstance(r.value, (int, float))]
        
        if len(recent_atr_values) < 20:
            return None
        
        current_atr = recent_atr_values[-1]
        avg_atr = sum(recent_atr_values) / len(recent_atr_values)
        
        if current_atr > avg_atr * 1.5:
            return "high"
        elif current_atr < avg_atr * 0.7:
            return "low"
        else:
            return "medium"
