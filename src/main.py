"""
AI Trading Bot - Main Application Entry Point
"""

import asyncio
import logging
import signal
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from src.core.config import get_settings
from src.core.engine import TradingEngine
from src.core.logger import setup_logging
from src.api.routes import api_router


# Global trading engine instance
trading_engine: TradingEngine = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager"""
    global trading_engine

    # Startup
    logger = logging.getLogger(__name__)
    logger.info("Starting AI Trading Bot...")

    try:
        # Initialize trading engine
        settings = get_settings()
        trading_engine = TradingEngine(settings)
        await trading_engine.initialize()

        # Start background tasks for in-memory data
        from src.core.memory_storage import get_memory_data_manager
        data_manager = get_memory_data_manager()
        data_manager.start_background_tasks()

        # Start trading engine if not in paper mode
        if settings.trading.mode != "paper":
            await trading_engine.start()

        logger.info("Trading bot started successfully")

    except Exception as e:
        logger.error(f"Failed to start trading bot: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down AI Trading Bot...")
    if trading_engine:
        await trading_engine.stop()
    logger.info("Trading bot stopped")


# Create FastAPI application
app = FastAPI(
    title="AI Trading Bot",
    description="Advanced AI-powered trading system with ICT and SMC strategies",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for dashboard
# Get the absolute path to the static directory
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint - Redirect to dashboard"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/dashboard")


@app.get("/dashboard")
async def dashboard():
    """Serve the trading dashboard"""
    from fastapi.responses import FileResponse
    # Use the same static directory path as configured above
    index_file = static_dir / "index.html"
    return FileResponse(str(index_file))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    global trading_engine

    if not trading_engine:
        raise HTTPException(status_code=503, detail="Trading engine not initialized")

    status = await trading_engine.get_status()
    return JSONResponse(content=status)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger = logging.getLogger(__name__)
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger = logging.getLogger(__name__)
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)


def main():
    """Main entry point"""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)

    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Get settings
    settings = get_settings()

    logger.info("Starting AI Trading Bot server...")

    # Run the application
    try:
        uvicorn.run(
            "main:app",
            host="127.0.0.1",  # Use localhost instead of 0.0.0.0
            port=8080,  # Use port 8080 to avoid conflicts
            reload=False,  # Disable reload for stability
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        print(f"❌ Server startup failed: {e}")
        print("🔄 Trying alternative port 8081...")
        try:
            uvicorn.run(
                "main:app",
                host="127.0.0.1",
                port=8081,
                reload=False,
                log_level="info"
            )
        except Exception as e2:
            logger.error(f"Alternative port also failed: {e2}")
            print(f"❌ Both ports failed. Error: {e2}")
            return


if __name__ == "__main__":
    main()
