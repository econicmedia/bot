"""
Order Block Detection for ICT Strategy

Implements order block identification and analysis including:
- Bullish and bearish order blocks
- Order block validation and strength
- Mitigation and retest detection
- Entry and exit signals based on order blocks
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum


class OrderBlockType(Enum):
    """Order block type enumeration"""
    BULLISH = "bullish"
    BEARISH = "bearish"


class OrderBlockStatus(Enum):
    """Order block status"""
    ACTIVE = "active"
    MITIGATED = "mitigated"
    INVALIDATED = "invalidated"


@dataclass
class OrderBlock:
    """Order block data structure"""
    id: str
    timestamp: datetime
    block_type: OrderBlockType
    high: float
    low: float
    open: float
    close: float
    volume: float
    strength: float  # 0.0 to 1.0
    status: OrderBlockStatus = OrderBlockStatus.ACTIVE
    mitigation_count: int = 0
    last_test: Optional[datetime] = None


@dataclass
class OrderBlockSignal:
    """Order block trading signal"""
    timestamp: datetime
    order_block: OrderBlock
    signal_type: str  # "entry", "exit", "retest"
    price: float
    confidence: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


class OrderBlockDetector:
    """
    Detects and analyzes order blocks for ICT trading
    
    Order blocks are areas where institutional orders are placed,
    creating significant support or resistance levels. This detector
    identifies these blocks and provides trading signals based on
    their interaction with price.
    """
    
    def __init__(
        self,
        min_block_size: float = 0.001,  # Minimum block size as percentage
        max_blocks: int = 10,           # Maximum number of active blocks
        mitigation_threshold: float = 0.5  # Percentage of block that must be mitigated
    ):
        """
        Initialize order block detector
        
        Args:
            min_block_size: Minimum size of order block as percentage of price
            max_blocks: Maximum number of active order blocks to track
            mitigation_threshold: Threshold for considering a block mitigated
        """
        self.min_block_size = min_block_size
        self.max_blocks = max_blocks
        self.mitigation_threshold = mitigation_threshold
        
        # State tracking
        self.active_blocks: List[OrderBlock] = []
        self.mitigated_blocks: List[OrderBlock] = []
        self.block_counter = 0
        
    def detect_order_blocks(self, data: pd.DataFrame) -> List[OrderBlock]:
        """
        Detect order blocks in price data
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            List of detected order blocks
        """
        new_blocks = []
        
        if len(data) < 10:
            return new_blocks
        
        # Look for potential order blocks in recent data
        for i in range(5, len(data) - 1):
            # Check for bullish order block pattern
            bullish_block = self._check_bullish_order_block(data, i)
            if bullish_block:
                new_blocks.append(bullish_block)
            
            # Check for bearish order block pattern
            bearish_block = self._check_bearish_order_block(data, i)
            if bearish_block:
                new_blocks.append(bearish_block)
        
        # Add new blocks to active list
        for block in new_blocks:
            self._add_order_block(block)
        
        # Update existing blocks
        self._update_order_blocks(data)
        
        return new_blocks
    
    def _check_bullish_order_block(self, data: pd.DataFrame, index: int) -> Optional[OrderBlock]:
        """Check for bullish order block pattern at given index"""
        if index < 5 or index >= len(data) - 1:
            return None
        
        current_candle = data.iloc[index]
        next_candle = data.iloc[index + 1]
        
        # Bullish order block criteria:
        # 1. Current candle is bearish or small bullish
        # 2. Next candle is strongly bullish and breaks above current high
        # 3. Volume is above average
        
        # Check if current candle is suitable for order block
        current_body_size = abs(current_candle['close'] - current_candle['open'])
        current_range = current_candle['high'] - current_candle['low']
        
        if current_body_size / current_range > 0.7:  # Too much body, not ideal
            return None
        
        # Check if next candle is strongly bullish
        next_body_size = next_candle['close'] - next_candle['open']
        next_range = next_candle['high'] - next_candle['low']
        
        if (next_candle['close'] <= next_candle['open'] or  # Not bullish
            next_body_size / next_range < 0.6 or  # Not strong enough
            next_candle['high'] <= current_candle['high']):  # Doesn't break above
            return None
        
        # Check volume
        avg_volume = data['volume'].rolling(20).mean().iloc[index]
        if current_candle['volume'] < avg_volume * 0.8:
            return None
        
        # Calculate block strength
        strength = self._calculate_block_strength(data, index, OrderBlockType.BULLISH)
        
        # Check minimum block size
        block_size = (current_candle['high'] - current_candle['low']) / current_candle['close']
        if block_size < self.min_block_size:
            return None
        
        # Create order block
        self.block_counter += 1
        return OrderBlock(
            id=f"OB_{self.block_counter}",
            timestamp=current_candle.name,
            block_type=OrderBlockType.BULLISH,
            high=current_candle['high'],
            low=current_candle['low'],
            open=current_candle['open'],
            close=current_candle['close'],
            volume=current_candle['volume'],
            strength=strength
        )
    
    def _check_bearish_order_block(self, data: pd.DataFrame, index: int) -> Optional[OrderBlock]:
        """Check for bearish order block pattern at given index"""
        if index < 5 or index >= len(data) - 1:
            return None
        
        current_candle = data.iloc[index]
        next_candle = data.iloc[index + 1]
        
        # Bearish order block criteria:
        # 1. Current candle is bullish or small bearish
        # 2. Next candle is strongly bearish and breaks below current low
        # 3. Volume is above average
        
        # Check if current candle is suitable for order block
        current_body_size = abs(current_candle['close'] - current_candle['open'])
        current_range = current_candle['high'] - current_candle['low']
        
        if current_body_size / current_range > 0.7:  # Too much body, not ideal
            return None
        
        # Check if next candle is strongly bearish
        next_body_size = next_candle['open'] - next_candle['close']
        next_range = next_candle['high'] - next_candle['low']
        
        if (next_candle['close'] >= next_candle['open'] or  # Not bearish
            next_body_size / next_range < 0.6 or  # Not strong enough
            next_candle['low'] >= current_candle['low']):  # Doesn't break below
            return None
        
        # Check volume
        avg_volume = data['volume'].rolling(20).mean().iloc[index]
        if current_candle['volume'] < avg_volume * 0.8:
            return None
        
        # Calculate block strength
        strength = self._calculate_block_strength(data, index, OrderBlockType.BEARISH)
        
        # Check minimum block size
        block_size = (current_candle['high'] - current_candle['low']) / current_candle['close']
        if block_size < self.min_block_size:
            return None
        
        # Create order block
        self.block_counter += 1
        return OrderBlock(
            id=f"OB_{self.block_counter}",
            timestamp=current_candle.name,
            block_type=OrderBlockType.BEARISH,
            high=current_candle['high'],
            low=current_candle['low'],
            open=current_candle['open'],
            close=current_candle['close'],
            volume=current_candle['volume'],
            strength=strength
        )
    
    def _calculate_block_strength(
        self, 
        data: pd.DataFrame, 
        index: int, 
        block_type: OrderBlockType
    ) -> float:
        """Calculate the strength of an order block"""
        strength = 0.0
        
        # Base strength from volume
        avg_volume = data['volume'].rolling(20).mean().iloc[index]
        volume_ratio = data.iloc[index]['volume'] / avg_volume
        strength += min(volume_ratio / 3.0, 0.4)  # Max 0.4 from volume
        
        # Strength from price movement after block
        if index < len(data) - 5:
            future_data = data.iloc[index+1:index+6]
            
            if block_type == OrderBlockType.BULLISH:
                # Check how much price moved up after bullish block
                max_high = future_data['high'].max()
                block_high = data.iloc[index]['high']
                if max_high > block_high:
                    move_pct = (max_high - block_high) / block_high
                    strength += min(move_pct * 10, 0.4)  # Max 0.4 from movement
            
            else:  # Bearish block
                # Check how much price moved down after bearish block
                min_low = future_data['low'].min()
                block_low = data.iloc[index]['low']
                if min_low < block_low:
                    move_pct = (block_low - min_low) / block_low
                    strength += min(move_pct * 10, 0.4)  # Max 0.4 from movement
        
        # Strength from block size relative to recent volatility
        block_size = data.iloc[index]['high'] - data.iloc[index]['low']
        avg_range = data['high'].rolling(20).mean().iloc[index] - data['low'].rolling(20).mean().iloc[index]
        if avg_range > 0:
            size_ratio = block_size / avg_range
            strength += min(size_ratio / 2.0, 0.2)  # Max 0.2 from size
        
        return min(strength, 1.0)
    
    def _add_order_block(self, block: OrderBlock) -> None:
        """Add a new order block to the active list"""
        self.active_blocks.append(block)
        
        # Remove oldest blocks if we exceed maximum
        if len(self.active_blocks) > self.max_blocks:
            # Sort by strength and keep the strongest blocks
            self.active_blocks.sort(key=lambda x: x.strength, reverse=True)
            removed_block = self.active_blocks.pop()
            self.mitigated_blocks.append(removed_block)
    
    def _update_order_blocks(self, data: pd.DataFrame) -> None:
        """Update status of existing order blocks"""
        current_price = data.iloc[-1]['close']
        current_time = data.index[-1]
        
        blocks_to_remove = []
        
        for block in self.active_blocks:
            # Check if block has been mitigated
            if self._is_block_mitigated(block, data):
                block.status = OrderBlockStatus.MITIGATED
                block.mitigation_count += 1
                blocks_to_remove.append(block)
            
            # Check if block has been invalidated (price moved too far away)
            elif self._is_block_invalidated(block, current_price):
                block.status = OrderBlockStatus.INVALIDATED
                blocks_to_remove.append(block)
            
            # Update last test time if price is near block
            elif self._is_price_near_block(block, current_price):
                block.last_test = current_time
        
        # Move mitigated/invalidated blocks to history
        for block in blocks_to_remove:
            self.active_blocks.remove(block)
            self.mitigated_blocks.append(block)
    
    def _is_block_mitigated(self, block: OrderBlock, data: pd.DataFrame) -> bool:
        """Check if an order block has been mitigated"""
        recent_data = data.tail(10)  # Check last 10 candles
        
        block_range = block.high - block.low
        mitigation_level = block_range * self.mitigation_threshold
        
        if block.block_type == OrderBlockType.BULLISH:
            # Bullish block is mitigated when price moves significantly into the block from above
            for _, candle in recent_data.iterrows():
                if (candle['low'] <= block.high and 
                    candle['low'] >= block.low and
                    (block.high - candle['low']) >= mitigation_level):
                    return True
        
        else:  # Bearish block
            # Bearish block is mitigated when price moves significantly into the block from below
            for _, candle in recent_data.iterrows():
                if (candle['high'] >= block.low and 
                    candle['high'] <= block.high and
                    (candle['high'] - block.low) >= mitigation_level):
                    return True
        
        return False
    
    def _is_block_invalidated(self, block: OrderBlock, current_price: float) -> bool:
        """Check if an order block has been invalidated"""
        # Block is invalidated if price moves too far away (more than 5% of block range)
        block_range = block.high - block.low
        invalidation_distance = block_range * 5.0
        
        if block.block_type == OrderBlockType.BULLISH:
            # Bullish block invalidated if price goes too far below
            return current_price < (block.low - invalidation_distance)
        else:
            # Bearish block invalidated if price goes too far above
            return current_price > (block.high + invalidation_distance)
    
    def _is_price_near_block(self, block: OrderBlock, current_price: float) -> bool:
        """Check if current price is near an order block"""
        block_range = block.high - block.low
        near_distance = block_range * 0.5  # Within 50% of block range
        
        return (current_price >= (block.low - near_distance) and 
                current_price <= (block.high + near_distance))
    
    def generate_signals(self, data: pd.DataFrame) -> List[OrderBlockSignal]:
        """Generate trading signals based on order block analysis"""
        signals = []
        
        if len(data) < 2:
            return signals
        
        current_candle = data.iloc[-1]
        current_price = current_candle['close']
        
        for block in self.active_blocks:
            # Check for entry signals
            signal = self._check_entry_signal(block, current_candle)
            if signal:
                signals.append(signal)
            
            # Check for retest signals
            retest_signal = self._check_retest_signal(block, current_candle)
            if retest_signal:
                signals.append(retest_signal)
        
        return signals
    
    def _check_entry_signal(self, block: OrderBlock, candle: pd.Series) -> Optional[OrderBlockSignal]:
        """Check for entry signal at order block"""
        if block.block_type == OrderBlockType.BULLISH:
            # Bullish entry: price touches block from above and shows bullish reaction
            if (candle['low'] <= block.high and 
                candle['low'] >= block.low and
                candle['close'] > candle['open']):  # Bullish candle
                
                confidence = block.strength * 0.8  # Base confidence on block strength
                
                return OrderBlockSignal(
                    timestamp=candle.name,
                    order_block=block,
                    signal_type="entry",
                    price=candle['close'],
                    confidence=confidence,
                    stop_loss=block.low * 0.999,  # Just below block
                    take_profit=block.high + (block.high - block.low) * 2  # 2:1 RR
                )
        
        else:  # Bearish block
            # Bearish entry: price touches block from below and shows bearish reaction
            if (candle['high'] >= block.low and 
                candle['high'] <= block.high and
                candle['close'] < candle['open']):  # Bearish candle
                
                confidence = block.strength * 0.8
                
                return OrderBlockSignal(
                    timestamp=candle.name,
                    order_block=block,
                    signal_type="entry",
                    price=candle['close'],
                    confidence=confidence,
                    stop_loss=block.high * 1.001,  # Just above block
                    take_profit=block.low - (block.high - block.low) * 2  # 2:1 RR
                )
        
        return None
    
    def _check_retest_signal(self, block: OrderBlock, candle: pd.Series) -> Optional[OrderBlockSignal]:
        """Check for retest signal at order block"""
        # Retest occurs when price returns to a previously respected block
        if block.mitigation_count > 0:  # Block has been tested before
            if self._is_price_near_block(block, candle['close']):
                return OrderBlockSignal(
                    timestamp=candle.name,
                    order_block=block,
                    signal_type="retest",
                    price=candle['close'],
                    confidence=block.strength * 0.6  # Lower confidence for retests
                )
        
        return None
    
    def get_active_blocks(self) -> List[OrderBlock]:
        """Get list of active order blocks"""
        return self.active_blocks.copy()
    
    def get_blocks_summary(self) -> Dict[str, Any]:
        """Get summary of order block analysis"""
        return {
            "active_blocks": len(self.active_blocks),
            "mitigated_blocks": len(self.mitigated_blocks),
            "bullish_blocks": len([b for b in self.active_blocks if b.block_type == OrderBlockType.BULLISH]),
            "bearish_blocks": len([b for b in self.active_blocks if b.block_type == OrderBlockType.BEARISH]),
            "avg_strength": sum(b.strength for b in self.active_blocks) / len(self.active_blocks) if self.active_blocks else 0.0
        }
