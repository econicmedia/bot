#!/usr/bin/env python3
"""
Test ICT Strategy Implementation

This script tests the ICT strategy components to ensure they work correctly.
"""

import sys
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add src to path
sys.path.append('src')

from core.config import get_settings
from strategies.ict.market_structure import MarketStructureAnalyzer, TrendDirection
from strategies.ict.order_blocks import OrderBlockDetector
from strategies.ict.ict_strategy import ICTStrategy


def create_sample_data(periods: int = 100) -> pd.DataFrame:
    """Create sample OHLCV data for testing"""
    dates = pd.date_range(start='2024-01-01', periods=periods, freq='1H')
    
    # Create realistic price data with trend
    base_price = 50000.0
    prices = []
    
    for i in range(periods):
        # Add some trend and noise
        trend = i * 10  # Upward trend
        noise = np.random.normal(0, 100)  # Random noise
        price = base_price + trend + noise
        prices.append(price)
    
    # Create OHLCV data
    data = []
    for i, price in enumerate(prices):
        high = price + np.random.uniform(50, 200)
        low = price - np.random.uniform(50, 200)
        open_price = price + np.random.uniform(-50, 50)
        close = price + np.random.uniform(-50, 50)
        volume = np.random.uniform(1000, 10000)
        
        data.append({
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })
    
    df = pd.DataFrame(data, index=dates)
    return df


async def test_market_structure_analyzer():
    """Test market structure analysis"""
    print("🔍 Testing Market Structure Analyzer...")
    
    try:
        # Create sample data
        data = create_sample_data(50)
        
        # Initialize analyzer
        analyzer = MarketStructureAnalyzer(lookback_period=20, min_significance=0.3)
        
        # Perform analysis
        result = analyzer.analyze(data)
        
        print(f"✅ Market structure analysis completed")
        print(f"   - Trend direction: {result.trend_direction.value}")
        print(f"   - Confidence: {result.confidence:.2f}")
        print(f"   - Structure points: {len(result.structure_points)}")
        print(f"   - Last BOS: {result.last_bos.structure_type.value if result.last_bos else 'None'}")
        print(f"   - Last CHoCH: {result.last_choch.structure_type.value if result.last_choch else 'None'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Market structure test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_order_block_detector():
    """Test order block detection"""
    print("\n📦 Testing Order Block Detector...")
    
    try:
        # Create sample data
        data = create_sample_data(50)
        
        # Initialize detector
        detector = OrderBlockDetector(min_block_size=0.001, max_blocks=10)
        
        # Detect order blocks
        blocks = detector.detect_order_blocks(data)
        
        print(f"✅ Order block detection completed")
        print(f"   - New blocks detected: {len(blocks)}")
        print(f"   - Active blocks: {len(detector.get_active_blocks())}")
        
        # Generate signals
        signals = detector.generate_signals(data)
        print(f"   - Signals generated: {len(signals)}")
        
        # Get summary
        summary = detector.get_blocks_summary()
        print(f"   - Summary: {summary}")
        
        return True
        
    except Exception as e:
        print(f"❌ Order block test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_ict_strategy():
    """Test complete ICT strategy"""
    print("\n🎯 Testing ICT Strategy...")
    
    try:
        # Get settings
        settings = get_settings()
        
        # Create ICT strategy
        strategy = ICTStrategy("test_ict", settings)
        
        print(f"✅ ICT strategy created: {strategy.name}")
        
        # Create sample data for multiple timeframes
        data = {
            "1h": create_sample_data(100),
            "4h": create_sample_data(25),
            "1d": create_sample_data(10)
        }
        
        # Perform analysis
        analysis = await strategy.analyze(data)
        
        print(f"✅ ICT analysis completed")
        print(f"   - Market structure trend: {analysis['market_structure']['trend_direction']}")
        print(f"   - Market structure confidence: {analysis['market_structure']['confidence']:.2f}")
        print(f"   - Order blocks: {analysis['order_blocks']}")
        print(f"   - Signals generated: {len(analysis['signals'])}")
        print(f"   - In kill zone: {analysis['in_kill_zone']}")
        print(f"   - Current price: {analysis['current_price']:.2f}")
        
        # Test entry signal
        entry_signal = await strategy.should_enter_trade("BTCUSDT", data)
        if entry_signal:
            print(f"✅ Entry signal generated:")
            print(f"   - Action: {entry_signal['action']}")
            print(f"   - Direction: {entry_signal['direction']}")
            print(f"   - Price: {entry_signal['price']:.2f}")
            print(f"   - Confidence: {entry_signal['confidence']:.2f}")
        else:
            print(f"ℹ️ No entry signal generated")
        
        # Test strategy status
        status = strategy.get_strategy_status()
        print(f"✅ Strategy status: {status}")
        
        return True
        
    except Exception as e:
        print(f"❌ ICT strategy test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_integration():
    """Test integration with existing components"""
    print("\n🔗 Testing Integration...")
    
    try:
        # Test imports
        from core.config import get_settings
        from strategies.base_strategy import BaseStrategy
        
        print("✅ Core imports successful")
        
        # Test settings
        settings = get_settings()
        ict_config = settings.strategies.ict
        
        print(f"✅ ICT configuration loaded:")
        print(f"   - Enabled: {ict_config.enabled}")
        print(f"   - Timeframes: {ict_config.timeframes}")
        print(f"   - Kill zones: {ict_config.kill_zones}")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all ICT strategy tests"""
    print("🚀 Starting ICT Strategy Tests")
    print("=" * 50)
    
    tests = [
        ("Integration", test_integration),
        ("Market Structure Analyzer", test_market_structure_analyzer),
        ("Order Block Detector", test_order_block_detector),
        ("ICT Strategy", test_ict_strategy),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All ICT strategy tests passed! Implementation is ready.")
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
    
    return passed == total


if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
