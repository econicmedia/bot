"""
Technical Analysis Strategy

Advanced trading strategy that combines multiple technical indicators and pattern recognition
for enhanced signal generation and market analysis.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import deque

from src.core.strategy_manager import BaseStrategy
from src.core.config import Settings
from src.core.data_manager import Candle

# Import our technical analysis components
from src.analysis.indicators.moving_averages import MovingAverageIndicator
from src.analysis.indicators.oscillators import RSIIndicator
from src.analysis.indicators.momentum import MACDIndicator
from src.analysis.indicators.volatility import BollingerBandsIndicator, ATRIndicator
from src.analysis.patterns.candlestick import CandlestickPatterns


class TechnicalAnalysisStrategy(BaseStrategy):
    """Advanced strategy using multiple technical indicators and pattern recognition"""
    
    def __init__(self, name: str, settings: Settings):
        """Initialize strategy"""
        super().__init__(name, settings)
        
        # Strategy parameters
        self.symbol = "BTCUSDT"
        self.timeframe = "1h"
        
        # Technical indicators
        self.indicators = {
            "sma_20": MovingAverageIndicator(period=20, ma_type="sma", timeframe=self.timeframe),
            "ema_12": MovingAverageIndicator(period=12, ma_type="ema", timeframe=self.timeframe),
            "ema_26": MovingAverageIndicator(period=26, ma_type="ema", timeframe=self.timeframe),
            "rsi": RSIIndicator(period=14, timeframe=self.timeframe),
            "macd": MACDIndicator(fast_period=12, slow_period=26, signal_period=9, timeframe=self.timeframe),
            "bb": BollingerBandsIndicator(period=20, std_dev=2.0, timeframe=self.timeframe),
            "atr": ATRIndicator(period=14, timeframe=self.timeframe)
        }
        
        # Pattern recognition
        self.pattern_detector = CandlestickPatterns(timeframe=self.timeframe)
        
        # Signal tracking
        self.signal_history = deque(maxlen=50)
        self.last_signal_time = None
        self.min_signal_interval = 3600  # 1 hour minimum between signals
        
        # Performance tracking
        self.signals_generated = 0
        self.successful_signals = 0
        
        self.logger.logger.info(f"Technical Analysis strategy initialized with {len(self.indicators)} indicators")
    
    async def initialize(self) -> None:
        """Initialize strategy components"""
        try:
            # Initialize all indicators
            for name, indicator in self.indicators.items():
                self.logger.logger.info(f"Initialized {name} indicator")
            
            self.logger.logger.info("Technical Analysis strategy components initialized")
        except Exception as e:
            self.logger.error("Failed to initialize Technical Analysis strategy", e)
            raise
    
    async def analyze_market(self, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze market data and generate signals using technical analysis"""
        try:
            # Check if this is candle data for our symbol
            if (market_data.get("data_type") != "candle" or 
                market_data.get("symbol") != self.symbol):
                return None
            
            candle_data = market_data.get("data", {})
            if not candle_data:
                return None
            
            # Create candle object
            candle = Candle(
                symbol=candle_data["symbol"],
                timeframe=candle_data["timeframe"],
                timestamp=datetime.fromisoformat(candle_data["timestamp"]),
                open_price=candle_data["open"],
                high_price=candle_data["high"],
                low_price=candle_data["low"],
                close_price=candle_data["close"],
                volume=candle_data["volume"]
            )
            
            # Update all indicators
            indicator_results = {}
            for name, indicator in self.indicators.items():
                result = indicator.update(candle)
                if result:
                    indicator_results[name] = result
            
            # Update pattern detection
            patterns = self.pattern_detector.update(candle)
            
            # Generate trading signal
            signal = self._generate_comprehensive_signal(candle, indicator_results, patterns)
            
            if signal:
                self.signals_generated += 1
                self.signal_history.append({
                    "timestamp": datetime.utcnow(),
                    "signal": signal,
                    "price": candle.close,
                    "indicators": {name: result.value for name, result in indicator_results.items()},
                    "patterns": [p.pattern_name for p in patterns]
                })
                
                self.last_signal_time = datetime.utcnow()
                
                self.logger.logger.info(
                    f"Technical Analysis signal: {signal['action']} at {candle.close:.2f} "
                    f"(Confidence: {signal['confidence']:.2f})"
                )
                
                return signal
            
            return None
            
        except Exception as e:
            self.logger.error("Error analyzing market data in Technical Analysis strategy", e)
            return None
    
    def _generate_comprehensive_signal(
        self, 
        candle: Candle, 
        indicator_results: Dict[str, Any], 
        patterns: List[Any]
    ) -> Optional[Dict[str, Any]]:
        """Generate trading signal based on comprehensive technical analysis"""
        
        # Check minimum time interval
        if (self.last_signal_time and 
            (datetime.utcnow() - self.last_signal_time).total_seconds() < self.min_signal_interval):
            return None
        
        # Collect signals from different sources
        signals = {
            "bullish": [],
            "bearish": [],
            "neutral": []
        }
        
        # Analyze indicator signals
        self._analyze_indicator_signals(indicator_results, signals)
        
        # Analyze pattern signals
        self._analyze_pattern_signals(patterns, signals)
        
        # Calculate overall signal strength
        bullish_strength = len(signals["bullish"])
        bearish_strength = len(signals["bearish"])
        total_signals = bullish_strength + bearish_strength + len(signals["neutral"])
        
        if total_signals == 0:
            return None
        
        # Determine action based on signal strength
        min_signals = 2  # Require at least 2 confirming signals
        
        if bullish_strength >= min_signals and bullish_strength > bearish_strength:
            action = "buy"
            confidence = min(bullish_strength / 5.0, 1.0)  # Scale confidence
            reason = f"Bullish signals: {', '.join(signals['bullish'])}"
        elif bearish_strength >= min_signals and bearish_strength > bullish_strength:
            action = "sell"
            confidence = min(bearish_strength / 5.0, 1.0)
            reason = f"Bearish signals: {', '.join(signals['bearish'])}"
        else:
            return None  # Not enough conviction
        
        # Calculate position size based on volatility (ATR)
        position_size = self._calculate_position_size(indicator_results, confidence)
        
        return {
            "action": action,
            "symbol": self.symbol,
            "price": candle.close,
            "quantity": position_size,
            "reason": reason,
            "confidence": confidence,
            "timeframe": self.timeframe,
            "indicators_used": list(indicator_results.keys()),
            "patterns_detected": [p.pattern_name for p in patterns],
            "signal_breakdown": {
                "bullish": signals["bullish"],
                "bearish": signals["bearish"],
                "neutral": signals["neutral"]
            }
        }
    
    def _analyze_indicator_signals(self, indicator_results: Dict[str, Any], signals: Dict[str, List[str]]) -> None:
        """Analyze signals from technical indicators"""
        
        # Moving Average signals
        if "sma_20" in indicator_results and "ema_12" in indicator_results:
            sma_result = indicator_results["sma_20"]
            ema_result = indicator_results["ema_12"]
            
            # EMA above SMA = bullish
            if ema_result.value > sma_result.value:
                signals["bullish"].append("EMA > SMA")
            elif ema_result.value < sma_result.value:
                signals["bearish"].append("EMA < SMA")
        
        # RSI signals
        if "rsi" in indicator_results:
            rsi_result = indicator_results["rsi"]
            if rsi_result.signal == "buy":
                signals["bullish"].append("RSI Oversold")
            elif rsi_result.signal == "sell":
                signals["bearish"].append("RSI Overbought")
        
        # MACD signals
        if "macd" in indicator_results:
            macd_result = indicator_results["macd"]
            if macd_result.signal == "buy":
                signals["bullish"].append("MACD Bullish")
            elif macd_result.signal == "sell":
                signals["bearish"].append("MACD Bearish")
        
        # Bollinger Bands signals
        if "bb" in indicator_results:
            bb_result = indicator_results["bb"]
            if bb_result.signal == "buy":
                signals["bullish"].append("BB Lower Band")
            elif bb_result.signal == "sell":
                signals["bearish"].append("BB Upper Band")
        
        # ATR for volatility context
        if "atr" in indicator_results:
            atr_result = indicator_results["atr"]
            volatility_level = self.indicators["atr"].get_volatility_level()
            if volatility_level == "high":
                signals["neutral"].append("High Volatility")
            elif volatility_level == "low":
                signals["neutral"].append("Low Volatility")
    
    def _analyze_pattern_signals(self, patterns: List[Any], signals: Dict[str, List[str]]) -> None:
        """Analyze signals from pattern recognition"""
        for pattern in patterns:
            if pattern.confidence >= 0.6:  # Only consider high-confidence patterns
                if pattern.signal.value == "bullish":
                    signals["bullish"].append(f"Pattern: {pattern.pattern_name}")
                elif pattern.signal.value == "bearish":
                    signals["bearish"].append(f"Pattern: {pattern.pattern_name}")
                else:
                    signals["neutral"].append(f"Pattern: {pattern.pattern_name}")
    
    def _calculate_position_size(self, indicator_results: Dict[str, Any], confidence: float) -> float:
        """Calculate position size based on volatility and confidence"""
        base_size = 1.0
        
        # Adjust for volatility (ATR)
        if "atr" in indicator_results:
            volatility_level = self.indicators["atr"].get_volatility_level()
            if volatility_level == "high":
                base_size *= 0.5  # Reduce size in high volatility
            elif volatility_level == "low":
                base_size *= 1.5  # Increase size in low volatility
        
        # Adjust for confidence
        size_multiplier = 0.5 + (confidence * 0.5)  # Range: 0.5 to 1.0
        
        return base_size * size_multiplier
    
    async def cleanup(self) -> None:
        """Cleanup strategy resources"""
        try:
            # Reset all indicators
            for indicator in self.indicators.values():
                indicator.reset()
            
            # Reset pattern detector
            self.pattern_detector.reset()
            
            # Clear signal history
            self.signal_history.clear()
            
            self.logger.logger.info("Technical Analysis strategy cleaned up")
        except Exception as e:
            self.logger.error("Error cleaning up Technical Analysis strategy", e)
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information"""
        indicator_status = {}
        for name, indicator in self.indicators.items():
            indicator_status[name] = {
                "ready": indicator.is_ready(),
                "current_value": indicator.get_current_value(),
                "signal": indicator.get_signal()
            }
        
        return {
            "name": self.name,
            "type": "technical_analysis",
            "parameters": {
                "symbol": self.symbol,
                "timeframe": self.timeframe,
                "indicators": list(self.indicators.keys()),
                "min_signal_interval": self.min_signal_interval
            },
            "state": {
                "signals_generated": self.signals_generated,
                "successful_signals": self.successful_signals,
                "last_signal_time": self.last_signal_time.isoformat() if self.last_signal_time else None,
                "recent_signals": len(self.signal_history)
            },
            "indicators": indicator_status,
            "patterns": {
                "detector_ready": self.pattern_detector.is_ready(),
                "patterns_detected": len(self.pattern_detector.detected_patterns)
            }
        }
