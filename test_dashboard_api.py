#!/usr/bin/env python3
"""
Test script to verify dashboard API endpoints are working
"""

import requests
import json
import time

def test_api_endpoint(url, endpoint_name):
    """Test a single API endpoint"""
    try:
        print(f"\n🔍 Testing {endpoint_name}: {url}")
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {endpoint_name} - SUCCESS")
            print(f"   Status: {response.status_code}")
            print(f"   Data preview: {json.dumps(data, indent=2)[:200]}...")
            return True
        else:
            print(f"❌ {endpoint_name} - FAILED")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ {endpoint_name} - ERROR: {e}")
        return False

def test_post_endpoint(url, endpoint_name, data=None):
    """Test a POST endpoint"""
    try:
        print(f"\n🔍 Testing {endpoint_name}: {url}")
        response = requests.post(url, json=data or {}, timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ {endpoint_name} - SUCCESS")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {json.dumps(result, indent=2)[:200]}...")
            return True
        else:
            print(f"❌ {endpoint_name} - FAILED")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ {endpoint_name} - ERROR: {e}")
        return False

def main():
    """Test all dashboard API endpoints"""
    base_url = "http://localhost:8000"
    
    print("🚀 AI Trading Bot Dashboard API Test")
    print("=" * 50)
    
    # Test basic connectivity
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and accessible")
        else:
            print("❌ Server health check failed")
            return
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return
    
    # Test all API endpoints that the dashboard uses
    endpoints = [
        ("/api/v1/trading/status", "Trading Status"),
        ("/api/v1/trading/positions", "Positions"),
        ("/api/v1/trading/trades", "Trades"),
        ("/api/v1/strategies/", "Strategies"),
        ("/api/v1/analytics/performance", "Performance"),
        ("/api/v1/analytics/risk-metrics", "Risk Metrics"),
        ("/api/v1/analytics/portfolio-history", "Portfolio History"),
        ("/api/v1/bot/status", "Bot Status"),
        ("/api/v1/market/prices", "Market Prices"),
    ]
    
    success_count = 0
    total_count = len(endpoints)
    
    for endpoint, name in endpoints:
        url = f"{base_url}{endpoint}"
        if test_api_endpoint(url, name):
            success_count += 1
    
    # Test POST endpoints
    post_endpoints = [
        ("/api/v1/bot/initialize-demo", "Initialize Demo"),
        ("/api/v1/bot/start", "Start Bot"),
        ("/api/v1/bot/stop", "Stop Bot"),
    ]
    
    for endpoint, name in post_endpoints:
        url = f"{base_url}{endpoint}"
        if test_post_endpoint(url, name):
            success_count += 1
    
    total_count += len(post_endpoints)
    
    # Summary
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {success_count}/{total_count} endpoints working")
    
    if success_count == total_count:
        print("🎉 All API endpoints are working correctly!")
        print("🔗 Dashboard should be fully functional at: http://localhost:8000")
    else:
        print(f"⚠️ {total_count - success_count} endpoints need attention")
    
    print("\n💡 Next steps:")
    print("   1. Open http://localhost:8000 in your browser")
    print("   2. Check browser console for any JavaScript errors")
    print("   3. Verify that data is updating every 5 seconds")
    print("   4. Test start/stop bot functionality")

if __name__ == "__main__":
    main()
