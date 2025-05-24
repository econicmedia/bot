#!/usr/bin/env python3
"""
Minimal Working Server - Bypass Import Issues
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

# Simple FastAPI server with static files
try:
    from fastapi import FastAPI
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse, JSONResponse
    import uvicorn
    
    print("✅ FastAPI imports successful")
    
    # Create app
    app = FastAPI(title="AI Trading Bot - Minimal")
    
    # Mount static files
    static_dir = Path("src/static")
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        print(f"✅ Static files mounted from: {static_dir}")
    else:
        print(f"❌ Static directory not found: {static_dir}")
    
    @app.get("/")
    async def root():
        return {"message": "AI Trading Bot Server is running!", "status": "ok"}
    
    @app.get("/dashboard")
    async def dashboard():
        index_file = static_dir / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        else:
            return JSONResponse({"error": "Dashboard not found"}, status_code=404)
    
    @app.get("/health")
    async def health():
        return {"status": "healthy", "message": "Server is running"}
    
    # Mock API endpoints for dashboard
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
            {
                "symbol": "BTCUSDT",
                "side": "long",
                "quantity": 0.25,
                "entry_price": 42800.0,
                "current_price": 43250.50,
                "unrealized_pnl": 112.63,
                "realized_pnl": 0.0,
                "margin_used": 1070.0,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T15:45:00Z"
            },
            {
                "symbol": "ETHUSDT", 
                "side": "long",
                "quantity": 2.5,
                "entry_price": 2520.0,
                "current_price": 2580.75,
                "unrealized_pnl": 151.88,
                "realized_pnl": 0.0,
                "margin_used": 630.0,
                "created_at": "2024-01-15T09:15:00Z",
                "updated_at": "2024-01-15T15:45:00Z"
            },
            {
                "symbol": "SOLUSDT",
                "side": "short", 
                "quantity": 10.0,
                "entry_price": 102.30,
                "current_price": 98.45,
                "unrealized_pnl": 38.50,
                "realized_pnl": 0.0,
                "margin_used": 255.75,
                "created_at": "2024-01-15T11:20:00Z",
                "updated_at": "2024-01-15T15:45:00Z"
            }
        ]
    
    @app.get("/api/v1/strategies/")
    async def get_strategies():
        return [
            {
                "name": "ICT",
                "enabled": True,
                "description": "Inner Circle Trader strategy with advanced market analysis",
                "performance": {
                    "total_return": 0.156,
                    "sharpe_ratio": 1.34,
                    "max_drawdown": 0.078,
                    "win_rate": 0.672,
                    "profit_factor": 2.18
                },
                "last_signal": "2024-01-15T15:30:00Z"
            },
            {
                "name": "SMC",
                "enabled": True,
                "description": "Smart Money Concepts strategy",
                "performance": {
                    "total_return": 0.089,
                    "sharpe_ratio": 0.98,
                    "max_drawdown": 0.045,
                    "win_rate": 0.614,
                    "profit_factor": 1.87
                },
                "last_signal": "2024-01-15T15:25:00Z"
            }
        ]
    
    @app.get("/api/v1/trading/trades")
    async def get_trades():
        return [
            {
                "trade_id": "trade_001",
                "order_id": "order_001", 
                "symbol": "BTCUSDT",
                "side": "buy",
                "quantity": 0.1,
                "price": 42500.0,
                "commission": 4.25,
                "timestamp": "2024-01-15T14:30:00Z",
                "strategy": "ICT",
                "pnl": 125.50
            },
            {
                "trade_id": "trade_002",
                "order_id": "order_002",
                "symbol": "ETHUSDT", 
                "side": "buy",
                "quantity": 1.0,
                "price": 2480.0,
                "commission": 2.48,
                "timestamp": "2024-01-15T13:15:00Z",
                "strategy": "SMC",
                "pnl": 87.25
            }
        ]
    
    @app.get("/api/v1/analytics/performance")
    async def get_performance():
        return {
            "total_return": 0.156,
            "sharpe_ratio": 1.18,
            "max_drawdown": 0.092,
            "win_rate": 0.644,
            "total_trades": 15,
            "daily_pnl": 245.67,
            "weekly_pnl": 892.34,
            "monthly_pnl": 1560.00,
            "volatility": 0.15,
            "beta": 0.85
        }
    
    @app.get("/api/v1/analytics/risk-metrics")
    async def get_risk_metrics():
        return {
            "var_95": 578.0,
            "var_99": 231.2,
            "expected_shortfall": 924.8,
            "max_position_size": 2312.0,
            "current_exposure": 1955.75,
            "leverage": 2.5,
            "margin_ratio": 0.15
        }
    
    @app.post("/api/v1/bot/start")
    async def start_bot():
        return {
            "message": "Trading bot started successfully",
            "status": "running",
            "mode": "paper",
            "started_at": "2024-01-15T15:45:00Z"
        }
    
    @app.post("/api/v1/bot/stop")
    async def stop_bot():
        return {
            "message": "Trading bot stopped",
            "status": "stopped",
            "stopped_at": "2024-01-15T15:45:00Z"
        }
    
    @app.get("/api/v1/bot/status")
    async def bot_status():
        return {
            "running": False,
            "started_at": None,
            "mode": "paper",
            "auto_trading": False,
            "uptime_seconds": 0
        }
    
    @app.post("/api/v1/bot/initialize-demo")
    async def initialize_demo():
        return {
            "message": "Demo data initialized successfully",
            "positions": 3,
            "trades": 15,
            "portfolio_value": 11560.0
        }
    
    if __name__ == "__main__":
        print("🚀 Starting AI Trading Bot Server...")
        print("📊 Dashboard: http://localhost:8000/dashboard")
        print("🔧 API Docs: http://localhost:8000/docs")
        print("❤️ Health: http://localhost:8000/health")
        
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
        
except Exception as e:
    print(f"❌ Server startup failed: {e}")
    import traceback
    traceback.print_exc()
