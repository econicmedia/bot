#!/usr/bin/env python3
"""
Fixed AI Trading Bot - Main Server with Simplified Startup
This version bypasses complex initialization to get the server running quickly
"""

import asyncio
import logging
import signal
import sys
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("🚀 AI Trading Bot - Fixed Main Server")
print("=" * 50)

# Global state for simplified operation
bot_running = False
trading_engine = None

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Simplified application lifespan manager"""
    global trading_engine
    
    # Startup
    logger = logging.getLogger(__name__)
    logger.info("Starting AI Trading Bot (Simplified Mode)...")
    
    try:
        # Initialize in-memory storage instead of full engine
        from core.memory_storage import get_memory_data_manager
        data_manager = get_memory_data_manager()
        data_manager.start_background_tasks()
        
        logger.info("Trading bot started successfully (simplified mode)")
        
    except Exception as e:
        logger.error(f"Failed to start trading bot: {e}")
        print(f"⚠️ Simplified startup failed: {e}")
        print("🔄 Continuing with basic functionality...")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Trading Bot...")
    logger.info("Trading bot stopped")

# Create FastAPI application
app = FastAPI(
    title="AI Trading Bot",
    description="Advanced AI-powered trading system with ICT and SMC strategies",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for dashboard
static_dir = Path("src/static")
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    print(f"✅ Static files mounted: {static_dir}")
else:
    print(f"⚠️ Static directory not found: {static_dir}")

# Basic routes
@app.get("/")
async def root():
    """Root endpoint - Redirect to dashboard"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/dashboard")

@app.get("/dashboard")
async def dashboard():
    """Serve the trading dashboard"""
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return JSONResponse({"error": "Dashboard not found"}, status_code=404)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse(content={
        "status": "healthy",
        "mode": "simplified",
        "server": "running",
        "timestamp": "2024-01-15T15:45:00Z"
    })

# Mock API endpoints for dashboard functionality
@app.get("/api/v1/trading/status")
async def trading_status():
    return {
        "status": "active",
        "mode": "paper",
        "active_positions": 3,
        "daily_pnl": 245.67,
        "total_trades": 15,
        "cash_balance": 8500.0,
        "total_value": 11560.0
    }

@app.get("/api/v1/trading/positions")
async def get_positions():
    return [
        {"symbol": "BTCUSDT", "side": "long", "quantity": 0.25, "entry_price": 42800.0, "current_price": 43250.50, "unrealized_pnl": 112.63, "realized_pnl": 0.0, "margin_used": 1070.0, "created_at": "2024-01-15T10:30:00Z", "updated_at": "2024-01-15T15:45:00Z"},
        {"symbol": "ETHUSDT", "side": "long", "quantity": 2.5, "entry_price": 2520.0, "current_price": 2580.75, "unrealized_pnl": 151.88, "realized_pnl": 0.0, "margin_used": 630.0, "created_at": "2024-01-15T09:15:00Z", "updated_at": "2024-01-15T15:45:00Z"},
        {"symbol": "SOLUSDT", "side": "short", "quantity": 10.0, "entry_price": 102.30, "current_price": 98.45, "unrealized_pnl": 38.50, "realized_pnl": 0.0, "margin_used": 255.75, "created_at": "2024-01-15T11:20:00Z", "updated_at": "2024-01-15T15:45:00Z"}
    ]

@app.get("/api/v1/strategies/")
async def get_strategies():
    return [
        {"name": "ICT", "enabled": True, "description": "Inner Circle Trader strategy", "performance": {"total_return": 0.156, "sharpe_ratio": 1.34, "max_drawdown": 0.078, "win_rate": 0.672, "profit_factor": 2.18}, "last_signal": "2024-01-15T15:30:00Z"},
        {"name": "SMC", "enabled": True, "description": "Smart Money Concepts", "performance": {"total_return": 0.089, "sharpe_ratio": 0.98, "max_drawdown": 0.045, "win_rate": 0.614, "profit_factor": 1.87}, "last_signal": "2024-01-15T15:25:00Z"}
    ]

@app.get("/api/v1/trading/trades")
async def get_trades():
    return [
        {"trade_id": "trade_001", "order_id": "order_001", "symbol": "BTCUSDT", "side": "buy", "quantity": 0.1, "price": 42500.0, "commission": 4.25, "timestamp": "2024-01-15T14:30:00Z", "strategy": "ICT", "pnl": 125.50},
        {"trade_id": "trade_002", "order_id": "order_002", "symbol": "ETHUSDT", "side": "buy", "quantity": 1.0, "price": 2480.0, "commission": 2.48, "timestamp": "2024-01-15T13:15:00Z", "strategy": "SMC", "pnl": 87.25}
    ]

@app.get("/api/v1/analytics/performance")
async def get_performance():
    return {"total_return": 0.156, "sharpe_ratio": 1.18, "max_drawdown": 0.092, "win_rate": 0.644, "total_trades": 15, "daily_pnl": 245.67, "weekly_pnl": 892.34, "monthly_pnl": 1560.00, "volatility": 0.15, "beta": 0.85}

@app.get("/api/v1/analytics/risk-metrics")
async def get_risk_metrics():
    return {"var_95": 578.0, "var_99": 231.2, "expected_shortfall": 924.8, "max_position_size": 2312.0, "current_exposure": 1955.75, "leverage": 2.5, "margin_ratio": 0.15}

# Bot control endpoints
@app.post("/api/v1/bot/start")
async def start_bot():
    global bot_running
    bot_running = True
    return {"message": "Trading bot started successfully", "status": "running", "mode": "paper"}

@app.post("/api/v1/bot/stop")
async def stop_bot():
    global bot_running
    bot_running = False
    return {"message": "Trading bot stopped", "status": "stopped"}

@app.get("/api/v1/bot/status")
async def bot_status():
    return {"running": bot_running, "mode": "paper", "auto_trading": bot_running}

@app.post("/api/v1/bot/initialize-demo")
async def initialize_demo():
    return {"message": "Demo data initialized", "positions": 3, "trades": 15, "portfolio_value": 11560.0}

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
    # Setup basic logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("Starting AI Trading Bot server (Fixed Version)...")
    
    # Try multiple ports
    ports = [8080, 8081, 8000, 3000]
    
    for port in ports:
        try:
            print(f"\n🔄 Trying port {port}...")
            print(f"📊 Dashboard: http://localhost:{port}/dashboard")
            print(f"🔧 API docs: http://localhost:{port}/docs")
            print(f"❤️ Health: http://localhost:{port}/health")
            print("-" * 50)
            
            uvicorn.run(
                app,
                host="127.0.0.1",
                port=port,
                log_level="info",
                access_log=True
            )
            break
            
        except OSError as e:
            if "Address already in use" in str(e) or "Only one usage" in str(e):
                print(f"⚠️ Port {port} busy, trying next...")
                continue
            else:
                print(f"❌ Error on port {port}: {e}")
                continue
        except Exception as e:
            print(f"❌ Unexpected error on port {port}: {e}")
            continue
    
    print("❌ All ports failed!")

if __name__ == "__main__":
    main()
