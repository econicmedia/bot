"""
Fair Value Gap Detection for ICT Strategy

Implements Fair Value Gap (FVG) detection according to ICT concepts.
A Fair Value Gap is an imbalance in price where there's a gap between
the high of one candle and the low of another candle with one candle in between.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import pandas as pd
import numpy as np


class FVGType(Enum):
    """Fair Value Gap type"""
    BULLISH = "bullish"
    BEARISH = "bearish"


class FVGStatus(Enum):
    """Fair Value Gap status"""
    ACTIVE = "active"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    INVALIDATED = "invalidated"


@dataclass
class FairValueGap:
    """Fair Value Gap data structure"""
    id: str
    timestamp: datetime
    fvg_type: FVGType
    high: float
    low: float
    gap_size: float
    strength: float  # 0.0 to 1.0
    status: FVGStatus = FVGStatus.ACTIVE
    fill_percentage: float = 0.0
    last_test: Optional[datetime] = None


class FairValueGapDetector:
    """
    Fair Value Gap detector for ICT strategy

    Detects and tracks Fair Value Gaps (FVGs) in price data.
    FVGs are imbalances in price that often get filled by future price action.
    """

    def __init__(self, min_gap_size: float = 0.001, max_gaps: int = 20):
        """
        Initialize FVG detector

        Args:
            min_gap_size: Minimum gap size as percentage of price
            max_gaps: Maximum number of active gaps to track
        """
        self.min_gap_size = min_gap_size
        self.max_gaps = max_gaps

        # State tracking
        self.active_gaps: List[FairValueGap] = []
        self.filled_gaps: List[FairValueGap] = []
        self.gap_counter = 0

    def detect_fvgs(self, data: pd.DataFrame) -> List[FairValueGap]:
        """
        Detect fair value gaps in price data

        Args:
            data: OHLCV DataFrame with columns ['open', 'high', 'low', 'close', 'volume']

        Returns:
            List of newly detected FVGs
        """
        if len(data) < 3:
            return []

        new_gaps = []

        # Check last few candles for new FVGs
        for i in range(2, min(len(data), 10)):  # Check last 10 candles
            # Get three consecutive candles
            candle1 = data.iloc[-(i+1)]  # First candle
            candle2 = data.iloc[-i]      # Middle candle
            candle3 = data.iloc[-(i-1)]  # Third candle

            # Check for bullish FVG
            bullish_gap = self._detect_bullish_fvg(candle1, candle2, candle3)
            if bullish_gap:
                new_gaps.append(bullish_gap)

            # Check for bearish FVG
            bearish_gap = self._detect_bearish_fvg(candle1, candle2, candle3)
            if bearish_gap:
                new_gaps.append(bearish_gap)

        # Add new gaps to active list
        for gap in new_gaps:
            self.active_gaps.append(gap)

        # Limit number of active gaps
        if len(self.active_gaps) > self.max_gaps:
            # Remove oldest gaps
            self.active_gaps = self.active_gaps[-self.max_gaps:]

        # Update existing gaps
        self._update_gaps(data)

        return new_gaps

    def _detect_bullish_fvg(self, candle1: pd.Series, candle2: pd.Series, candle3: pd.Series) -> Optional[FairValueGap]:
        """Detect bullish Fair Value Gap"""
        # Bullish FVG: Gap between high of candle1 and low of candle3
        # with candle2 in between (upward move)

        gap_low = candle1['high']
        gap_high = candle3['low']

        # Check if there's actually a gap
        if gap_high <= gap_low:
            return None

        gap_size = gap_high - gap_low
        gap_size_pct = gap_size / candle2['close']

        # Check minimum gap size
        if gap_size_pct < self.min_gap_size:
            return None

        # Check if it's a valid bullish move
        if candle3['close'] <= candle1['close']:
            return None

        # Calculate strength based on volume and gap size
        strength = self._calculate_gap_strength(candle1, candle2, candle3, gap_size_pct)

        self.gap_counter += 1
        return FairValueGap(
            id=f"FVG_BULL_{self.gap_counter}",
            timestamp=candle3.name,
            fvg_type=FVGType.BULLISH,
            high=gap_high,
            low=gap_low,
            gap_size=gap_size,
            strength=strength
        )

    def _detect_bearish_fvg(self, candle1: pd.Series, candle2: pd.Series, candle3: pd.Series) -> Optional[FairValueGap]:
        """Detect bearish Fair Value Gap"""
        # Bearish FVG: Gap between low of candle1 and high of candle3
        # with candle2 in between (downward move)

        gap_high = candle1['low']
        gap_low = candle3['high']

        # Check if there's actually a gap
        if gap_low >= gap_high:
            return None

        gap_size = gap_high - gap_low
        gap_size_pct = gap_size / candle2['close']

        # Check minimum gap size
        if gap_size_pct < self.min_gap_size:
            return None

        # Check if it's a valid bearish move
        if candle3['close'] >= candle1['close']:
            return None

        # Calculate strength based on volume and gap size
        strength = self._calculate_gap_strength(candle1, candle2, candle3, gap_size_pct)

        self.gap_counter += 1
        return FairValueGap(
            id=f"FVG_BEAR_{self.gap_counter}",
            timestamp=candle3.name,
            fvg_type=FVGType.BEARISH,
            high=gap_high,
            low=gap_low,
            gap_size=gap_size,
            strength=strength
        )

    def _calculate_gap_strength(self, candle1: pd.Series, candle2: pd.Series, candle3: pd.Series, gap_size_pct: float) -> float:
        """Calculate the strength of a Fair Value Gap"""
        # Base strength from gap size
        strength = min(gap_size_pct * 100, 1.0)  # Cap at 1.0

        # Adjust for volume
        avg_volume = (candle1['volume'] + candle2['volume'] + candle3['volume']) / 3
        if avg_volume > 0:
            volume_factor = min(candle2['volume'] / avg_volume, 2.0)
            strength *= (0.5 + volume_factor * 0.5)

        # Adjust for candle body size (larger bodies = stronger gaps)
        body_size = abs(candle2['close'] - candle2['open']) / candle2['close']
        strength *= (0.7 + body_size * 0.3)

        return min(strength, 1.0)

    def _update_gaps(self, data: pd.DataFrame) -> None:
        """Update status of existing Fair Value Gaps"""
        if data.empty:
            return

        current_price = data.iloc[-1]['close']
        current_high = data.iloc[-1]['high']
        current_low = data.iloc[-1]['low']
        current_time = data.index[-1]

        gaps_to_remove = []

        for gap in self.active_gaps:
            # Check if gap has been filled
            fill_percentage = self._calculate_fill_percentage(gap, current_high, current_low)
            gap.fill_percentage = fill_percentage

            if fill_percentage >= 1.0:
                gap.status = FVGStatus.FILLED
                gaps_to_remove.append(gap)
            elif fill_percentage > 0:
                gap.status = FVGStatus.PARTIALLY_FILLED
                gap.last_test = current_time

            # Check if price is testing the gap
            if self._is_price_testing_gap(gap, current_high, current_low):
                gap.last_test = current_time

        # Move filled gaps to history
        for gap in gaps_to_remove:
            self.active_gaps.remove(gap)
            self.filled_gaps.append(gap)

    def _calculate_fill_percentage(self, gap: FairValueGap, current_high: float, current_low: float) -> float:
        """Calculate how much of the gap has been filled"""
        if gap.fvg_type == FVGType.BULLISH:
            # For bullish gaps, check how much price has moved down into the gap
            if current_low >= gap.high:
                return 0.0  # No fill
            elif current_low <= gap.low:
                return 1.0  # Completely filled
            else:
                return (gap.high - current_low) / gap.gap_size
        else:  # Bearish gap
            # For bearish gaps, check how much price has moved up into the gap
            if current_high <= gap.low:
                return 0.0  # No fill
            elif current_high >= gap.high:
                return 1.0  # Completely filled
            else:
                return (current_high - gap.low) / gap.gap_size

    def _is_price_testing_gap(self, gap: FairValueGap, current_high: float, current_low: float) -> bool:
        """Check if current price is testing the gap"""
        if gap.fvg_type == FVGType.BULLISH:
            return current_low <= gap.high and current_high >= gap.low
        else:
            return current_high >= gap.low and current_low <= gap.high

    def get_active_fvgs(self) -> List[FairValueGap]:
        """Get active fair value gaps"""
        return self.active_gaps.copy()

    def get_filled_fvgs(self) -> List[FairValueGap]:
        """Get filled fair value gaps"""
        return self.filled_gaps.copy()

    def get_fvg_signals(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Generate trading signals based on FVG analysis

        Returns:
            List of trading signals
        """
        signals = []

        if data.empty:
            return signals

        current_price = data.iloc[-1]['close']

        for gap in self.active_gaps:
            # Signal when price approaches an unfilled gap
            if gap.status == FVGStatus.ACTIVE:
                if gap.fvg_type == FVGType.BULLISH and current_price > gap.high:
                    # Price above bullish gap - potential retracement target
                    signals.append({
                        'type': 'fvg_retracement',
                        'direction': 'bearish',
                        'gap_id': gap.id,
                        'target_high': gap.high,
                        'target_low': gap.low,
                        'strength': gap.strength,
                        'timestamp': data.index[-1]
                    })
                elif gap.fvg_type == FVGType.BEARISH and current_price < gap.low:
                    # Price below bearish gap - potential retracement target
                    signals.append({
                        'type': 'fvg_retracement',
                        'direction': 'bullish',
                        'gap_id': gap.id,
                        'target_high': gap.high,
                        'target_low': gap.low,
                        'strength': gap.strength,
                        'timestamp': data.index[-1]
                    })

        return signals
