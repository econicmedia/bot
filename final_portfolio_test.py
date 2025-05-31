#!/usr/bin/env python3
"""
Final Portfolio History Test - Comprehensive Verification
"""

import sys
import os
sys.path.append('.')

import requests
import json
from datetime import datetime

def test_all_endpoints():
    """Test all critical dashboard endpoints"""
    print("🚀 Final Portfolio History Test")
    print("=" * 60)
    
    base_url = "http://localhost:8080"
    endpoints = [
        "/api/v1/analytics/portfolio-history",
        "/api/v1/trading/status",
        "/api/v1/trading/positions",
        "/api/v1/trading/trades",
        "/api/v1/strategies/",
        "/api/v1/analytics/performance",
        "/api/v1/analytics/risk-metrics",
        "/api/v1/bot/status"
    ]
    
    results = {}
    
    for endpoint in endpoints:
        try:
            print(f"\n🧪 Testing {endpoint}...")
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                results[endpoint] = {
                    "status": "✅ SUCCESS",
                    "status_code": response.status_code,
                    "data_length": len(data) if isinstance(data, list) else "object",
                    "sample": data[0] if isinstance(data, list) and data else str(data)[:100] + "..."
                }
                print(f"   ✅ Status: {response.status_code}")
                print(f"   📊 Data: {len(data) if isinstance(data, list) else 'object'}")
                
                # Special handling for portfolio-history
                if endpoint == "/api/v1/analytics/portfolio-history":
                    print(f"   📈 Portfolio entries: {len(data)}")
                    if data:
                        print(f"   📅 Date range: {data[0]['timestamp'][:10]} to {data[-1]['timestamp'][:10]}")
                        print(f"   💰 Value range: ${data[0]['total_value']:,.2f} to ${data[-1]['total_value']:,.2f}")
                
            else:
                results[endpoint] = {
                    "status": "❌ FAILED",
                    "status_code": response.status_code,
                    "error": response.text
                }
                print(f"   ❌ Status: {response.status_code}")
                print(f"   📄 Response: {response.text}")
                
        except requests.exceptions.ConnectionError:
            results[endpoint] = {
                "status": "❌ CONNECTION ERROR",
                "error": "Cannot connect to server"
            }
            print(f"   ❌ Cannot connect to server")
            
        except Exception as e:
            results[endpoint] = {
                "status": "❌ ERROR",
                "error": str(e)
            }
            print(f"   ❌ Error: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 FINAL TEST RESULTS")
    print("=" * 60)
    
    success_count = 0
    total_count = len(endpoints)
    
    for endpoint, result in results.items():
        status = result["status"]
        print(f"{status} {endpoint}")
        if "SUCCESS" in status:
            success_count += 1
    
    print(f"\n🎯 SUCCESS RATE: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
    
    if success_count == total_count:
        print("🎉 ALL TESTS PASSED! Dashboard is fully functional.")
        print("\n✅ PORTFOLIO HISTORY 404 ERROR - COMPLETELY FIXED!")
        print("✅ Dashboard ready for production use")
    else:
        print(f"⚠️ {total_count - success_count} endpoints failed")
        print("❌ Some issues remain")
    
    return success_count == total_count

def test_dashboard_access():
    """Test dashboard page access"""
    print("\n🌐 Testing Dashboard Access...")
    
    try:
        response = requests.get("http://localhost:8080/dashboard", timeout=5)
        if response.status_code == 200:
            print("✅ Dashboard page accessible")
            return True
        else:
            print(f"❌ Dashboard page failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Dashboard access error: {e}")
        return False

def test_server_health():
    """Test server health"""
    print("\n❤️ Testing Server Health...")
    
    try:
        response = requests.get("http://localhost:8080/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Server is healthy")
            print(f"   📊 Status: {data.get('status', 'unknown')}")
            print(f"   🕐 Timestamp: {data.get('timestamp', 'unknown')}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Starting comprehensive dashboard test...")
    print(f"🕐 Test time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run all tests
    health_ok = test_server_health()
    dashboard_ok = test_dashboard_access()
    endpoints_ok = test_all_endpoints()
    
    print("\n" + "=" * 60)
    print("🏁 FINAL VERIFICATION COMPLETE")
    print("=" * 60)
    
    if health_ok and dashboard_ok and endpoints_ok:
        print("🎉 ALL SYSTEMS OPERATIONAL!")
        print("✅ Portfolio History 404 Error: RESOLVED")
        print("✅ Dashboard: FULLY FUNCTIONAL")
        print("✅ API Endpoints: ALL WORKING")
        print("✅ Server Health: EXCELLENT")
        print("\n🚀 Ready for production use!")
    else:
        print("⚠️ Some issues detected:")
        if not health_ok:
            print("   ❌ Server health check failed")
        if not dashboard_ok:
            print("   ❌ Dashboard access failed")
        if not endpoints_ok:
            print("   ❌ Some API endpoints failed")
        print("\n🔧 Please review the issues above")
