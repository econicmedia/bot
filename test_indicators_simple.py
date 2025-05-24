#!/usr/bin/env python3
"""
Simple test script for technical indicators
"""

import sys
import os
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from core.data_manager import Candle
    from analysis.indicators.moving_averages import MovingAverageIndicator
    from analysis.indicators.oscillators import RSIIndicator
    from analysis.indicators.base import IndicatorType
    
    print("✅ All imports successful!")
    
    # Create test data
    def create_test_candles(count=20):
        candles = []
        base_price = 100.0
        
        for i in range(count):
            price = base_price + (i * 0.5)  # Simple uptrend
            candle = Candle(
                symbol="TESTUSDT",
                timeframe="1m", 
                timestamp=datetime.utcnow() + timedelta(minutes=i),
                open_price=price,
                high_price=price + 0.2,
                low_price=price - 0.2,
                close_price=price + 0.1,
                volume=1000.0
            )
            candles.append(candle)
        
        return candles
    
    # Test Moving Average
    print("\n🔄 Testing Moving Average Indicator...")
    ma_indicator = MovingAverageIndicator(period=5, ma_type="sma")
    test_candles = create_test_candles(10)
    
    for i, candle in enumerate(test_candles):
        result = ma_indicator.update(candle)
        if result:
            print(f"  Candle {i+1}: MA = {result.value:.2f}, Signal = {result.signal}")
    
    print("✅ Moving Average test completed!")
    
    # Test RSI
    print("\n🔄 Testing RSI Indicator...")
    rsi_indicator = RSIIndicator(period=5)
    
    for i, candle in enumerate(test_candles):
        result = rsi_indicator.update(candle)
        if result:
            print(f"  Candle {i+1}: RSI = {result.value:.2f}, Signal = {result.signal}")
    
    print("✅ RSI test completed!")
    
    print("\n🎉 All indicator tests passed successfully!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Test error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
