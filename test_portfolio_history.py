#!/usr/bin/env python3
"""
Test script to verify portfolio history functionality
"""

import sys
import os
sys.path.append('.')

def test_portfolio_history():
    """Test portfolio history data"""
    try:
        from src.core.memory_storage import get_memory_data_manager
        
        print("🧪 Testing portfolio history...")
        
        # Get memory data manager
        dm = get_memory_data_manager()
        
        print(f"✅ Memory data manager created")
        print(f"📊 Portfolio history entries: {len(dm.portfolio_history)}")
        print(f"💰 Cash balance: ${dm.cash_balance:,.2f}")
        print(f"📈 Positions: {len(dm.positions)}")
        print(f"📋 Trades: {len(dm.trades)}")
        
        if dm.portfolio_history:
            print("\n📈 Sample portfolio history entries:")
            for i, snapshot in enumerate(dm.portfolio_history[:3]):
                print(f"  {i+1}. {snapshot.timestamp.strftime('%Y-%m-%d %H:%M')} - Total: ${snapshot.total_value:,.2f}")
            
            print(f"\n🔄 Latest entry: {dm.portfolio_history[-1].timestamp.strftime('%Y-%m-%d %H:%M')} - ${dm.portfolio_history[-1].total_value:,.2f}")
            
            # Test JSON serialization (what the API endpoint does)
            print("\n🔧 Testing API response format...")
            api_response = [
                {
                    "timestamp": snapshot.timestamp.isoformat(),
                    "total_value": snapshot.total_value,
                    "cash_balance": snapshot.cash_balance,
                    "positions_value": snapshot.positions_value,
                    "unrealized_pnl": snapshot.unrealized_pnl,
                    "realized_pnl": snapshot.realized_pnl,
                    "daily_pnl": snapshot.daily_pnl
                }
                for snapshot in dm.portfolio_history[:2]  # Just first 2 for testing
            ]
            
            print(f"✅ API response format test successful - {len(api_response)} entries")
            print(f"📊 Sample API entry: {api_response[0]}")
            
        else:
            print("❌ No portfolio history found!")
            print("🔄 Trying to initialize demo data...")
            dm._initialize_demo_data()
            print(f"📊 After initialization: {len(dm.portfolio_history)} entries")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing portfolio history: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_endpoint():
    """Test the actual API endpoint"""
    try:
        import requests
        
        print("\n🌐 Testing API endpoint...")
        
        response = requests.get("http://localhost:8080/api/v1/analytics/portfolio-history", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API endpoint working - {len(data)} entries returned")
            if data:
                print(f"📊 Sample entry: {data[0]}")
        else:
            print(f"❌ API endpoint failed - Status: {response.status_code}")
            print(f"📄 Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server on localhost:8080")
    except Exception as e:
        print(f"❌ Error testing API endpoint: {e}")

if __name__ == "__main__":
    print("🚀 Portfolio History Test")
    print("=" * 50)
    
    # Test memory storage
    success = test_portfolio_history()
    
    # Test API endpoint
    test_api_endpoint()
    
    print("\n" + "=" * 50)
    print("✅ Test completed" if success else "❌ Test failed")
