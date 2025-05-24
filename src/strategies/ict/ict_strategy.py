"""
ICT (Inner Circle Trader) Strategy Implementation

This strategy implements ICT trading concepts including:
- Market structure analysis
- Order block trading
- Fair value gaps
- Liquidity analysis
- Session-based trading
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, time

from ..base_strategy import BaseStrategy
from core.config import Settings
from core.logger import get_trading_logger
from .market_structure import MarketStructureAnalyzer, TrendDirection
from .order_blocks import OrderBlockDetector, OrderBlockSignal
from .fair_value_gaps import FairValueGapDetector, FairValueGap


class ICTStrategy(BaseStrategy):
    """
    ICT (Inner Circle Trader) Strategy

    This strategy combines multiple ICT concepts to generate trading signals:
    1. Market structure analysis for trend direction
    2. Order block identification for entry points
    3. Session analysis for timing
    4. Risk management based on ICT principles
    """

    def __init__(self, name: str, settings: Settings):
        """
        Initialize ICT strategy

        Args:
            name: Strategy name
            settings: Application settings
        """
        super().__init__(name, settings)

        self.logger = get_trading_logger(f"ICTStrategy_{name}")

        # ICT configuration
        self.ict_config = settings.strategies.ict

        # Initialize ICT components
        self.market_structure = MarketStructureAnalyzer(
            lookback_period=20,
            min_significance=0.3
        )

        self.order_blocks = OrderBlockDetector(
            min_block_size=0.001,
            max_blocks=10,
            mitigation_threshold=0.5
        )

        self.fvg_detector = FairValueGapDetector(
            min_gap_size=0.001,
            max_gaps=15
        )

        # Strategy state
        self.current_trend: Optional[TrendDirection] = None
        self.active_signals: List[Dict[str, Any]] = []
        self.last_analysis_time: Optional[datetime] = None

        # Kill zones (trading sessions)
        self.kill_zones = self.ict_config.kill_zones

        self.logger.logger.info(f"ICT Strategy '{name}' initialized")

    async def initialize(self) -> None:
        """Initialize strategy components"""
        self.logger.logger.info(f"Initializing ICT strategy: {self.name}")
        # Strategy is ready to use immediately
        pass

    async def cleanup(self) -> None:
        """Cleanup strategy resources"""
        self.logger.logger.info(f"Cleaning up ICT strategy: {self.name}")
        # Clear any cached data
        self.active_signals.clear()

    async def analyze_market(self, data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Analyze market data using ICT concepts"""
        return await self.analyze(data)

    async def analyze(self, data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Analyze market data using ICT concepts

        Args:
            data: Dictionary of timeframe data

        Returns:
            Analysis results
        """
        try:
            # Get primary timeframe data
            primary_tf = "1h"  # Primary analysis timeframe
            if primary_tf not in data or data[primary_tf].empty:
                return {"error": "No data available for analysis"}

            df = data[primary_tf]

            # Perform market structure analysis
            market_structure = self.market_structure.analyze(df)
            self.current_trend = market_structure.trend_direction

            # Detect order blocks
            new_order_blocks = self.order_blocks.detect_order_blocks(df)

            # Generate order block signals
            ob_signals = self.order_blocks.generate_signals(df)

            # Detect Fair Value Gaps
            new_fvgs = self.fvg_detector.detect_fvgs(df)

            # Generate FVG signals
            fvg_signals = self.fvg_detector.get_fvg_signals(df)

            # Check if we're in a kill zone
            in_kill_zone = self._is_in_kill_zone()

            # Generate trading signals
            signals = self._generate_trading_signals(
                market_structure,
                ob_signals,
                fvg_signals,
                df,
                in_kill_zone
            )

            # Update strategy state
            self.active_signals = signals
            self.last_analysis_time = datetime.utcnow()

            # Create analysis result
            analysis_result = {
                "timestamp": datetime.utcnow().isoformat(),
                "market_structure": {
                    "trend_direction": market_structure.trend_direction.value,
                    "confidence": market_structure.confidence,
                    "structure_points": len(market_structure.structure_points),
                    "last_bos": market_structure.last_bos.structure_type.value if market_structure.last_bos else None,
                    "last_choch": market_structure.last_choch.structure_type.value if market_structure.last_choch else None
                },
                "order_blocks": self.order_blocks.get_blocks_summary(),
                "new_order_blocks": len(new_order_blocks),
                "signals": signals,
                "in_kill_zone": in_kill_zone,
                "current_price": float(df.iloc[-1]['close'])
            }

            self.logger.logger.info(f"ICT analysis completed: {len(signals)} signals generated")

            return analysis_result

        except Exception as e:
            self.logger.error(f"Error in ICT analysis: {e}")
            return {"error": str(e)}

    def _generate_trading_signals(
        self,
        market_structure,
        ob_signals: List[OrderBlockSignal],
        fvg_signals: List[Dict[str, Any]],
        data: pd.DataFrame,
        in_kill_zone: bool
    ) -> List[Dict[str, Any]]:
        """Generate trading signals based on ICT analysis"""
        signals = []

        if not in_kill_zone:
            # Don't trade outside kill zones
            return signals

        current_price = float(data.iloc[-1]['close'])

        for ob_signal in ob_signals:
            # Filter signals based on market structure
            if not self._is_signal_aligned_with_trend(ob_signal, market_structure):
                continue

            # Create trading signal
            signal = {
                "timestamp": ob_signal.timestamp.isoformat(),
                "type": "entry",
                "direction": "long" if ob_signal.order_block.block_type.value == "bullish" else "short",
                "price": ob_signal.price,
                "confidence": ob_signal.confidence,
                "stop_loss": ob_signal.stop_loss,
                "take_profit": ob_signal.take_profit,
                "order_block_id": ob_signal.order_block.id,
                "signal_source": "order_block",
                "market_structure_trend": market_structure.trend_direction.value,
                "risk_reward_ratio": self._calculate_risk_reward(ob_signal)
            }

            # Add additional ICT context
            signal["ict_context"] = {
                "order_block_strength": ob_signal.order_block.strength,
                "market_structure_confidence": market_structure.confidence,
                "kill_zone_active": in_kill_zone
            }

            signals.append(signal)

        # Process FVG signals
        for fvg_signal in fvg_signals:
            # Filter FVG signals based on market structure
            if self._is_fvg_signal_aligned_with_trend(fvg_signal, market_structure):
                signal = {
                    "timestamp": fvg_signal["timestamp"].isoformat(),
                    "type": "entry",
                    "direction": fvg_signal["direction"],
                    "gap_id": fvg_signal["gap_id"],
                    "target_high": fvg_signal["target_high"],
                    "target_low": fvg_signal["target_low"],
                    "confidence": fvg_signal["strength"],
                    "signal_source": "fair_value_gap",
                    "market_structure_trend": market_structure.trend_direction.value,
                    "price": (fvg_signal["target_high"] + fvg_signal["target_low"]) / 2  # Mid-point entry
                }

                # Add ICT context
                signal["ict_context"] = {
                    "fvg_strength": fvg_signal["strength"],
                    "market_structure_confidence": market_structure.confidence,
                    "kill_zone_active": in_kill_zone
                }

                signals.append(signal)

        return signals

    def _is_signal_aligned_with_trend(self, signal: OrderBlockSignal, market_structure) -> bool:
        """Check if signal is aligned with market structure trend"""
        trend = market_structure.trend_direction
        signal_direction = signal.order_block.block_type.value

        # Only take signals aligned with trend
        if trend == TrendDirection.BULLISH and signal_direction == "bullish":
            return True
        elif trend == TrendDirection.BEARISH and signal_direction == "bearish":
            return True

        # Allow counter-trend signals if market structure confidence is low
        if market_structure.confidence < 0.5:
            return True

        return False

    def _is_fvg_signal_aligned_with_trend(self, fvg_signal: Dict[str, Any], market_structure) -> bool:
        """Check if FVG signal is aligned with market structure trend"""
        trend = market_structure.trend_direction
        signal_direction = fvg_signal["direction"]

        # Only take signals aligned with trend
        if trend == TrendDirection.BULLISH and signal_direction == "bullish":
            return True
        elif trend == TrendDirection.BEARISH and signal_direction == "bearish":
            return True

        # Allow counter-trend signals if market structure confidence is low
        if market_structure.confidence < 0.5:
            return True

        return False

    def _is_in_kill_zone(self) -> bool:
        """Check if current time is within a kill zone"""
        current_time = datetime.utcnow().time()

        for zone_name, time_range in self.kill_zones.items():
            start_time = time.fromisoformat(time_range[0])
            end_time = time.fromisoformat(time_range[1])

            if start_time <= current_time <= end_time:
                return True

        return False

    def _calculate_risk_reward(self, signal: OrderBlockSignal) -> float:
        """Calculate risk-reward ratio for a signal"""
        if not signal.stop_loss or not signal.take_profit:
            return 0.0

        risk = abs(signal.price - signal.stop_loss)
        reward = abs(signal.take_profit - signal.price)

        if risk == 0:
            return 0.0

        return reward / risk

    async def should_enter_trade(self, symbol: str, data: Dict[str, pd.DataFrame]) -> Optional[Dict[str, Any]]:
        """
        Determine if we should enter a trade

        Args:
            symbol: Trading symbol
            data: Market data

        Returns:
            Trade entry signal or None
        """
        # Perform analysis
        analysis = await self.analyze(data)

        if "error" in analysis:
            return None

        # Check for valid entry signals
        signals = analysis.get("signals", [])

        for signal in signals:
            if signal["type"] == "entry" and signal["confidence"] > 0.6:
                # Additional validation
                if self._validate_entry_signal(signal, analysis):
                    return {
                        "action": "enter",
                        "direction": signal["direction"],
                        "price": signal["price"],
                        "stop_loss": signal["stop_loss"],
                        "take_profit": signal["take_profit"],
                        "confidence": signal["confidence"],
                        "strategy": self.name,
                        "reason": f"ICT {signal['signal_source']} signal",
                        "metadata": signal
                    }

        return None

    def _validate_entry_signal(self, signal: Dict[str, Any], analysis: Dict[str, Any]) -> bool:
        """Validate an entry signal before execution"""
        # Check minimum confidence
        if signal["confidence"] < 0.6:
            return False

        # Check risk-reward ratio
        if signal.get("risk_reward_ratio", 0) < 1.5:
            return False

        # Check market structure confidence
        ms_confidence = analysis["market_structure"]["confidence"]
        if ms_confidence < 0.4:
            return False

        # Check if we're in a kill zone
        if not analysis["in_kill_zone"]:
            return False

        return True

    async def should_exit_trade(self, position: Dict[str, Any], data: Dict[str, pd.DataFrame]) -> Optional[Dict[str, Any]]:
        """
        Determine if we should exit a trade

        Args:
            position: Current position information
            data: Market data

        Returns:
            Trade exit signal or None
        """
        # Perform analysis
        analysis = await self.analyze(data)

        if "error" in analysis:
            return None

        # Check for exit conditions
        current_price = analysis["current_price"]
        entry_price = position.get("entry_price", 0)
        direction = position.get("direction", "")

        # Check stop loss and take profit
        stop_loss = position.get("stop_loss")
        take_profit = position.get("take_profit")

        if direction == "long":
            if stop_loss and current_price <= stop_loss:
                return {"action": "exit", "reason": "stop_loss", "price": current_price}
            if take_profit and current_price >= take_profit:
                return {"action": "exit", "reason": "take_profit", "price": current_price}

        elif direction == "short":
            if stop_loss and current_price >= stop_loss:
                return {"action": "exit", "reason": "stop_loss", "price": current_price}
            if take_profit and current_price <= take_profit:
                return {"action": "exit", "reason": "take_profit", "price": current_price}

        # Check for trend reversal
        if self._check_trend_reversal(analysis, position):
            return {"action": "exit", "reason": "trend_reversal", "price": current_price}

        return None

    def _check_trend_reversal(self, analysis: Dict[str, Any], position: Dict[str, Any]) -> bool:
        """Check if trend has reversed against our position"""
        current_trend = analysis["market_structure"]["trend_direction"]
        position_direction = position.get("direction", "")

        # Exit long positions if trend turns bearish
        if position_direction == "long" and current_trend == "bearish":
            return True

        # Exit short positions if trend turns bullish
        if position_direction == "short" and current_trend == "bullish":
            return True

        return False

    def get_strategy_status(self) -> Dict[str, Any]:
        """Get current strategy status"""
        return {
            "name": self.name,
            "type": "ICT",
            "current_trend": self.current_trend.value if self.current_trend else None,
            "active_signals": len(self.active_signals),
            "active_order_blocks": len(self.order_blocks.get_active_blocks()),
            "last_analysis": self.last_analysis_time.isoformat() if self.last_analysis_time else None,
            "in_kill_zone": self._is_in_kill_zone(),
            "enabled": self.enabled
        }
