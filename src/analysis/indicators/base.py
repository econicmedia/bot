"""
Base classes for technical indicators

Provides the foundation for all technical indicators with consistent interface,
validation, and multi-timeframe support.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import numpy as np
import pandas as pd

from src.core.data_manager import Candle
from src.core.logger import get_trading_logger


class IndicatorType(Enum):
    """Types of technical indicators"""
    TREND = "trend"
    MOMENTUM = "momentum"
    VOLATILITY = "volatility"
    VOLUME = "volume"
    OSCILLATOR = "oscillator"


@dataclass
class IndicatorResult:
    """Result from indicator calculation"""
    timestamp: datetime
    value: Union[float, Dict[str, float]]
    signal: Optional[str] = None  # "buy", "sell", "hold", None
    confidence: float = 0.0
    metadata: Optional[Dict[str, Any]] = None


class IndicatorBase(ABC):
    """Base class for all technical indicators"""
    
    def __init__(
        self,
        name: str,
        indicator_type: IndicatorType,
        period: int = 14,
        timeframe: str = "1m",
        **kwargs
    ):
        """
        Initialize indicator
        
        Args:
            name: Indicator name
            indicator_type: Type of indicator
            period: Calculation period
            timeframe: Data timeframe
            **kwargs: Additional parameters
        """
        self.name = name
        self.indicator_type = indicator_type
        self.period = period
        self.timeframe = timeframe
        self.parameters = kwargs
        
        # Data storage
        self.candles: List[Candle] = []
        self.results: List[IndicatorResult] = []
        
        # Configuration
        self.max_history = kwargs.get("max_history", 1000)
        self.min_periods = kwargs.get("min_periods", period)
        
        # Logger
        self.logger = get_trading_logger(f"Indicator.{name}")
        
        self.logger.logger.info(f"Initialized {name} indicator (period={period}, timeframe={timeframe})")
    
    @abstractmethod
    def calculate(self, candles: List[Candle]) -> Optional[IndicatorResult]:
        """
        Calculate indicator value for given candles
        
        Args:
            candles: List of candle data
            
        Returns:
            IndicatorResult or None if insufficient data
        """
        pass
    
    def update(self, candle: Candle) -> Optional[IndicatorResult]:
        """
        Update indicator with new candle data
        
        Args:
            candle: New candle data
            
        Returns:
            IndicatorResult or None if insufficient data
        """
        try:
            # Add new candle
            self.candles.append(candle)
            
            # Maintain history limit
            if len(self.candles) > self.max_history:
                self.candles = self.candles[-self.max_history:]
            
            # Calculate indicator
            result = self.calculate(self.candles)
            
            if result:
                self.results.append(result)
                
                # Maintain results history
                if len(self.results) > self.max_history:
                    self.results = self.results[-self.max_history:]
                
                return result
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error updating {self.name} indicator", e)
            return None
    
    def get_current_value(self) -> Optional[Union[float, Dict[str, float]]]:
        """Get current indicator value"""
        if self.results:
            return self.results[-1].value
        return None
    
    def get_signal(self) -> Optional[str]:
        """Get current trading signal"""
        if self.results:
            return self.results[-1].signal
        return None
    
    def get_history(self, periods: int = 100) -> List[IndicatorResult]:
        """Get historical indicator values"""
        return self.results[-periods:] if self.results else []
    
    def reset(self) -> None:
        """Reset indicator state"""
        self.candles.clear()
        self.results.clear()
        self.logger.logger.info(f"Reset {self.name} indicator")
    
    def is_ready(self) -> bool:
        """Check if indicator has enough data for calculation"""
        return len(self.candles) >= self.min_periods
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert indicator to dictionary representation"""
        return {
            "name": self.name,
            "type": self.indicator_type.value,
            "period": self.period,
            "timeframe": self.timeframe,
            "parameters": self.parameters,
            "current_value": self.get_current_value(),
            "current_signal": self.get_signal(),
            "is_ready": self.is_ready(),
            "data_points": len(self.candles),
            "results_count": len(self.results)
        }
    
    @staticmethod
    def validate_candles(candles: List[Candle], min_periods: int) -> bool:
        """Validate candle data for calculation"""
        if not candles or len(candles) < min_periods:
            return False
        
        # Check for valid price data
        for candle in candles[-min_periods:]:
            if any(price <= 0 for price in [candle.open, candle.high, candle.low, candle.close]):
                return False
        
        return True
    
    @staticmethod
    def extract_prices(candles: List[Candle], price_type: str = "close") -> np.ndarray:
        """Extract price array from candles"""
        if price_type == "close":
            return np.array([c.close for c in candles])
        elif price_type == "open":
            return np.array([c.open for c in candles])
        elif price_type == "high":
            return np.array([c.high for c in candles])
        elif price_type == "low":
            return np.array([c.low for c in candles])
        elif price_type == "hl2":
            return np.array([(c.high + c.low) / 2 for c in candles])
        elif price_type == "hlc3":
            return np.array([(c.high + c.low + c.close) / 3 for c in candles])
        elif price_type == "ohlc4":
            return np.array([(c.open + c.high + c.low + c.close) / 4 for c in candles])
        else:
            raise ValueError(f"Invalid price type: {price_type}")
