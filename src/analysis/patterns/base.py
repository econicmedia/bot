"""
Base classes for pattern recognition

Provides the foundation for all pattern detection algorithms with consistent
interface and validation.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from src.core.data_manager import Candle
from src.core.logger import get_trading_logger


class PatternType(Enum):
    """Types of patterns"""
    CANDLESTICK = "candlestick"
    CHART = "chart"
    HARMONIC = "harmonic"
    ELLIOTT_WAVE = "elliott_wave"


class PatternSignal(Enum):
    """Pattern signals"""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"
    REVERSAL = "reversal"
    CONTINUATION = "continuation"


@dataclass
class PatternResult:
    """Result from pattern detection"""
    pattern_name: str
    pattern_type: PatternType
    signal: PatternSignal
    confidence: float
    timestamp: datetime
    start_index: int
    end_index: int
    key_levels: Dict[str, float]
    metadata: Optional[Dict[str, Any]] = None


class PatternDetector(ABC):
    """Base class for all pattern detectors"""
    
    def __init__(
        self,
        name: str,
        pattern_type: PatternType,
        min_candles: int = 3,
        timeframe: str = "1m",
        **kwargs
    ):
        """
        Initialize pattern detector
        
        Args:
            name: Detector name
            pattern_type: Type of patterns to detect
            min_candles: Minimum candles required
            timeframe: Data timeframe
            **kwargs: Additional parameters
        """
        self.name = name
        self.pattern_type = pattern_type
        self.min_candles = min_candles
        self.timeframe = timeframe
        self.parameters = kwargs
        
        # Data storage
        self.candles: List[Candle] = []
        self.detected_patterns: List[PatternResult] = []
        
        # Configuration
        self.max_history = kwargs.get("max_history", 1000)
        self.min_confidence = kwargs.get("min_confidence", 0.5)
        
        # Logger
        self.logger = get_trading_logger(f"Pattern.{name}")
        
        self.logger.logger.info(f"Initialized {name} pattern detector")
    
    @abstractmethod
    def detect_patterns(self, candles: List[Candle]) -> List[PatternResult]:
        """
        Detect patterns in candle data
        
        Args:
            candles: List of candle data
            
        Returns:
            List of detected patterns
        """
        pass
    
    def update(self, candle: Candle) -> List[PatternResult]:
        """
        Update detector with new candle data
        
        Args:
            candle: New candle data
            
        Returns:
            List of newly detected patterns
        """
        try:
            # Add new candle
            self.candles.append(candle)
            
            # Maintain history limit
            if len(self.candles) > self.max_history:
                self.candles = self.candles[-self.max_history:]
            
            # Detect patterns
            new_patterns = self.detect_patterns(self.candles)
            
            # Filter by confidence
            filtered_patterns = [
                p for p in new_patterns 
                if p.confidence >= self.min_confidence
            ]
            
            # Store detected patterns
            self.detected_patterns.extend(filtered_patterns)
            
            # Maintain pattern history
            if len(self.detected_patterns) > self.max_history:
                self.detected_patterns = self.detected_patterns[-self.max_history:]
            
            return filtered_patterns
            
        except Exception as e:
            self.logger.error(f"Error updating {self.name} pattern detector", e)
            return []
    
    def get_recent_patterns(self, count: int = 10) -> List[PatternResult]:
        """Get recent detected patterns"""
        return self.detected_patterns[-count:] if self.detected_patterns else []
    
    def get_patterns_by_signal(self, signal: PatternSignal) -> List[PatternResult]:
        """Get patterns by signal type"""
        return [p for p in self.detected_patterns if p.signal == signal]
    
    def reset(self) -> None:
        """Reset detector state"""
        self.candles.clear()
        self.detected_patterns.clear()
        self.logger.logger.info(f"Reset {self.name} pattern detector")
    
    def is_ready(self) -> bool:
        """Check if detector has enough data"""
        return len(self.candles) >= self.min_candles
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert detector to dictionary representation"""
        return {
            "name": self.name,
            "type": self.pattern_type.value,
            "min_candles": self.min_candles,
            "timeframe": self.timeframe,
            "parameters": self.parameters,
            "is_ready": self.is_ready(),
            "data_points": len(self.candles),
            "patterns_detected": len(self.detected_patterns),
            "recent_patterns": [
                {
                    "name": p.pattern_name,
                    "signal": p.signal.value,
                    "confidence": p.confidence,
                    "timestamp": p.timestamp.isoformat()
                }
                for p in self.get_recent_patterns(5)
            ]
        }
    
    @staticmethod
    def validate_candles(candles: List[Candle], min_count: int) -> bool:
        """Validate candle data for pattern detection"""
        if not candles or len(candles) < min_count:
            return False
        
        # Check for valid price data
        for candle in candles[-min_count:]:
            if any(price <= 0 for price in [candle.open, candle.high, candle.low, candle.close]):
                return False
            
            # Check for valid OHLC relationships
            if not (candle.low <= candle.open <= candle.high and 
                   candle.low <= candle.close <= candle.high):
                return False
        
        return True
    
    @staticmethod
    def calculate_body_size(candle: Candle) -> float:
        """Calculate candle body size"""
        return abs(candle.close - candle.open)
    
    @staticmethod
    def calculate_upper_shadow(candle: Candle) -> float:
        """Calculate upper shadow size"""
        return candle.high - max(candle.open, candle.close)
    
    @staticmethod
    def calculate_lower_shadow(candle: Candle) -> float:
        """Calculate lower shadow size"""
        return min(candle.open, candle.close) - candle.low
    
    @staticmethod
    def calculate_total_range(candle: Candle) -> float:
        """Calculate total candle range"""
        return candle.high - candle.low
    
    @staticmethod
    def is_bullish_candle(candle: Candle) -> bool:
        """Check if candle is bullish"""
        return candle.close > candle.open
    
    @staticmethod
    def is_bearish_candle(candle: Candle) -> bool:
        """Check if candle is bearish"""
        return candle.close < candle.open
    
    @staticmethod
    def is_doji_candle(candle: Candle, threshold: float = 0.1) -> bool:
        """Check if candle is a doji (small body relative to range)"""
        body_size = PatternDetector.calculate_body_size(candle)
        total_range = PatternDetector.calculate_total_range(candle)
        
        if total_range == 0:
            return True
        
        body_ratio = body_size / total_range
        return body_ratio <= threshold
    
    @staticmethod
    def calculate_average_range(candles: List[Candle], periods: int = 10) -> float:
        """Calculate average true range for recent candles"""
        if len(candles) < periods:
            periods = len(candles)
        
        if periods <= 1:
            return 0.0
        
        recent_candles = candles[-periods:]
        total_range = sum(PatternDetector.calculate_total_range(c) for c in recent_candles)
        
        return total_range / periods
    
    @staticmethod
    def find_support_resistance(
        candles: List[Candle], 
        lookback: int = 20,
        min_touches: int = 2
    ) -> Tuple[List[float], List[float]]:
        """
        Find support and resistance levels
        
        Args:
            candles: Candle data
            lookback: Number of candles to look back
            min_touches: Minimum touches required for a level
            
        Returns:
            Tuple of (support_levels, resistance_levels)
        """
        if len(candles) < lookback:
            return [], []
        
        recent_candles = candles[-lookback:]
        
        # Find potential support levels (lows)
        lows = [c.low for c in recent_candles]
        highs = [c.high for c in recent_candles]
        
        support_levels = []
        resistance_levels = []
        
        # Simple approach: find levels that have been touched multiple times
        tolerance = 0.001  # 0.1% tolerance
        
        for i, low in enumerate(lows):
            touches = sum(1 for other_low in lows if abs(other_low - low) / low <= tolerance)
            if touches >= min_touches:
                support_levels.append(low)
        
        for i, high in enumerate(highs):
            touches = sum(1 for other_high in highs if abs(other_high - high) / high <= tolerance)
            if touches >= min_touches:
                resistance_levels.append(high)
        
        # Remove duplicates and sort
        support_levels = sorted(list(set(support_levels)))
        resistance_levels = sorted(list(set(resistance_levels)), reverse=True)
        
        return support_levels, resistance_levels
