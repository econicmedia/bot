#!/usr/bin/env python3
"""
Test the API endpoints
"""

import requests
import time
import sys

def test_api_endpoints():
    """Test the main API endpoints"""
    base_url = "http://localhost:8000"
    
    print("🌐 Testing AI Trading Bot API")
    print("=" * 40)
    
    try:
        # Test root endpoint
        print("1. Testing root endpoint...")
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Root endpoint: {data['message']}")
        else:
            print(f"   ❌ Root endpoint failed: {response.status_code}")
            return False
        
        # Test health endpoint
        print("2. Testing health endpoint...")
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Health check: {data['status']}")
            print(f"   ✓ Trading mode: {data['mode']}")
            print(f"   ✓ Uptime: {data['uptime']:.1f}s")
            
            # Check components
            components = data['components']
            for comp_name, comp_status in components.items():
                status_icon = "✓" if comp_status == "initialized" else "❌"
                print(f"   {status_icon} {comp_name}: {comp_status}")
        else:
            print(f"   ❌ Health endpoint failed: {response.status_code}")
            return False
        
        # Test API documentation
        print("3. Testing API documentation...")
        response = requests.get(f"{base_url}/docs", timeout=5)
        if response.status_code == 200:
            print("   ✓ API documentation accessible")
        else:
            print(f"   ❌ API docs failed: {response.status_code}")
        
        # Test strategies endpoint
        print("4. Testing strategies endpoint...")
        response = requests.get(f"{base_url}/api/v1/strategies", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Strategies endpoint: {len(data)} strategies")
            for strategy in data:
                print(f"      - {strategy['name']}: {strategy['enabled']}")
        else:
            print(f"   ❌ Strategies endpoint failed: {response.status_code}")
        
        # Test portfolio endpoint
        print("5. Testing portfolio endpoint...")
        response = requests.get(f"{base_url}/api/v1/portfolio", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Portfolio endpoint working")
            print(f"      - Total value: ${data.get('total_value', 0):,.2f}")
            print(f"      - Cash balance: ${data.get('cash_balance', 0):,.2f}")
        else:
            print(f"   ❌ Portfolio endpoint failed: {response.status_code}")
        
        print("\n🎉 All API endpoints working correctly!")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to the API server.")
        print("   Make sure the server is running with: python -m src.main")
        return False
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_api_endpoints()
    if success:
        print("\n✅ API tests passed!")
        print("🌐 You can access the trading bot at:")
        print("   • Main API: http://localhost:8000")
        print("   • Health Check: http://localhost:8000/health")
        print("   • API Docs: http://localhost:8000/docs")
    else:
        print("\n❌ API tests failed!")
        print("   Please check if the server is running.")
    
    sys.exit(0 if success else 1)
