#!/usr/bin/env python3
"""
Quick Start Script for AI Trading Bot Database Setup

This script guides you through the database setup process step by step.
"""

import sys
import os
import subprocess
import time
from pathlib import Path

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_step(step_num, title):
    """Print a formatted step"""
    print(f"\n🔸 Step {step_num}: {title}")
    print("-" * 40)

def check_docker():
    """Check if Docker is available"""
    try:
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Docker is available")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    print("❌ Docker not found")
    return False

def start_postgres_docker():
    """Start PostgreSQL with Docker"""
    print("Starting PostgreSQL container...")
    
    try:
        # Try docker compose
        result = subprocess.run(['docker', 'compose', 'up', 'postgres', '-d'], 
                              capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("✅ PostgreSQL container started successfully")
            print("   Container: trading-postgres")
            print("   Port: 5432")
            return True
        else:
            print(f"❌ Failed to start PostgreSQL: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error starting PostgreSQL: {e}")
        return False

def test_configuration():
    """Test database configuration"""
    print("Testing database configuration...")
    
    try:
        result = subprocess.run([sys.executable, 'test_database_config.py'], 
                              capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Configuration tests passed")
            return True
        else:
            print(f"❌ Configuration tests failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error running configuration tests: {e}")
        return False

def setup_database():
    """Set up database connection"""
    print("Setting up database connection...")
    
    try:
        result = subprocess.run([sys.executable, 'setup_database.py'], 
                              capture_output=True, text=True, timeout=60)
        
        if "Database connection initialized successfully" in result.stdout:
            print("✅ Database connection established")
            return True
        else:
            print("❌ Database connection failed")
            print("Output:", result.stdout)
            return False
            
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        return False

def test_paper_trading():
    """Test paper trading workflow"""
    print("Testing paper trading workflow...")
    
    try:
        result = subprocess.run([sys.executable, 'test_paper_trading.py'], 
                              capture_output=True, text=True, timeout=60)
        
        if "All paper trading tests completed!" in result.stdout:
            print("✅ Paper trading tests passed")
            return True
        else:
            print("❌ Paper trading tests failed")
            print("Output:", result.stdout)
            return False
            
    except Exception as e:
        print(f"❌ Error testing paper trading: {e}")
        return False

def main():
    """Main quick start process"""
    print_header("🚀 AI Trading Bot - Quick Start Setup")
    
    print("This script will help you set up the database for paper trading.")
    print("Make sure you're in the project root directory and virtual environment is activated.")
    
    # Check prerequisites
    print_step(1, "Checking Prerequisites")
    
    # Check .env file
    if not Path('.env').exists():
        print("❌ .env file not found")
        print("   Please run the database setup first or copy from .env.example")
        return False
    else:
        print("✅ .env file found")
    
    # Check virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Virtual environment detected")
    else:
        print("⚠️  Virtual environment not detected")
        print("   Consider activating your virtual environment")
    
    # Test configuration
    print_step(2, "Testing Configuration")
    if not test_configuration():
        print("❌ Configuration tests failed. Please check your setup.")
        return False
    
    # Check Docker
    print_step(3, "Database Setup")
    docker_available = check_docker()
    
    if docker_available:
        print("\nOption 1: Using Docker (Recommended)")
        response = input("Start PostgreSQL with Docker? (y/n): ").lower().strip()
        
        if response == 'y':
            if start_postgres_docker():
                print("Waiting for PostgreSQL to be ready...")
                time.sleep(10)
                
                # Test database connection
                print_step(4, "Testing Database Connection")
                if setup_database():
                    print("✅ Database setup complete!")
                else:
                    print("❌ Database connection failed")
                    print("   PostgreSQL might still be starting up")
                    print("   Try running: python setup_database.py")
                    return False
            else:
                print("❌ Failed to start PostgreSQL with Docker")
                return False
        else:
            print("Skipping Docker setup")
    else:
        print("\nDocker not available. Please install PostgreSQL manually:")
        print("1. Install PostgreSQL 15+")
        print("2. Create database 'trading_db'")
        print("3. Create user 'trading_user' with password 'trading_pass'")
        print("4. Run: psql -U trading_user -d trading_db -f sql/init.sql")
        print("5. Then run: python setup_database.py")
        return False
    
    # Test paper trading
    print_step(5, "Testing Paper Trading")
    if test_paper_trading():
        print("✅ Paper trading setup complete!")
    else:
        print("❌ Paper trading tests failed")
        print("   Database might not be fully initialized")
        print("   Try running: python test_paper_trading.py")
    
    # Success message
    print_header("🎉 Setup Complete!")
    print("Your AI Trading Bot database is ready for paper trading!")
    print("\n📋 Next Steps:")
    print("   1. Configure exchange API keys (optional for paper trading)")
    print("   2. Run the trading bot: python src/main.py")
    print("   3. Access the API: http://localhost:8000")
    print("   4. View logs: tail -f logs/trading_bot.log")
    print("\n📊 Available Commands:")
    print("   - Test configuration: python test_database_config.py")
    print("   - Test database: python setup_database.py")
    print("   - Test paper trading: python test_paper_trading.py")
    print("   - Start trading bot: python src/main.py")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        sys.exit(1)
