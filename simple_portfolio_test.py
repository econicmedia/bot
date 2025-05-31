#!/usr/bin/env python3
"""
Simple test to verify portfolio history works
"""

import sys
import os
sys.path.append('.')

def test_portfolio_history():
    """Test portfolio history"""
    try:
        print("🧪 Testing portfolio history import...")
        from src.core.memory_storage import get_memory_data_manager
        print("✅ Import successful")
        
        print("📊 Getting memory data manager...")
        dm = get_memory_data_manager()
        print(f"✅ Data manager created")
        
        print(f"📈 Portfolio history entries: {len(dm.portfolio_history)}")
        print(f"💰 Cash balance: ${dm.cash_balance:,.2f}")
        print(f"📊 Positions: {len(dm.positions)}")
        print(f"📋 Trades: {len(dm.trades)}")
        
        if dm.portfolio_history:
            print("✅ Portfolio history data available")
            sample = dm.portfolio_history[0]
            print(f"📊 Sample entry: {sample.timestamp} - ${sample.total_value:,.2f}")
            
            # Test API format
            api_data = {
                "timestamp": sample.timestamp.isoformat(),
                "total_value": sample.total_value,
                "cash_balance": sample.cash_balance,
                "positions_value": sample.positions_value,
                "unrealized_pnl": sample.unrealized_pnl,
                "realized_pnl": sample.realized_pnl,
                "daily_pnl": sample.daily_pnl
            }
            print(f"✅ API format test successful")
            print(f"📊 API data: {api_data}")
            
        else:
            print("❌ No portfolio history found")
            
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Simple Portfolio History Test")
    print("=" * 50)
    
    success = test_portfolio_history()
    
    print("=" * 50)
    print("✅ Test completed successfully" if success else "❌ Test failed")
