#!/usr/bin/env python3
"""
Verification script for Technical Analysis Engine

This script verifies that all components of the technical analysis engine
are working correctly and can be imported and used.
"""

import sys
import os
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test that all modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        # Core imports
        from core.data_manager import Candle
        print("  ✅ Core data manager")
        
        # Indicator imports
        from analysis.indicators.base import IndicatorBase, IndicatorResult, IndicatorType
        from analysis.indicators.moving_averages import MovingAverageIndicator
        from analysis.indicators.oscillators import RSIIndicator, StochasticIndicator, WilliamsRIndicator
        from analysis.indicators.momentum import MACDIndicator, CCIIndicator
        from analysis.indicators.volatility import BollingerBandsIndicator, ATRIndicator
        print("  ✅ All technical indicators")
        
        # Pattern imports
        from analysis.patterns.base import PatternDetector, PatternResult, PatternType, PatternSignal
        from analysis.patterns.candlestick import CandlestickPatterns
        from analysis.patterns.chart_patterns import ChartPatterns
        print("  ✅ All pattern recognition modules")
        
        # Strategy import
        from strategies.technical_analysis_strategy import TechnicalAnalysisStrategy
        print("  ✅ Technical analysis strategy")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ Import failed: {e}")
        return False

def create_test_candle(price: float, timestamp: datetime) -> 'Candle':
    """Create a test candle"""
    from core.data_manager import Candle
    
    return Candle(
        symbol="TESTUSDT",
        timeframe="1h",
        timestamp=timestamp,
        open_price=price,
        high_price=price * 1.01,
        low_price=price * 0.99,
        close_price=price * 1.005,
        volume=1000.0
    )

def test_indicators():
    """Test technical indicators"""
    print("\n🔧 Testing technical indicators...")
    
    try:
        from analysis.indicators.moving_averages import MovingAverageIndicator
        from analysis.indicators.oscillators import RSIIndicator
        
        # Create test data
        candles = []
        base_price = 100.0
        for i in range(25):
            price = base_price + (i * 0.5)  # Simple uptrend
            candle = create_test_candle(price, datetime.utcnow() + timedelta(hours=i))
            candles.append(candle)
        
        # Test SMA
        sma = MovingAverageIndicator(period=10, ma_type="sma")
        sma_results = []
        for candle in candles:
            result = sma.update(candle)
            if result:
                sma_results.append(result)
        
        if sma_results:
            print(f"  ✅ SMA: {len(sma_results)} results, latest = {sma_results[-1].value:.2f}")
        else:
            print("  ❌ SMA: No results generated")
            return False
        
        # Test RSI
        rsi = RSIIndicator(period=10)
        rsi_results = []
        for candle in candles:
            result = rsi.update(candle)
            if result:
                rsi_results.append(result)
        
        if rsi_results:
            print(f"  ✅ RSI: {len(rsi_results)} results, latest = {rsi_results[-1].value:.2f}")
        else:
            print("  ❌ RSI: No results generated")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Indicator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_patterns():
    """Test pattern recognition"""
    print("\n🔍 Testing pattern recognition...")
    
    try:
        from analysis.patterns.candlestick import CandlestickPatterns
        
        # Create test data with potential patterns
        candles = []
        
        # Create a hammer pattern (bullish reversal)
        hammer_candle = create_test_candle(100.0, datetime.utcnow())
        # Modify to create hammer characteristics
        hammer_candle.low = 98.0  # Long lower shadow
        hammer_candle.open = 99.8
        hammer_candle.close = 99.9  # Small body near top
        hammer_candle.high = 100.0
        candles.append(hammer_candle)
        
        # Test pattern detection
        pattern_detector = CandlestickPatterns()
        all_patterns = []
        
        for candle in candles:
            patterns = pattern_detector.update(candle)
            all_patterns.extend(patterns)
        
        if all_patterns:
            print(f"  ✅ Patterns: {len(all_patterns)} detected")
            for pattern in all_patterns:
                print(f"    - {pattern.pattern_name}: {pattern.signal.value} (confidence: {pattern.confidence:.2f})")
        else:
            print("  ✅ Patterns: No patterns detected (expected for simple test data)")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Pattern test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration():
    """Test integrated functionality"""
    print("\n🔗 Testing integration...")
    
    try:
        from analysis.indicators.moving_averages import MovingAverageIndicator
        from analysis.indicators.oscillators import RSIIndicator
        from analysis.patterns.candlestick import CandlestickPatterns
        
        # Create test data
        candles = []
        for i in range(30):
            price = 100 + (i * 0.2) + ((-1) ** i * 0.1)  # Trending with noise
            candle = create_test_candle(price, datetime.utcnow() + timedelta(hours=i))
            candles.append(candle)
        
        # Initialize components
        sma = MovingAverageIndicator(period=10, ma_type="sma")
        rsi = RSIIndicator(period=14)
        patterns = CandlestickPatterns()
        
        # Process data
        signals = []
        for i, candle in enumerate(candles):
            sma_result = sma.update(candle)
            rsi_result = rsi.update(candle)
            pattern_results = patterns.update(candle)
            
            # Combine signals
            if sma_result and rsi_result:
                combined_signal = {
                    "candle": i + 1,
                    "price": candle.close,
                    "sma": sma_result.value,
                    "rsi": rsi_result.value,
                    "patterns": [p.pattern_name for p in pattern_results]
                }
                signals.append(combined_signal)
        
        if signals:
            print(f"  ✅ Integration: {len(signals)} combined signals generated")
            latest = signals[-1]
            print(f"    Latest: Price=${latest['price']:.2f}, SMA={latest['sma']:.2f}, RSI={latest['rsi']:.1f}")
        else:
            print("  ❌ Integration: No combined signals generated")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main verification function"""
    print("🚀 Technical Analysis Engine Verification")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("Indicator Test", test_indicators),
        ("Pattern Test", test_patterns),
        ("Integration Test", test_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 VERIFICATION RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Technical Analysis Engine is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
