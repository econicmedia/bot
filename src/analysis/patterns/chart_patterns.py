"""
Chart Pattern Recognition

Implements detection of chart patterns including:
- Support and resistance levels
- Trend lines
- Triangle patterns
- Head and shoulders patterns
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
import numpy as np

from .base import PatternDetector, PatternResult, PatternType, PatternSignal
from src.core.data_manager import Candle


class ChartPatterns(PatternDetector):
    """Chart pattern detector"""
    
    def __init__(
        self,
        timeframe: str = "1m",
        min_pattern_length: int = 10,
        **kwargs
    ):
        """
        Initialize chart pattern detector
        
        Args:
            timeframe: Data timeframe
            min_pattern_length: Minimum candles required for pattern
        """
        super().__init__(
            name="ChartPatterns",
            pattern_type=PatternType.CHART,
            min_candles=min_pattern_length,
            timeframe=timeframe,
            **kwargs
        )
        
        self.min_pattern_length = min_pattern_length
        
        self.logger.logger.info("Initialized Chart pattern detector")
    
    def detect_patterns(self, candles: List[Candle]) -> List[PatternResult]:
        """Detect chart patterns in candle data"""
        if not self.validate_candles(candles, self.min_pattern_length):
            return []
        
        patterns = []
        
        # Support and resistance levels
        support_resistance = self._detect_support_resistance(candles)
        patterns.extend(support_resistance)
        
        # Triangle patterns
        if len(candles) >= 20:
            triangle_patterns = self._detect_triangle_patterns(candles)
            patterns.extend(triangle_patterns)
        
        return patterns
    
    def _detect_support_resistance(self, candles: List[Candle]) -> List[PatternResult]:
        """Detect support and resistance levels"""
        patterns = []
        
        if len(candles) < self.min_pattern_length:
            return patterns
        
        # Find support and resistance levels
        support_levels, resistance_levels = self.find_support_resistance(
            candles, 
            lookback=min(len(candles), 50),
            min_touches=3
        )
        
        current_price = candles[-1].close
        
        # Create pattern results for significant levels
        for support in support_levels:
            if abs(current_price - support) / current_price <= 0.02:  # Within 2%
                confidence = self._calculate_level_confidence(candles, support, "support")
                
                patterns.append(PatternResult(
                    pattern_name="Support Level",
                    pattern_type=PatternType.CHART,
                    signal=PatternSignal.BULLISH,
                    confidence=confidence,
                    timestamp=candles[-1].timestamp,
                    start_index=0,
                    end_index=len(candles) - 1,
                    key_levels={"support": support, "current_price": current_price},
                    metadata={
                        "level_type": "support",
                        "distance_pct": abs(current_price - support) / current_price * 100,
                        "description": f"Support level at {support:.4f}"
                    }
                ))
        
        for resistance in resistance_levels:
            if abs(current_price - resistance) / current_price <= 0.02:  # Within 2%
                confidence = self._calculate_level_confidence(candles, resistance, "resistance")
                
                patterns.append(PatternResult(
                    pattern_name="Resistance Level",
                    pattern_type=PatternType.CHART,
                    signal=PatternSignal.BEARISH,
                    confidence=confidence,
                    timestamp=candles[-1].timestamp,
                    start_index=0,
                    end_index=len(candles) - 1,
                    key_levels={"resistance": resistance, "current_price": current_price},
                    metadata={
                        "level_type": "resistance",
                        "distance_pct": abs(current_price - resistance) / current_price * 100,
                        "description": f"Resistance level at {resistance:.4f}"
                    }
                ))
        
        return patterns
    
    def _detect_triangle_patterns(self, candles: List[Candle]) -> List[PatternResult]:
        """Detect triangle patterns"""
        patterns = []
        
        if len(candles) < 20:
            return patterns
        
        # Get recent candles for pattern analysis
        recent_candles = candles[-30:] if len(candles) >= 30 else candles
        
        # Find swing highs and lows
        swing_highs = self._find_swing_points(recent_candles, "high")
        swing_lows = self._find_swing_points(recent_candles, "low")
        
        if len(swing_highs) < 3 or len(swing_lows) < 3:
            return patterns
        
        # Analyze trend lines
        high_trend = self._analyze_trend_line(swing_highs)
        low_trend = self._analyze_trend_line(swing_lows)
        
        if high_trend and low_trend:
            triangle_type = self._classify_triangle(high_trend, low_trend)
            
            if triangle_type:
                confidence = self._calculate_triangle_confidence(high_trend, low_trend)
                
                patterns.append(PatternResult(
                    pattern_name=f"{triangle_type} Triangle",
                    pattern_type=PatternType.CHART,
                    signal=self._get_triangle_signal(triangle_type),
                    confidence=confidence,
                    timestamp=candles[-1].timestamp,
                    start_index=len(candles) - len(recent_candles),
                    end_index=len(candles) - 1,
                    key_levels={
                        "upper_trend": high_trend,
                        "lower_trend": low_trend,
                        "current_price": candles[-1].close
                    },
                    metadata={
                        "triangle_type": triangle_type,
                        "swing_highs": len(swing_highs),
                        "swing_lows": len(swing_lows),
                        "description": f"{triangle_type} triangle pattern detected"
                    }
                ))
        
        return patterns
    
    def _find_swing_points(self, candles: List[Candle], point_type: str = "high") -> List[Tuple[int, float]]:
        """Find swing highs or lows"""
        swing_points = []
        lookback = 3  # Look 3 candles back and forward
        
        for i in range(lookback, len(candles) - lookback):
            if point_type == "high":
                current_value = candles[i].high
                is_swing = all(
                    current_value >= candles[j].high 
                    for j in range(i - lookback, i + lookback + 1) 
                    if j != i
                )
            else:  # low
                current_value = candles[i].low
                is_swing = all(
                    current_value <= candles[j].low 
                    for j in range(i - lookback, i + lookback + 1) 
                    if j != i
                )
            
            if is_swing:
                swing_points.append((i, current_value))
        
        return swing_points
    
    def _analyze_trend_line(self, swing_points: List[Tuple[int, float]]) -> Optional[Dict[str, float]]:
        """Analyze trend line from swing points"""
        if len(swing_points) < 2:
            return None
        
        # Use linear regression to find trend line
        x_values = np.array([point[0] for point in swing_points])
        y_values = np.array([point[1] for point in swing_points])
        
        if len(x_values) < 2:
            return None
        
        # Calculate slope and intercept
        slope, intercept = np.polyfit(x_values, y_values, 1)
        
        # Calculate R-squared for trend line quality
        y_pred = slope * x_values + intercept
        ss_res = np.sum((y_values - y_pred) ** 2)
        ss_tot = np.sum((y_values - np.mean(y_values)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        return {
            "slope": slope,
            "intercept": intercept,
            "r_squared": r_squared,
            "points": len(swing_points)
        }
    
    def _classify_triangle(self, high_trend: Dict, low_trend: Dict) -> Optional[str]:
        """Classify triangle pattern type"""
        high_slope = high_trend["slope"]
        low_slope = low_trend["slope"]
        
        # Thresholds for slope classification
        flat_threshold = 0.001
        
        if abs(high_slope) < flat_threshold and low_slope > flat_threshold:
            return "Ascending"
        elif high_slope < -flat_threshold and abs(low_slope) < flat_threshold:
            return "Descending"
        elif high_slope < -flat_threshold and low_slope > flat_threshold:
            return "Symmetrical"
        
        return None
    
    def _get_triangle_signal(self, triangle_type: str) -> PatternSignal:
        """Get signal for triangle pattern"""
        if triangle_type == "Ascending":
            return PatternSignal.BULLISH
        elif triangle_type == "Descending":
            return PatternSignal.BEARISH
        else:  # Symmetrical
            return PatternSignal.NEUTRAL
    
    def _calculate_level_confidence(self, candles: List[Candle], level: float, level_type: str) -> float:
        """Calculate confidence for support/resistance level"""
        touches = 0
        tolerance = 0.002  # 0.2% tolerance
        
        for candle in candles:
            if level_type == "support":
                if abs(candle.low - level) / level <= tolerance:
                    touches += 1
            else:  # resistance
                if abs(candle.high - level) / level <= tolerance:
                    touches += 1
        
        # More touches = higher confidence
        confidence = min(touches / 5.0, 1.0)
        return confidence
    
    def _calculate_triangle_confidence(self, high_trend: Dict, low_trend: Dict) -> float:
        """Calculate confidence for triangle pattern"""
        # Base confidence on R-squared values and number of points
        high_quality = high_trend["r_squared"]
        low_quality = low_trend["r_squared"]
        
        avg_quality = (high_quality + low_quality) / 2
        
        # Bonus for more swing points
        point_bonus = min((high_trend["points"] + low_trend["points"]) / 10, 0.3)
        
        confidence = min(avg_quality + point_bonus, 1.0)
        return confidence
