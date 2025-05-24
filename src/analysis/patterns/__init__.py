"""
Pattern Recognition Module

Provides comprehensive pattern recognition capabilities including:
- Candlestick pattern detection
- Chart pattern identification
- Support and resistance level detection
"""

from .base import PatternDetector, PatternResult, PatternType
from .candlestick import CandlestickPatterns
from .chart_patterns import ChartPatterns

__all__ = [
    # Base classes
    "PatternDetector",
    "PatternResult", 
    "PatternType",
    
    # Pattern detectors
    "CandlestickPatterns",
    "ChartPatterns",
]
