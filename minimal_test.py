#!/usr/bin/env python3
"""
Minimal test to check config only
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_config_only():
    """Test config import only"""
    print("Testing config import...")
    
    try:
        # Test config without logger
        print("1. Testing config module...")
        
        # Import config directly
        from src.core.config import DatabaseConfig, TradingConfig
        print("   ✓ Config classes imported")
        
        # Test creating config objects
        db_config = DatabaseConfig()
        trading_config = TradingConfig()
        print("   ✓ Config objects created")
        
        print(f"   - Database host: {db_config.host}")
        print(f"   - Trading mode: {trading_config.mode}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_config_only()
    print("✓ Config working!" if success else "❌ Config failed")
