#!/usr/bin/env python3
"""
Simple ICT Test
"""

import sys
sys.path.append('src')

def test_basic_imports():
    """Test basic imports"""
    try:
        print("Testing basic imports...")
        
        # Test pandas and numpy
        import pandas as pd
        import numpy as np
        print("✅ Pandas and numpy imported")
        
        # Test core imports
        from core.config import get_settings
        print("✅ Core config imported")
        
        # Test market structure
        from strategies.ict.market_structure import MarketStructureAnalyzer
        print("✅ Market structure imported")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_market_structure():
    """Test market structure analyzer"""
    try:
        print("\nTesting market structure...")
        
        import pandas as pd
        import numpy as np
        from strategies.ict.market_structure import MarketStructureAnalyzer
        
        # Create simple test data
        dates = pd.date_range('2024-01-01', periods=20, freq='1H')
        data = pd.DataFrame({
            'open': np.random.uniform(100, 110, 20),
            'high': np.random.uniform(110, 120, 20),
            'low': np.random.uniform(90, 100, 20),
            'close': np.random.uniform(100, 110, 20),
            'volume': np.random.uniform(1000, 5000, 20)
        }, index=dates)
        
        # Test analyzer
        analyzer = MarketStructureAnalyzer()
        result = analyzer.analyze(data)
        
        print(f"✅ Market structure analysis completed")
        print(f"   - Trend: {result.trend_direction.value}")
        print(f"   - Confidence: {result.confidence:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Market structure test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Simple ICT Test")
    print("=" * 30)
    
    success = True
    
    if not test_basic_imports():
        success = False
    
    if not test_market_structure():
        success = False
    
    print("\n" + "=" * 30)
    if success:
        print("🎉 All tests passed!")
    else:
        print("❌ Some tests failed!")
    
    print("Test completed.")
