"""
Market Structure Analysis for ICT Strategy

Implements market structure analysis including:
- Higher highs and lower lows identification
- Break of structure (BOS) detection
- Change of character (CHoCH) identification
- Trend analysis and confirmation
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


class TrendDirection(Enum):
    """Trend direction enumeration"""
    BULLISH = "bullish"
    BEARISH = "bearish"
    SIDEWAYS = "sideways"


class StructureType(Enum):
    """Market structure type"""
    HIGHER_HIGH = "higher_high"
    LOWER_HIGH = "lower_high"
    HIGHER_LOW = "higher_low"
    LOWER_LOW = "lower_low"
    BREAK_OF_STRUCTURE = "break_of_structure"
    CHANGE_OF_CHARACTER = "change_of_character"


@dataclass
class StructurePoint:
    """Market structure point"""
    timestamp: datetime
    price: float
    structure_type: StructureType
    significance: float  # 0.0 to 1.0
    confirmed: bool = False


@dataclass
class MarketStructure:
    """Market structure analysis result"""
    trend_direction: TrendDirection
    structure_points: List[StructurePoint]
    last_bos: Optional[StructurePoint] = None
    last_choch: Optional[StructurePoint] = None
    confidence: float = 0.0


class MarketStructureAnalyzer:
    """
    Analyzes market structure for ICT trading concepts
    
    This analyzer identifies key market structure elements including:
    - Higher highs and lower lows
    - Break of structure (BOS)
    - Change of character (CHoCH)
    - Trend direction and strength
    """
    
    def __init__(self, lookback_period: int = 20, min_significance: float = 0.3):
        """
        Initialize market structure analyzer
        
        Args:
            lookback_period: Number of periods to look back for structure analysis
            min_significance: Minimum significance level for structure points
        """
        self.lookback_period = lookback_period
        self.min_significance = min_significance
        
        # State tracking
        self.last_analysis: Optional[MarketStructure] = None
        self.structure_history: List[StructurePoint] = []
        
    def analyze(self, data: pd.DataFrame) -> MarketStructure:
        """
        Analyze market structure from price data
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            MarketStructure object with analysis results
        """
        if len(data) < self.lookback_period:
            return MarketStructure(
                trend_direction=TrendDirection.SIDEWAYS,
                structure_points=[],
                confidence=0.0
            )
        
        # Find swing highs and lows
        swing_highs, swing_lows = self._find_swing_points(data)
        
        # Identify structure points
        structure_points = self._identify_structure_points(swing_highs, swing_lows)
        
        # Determine trend direction
        trend_direction = self._determine_trend_direction(structure_points)
        
        # Find break of structure and change of character
        last_bos, last_choch = self._find_bos_and_choch(structure_points)
        
        # Calculate confidence
        confidence = self._calculate_confidence(structure_points, trend_direction)
        
        # Create market structure result
        market_structure = MarketStructure(
            trend_direction=trend_direction,
            structure_points=structure_points,
            last_bos=last_bos,
            last_choch=last_choch,
            confidence=confidence
        )
        
        self.last_analysis = market_structure
        return market_structure
    
    def _find_swing_points(self, data: pd.DataFrame) -> Tuple[List[Tuple], List[Tuple]]:
        """Find swing highs and lows in the data"""
        highs = []
        lows = []
        
        high_prices = data['high'].values
        low_prices = data['low'].values
        timestamps = data.index
        
        # Find swing highs (local maxima)
        for i in range(2, len(high_prices) - 2):
            if (high_prices[i] > high_prices[i-1] and 
                high_prices[i] > high_prices[i-2] and
                high_prices[i] > high_prices[i+1] and 
                high_prices[i] > high_prices[i+2]):
                
                highs.append((timestamps[i], high_prices[i], i))
        
        # Find swing lows (local minima)
        for i in range(2, len(low_prices) - 2):
            if (low_prices[i] < low_prices[i-1] and 
                low_prices[i] < low_prices[i-2] and
                low_prices[i] < low_prices[i+1] and 
                low_prices[i] < low_prices[i+2]):
                
                lows.append((timestamps[i], low_prices[i], i))
        
        return highs, lows
    
    def _identify_structure_points(
        self, 
        swing_highs: List[Tuple], 
        swing_lows: List[Tuple]
    ) -> List[StructurePoint]:
        """Identify market structure points from swing highs and lows"""
        structure_points = []
        
        # Process swing highs
        for i in range(1, len(swing_highs)):
            prev_high = swing_highs[i-1]
            curr_high = swing_highs[i]
            
            if curr_high[1] > prev_high[1]:
                # Higher high
                significance = self._calculate_significance(curr_high[1], prev_high[1])
                if significance >= self.min_significance:
                    structure_points.append(StructurePoint(
                        timestamp=curr_high[0],
                        price=curr_high[1],
                        structure_type=StructureType.HIGHER_HIGH,
                        significance=significance,
                        confirmed=True
                    ))
            else:
                # Lower high
                significance = self._calculate_significance(prev_high[1], curr_high[1])
                if significance >= self.min_significance:
                    structure_points.append(StructurePoint(
                        timestamp=curr_high[0],
                        price=curr_high[1],
                        structure_type=StructureType.LOWER_HIGH,
                        significance=significance,
                        confirmed=True
                    ))
        
        # Process swing lows
        for i in range(1, len(swing_lows)):
            prev_low = swing_lows[i-1]
            curr_low = swing_lows[i]
            
            if curr_low[1] > prev_low[1]:
                # Higher low
                significance = self._calculate_significance(curr_low[1], prev_low[1])
                if significance >= self.min_significance:
                    structure_points.append(StructurePoint(
                        timestamp=curr_low[0],
                        price=curr_low[1],
                        structure_type=StructureType.HIGHER_LOW,
                        significance=significance,
                        confirmed=True
                    ))
            else:
                # Lower low
                significance = self._calculate_significance(prev_low[1], curr_low[1])
                if significance >= self.min_significance:
                    structure_points.append(StructurePoint(
                        timestamp=curr_low[0],
                        price=curr_low[1],
                        structure_type=StructureType.LOWER_LOW,
                        significance=significance,
                        confirmed=True
                    ))
        
        # Sort by timestamp
        structure_points.sort(key=lambda x: x.timestamp)
        
        return structure_points
    
    def _calculate_significance(self, price1: float, price2: float) -> float:
        """Calculate significance of a structure point"""
        if price2 == 0:
            return 0.0
        
        # Calculate percentage difference
        pct_diff = abs(price1 - price2) / price2
        
        # Normalize to 0-1 scale (assuming max 10% move is highly significant)
        significance = min(pct_diff / 0.1, 1.0)
        
        return significance
    
    def _determine_trend_direction(self, structure_points: List[StructurePoint]) -> TrendDirection:
        """Determine overall trend direction from structure points"""
        if not structure_points:
            return TrendDirection.SIDEWAYS
        
        # Count recent structure types
        recent_points = structure_points[-10:]  # Last 10 structure points
        
        bullish_count = sum(1 for point in recent_points 
                           if point.structure_type in [StructureType.HIGHER_HIGH, StructureType.HIGHER_LOW])
        
        bearish_count = sum(1 for point in recent_points 
                           if point.structure_type in [StructureType.LOWER_HIGH, StructureType.LOWER_LOW])
        
        if bullish_count > bearish_count * 1.5:
            return TrendDirection.BULLISH
        elif bearish_count > bullish_count * 1.5:
            return TrendDirection.BEARISH
        else:
            return TrendDirection.SIDEWAYS
    
    def _find_bos_and_choch(
        self, 
        structure_points: List[StructurePoint]
    ) -> Tuple[Optional[StructurePoint], Optional[StructurePoint]]:
        """Find break of structure and change of character"""
        last_bos = None
        last_choch = None
        
        # Look for pattern changes in recent structure points
        if len(structure_points) >= 4:
            recent_points = structure_points[-4:]
            
            # Check for break of structure (continuation pattern)
            for i in range(1, len(recent_points)):
                prev_point = recent_points[i-1]
                curr_point = recent_points[i]
                
                # BOS: continuation of trend with strong momentum
                if (prev_point.structure_type == StructureType.HIGHER_HIGH and 
                    curr_point.structure_type == StructureType.HIGHER_HIGH and
                    curr_point.significance > 0.7):
                    last_bos = curr_point
                
                elif (prev_point.structure_type == StructureType.LOWER_LOW and 
                      curr_point.structure_type == StructureType.LOWER_LOW and
                      curr_point.significance > 0.7):
                    last_bos = curr_point
            
            # Check for change of character (reversal pattern)
            for i in range(1, len(recent_points)):
                prev_point = recent_points[i-1]
                curr_point = recent_points[i]
                
                # CHoCH: trend reversal pattern
                if (prev_point.structure_type in [StructureType.HIGHER_HIGH, StructureType.HIGHER_LOW] and
                    curr_point.structure_type in [StructureType.LOWER_HIGH, StructureType.LOWER_LOW]):
                    last_choch = curr_point
                
                elif (prev_point.structure_type in [StructureType.LOWER_HIGH, StructureType.LOWER_LOW] and
                      curr_point.structure_type in [StructureType.HIGHER_HIGH, StructureType.HIGHER_LOW]):
                    last_choch = curr_point
        
        return last_bos, last_choch
    
    def _calculate_confidence(
        self, 
        structure_points: List[StructurePoint], 
        trend_direction: TrendDirection
    ) -> float:
        """Calculate confidence in the market structure analysis"""
        if not structure_points:
            return 0.0
        
        # Base confidence on number of confirmed structure points
        base_confidence = min(len(structure_points) / 10.0, 0.5)
        
        # Add confidence based on trend clarity
        if trend_direction != TrendDirection.SIDEWAYS:
            base_confidence += 0.3
        
        # Add confidence based on recent structure significance
        recent_points = structure_points[-5:]
        avg_significance = sum(point.significance for point in recent_points) / len(recent_points)
        base_confidence += avg_significance * 0.2
        
        return min(base_confidence, 1.0)
    
    def get_current_trend(self) -> Optional[TrendDirection]:
        """Get current trend direction"""
        if self.last_analysis:
            return self.last_analysis.trend_direction
        return None
    
    def get_structure_summary(self) -> Dict[str, Any]:
        """Get summary of current market structure"""
        if not self.last_analysis:
            return {}
        
        return {
            "trend_direction": self.last_analysis.trend_direction.value,
            "structure_points_count": len(self.last_analysis.structure_points),
            "last_bos": self.last_analysis.last_bos.structure_type.value if self.last_analysis.last_bos else None,
            "last_choch": self.last_analysis.last_choch.structure_type.value if self.last_analysis.last_choch else None,
            "confidence": self.last_analysis.confidence
        }
