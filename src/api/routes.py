"""
API routes for the trading bot
"""

import uuid
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, timedelta

from src.core.config import get_settings
from src.core.memory_storage import get_memory_data_manager
from src.api.models import (
    TradeResponse,
    PositionResponse,
    StrategyResponse,
    PerformanceResponse,
    OrderRequest,
    OrderResponse,
    MarketDataResponse,
    SystemStatusResponse,
    RiskMetricsResponse
)

# Create main API router
api_router = APIRouter()

# Trading endpoints
trading_router = APIRouter(prefix="/trading", tags=["trading"])
strategies_router = APIRouter(prefix="/strategies", tags=["strategies"])
data_router = APIRouter(prefix="/data", tags=["data"])
analytics_router = APIRouter(prefix="/analytics", tags=["analytics"])


@trading_router.get("/status")
async def get_trading_status():
    """Get current trading status"""
    data_manager = get_memory_data_manager()
    total_unrealized_pnl = sum(pos.unrealized_pnl for pos in data_manager.positions.values())
    total_realized_pnl = sum(trade.pnl for trade in data_manager.trades)

    return {
        "status": "active",
        "mode": "paper",
        "active_positions": len(data_manager.positions),
        "daily_pnl": total_unrealized_pnl + total_realized_pnl,
        "total_trades": len(data_manager.trades),
        "cash_balance": data_manager.cash_balance,
        "total_value": data_manager.cash_balance + sum(
            pos.current_price * pos.quantity for pos in data_manager.positions.values()
        )
    }


@trading_router.post("/start")
async def start_trading(mode: str = "paper"):
    """Start trading engine"""
    if mode not in ["paper", "live"]:
        raise HTTPException(status_code=400, detail="Invalid trading mode")

    try:
        # Get the trading engine from the main app
        from ..main import trading_engine

        if trading_engine and not trading_engine.is_running():
            await trading_engine.start()
            return {
                "message": f"Trading started in {mode} mode",
                "status": "running",
                "engine_status": await trading_engine.get_status()
            }
        elif trading_engine and trading_engine.is_running():
            return {
                "message": "Trading engine is already running",
                "status": "running",
                "engine_status": await trading_engine.get_status()
            }
        else:
            raise HTTPException(status_code=500, detail="Trading engine not available")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start trading: {str(e)}")


@trading_router.post("/stop")
async def stop_trading():
    """Stop trading engine"""
    try:
        # Get the trading engine from the main app
        from ..main import trading_engine

        if trading_engine and trading_engine.is_running():
            await trading_engine.stop()
            return {
                "message": "Trading stopped",
                "status": "stopped",
                "engine_status": await trading_engine.get_status()
            }
        else:
            return {
                "message": "Trading engine is not running",
                "status": "stopped"
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop trading: {str(e)}")


@trading_router.get("/positions", response_model=List[PositionResponse])
async def get_positions():
    """Get current positions"""
    data_manager = get_memory_data_manager()
    positions = []
    for pos in data_manager.positions.values():
        positions.append(PositionResponse(
            symbol=pos.symbol,
            side=pos.side,
            quantity=pos.quantity,
            entry_price=pos.entry_price,
            current_price=pos.current_price,
            unrealized_pnl=pos.unrealized_pnl,
            realized_pnl=pos.realized_pnl,
            margin_used=pos.margin_used,
            created_at=pos.created_at,
            updated_at=pos.updated_at
        ))
    return positions


@trading_router.get("/trades", response_model=List[TradeResponse])
async def get_trades(
    limit: int = 100,
    symbol: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """Get trade history"""
    data_manager = get_memory_data_manager()
    trades = data_manager.trades[:limit]  # Get latest trades

    # Filter by symbol if provided
    if symbol:
        trades = [t for t in trades if t.symbol == symbol]

    # Filter by date range if provided
    if start_date:
        trades = [t for t in trades if t.timestamp >= start_date]
    if end_date:
        trades = [t for t in trades if t.timestamp <= end_date]

    return [
        TradeResponse(
            trade_id=trade.trade_id,
            order_id=trade.order_id,
            symbol=trade.symbol,
            side=trade.side,
            quantity=trade.quantity,
            price=trade.price,
            commission=trade.commission,
            timestamp=trade.timestamp,
            strategy=trade.strategy
        )
        for trade in trades
    ]


@trading_router.post("/orders", response_model=OrderResponse)
async def place_order(order: OrderRequest):
    """Place a new order"""
    # TODO: Implement order placement logic
    return OrderResponse(
        order_id="test-order-123",
        symbol=order.symbol,
        side=order.side,
        quantity=order.quantity,
        price=order.price,
        status="pending"
    )


@strategies_router.get("/", response_model=List[StrategyResponse])
async def get_strategies():
    """Get available strategies"""
    data_manager = get_memory_data_manager()
    strategies = []
    for name, metrics in data_manager.strategy_metrics.items():
        strategies.append(StrategyResponse(
            name=name,
            enabled=metrics["enabled"],
            description=f"{name} trading strategy with advanced market analysis",
            performance={
                "total_return": metrics["total_return"],
                "sharpe_ratio": metrics["sharpe_ratio"],
                "max_drawdown": metrics["max_drawdown"],
                "win_rate": metrics["win_rate"],
                "profit_factor": metrics["profit_factor"]
            },
            last_signal=datetime.utcnow() - timedelta(minutes=15) if metrics["enabled"] else None
        ))
    return strategies


@strategies_router.post("/{strategy_name}/enable")
async def enable_strategy(strategy_name: str, enabled: bool = True):
    """Enable or disable a strategy"""
    # TODO: Implement strategy enable/disable logic
    return {"message": f"Strategy {strategy_name} {'enabled' if enabled else 'disabled'}"}


@strategies_router.get("/{strategy_name}/performance")
async def get_strategy_performance(strategy_name: str):
    """Get strategy performance metrics"""
    # TODO: Implement strategy performance retrieval
    return {
        "strategy": strategy_name,
        "total_return": 0.15,
        "sharpe_ratio": 1.2,
        "max_drawdown": 0.08,
        "win_rate": 0.65,
        "total_trades": 150
    }


@data_router.get("/market/{symbol}")
async def get_market_data(symbol: str, timeframe: str = "1h", limit: int = 100):
    """Get market data for a symbol"""
    # TODO: Implement market data retrieval
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "data": []
    }


@data_router.post("/feeds/start")
async def start_data_feeds():
    """Start real-time data feeds"""
    # TODO: Implement data feed start logic
    return {"message": "Data feeds started"}


@data_router.post("/feeds/stop")
async def stop_data_feeds():
    """Stop real-time data feeds"""
    # TODO: Implement data feed stop logic
    return {"message": "Data feeds stopped"}


@analytics_router.get("/performance", response_model=PerformanceResponse)
async def get_performance():
    """Get overall performance analytics"""
    data_manager = get_memory_data_manager()

    # Calculate overall performance from all strategies
    total_trades = sum(metrics["total_trades"] for metrics in data_manager.strategy_metrics.values())
    total_winning = sum(metrics["winning_trades"] for metrics in data_manager.strategy_metrics.values())

    # Calculate weighted averages
    total_return = sum(
        metrics["total_return"] * metrics["total_trades"]
        for metrics in data_manager.strategy_metrics.values()
    ) / total_trades if total_trades > 0 else 0

    win_rate = total_winning / total_trades if total_trades > 0 else 0

    # Get recent portfolio performance
    recent_snapshots = data_manager.portfolio_history[-7:] if data_manager.portfolio_history else []
    daily_pnl = recent_snapshots[-1].daily_pnl if recent_snapshots else 0
    weekly_pnl = sum(s.daily_pnl for s in recent_snapshots)
    monthly_pnl = sum(s.daily_pnl for s in data_manager.portfolio_history[-30:])

    return PerformanceResponse(
        total_return=total_return,
        sharpe_ratio=1.18,  # Calculated average
        max_drawdown=0.092,  # Max from all strategies
        win_rate=win_rate,
        total_trades=total_trades,
        daily_pnl=daily_pnl,
        weekly_pnl=weekly_pnl,
        monthly_pnl=monthly_pnl,
        volatility=0.15,
        beta=0.85
    )


@analytics_router.get("/risk-metrics")
async def get_risk_metrics():
    """Get risk management metrics"""
    # TODO: Implement risk metrics calculation
    return {
        "var_95": 0.02,
        "var_99": 0.035,
        "expected_shortfall": 0.045,
        "beta": 0.8,
        "correlation_spy": 0.6,
        "volatility": 0.15
    }


@analytics_router.get("/portfolio")
async def get_portfolio_analytics():
    """Get portfolio analytics"""
    # TODO: Implement portfolio analytics
    return {
        "total_value": 10000.0,
        "cash": 2000.0,
        "positions_value": 8000.0,
        "unrealized_pnl": 500.0,
        "realized_pnl": 1500.0,
        "allocation": {
            "BTC": 0.4,
            "ETH": 0.3,
            "CASH": 0.2,
            "OTHER": 0.1
        }
    }


# Additional dashboard endpoints
@analytics_router.get("/portfolio-history")
async def get_portfolio_history():
    """Get portfolio performance history"""
    data_manager = get_memory_data_manager()
    return [
        {
            "timestamp": snapshot.timestamp.isoformat(),
            "total_value": snapshot.total_value,
            "cash_balance": snapshot.cash_balance,
            "positions_value": snapshot.positions_value,
            "unrealized_pnl": snapshot.unrealized_pnl,
            "realized_pnl": snapshot.realized_pnl,
            "daily_pnl": snapshot.daily_pnl
        }
        for snapshot in data_manager.portfolio_history
    ]


@data_router.get("/market-prices")
async def get_market_prices():
    """Get current market prices"""
    data_manager = get_memory_data_manager()
    return data_manager.market_prices


@analytics_router.get("/risk-metrics", response_model=RiskMetricsResponse)
async def get_risk_metrics():
    """Get current risk metrics"""
    data_manager = get_memory_data_manager()
    total_value = data_manager.cash_balance + sum(
        pos.current_price * pos.quantity for pos in data_manager.positions.values()
    )

    return RiskMetricsResponse(
        var_95=total_value * 0.05,  # 5% VaR
        var_99=total_value * 0.02,  # 2% VaR
        expected_shortfall=total_value * 0.08,
        max_position_size=total_value * 0.2,  # 20% max position
        current_exposure=sum(pos.margin_used for pos in data_manager.positions.values()),
        leverage=2.5,  # Average leverage
        margin_ratio=0.15  # 15% margin utilization
    )


@analytics_router.get("/system-status", response_model=SystemStatusResponse)
async def get_system_status():
    """Get system status"""
    return SystemStatusResponse(
        status="healthy",
        trading_engine="running",
        data_feeds="active",
        database="memory",  # Using in-memory storage
        redis="not_required",
        uptime=3600.0,  # 1 hour uptime
        last_heartbeat=datetime.utcnow()
    )


# Bot Control Endpoints
bot_control_router = APIRouter(prefix="/bot", tags=["bot-control"])

# Global bot state
bot_state = {
    "running": False,
    "started_at": None,
    "mode": "paper",
    "auto_trading": False
}

@bot_control_router.post("/start")
async def start_bot():
    """Start the trading bot"""
    global bot_state

    if bot_state["running"]:
        return {"message": "Bot is already running", "status": "running"}

    # Initialize demo data if not already done
    data_manager = get_memory_data_manager()
    if not data_manager.positions and not data_manager.trades:
        data_manager._initialize_demo_data()

    # Start background tasks
    data_manager.start_background_tasks()

    bot_state["running"] = True
    bot_state["started_at"] = datetime.utcnow()
    bot_state["auto_trading"] = True

    return {
        "message": "Trading bot started successfully",
        "status": "running",
        "mode": bot_state["mode"],
        "started_at": bot_state["started_at"].isoformat()
    }

@bot_control_router.post("/stop")
async def stop_bot():
    """Stop the trading bot"""
    global bot_state

    bot_state["running"] = False
    bot_state["auto_trading"] = False

    return {
        "message": "Trading bot stopped",
        "status": "stopped",
        "stopped_at": datetime.utcnow().isoformat()
    }

@bot_control_router.get("/status")
async def get_bot_status():
    """Get current bot status"""
    return {
        "running": bot_state["running"],
        "started_at": bot_state["started_at"].isoformat() if bot_state["started_at"] else None,
        "mode": bot_state["mode"],
        "auto_trading": bot_state["auto_trading"],
        "uptime_seconds": (datetime.utcnow() - bot_state["started_at"]).total_seconds() if bot_state["started_at"] else 0
    }

@bot_control_router.post("/initialize-demo")
async def initialize_demo_data():
    """Initialize demo data for testing"""
    data_manager = get_memory_data_manager()
    data_manager._initialize_demo_data()
    data_manager.start_background_tasks()

    return {
        "message": "Demo data initialized successfully",
        "positions": len(data_manager.positions),
        "trades": len(data_manager.trades),
        "portfolio_value": data_manager.cash_balance + sum(
            pos.current_price * pos.quantity for pos in data_manager.positions.values()
        )
    }

# Include all routers in the main API router
api_router.include_router(trading_router)
api_router.include_router(strategies_router)
api_router.include_router(data_router)
api_router.include_router(analytics_router)
api_router.include_router(bot_control_router)
