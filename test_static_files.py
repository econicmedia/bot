#!/usr/bin/env python3
"""
Test Static File Serving for AI Trading Bot Dashboard

This script tests that the FastAPI server properly serves static files
and that the dashboard loads with correct styling and functionality.
"""

import requests
import time
import subprocess
import sys
import os
from pathlib import Path

def print_success(message):
    """Print success message"""
    print(f"✅ {message}")

def print_error(message):
    """Print error message"""
    print(f"❌ {message}")

def print_info(message):
    """Print info message"""
    print(f"ℹ️  {message}")

def check_static_files_exist():
    """Check that static files exist on disk"""
    print("\n🔍 Checking static files on disk...")
    
    static_files = [
        "src/static/index.html",
        "src/static/styles.css",
        "src/static/dashboard.js"
    ]
    
    all_exist = True
    for file_path in static_files:
        if Path(file_path).exists():
            size = Path(file_path).stat().st_size
            print_success(f"{file_path} exists ({size} bytes)")
        else:
            print_error(f"{file_path} missing")
            all_exist = False
    
    return all_exist

def check_html_references():
    """Check that HTML file has correct static file references"""
    print("\n🔍 Checking HTML static file references...")
    
    html_file = Path("src/static/index.html")
    if not html_file.exists():
        print_error("index.html not found")
        return False
    
    content = html_file.read_text()
    
    # Check for correct static file references
    checks = [
        ('/static/styles.css', 'CSS file reference'),
        ('/static/dashboard.js', 'JavaScript file reference'),
        ('AI Trading Bot Dashboard', 'Page title')
    ]
    
    all_good = True
    for check_text, description in checks:
        if check_text in content:
            print_success(f"{description} found")
        else:
            print_error(f"{description} missing or incorrect")
            all_good = False
    
    return all_good

def test_server_static_files():
    """Test that server serves static files correctly"""
    print("\n🌐 Testing server static file serving...")
    
    base_url = "http://localhost:8000"
    
    # Test endpoints
    endpoints = [
        ("/", "Root redirect"),
        ("/dashboard", "Dashboard page"),
        ("/static/styles.css", "CSS file"),
        ("/static/dashboard.js", "JavaScript file"),
        ("/health", "Health check")
    ]
    
    results = {}
    
    for endpoint, description in endpoints:
        try:
            print_info(f"Testing {description}: {endpoint}")
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            
            if response.status_code == 200:
                print_success(f"{description} - HTTP 200 OK")
                
                # Additional checks for specific endpoints
                if endpoint == "/dashboard":
                    if "AI Trading Bot Dashboard" in response.text:
                        print_success("Dashboard contains correct title")
                    else:
                        print_error("Dashboard missing title")
                
                elif endpoint == "/static/styles.css":
                    if "dashboard-container" in response.text:
                        print_success("CSS contains dashboard styles")
                    else:
                        print_error("CSS missing dashboard styles")
                
                elif endpoint == "/static/dashboard.js":
                    if "TradingDashboard" in response.text:
                        print_success("JavaScript contains dashboard class")
                    else:
                        print_error("JavaScript missing dashboard class")
                
                results[endpoint] = True
            else:
                print_error(f"{description} - HTTP {response.status_code}")
                results[endpoint] = False
                
        except requests.exceptions.RequestException as e:
            print_error(f"{description} - Connection error: {e}")
            results[endpoint] = False
    
    return results

def main():
    """Main test function"""
    print("🧪 AI Trading Bot - Static File Serving Test")
    print("=" * 50)
    
    # Check if files exist
    if not check_static_files_exist():
        print_error("Static files missing. Cannot proceed with server tests.")
        return False
    
    # Check HTML references
    if not check_html_references():
        print_error("HTML file has incorrect static file references.")
        return False
    
    # Check if server is running
    print_info("Checking if server is running on http://localhost:8000...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print_success("Server is running")
            
            # Test static file serving
            results = test_server_static_files()
            
            # Summary
            print("\n📊 Test Results Summary:")
            print("-" * 30)
            
            success_count = sum(1 for success in results.values() if success)
            total_count = len(results)
            
            for endpoint, success in results.items():
                status = "✅ PASS" if success else "❌ FAIL"
                print(f"{endpoint:<25} {status}")
            
            print(f"\nOverall: {success_count}/{total_count} tests passed")
            
            if success_count == total_count:
                print_success("All static file tests passed! 🎉")
                print("\n📋 Dashboard should now be accessible at:")
                print("   http://localhost:8000/dashboard")
                return True
            else:
                print_error("Some tests failed. Check the issues above.")
                return False
        else:
            print_error(f"Server health check failed: HTTP {response.status_code}")
            
    except requests.exceptions.RequestException:
        print_error("Server is not running or not accessible")
        print_info("Start the server with: python src/main.py")
        print_info("Or with Docker: docker-compose up")
    
    return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
