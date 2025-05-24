#!/usr/bin/env python3
"""
Database Setup and Testing Script

This script helps set up and test the PostgreSQL database for the trading bot.
It can work with both Docker and local PostgreSQL installations.
"""

import sys
import os
import asyncio
import subprocess
from pathlib import Path

# Add src to path
sys.path.append('src')

from core.config import get_settings
from database.connection import DatabaseManager
from database.models import Base, User, Strategy, Order, Trade, Position, Portfolio
from database.repositories import OrderRepository, TradeRepository, PositionRepository


async def check_database_connection():
    """Test basic database connectivity"""
    print("🔗 Testing Database Connection...")
    
    try:
        settings = get_settings()
        db_manager = DatabaseManager(settings)
        
        # Test initialization
        await db_manager.initialize()
        print("✅ Database connection initialized successfully")
        
        # Test health check
        health = await db_manager.health_check()
        print(f"   - Status: {health['status']}")
        print(f"   - Connected: {health['connected']}")
        print(f"   - Database: {health['database']}")
        
        # Test basic query
        async with db_manager.get_session() as session:
            from sqlalchemy import text
            result = await session.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"   - PostgreSQL Version: {version}")
        
        await db_manager.close()
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


async def test_database_models():
    """Test database models and basic operations"""
    print("\n📊 Testing Database Models...")
    
    try:
        settings = get_settings()
        db_manager = DatabaseManager(settings)
        await db_manager.initialize()
        
        async with db_manager.get_session() as session:
            # Test creating a test user
            from sqlalchemy import text
            
            # Check if tables exist
            result = await session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'trading'
            """))
            tables = [row[0] for row in result.fetchall()]
            print(f"   - Found tables: {tables}")
            
            # Test user creation
            if 'users' in tables:
                result = await session.execute(text("SELECT COUNT(*) FROM trading.users"))
                user_count = result.scalar()
                print(f"   - Users in database: {user_count}")
            
            # Test strategies
            if 'strategies' in tables:
                result = await session.execute(text("SELECT COUNT(*) FROM trading.strategies"))
                strategy_count = result.scalar()
                print(f"   - Strategies in database: {strategy_count}")
        
        await db_manager.close()
        print("✅ Database models test completed")
        return True
        
    except Exception as e:
        print(f"❌ Database models test failed: {e}")
        return False


async def test_repositories():
    """Test database repositories"""
    print("\n🏪 Testing Database Repositories...")
    
    try:
        settings = get_settings()
        db_manager = DatabaseManager(settings)
        await db_manager.initialize()
        
        async with db_manager.get_session() as session:
            # Test OrderRepository
            order_repo = OrderRepository(session)
            
            # Test basic repository functionality
            print("   - OrderRepository initialized")
            
            # Test TradeRepository
            trade_repo = TradeRepository(session)
            print("   - TradeRepository initialized")
            
            # Test PositionRepository
            position_repo = PositionRepository(session)
            print("   - PositionRepository initialized")
        
        await db_manager.close()
        print("✅ Repository tests completed")
        return True
        
    except Exception as e:
        print(f"❌ Repository tests failed: {e}")
        return False


def check_docker_availability():
    """Check if Docker is available"""
    try:
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ Docker available: {result.stdout.strip()}")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    print("❌ Docker not available")
    return False


def start_postgres_docker():
    """Start PostgreSQL using Docker Compose"""
    print("\n🐳 Starting PostgreSQL with Docker...")
    
    try:
        # Try docker compose first (newer syntax)
        result = subprocess.run(['docker', 'compose', 'up', 'postgres', '-d'], 
                              capture_output=True, text=True, timeout=120)
        
        if result.returncode != 0:
            # Try docker-compose (older syntax)
            result = subprocess.run(['docker-compose', 'up', 'postgres', '-d'], 
                                  capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("✅ PostgreSQL started successfully")
            print("   - Container: trading-postgres")
            print("   - Port: 5432")
            print("   - Database: trading_db")
            print("   - User: trading_user")
            return True
        else:
            print(f"❌ Failed to start PostgreSQL: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Docker command timed out")
        return False
    except FileNotFoundError:
        print("❌ Docker command not found")
        return False


async def main():
    """Main setup and testing function"""
    print("🚀 AI Trading Bot Database Setup")
    print("=" * 50)
    
    # Check environment
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ .env file not found. Please create it first.")
        return
    
    print("✅ Environment file found")
    
    # Check Docker availability
    docker_available = check_docker_availability()
    
    if docker_available:
        # Try to start PostgreSQL with Docker
        postgres_started = start_postgres_docker()
        
        if postgres_started:
            print("\n⏳ Waiting for PostgreSQL to be ready...")
            await asyncio.sleep(10)  # Give PostgreSQL time to start
    else:
        print("\n📝 Docker not available. Please install PostgreSQL manually:")
        print("   1. Install PostgreSQL 15+")
        print("   2. Create database 'trading_db'")
        print("   3. Create user 'trading_user' with password 'trading_pass'")
        print("   4. Run the SQL initialization script: sql/init.sql")
        print("\n   Or install Docker and run: docker compose up postgres -d")
    
    # Test database connection
    connection_ok = await check_database_connection()
    
    if connection_ok:
        # Test models
        await test_database_models()
        
        # Test repositories
        await test_repositories()
        
        print("\n🎉 Database setup completed successfully!")
        print("\n📋 Next steps:")
        print("   1. Run paper trading tests: python test_paper_trading.py")
        print("   2. Start the trading bot: python src/main.py")
        print("   3. Access the API: http://localhost:8000")
        
    else:
        print("\n❌ Database setup failed. Please check:")
        print("   1. PostgreSQL is running")
        print("   2. Database credentials are correct")
        print("   3. Database 'trading_db' exists")
        print("   4. Network connectivity")


if __name__ == "__main__":
    asyncio.run(main())
