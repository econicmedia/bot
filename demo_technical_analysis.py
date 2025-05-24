#!/usr/bin/env python3
"""
Demo script for the Technical Analysis Engine

This script demonstrates the new technical analysis capabilities including:
- Technical indicators (Moving Averages, RSI, MACD, Bollinger Bands)
- Pattern recognition (Candlestick patterns)
- Integration with the existing trading engine
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import List

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.data_manager import Candle
from core.config import get_settings
from core.logger import setup_logging

# Import our new technical analysis components
from analysis.indicators.moving_averages import MovingAverageIndicator
from analysis.indicators.oscillators import RSIIndicator
from analysis.indicators.momentum import MACDIndicator
from analysis.indicators.volatility import BollingerBandsIndicator
from analysis.patterns.candlestick import CandlestickPatterns


def create_realistic_market_data(count: int = 100) -> List[Candle]:
    """Create realistic market data for demonstration"""
    candles = []
    base_price = 50000.0  # Starting at $50,000 (like Bitcoin)
    
    print(f"📊 Generating {count} candles of realistic market data...")
    
    for i in range(count):
        # Simulate realistic price movements
        if i < 30:
            # Uptrend phase
            trend = 0.002 + (i * 0.0001)
        elif i < 60:
            # Consolidation phase
            trend = 0.0005 * (1 if i % 2 == 0 else -1)
        else:
            # Downtrend phase
            trend = -0.001 - ((i - 60) * 0.0001)
        
        # Add some randomness
        import random
        random_factor = random.uniform(-0.01, 0.01)
        price_change = trend + random_factor
        
        new_price = base_price * (1 + price_change)
        
        # Create realistic OHLC
        open_price = base_price
        close_price = new_price
        
        if close_price > open_price:  # Bullish candle
            high_price = close_price * (1 + random.uniform(0, 0.005))
            low_price = open_price * (1 - random.uniform(0, 0.003))
        else:  # Bearish candle
            high_price = open_price * (1 + random.uniform(0, 0.003))
            low_price = close_price * (1 - random.uniform(0, 0.005))
        
        candle = Candle(
            symbol="BTCUSDT",
            timeframe="1h",
            timestamp=datetime.utcnow() + timedelta(hours=i),
            open_price=open_price,
            high_price=high_price,
            low_price=low_price,
            close_price=close_price,
            volume=random.uniform(100, 1000)
        )
        
        candles.append(candle)
        base_price = new_price
    
    print(f"✅ Generated market data: ${candles[0].close:.2f} → ${candles[-1].close:.2f}")
    return candles


async def demo_technical_indicators():
    """Demonstrate technical indicators"""
    print("\n" + "="*60)
    print("🔧 TECHNICAL INDICATORS DEMONSTRATION")
    print("="*60)
    
    # Create test data
    candles = create_realistic_market_data(50)
    
    # Initialize indicators
    indicators = {
        "SMA_20": MovingAverageIndicator(period=20, ma_type="sma"),
        "EMA_12": MovingAverageIndicator(period=12, ma_type="ema"),
        "RSI_14": RSIIndicator(period=14),
        "MACD": MACDIndicator(fast_period=12, slow_period=26, signal_period=9),
        "BB_20": BollingerBandsIndicator(period=20, std_dev=2.0)
    }
    
    print(f"\n📈 Processing {len(candles)} candles through {len(indicators)} indicators...")
    
    # Process candles through indicators
    results = {name: [] for name in indicators.keys()}
    
    for i, candle in enumerate(candles):
        print(f"\r⏳ Processing candle {i+1}/{len(candles)}: ${candle.close:.2f}", end="")
        
        for name, indicator in indicators.items():
            result = indicator.update(candle)
            if result:
                results[name].append(result)
    
    print("\n")
    
    # Display results
    for name, indicator_results in results.items():
        if indicator_results:
            latest = indicator_results[-1]
            print(f"\n📊 {name}:")
            print(f"   Current Value: {latest.value}")
            print(f"   Signal: {latest.signal}")
            print(f"   Confidence: {latest.confidence:.2f}")
            
            # Show trend for moving averages
            if "MA" in name and len(indicator_results) >= 2:
                prev_value = indicator_results[-2].value
                trend = "📈 Rising" if latest.value > prev_value else "📉 Falling"
                print(f"   Trend: {trend}")
    
    # Demonstrate crossover signals
    sma_indicator = indicators["SMA_20"]
    ema_indicator = indicators["EMA_12"]
    
    if len(sma_indicator.results) > 0 and len(ema_indicator.results) > 0:
        cross_signal = ema_indicator.get_ma_cross_signals(sma_indicator)
        if cross_signal:
            print(f"\n🎯 MA Crossover Signal: {cross_signal}")


async def demo_pattern_recognition():
    """Demonstrate pattern recognition"""
    print("\n" + "="*60)
    print("🔍 PATTERN RECOGNITION DEMONSTRATION")
    print("="*60)
    
    # Create test data with some specific patterns
    candles = create_realistic_market_data(30)
    
    # Initialize pattern detector
    pattern_detector = CandlestickPatterns(timeframe="1h")
    
    print(f"\n🕵️ Analyzing {len(candles)} candles for patterns...")
    
    all_patterns = []
    
    for i, candle in enumerate(candles):
        patterns = pattern_detector.update(candle)
        if patterns:
            all_patterns.extend(patterns)
            for pattern in patterns:
                print(f"\n🎯 Pattern Detected at Candle {i+1}:")
                print(f"   Name: {pattern.pattern_name}")
                print(f"   Signal: {pattern.signal.value}")
                print(f"   Confidence: {pattern.confidence:.2f}")
                print(f"   Price: ${candle.close:.2f}")
    
    if not all_patterns:
        print("   No significant patterns detected in this dataset")
    else:
        print(f"\n📊 Summary: {len(all_patterns)} patterns detected")
        
        # Group by pattern type
        pattern_counts = {}
        for pattern in all_patterns:
            pattern_counts[pattern.pattern_name] = pattern_counts.get(pattern.pattern_name, 0) + 1
        
        for pattern_name, count in pattern_counts.items():
            print(f"   {pattern_name}: {count}")


async def demo_integrated_analysis():
    """Demonstrate integrated technical analysis"""
    print("\n" + "="*60)
    print("🔗 INTEGRATED ANALYSIS DEMONSTRATION")
    print("="*60)
    
    # Create test data
    candles = create_realistic_market_data(40)
    
    # Initialize components
    rsi = RSIIndicator(period=14)
    bb = BollingerBandsIndicator(period=20)
    patterns = CandlestickPatterns()
    
    print(f"\n🧠 Running integrated analysis on {len(candles)} candles...")
    
    signals = []
    
    for i, candle in enumerate(candles):
        # Update all indicators
        rsi_result = rsi.update(candle)
        bb_result = bb.update(candle)
        pattern_results = patterns.update(candle)
        
        # Combine signals for trading decision
        if rsi_result and bb_result:
            current_signals = []
            
            # RSI signals
            if rsi_result.signal == "buy":
                current_signals.append("RSI: Oversold")
            elif rsi_result.signal == "sell":
                current_signals.append("RSI: Overbought")
            
            # Bollinger Bands signals
            if bb_result.signal == "buy":
                current_signals.append("BB: Near Lower Band")
            elif bb_result.signal == "sell":
                current_signals.append("BB: Near Upper Band")
            
            # Pattern signals
            for pattern in pattern_results:
                if pattern.confidence > 0.6:
                    current_signals.append(f"Pattern: {pattern.pattern_name}")
            
            if current_signals:
                signals.append({
                    "candle": i + 1,
                    "price": candle.close,
                    "signals": current_signals,
                    "rsi": rsi_result.value,
                    "bb_percent": bb_result.value.get("percent_b", 0) if isinstance(bb_result.value, dict) else 0
                })
    
    # Display integrated signals
    print(f"\n📡 Found {len(signals)} significant signal combinations:")
    
    for signal_data in signals[-5:]:  # Show last 5 signals
        print(f"\n🎯 Candle {signal_data['candle']} (${signal_data['price']:.2f}):")
        print(f"   RSI: {signal_data['rsi']:.1f}")
        print(f"   BB %B: {signal_data['bb_percent']:.2f}")
        print("   Signals:")
        for signal in signal_data['signals']:
            print(f"     • {signal}")


async def main():
    """Main demonstration function"""
    print("🚀 AI Trading Bot - Technical Analysis Engine Demo")
    print("=" * 60)
    
    # Setup logging
    setup_logging()
    
    try:
        # Run demonstrations
        await demo_technical_indicators()
        await demo_pattern_recognition()
        await demo_integrated_analysis()
        
        print("\n" + "="*60)
        print("✅ TECHNICAL ANALYSIS ENGINE DEMO COMPLETED")
        print("="*60)
        print("\n🎉 Key Features Demonstrated:")
        print("   ✅ Moving Averages (SMA, EMA)")
        print("   ✅ RSI Oscillator")
        print("   ✅ MACD Momentum Indicator")
        print("   ✅ Bollinger Bands")
        print("   ✅ Candlestick Pattern Recognition")
        print("   ✅ Integrated Signal Analysis")
        print("\n📈 The technical analysis engine is ready for integration!")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
