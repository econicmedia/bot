"""
Candlestick Pattern Recognition

Implements detection of common candlestick patterns including:
- Single candlestick patterns (Doji, Hammer, Shooting Star, etc.)
- Multi-candlestick patterns (Engulfing, Harami, etc.)
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
import numpy as np

from .base import PatternDetector, PatternResult, PatternType, PatternSignal
from src.core.data_manager import Candle


class CandlestickPatterns(PatternDetector):
    """Candlestick pattern detector"""
    
    def __init__(
        self,
        timeframe: str = "1m",
        body_threshold: float = 0.1,
        shadow_threshold: float = 2.0,
        **kwargs
    ):
        """
        Initialize candlestick pattern detector
        
        Args:
            timeframe: Data timeframe
            body_threshold: Minimum body size ratio for pattern validation
            shadow_threshold: Shadow to body ratio threshold
        """
        super().__init__(
            name="CandlestickPatterns",
            pattern_type=PatternType.CANDLESTICK,
            min_candles=1,
            timeframe=timeframe,
            **kwargs
        )
        
        self.body_threshold = body_threshold
        self.shadow_threshold = shadow_threshold
        
        self.logger.logger.info("Initialized Candlestick pattern detector")
    
    def detect_patterns(self, candles: List[Candle]) -> List[PatternResult]:
        """Detect candlestick patterns in candle data"""
        if not self.validate_candles(candles, 1):
            return []
        
        patterns = []
        
        # Single candlestick patterns
        patterns.extend(self._detect_single_patterns(candles))
        
        # Multi-candlestick patterns (need at least 2 candles)
        if len(candles) >= 2:
            patterns.extend(self._detect_multi_patterns(candles))
        
        return patterns
    
    def _detect_single_patterns(self, candles: List[Candle]) -> List[PatternResult]:
        """Detect single candlestick patterns"""
        patterns = []
        current_candle = candles[-1]
        
        # Calculate candle metrics
        body_size = self.calculate_body_size(current_candle)
        upper_shadow = self.calculate_upper_shadow(current_candle)
        lower_shadow = self.calculate_lower_shadow(current_candle)
        total_range = self.calculate_total_range(current_candle)
        
        if total_range == 0:
            return patterns
        
        # Doji pattern
        doji_result = self._detect_doji(current_candle, body_size, total_range)
        if doji_result:
            patterns.append(doji_result)
        
        # Hammer pattern
        hammer_result = self._detect_hammer(current_candle, body_size, upper_shadow, lower_shadow, total_range)
        if hammer_result:
            patterns.append(hammer_result)
        
        # Shooting Star pattern
        shooting_star_result = self._detect_shooting_star(current_candle, body_size, upper_shadow, lower_shadow, total_range)
        if shooting_star_result:
            patterns.append(shooting_star_result)
        
        # Spinning Top pattern
        spinning_top_result = self._detect_spinning_top(current_candle, body_size, upper_shadow, lower_shadow, total_range)
        if spinning_top_result:
            patterns.append(spinning_top_result)
        
        return patterns
    
    def _detect_multi_patterns(self, candles: List[Candle]) -> List[PatternResult]:
        """Detect multi-candlestick patterns"""
        patterns = []
        
        if len(candles) < 2:
            return patterns
        
        current_candle = candles[-1]
        previous_candle = candles[-2]
        
        # Engulfing pattern
        engulfing_result = self._detect_engulfing(previous_candle, current_candle)
        if engulfing_result:
            patterns.append(engulfing_result)
        
        # Harami pattern
        harami_result = self._detect_harami(previous_candle, current_candle)
        if harami_result:
            patterns.append(harami_result)
        
        return patterns
    
    def _detect_doji(self, candle: Candle, body_size: float, total_range: float) -> Optional[PatternResult]:
        """Detect Doji pattern"""
        if total_range == 0:
            return None
        
        body_ratio = body_size / total_range
        
        if body_ratio <= 0.05:  # Very small body
            confidence = 1.0 - (body_ratio / 0.05)  # Higher confidence for smaller body
            
            return PatternResult(
                pattern_name="Doji",
                pattern_type=PatternType.CANDLESTICK,
                signal=PatternSignal.NEUTRAL,
                confidence=confidence,
                timestamp=candle.timestamp,
                start_index=len(self.candles) - 1,
                end_index=len(self.candles) - 1,
                key_levels={
                    "open": candle.open,
                    "close": candle.close,
                    "high": candle.high,
                    "low": candle.low
                },
                metadata={
                    "body_ratio": body_ratio,
                    "description": "Indecision pattern - potential reversal"
                }
            )
        
        return None
    
    def _detect_hammer(self, candle: Candle, body_size: float, upper_shadow: float, lower_shadow: float, total_range: float) -> Optional[PatternResult]:
        """Detect Hammer pattern"""
        if total_range == 0 or body_size == 0:
            return None
        
        # Hammer criteria:
        # 1. Small body in upper part of range
        # 2. Long lower shadow (at least 2x body size)
        # 3. Little or no upper shadow
        
        body_position = (min(candle.open, candle.close) - candle.low) / total_range
        lower_shadow_ratio = lower_shadow / body_size if body_size > 0 else 0
        upper_shadow_ratio = upper_shadow / body_size if body_size > 0 else 0
        
        if (body_position >= 0.6 and  # Body in upper part
            lower_shadow_ratio >= 2.0 and  # Long lower shadow
            upper_shadow_ratio <= 0.5):  # Short upper shadow
            
            confidence = min(lower_shadow_ratio / 3.0, 1.0)  # Higher confidence for longer shadow
            
            return PatternResult(
                pattern_name="Hammer",
                pattern_type=PatternType.CANDLESTICK,
                signal=PatternSignal.BULLISH,
                confidence=confidence,
                timestamp=candle.timestamp,
                start_index=len(self.candles) - 1,
                end_index=len(self.candles) - 1,
                key_levels={
                    "support": candle.low,
                    "body_low": min(candle.open, candle.close),
                    "body_high": max(candle.open, candle.close)
                },
                metadata={
                    "lower_shadow_ratio": lower_shadow_ratio,
                    "description": "Bullish reversal pattern"
                }
            )
        
        return None
    
    def _detect_shooting_star(self, candle: Candle, body_size: float, upper_shadow: float, lower_shadow: float, total_range: float) -> Optional[PatternResult]:
        """Detect Shooting Star pattern"""
        if total_range == 0 or body_size == 0:
            return None
        
        # Shooting Star criteria:
        # 1. Small body in lower part of range
        # 2. Long upper shadow (at least 2x body size)
        # 3. Little or no lower shadow
        
        body_position = (max(candle.open, candle.close) - candle.low) / total_range
        upper_shadow_ratio = upper_shadow / body_size if body_size > 0 else 0
        lower_shadow_ratio = lower_shadow / body_size if body_size > 0 else 0
        
        if (body_position <= 0.4 and  # Body in lower part
            upper_shadow_ratio >= 2.0 and  # Long upper shadow
            lower_shadow_ratio <= 0.5):  # Short lower shadow
            
            confidence = min(upper_shadow_ratio / 3.0, 1.0)
            
            return PatternResult(
                pattern_name="Shooting Star",
                pattern_type=PatternType.CANDLESTICK,
                signal=PatternSignal.BEARISH,
                confidence=confidence,
                timestamp=candle.timestamp,
                start_index=len(self.candles) - 1,
                end_index=len(self.candles) - 1,
                key_levels={
                    "resistance": candle.high,
                    "body_low": min(candle.open, candle.close),
                    "body_high": max(candle.open, candle.close)
                },
                metadata={
                    "upper_shadow_ratio": upper_shadow_ratio,
                    "description": "Bearish reversal pattern"
                }
            )
        
        return None
    
    def _detect_spinning_top(self, candle: Candle, body_size: float, upper_shadow: float, lower_shadow: float, total_range: float) -> Optional[PatternResult]:
        """Detect Spinning Top pattern"""
        if total_range == 0 or body_size == 0:
            return None
        
        # Spinning Top criteria:
        # 1. Small body
        # 2. Long shadows on both sides
        
        body_ratio = body_size / total_range
        upper_shadow_ratio = upper_shadow / body_size if body_size > 0 else 0
        lower_shadow_ratio = lower_shadow / body_size if body_size > 0 else 0
        
        if (body_ratio <= 0.3 and  # Small body
            upper_shadow_ratio >= 1.0 and  # Decent upper shadow
            lower_shadow_ratio >= 1.0):  # Decent lower shadow
            
            confidence = 1.0 - body_ratio  # Smaller body = higher confidence
            
            return PatternResult(
                pattern_name="Spinning Top",
                pattern_type=PatternType.CANDLESTICK,
                signal=PatternSignal.NEUTRAL,
                confidence=confidence,
                timestamp=candle.timestamp,
                start_index=len(self.candles) - 1,
                end_index=len(self.candles) - 1,
                key_levels={
                    "high": candle.high,
                    "low": candle.low,
                    "body_mid": (candle.open + candle.close) / 2
                },
                metadata={
                    "body_ratio": body_ratio,
                    "description": "Indecision pattern"
                }
            )
        
        return None
    
    def _detect_engulfing(self, prev_candle: Candle, curr_candle: Candle) -> Optional[PatternResult]:
        """Detect Engulfing pattern"""
        prev_body_size = self.calculate_body_size(prev_candle)
        curr_body_size = self.calculate_body_size(curr_candle)
        
        # Bullish Engulfing: bearish candle followed by larger bullish candle
        if (self.is_bearish_candle(prev_candle) and 
            self.is_bullish_candle(curr_candle) and
            curr_candle.open < prev_candle.close and
            curr_candle.close > prev_candle.open):
            
            size_ratio = curr_body_size / prev_body_size if prev_body_size > 0 else 1.0
            confidence = min(size_ratio / 2.0, 1.0)  # Larger engulfing = higher confidence
            
            return PatternResult(
                pattern_name="Bullish Engulfing",
                pattern_type=PatternType.CANDLESTICK,
                signal=PatternSignal.BULLISH,
                confidence=confidence,
                timestamp=curr_candle.timestamp,
                start_index=len(self.candles) - 2,
                end_index=len(self.candles) - 1,
                key_levels={
                    "support": min(prev_candle.low, curr_candle.low),
                    "engulf_low": prev_candle.close,
                    "engulf_high": prev_candle.open
                },
                metadata={
                    "size_ratio": size_ratio,
                    "description": "Bullish reversal pattern"
                }
            )
        
        # Bearish Engulfing: bullish candle followed by larger bearish candle
        elif (self.is_bullish_candle(prev_candle) and 
              self.is_bearish_candle(curr_candle) and
              curr_candle.open > prev_candle.close and
              curr_candle.close < prev_candle.open):
            
            size_ratio = curr_body_size / prev_body_size if prev_body_size > 0 else 1.0
            confidence = min(size_ratio / 2.0, 1.0)
            
            return PatternResult(
                pattern_name="Bearish Engulfing",
                pattern_type=PatternType.CANDLESTICK,
                signal=PatternSignal.BEARISH,
                confidence=confidence,
                timestamp=curr_candle.timestamp,
                start_index=len(self.candles) - 2,
                end_index=len(self.candles) - 1,
                key_levels={
                    "resistance": max(prev_candle.high, curr_candle.high),
                    "engulf_low": prev_candle.open,
                    "engulf_high": prev_candle.close
                },
                metadata={
                    "size_ratio": size_ratio,
                    "description": "Bearish reversal pattern"
                }
            )
        
        return None
    
    def _detect_harami(self, prev_candle: Candle, curr_candle: Candle) -> Optional[PatternResult]:
        """Detect Harami pattern"""
        # Harami: large candle followed by smaller candle contained within the first
        
        if (curr_candle.open > min(prev_candle.open, prev_candle.close) and
            curr_candle.close < max(prev_candle.open, prev_candle.close) and
            curr_candle.open < max(prev_candle.open, prev_candle.close) and
            curr_candle.close > min(prev_candle.open, prev_candle.close)):
            
            prev_body_size = self.calculate_body_size(prev_candle)
            curr_body_size = self.calculate_body_size(curr_candle)
            
            size_ratio = curr_body_size / prev_body_size if prev_body_size > 0 else 0
            confidence = 1.0 - size_ratio  # Smaller inside candle = higher confidence
            
            # Determine signal based on previous candle direction
            if self.is_bearish_candle(prev_candle):
                signal = PatternSignal.BULLISH
                pattern_name = "Bullish Harami"
            else:
                signal = PatternSignal.BEARISH
                pattern_name = "Bearish Harami"
            
            return PatternResult(
                pattern_name=pattern_name,
                pattern_type=PatternType.CANDLESTICK,
                signal=signal,
                confidence=confidence,
                timestamp=curr_candle.timestamp,
                start_index=len(self.candles) - 2,
                end_index=len(self.candles) - 1,
                key_levels={
                    "outer_high": prev_candle.high,
                    "outer_low": prev_candle.low,
                    "inner_high": curr_candle.high,
                    "inner_low": curr_candle.low
                },
                metadata={
                    "size_ratio": size_ratio,
                    "description": "Potential reversal pattern"
                }
            )
        
        return None
