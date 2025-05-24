"""
Database Connection Management

Handles PostgreSQL database connections, connection pooling, and session management.
"""

import asyncio
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager
import logging

from sqlalchemy.ext.asyncio import (
    create_async_engine, AsyncEngine, AsyncSession, async_sessionmaker
)
from sqlalchemy import text

from core.config import Settings, get_settings
from core.logger import get_trading_logger


class DatabaseManager:
    """
    Database connection and session manager

    Provides connection pooling, session management, and database operations
    for the trading bot's data persistence needs.
    """

    def __init__(self, settings: Settings):
        """
        Initialize database manager

        Args:
            settings: Application settings containing database configuration
        """
        self.settings = settings
        self.logger = get_trading_logger("DatabaseManager")

        # Database configuration
        self.db_config = settings.database

        # Connection components
        self.engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[async_sessionmaker] = None

        # Connection state
        self.is_connected = False
        self.connection_retries = 0
        self.max_retries = 3

    async def initialize(self) -> None:
        """Initialize database connection and engine"""
        try:
            # Build database URL
            db_url = self._build_database_url()

            # Create async engine with connection pooling
            self.engine = create_async_engine(
                db_url,
                pool_size=self.db_config.pool_size,
                max_overflow=self.db_config.max_overflow,
                pool_pre_ping=True,  # Validate connections before use
                pool_recycle=3600,   # Recycle connections every hour
                echo=self.settings.app.debug,  # Log SQL queries in debug mode
            )

            # Create session factory
            self.session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )

            # Test connection
            await self._test_connection()

            self.is_connected = True
            self.logger.logger.info("Database connection initialized successfully")

        except Exception as e:
            self.logger.error("Failed to initialize database connection", e)
            raise

    def _build_database_url(self) -> str:
        """Build database URL from configuration"""
        return (
            f"postgresql+asyncpg://"
            f"{self.db_config.username}:{self.db_config.password}@"
            f"{self.db_config.host}:{self.db_config.port}/"
            f"{self.db_config.database}"
        )

    async def _test_connection(self) -> None:
        """Test database connection"""
        if not self.engine:
            raise RuntimeError("Database engine not initialized")

        try:
            async with self.engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                await result.fetchone()

            self.logger.logger.info("Database connection test successful")

        except Exception as e:
            self.logger.error("Database connection test failed", e)
            raise

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get database session with automatic cleanup

        Usage:
            async with db_manager.get_session() as session:
                # Use session for database operations
                result = await session.execute(query)
        """
        if not self.session_factory:
            raise RuntimeError("Database not initialized")

        session = self.session_factory()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            self.logger.error("Database session error", e)
            raise
        finally:
            await session.close()

    async def execute_query(self, query: str, params: Optional[dict] = None) -> any:
        """
        Execute a raw SQL query

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Query result
        """
        async with self.get_session() as session:
            result = await session.execute(text(query), params or {})
            return result

    async def health_check(self) -> dict:
        """
        Perform database health check

        Returns:
            Health check results
        """
        try:
            start_time = asyncio.get_event_loop().time()

            # Test basic connectivity
            async with self.get_session() as session:
                await session.execute(text("SELECT 1"))

            end_time = asyncio.get_event_loop().time()
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds

            # Get connection pool status
            pool_status = {}
            if self.engine and hasattr(self.engine.pool, 'size'):
                pool_status = {
                    "pool_size": self.engine.pool.size(),
                    "checked_in": self.engine.pool.checkedin(),
                    "checked_out": self.engine.pool.checkedout(),
                    "overflow": self.engine.pool.overflow(),
                }

            return {
                "status": "healthy",
                "connected": self.is_connected,
                "response_time_ms": round(response_time, 2),
                "pool_status": pool_status,
                "database": self.db_config.database,
                "host": self.db_config.host
            }

        except Exception as e:
            self.logger.error("Database health check failed", e)
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e),
                "database": self.db_config.database,
                "host": self.db_config.host
            }

    async def create_tables(self) -> None:
        """Create database tables if they don't exist"""
        try:
            from .models import Base

            if not self.engine:
                raise RuntimeError("Database engine not initialized")

            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            self.logger.logger.info("Database tables created successfully")

        except Exception as e:
            self.logger.error("Failed to create database tables", e)
            raise

    async def drop_tables(self) -> None:
        """Drop all database tables (use with caution!)"""
        try:
            from .models import Base

            if not self.engine:
                raise RuntimeError("Database engine not initialized")

            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)

            self.logger.logger.warning("All database tables dropped")

        except Exception as e:
            self.logger.error("Failed to drop database tables", e)
            raise

    async def close(self) -> None:
        """Close database connections"""
        try:
            if self.engine:
                await self.engine.dispose()
                self.engine = None

            self.session_factory = None
            self.is_connected = False

            self.logger.logger.info("Database connections closed")

        except Exception as e:
            self.logger.error("Error closing database connections", e)

    def __del__(self):
        """Cleanup on object destruction"""
        if self.is_connected and self.engine:
            # Note: This is not ideal for async cleanup, but serves as a fallback
            self.logger.logger.warning("DatabaseManager destroyed with active connections")


# Global database manager instance
_database_manager: Optional[DatabaseManager] = None


async def get_database_manager() -> DatabaseManager:
    """
    Get global database manager instance

    Returns:
        DatabaseManager instance
    """
    global _database_manager

    if _database_manager is None:
        settings = get_settings()
        _database_manager = DatabaseManager(settings)
        await _database_manager.initialize()

    return _database_manager


async def close_database_manager() -> None:
    """Close global database manager"""
    global _database_manager

    if _database_manager:
        await _database_manager.close()
        _database_manager = None
