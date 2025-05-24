#!/usr/bin/env python3
"""
Verify Static File Fixes for AI Trading Bot Dashboard

This script verifies that our static file fixes are correct without needing to run the server.
"""

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
            print_success(f"{file_path} exists ({size:,} bytes)")
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

    content = html_file.read_text(encoding='utf-8')

    # Check for correct static file references
    checks = [
        ('/static/styles.css', 'CSS file reference'),
        ('/static/dashboard.js', 'JavaScript file reference'),
        ('AI Trading Bot Dashboard', 'Page title'),
        ('dashboard-container', 'Main container class')
    ]

    all_good = True
    for check_text, description in checks:
        if check_text in content:
            print_success(f"{description} found")
        else:
            print_error(f"{description} missing or incorrect")
            all_good = False

    return all_good

def check_css_content():
    """Check that CSS file has expected content"""
    print("\n🔍 Checking CSS file content...")

    css_file = Path("src/static/styles.css")
    if not css_file.exists():
        print_error("styles.css not found")
        return False

    content = css_file.read_text(encoding='utf-8')

    # Check for key CSS classes and styles
    css_checks = [
        ('dashboard-container', 'Main dashboard container'),
        ('dashboard-header', 'Header styles'),
        ('metric-card', 'Portfolio metric cards'),
        ('chart-container', 'Chart container'),
        ('trading-modal', 'Trading modal'),
        ('linear-gradient', 'Background gradient'),
        ('backdrop-filter', 'Glass effect'),
        ('@keyframes pulse', 'Animation keyframes')
    ]

    all_good = True
    for check_text, description in css_checks:
        if check_text in content:
            print_success(f"{description} found")
        else:
            print_error(f"{description} missing")
            all_good = False

    return all_good

def check_js_content():
    """Check that JavaScript file has expected content"""
    print("\n🔍 Checking JavaScript file content...")

    js_file = Path("src/static/dashboard.js")
    if not js_file.exists():
        print_error("dashboard.js not found")
        return False

    content = js_file.read_text(encoding='utf-8')

    # Check for key JavaScript components
    js_checks = [
        ('class TradingDashboard', 'Main dashboard class'),
        ('async init()', 'Initialization method'),
        ('loadDashboardData', 'Data loading method'),
        ('updatePortfolioChart', 'Chart update method'),
        ('fetchAPI', 'API helper method'),
        ('formatCurrency', 'Currency formatting'),
        ('Chart.js', 'Chart.js integration'),
        ('/api/v1', 'API base path')
    ]

    all_good = True
    for check_text, description in js_checks:
        if check_text in content:
            print_success(f"{description} found")
        else:
            print_error(f"{description} missing")
            all_good = False

    return all_good

def check_fastapi_config():
    """Check FastAPI static file configuration"""
    print("\n🔍 Checking FastAPI static file configuration...")

    main_file = Path("src/main.py")
    if not main_file.exists():
        print_error("src/main.py not found")
        return False

    content = main_file.read_text(encoding='utf-8')

    # Check for correct FastAPI static file setup
    config_checks = [
        ('from pathlib import Path', 'Path import'),
        ('StaticFiles', 'StaticFiles import'),
        ('static_dir = Path(__file__).parent / "static"', 'Static directory path'),
        ('app.mount("/static"', 'Static file mount'),
        ('FileResponse(str(index_file))', 'Dashboard file response')
    ]

    all_good = True
    for check_text, description in config_checks:
        if check_text in content:
            print_success(f"{description} found")
        else:
            print_error(f"{description} missing")
            all_good = False

    return all_good

def main():
    """Main verification function"""
    print("🧪 AI Trading Bot - Static File Fixes Verification")
    print("=" * 60)

    print_info("This script verifies that static file serving fixes are correctly implemented.")
    print_info("It checks file existence, content, and configuration without running the server.")

    # Run all checks
    checks = [
        ("Static Files Existence", check_static_files_exist),
        ("HTML File References", check_html_references),
        ("CSS File Content", check_css_content),
        ("JavaScript File Content", check_js_content),
        ("FastAPI Configuration", check_fastapi_config)
    ]

    passed_checks = 0
    total_checks = len(checks)

    for check_name, check_func in checks:
        print(f"\n🔍 Running {check_name} check...")
        try:
            if check_func():
                passed_checks += 1
                print_success(f"{check_name} check PASSED")
            else:
                print_error(f"{check_name} check FAILED")
        except Exception as e:
            print_error(f"{check_name} check ERROR: {e}")

    # Display results
    print("\n" + "=" * 60)
    print("📊 VERIFICATION RESULTS SUMMARY")
    print("=" * 60)
    print(f"Checks Passed: {passed_checks}/{total_checks}")

    if passed_checks == total_checks:
        print_success("🎉 ALL CHECKS PASSED!")
        print("\n✨ Static file fixes have been successfully implemented:")
        print("   • HTML file now references /static/styles.css and /static/dashboard.js")
        print("   • FastAPI is configured with robust static file serving")
        print("   • All static files exist and have correct content")
        print("   • Dashboard should now load with proper styling and functionality")

        print("\n🚀 Next Steps:")
        print("   1. Start the server: python src/main.py")
        print("   2. Open browser: http://localhost:8000/dashboard")
        print("   3. Verify the dashboard loads with proper styling")
        print("   4. Test interactive elements and real-time updates")

        return True
    else:
        print_error(f"❌ {total_checks - passed_checks} checks failed.")
        print_info("Please review the failed checks above and fix any issues.")
        return False

if __name__ == "__main__":
    import sys
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Verification interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
