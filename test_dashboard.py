#!/usr/bin/env python3
"""
AI Trading Bot Dashboard Test Script

This script tests the complete dashboard functionality including:
- API endpoints with in-memory data
- Web dashboard interface
- Real-time data updates
- Paper trading capabilities

Run this script to verify the dashboard works immediately without PostgreSQL.
"""

import asyncio
import sys
import os
import time
import requests
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def print_header(title):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f"🚀 {title}")
    print("="*60)

def print_success(message):
    """Print a success message"""
    print(f"✅ {message}")

def print_error(message):
    """Print an error message"""
    print(f"❌ {message}")

def print_info(message):
    """Print an info message"""
    print(f"ℹ️  {message}")

def test_api_endpoints():
    """Test all API endpoints"""
    print_header("Testing API Endpoints")
    
    base_url = "http://localhost:8000/api/v1"
    
    endpoints = [
        ("/trading/status", "Trading Status"),
        ("/trading/positions", "Active Positions"),
        ("/trading/trades", "Trade History"),
        ("/strategies/", "Available Strategies"),
        ("/analytics/performance", "Performance Analytics"),
        ("/analytics/portfolio-history", "Portfolio History"),
        ("/analytics/risk-metrics", "Risk Metrics"),
        ("/analytics/system-status", "System Status"),
        ("/data/market-prices", "Market Prices")
    ]
    
    successful_tests = 0
    total_tests = len(endpoints)
    
    for endpoint, description in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print_success(f"{description}: {len(data) if isinstance(data, list) else 'OK'}")
                successful_tests += 1
            else:
                print_error(f"{description}: HTTP {response.status_code}")
        except requests.exceptions.RequestException as e:
            print_error(f"{description}: Connection failed - {e}")
        except Exception as e:
            print_error(f"{description}: {e}")
    
    print(f"\n📊 API Test Results: {successful_tests}/{total_tests} endpoints working")
    return successful_tests == total_tests

def test_dashboard_access():
    """Test dashboard web interface access"""
    print_header("Testing Dashboard Web Interface")
    
    try:
        # Test dashboard page
        response = requests.get("http://localhost:8000/dashboard", timeout=5)
        if response.status_code == 200 and "AI Trading Bot Dashboard" in response.text:
            print_success("Dashboard HTML page loads correctly")
            
            # Test static files
            static_files = [
                "/static/styles.css",
                "/static/dashboard.js"
            ]
            
            static_success = 0
            for static_file in static_files:
                try:
                    static_response = requests.get(f"http://localhost:8000{static_file}", timeout=5)
                    if static_response.status_code == 200:
                        print_success(f"Static file {static_file} loads correctly")
                        static_success += 1
                    else:
                        print_error(f"Static file {static_file}: HTTP {static_response.status_code}")
                except Exception as e:
                    print_error(f"Static file {static_file}: {e}")
            
            print(f"\n📊 Dashboard Test Results: {static_success + 1}/{len(static_files) + 1} components working")
            return static_success == len(static_files)
            
        else:
            print_error(f"Dashboard page: HTTP {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print_error(f"Dashboard access failed: {e}")
        return False
    except Exception as e:
        print_error(f"Dashboard test error: {e}")
        return False

def test_paper_trading():
    """Test paper trading functionality"""
    print_header("Testing Paper Trading Functionality")
    
    base_url = "http://localhost:8000/api/v1"
    
    try:
        # Test placing a paper trade order
        order_data = {
            "symbol": "BTCUSDT",
            "side": "buy",
            "quantity": 0.001,
            "order_type": "market"
        }
        
        response = requests.post(f"{base_url}/trading/orders", json=order_data, timeout=5)
        if response.status_code == 200:
            order_result = response.json()
            print_success(f"Paper order placed: {order_result.get('order_id', 'Unknown ID')}")
            
            # Test getting updated positions
            positions_response = requests.get(f"{base_url}/trading/positions", timeout=5)
            if positions_response.status_code == 200:
                positions = positions_response.json()
                print_success(f"Retrieved {len(positions)} active positions")
                
                # Display position details
                for pos in positions[:3]:  # Show first 3 positions
                    pnl_status = "📈" if pos['unrealized_pnl'] >= 0 else "📉"
                    print_info(f"  {pos['symbol']}: {pos['side']} {pos['quantity']} @ ${pos['current_price']:.2f} {pnl_status}")
                
                return True
            else:
                print_error(f"Failed to retrieve positions: HTTP {positions_response.status_code}")
                return False
        else:
            print_error(f"Failed to place order: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Paper trading test failed: {e}")
        return False

def test_real_time_updates():
    """Test real-time data updates"""
    print_header("Testing Real-time Data Updates")
    
    base_url = "http://localhost:8000/api/v1"
    
    try:
        print_info("Monitoring market prices for 10 seconds...")
        
        initial_prices = requests.get(f"{base_url}/data/market-prices", timeout=5).json()
        print_info(f"Initial BTC price: ${initial_prices.get('BTCUSDT', 0):.2f}")
        
        time.sleep(10)  # Wait for price updates
        
        updated_prices = requests.get(f"{base_url}/data/market-prices", timeout=5).json()
        print_info(f"Updated BTC price: ${updated_prices.get('BTCUSDT', 0):.2f}")
        
        # Check if prices changed (they should due to simulation)
        if initial_prices != updated_prices:
            print_success("Real-time price updates working correctly")
            return True
        else:
            print_error("Prices did not update (simulation may not be running)")
            return False
            
    except Exception as e:
        print_error(f"Real-time update test failed: {e}")
        return False

def display_dashboard_info():
    """Display dashboard access information"""
    print_header("Dashboard Access Information")
    
    print_info("🌐 Dashboard URL: http://localhost:8000/dashboard")
    print_info("🔗 API Documentation: http://localhost:8000/docs")
    print_info("📊 Health Check: http://localhost:8000/health")
    print_info("💹 Trading Mode: Paper Trading (Safe for testing)")
    
    print("\n🎯 Dashboard Features:")
    print("   • Real-time portfolio performance tracking")
    print("   • Live position monitoring with P&L")
    print("   • Strategy performance comparison")
    print("   • Interactive trading interface")
    print("   • Risk metrics visualization")
    print("   • Trade history and analytics")
    
    print("\n🔧 Testing Instructions:")
    print("   1. Open http://localhost:8000/dashboard in your browser")
    print("   2. Verify all metrics are displaying correctly")
    print("   3. Test the trading interface (+ button)")
    print("   4. Check real-time updates (data refreshes every 5 seconds)")
    print("   5. Explore strategy performance cards")

def main():
    """Main test function"""
    print_header("AI Trading Bot Dashboard Comprehensive Test")
    print_info(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code != 200:
            print_error("Trading bot server is not running!")
            print_info("Please start the server first:")
            print_info("   cd src && python main.py")
            return False
    except requests.exceptions.RequestException:
        print_error("Cannot connect to trading bot server!")
        print_info("Please start the server first:")
        print_info("   cd src && python main.py")
        return False
    
    print_success("Trading bot server is running")
    
    # Run all tests
    tests = [
        ("API Endpoints", test_api_endpoints),
        ("Dashboard Interface", test_dashboard_access),
        ("Paper Trading", test_paper_trading),
        ("Real-time Updates", test_real_time_updates)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} test...")
        try:
            if test_func():
                passed_tests += 1
                print_success(f"{test_name} test PASSED")
            else:
                print_error(f"{test_name} test FAILED")
        except Exception as e:
            print_error(f"{test_name} test ERROR: {e}")
    
    # Display results
    print_header("Test Results Summary")
    print(f"📊 Tests Passed: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print_success("🎉 ALL TESTS PASSED! Dashboard is fully functional!")
        display_dashboard_info()
        return True
    else:
        print_error(f"❌ {total_tests - passed_tests} tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
