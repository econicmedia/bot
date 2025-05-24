"""
Pydantic models for API requests and responses
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

from pydantic import BaseModel, Field


class OrderSide(str, Enum):
    """Order side enumeration"""
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    """Order type enumeration"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderStatus(str, Enum):
    """Order status enumeration"""
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class PositionSide(str, Enum):
    """Position side enumeration"""
    LONG = "long"
    SHORT = "short"


# Request Models

class OrderRequest(BaseModel):
    """Order placement request"""
    symbol: str = Field(..., description="Trading symbol (e.g., BTCUSDT)")
    side: OrderSide = Field(..., description="Order side (buy/sell)")
    quantity: float = Field(..., gt=0, description="Order quantity")
    order_type: OrderType = Field(default=OrderType.MARKET, description="Order type")
    price: Optional[float] = Field(None, gt=0, description="Order price (for limit orders)")
    stop_price: Optional[float] = Field(None, gt=0, description="Stop price (for stop orders)")
    time_in_force: str = Field(default="GTC", description="Time in force")


class StrategyConfigRequest(BaseModel):
    """Strategy configuration request"""
    strategy_name: str = Field(..., description="Strategy name")
    enabled: bool = Field(..., description="Enable/disable strategy")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Strategy parameters")


# Response Models

class OrderResponse(BaseModel):
    """Order response"""
    order_id: str = Field(..., description="Unique order identifier")
    symbol: str = Field(..., description="Trading symbol")
    side: OrderSide = Field(..., description="Order side")
    quantity: float = Field(..., description="Order quantity")
    price: Optional[float] = Field(None, description="Order price")
    status: OrderStatus = Field(..., description="Order status")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")


class TradeResponse(BaseModel):
    """Trade execution response"""
    trade_id: str = Field(..., description="Unique trade identifier")
    order_id: str = Field(..., description="Associated order ID")
    symbol: str = Field(..., description="Trading symbol")
    side: OrderSide = Field(..., description="Trade side")
    quantity: float = Field(..., description="Executed quantity")
    price: float = Field(..., description="Execution price")
    commission: float = Field(..., description="Commission paid")
    timestamp: datetime = Field(..., description="Execution timestamp")
    strategy: Optional[str] = Field(None, description="Strategy that generated the trade")


class PositionResponse(BaseModel):
    """Position response"""
    symbol: str = Field(..., description="Trading symbol")
    side: PositionSide = Field(..., description="Position side")
    quantity: float = Field(..., description="Position quantity")
    entry_price: float = Field(..., description="Average entry price")
    current_price: float = Field(..., description="Current market price")
    unrealized_pnl: float = Field(..., description="Unrealized P&L")
    realized_pnl: float = Field(..., description="Realized P&L")
    margin_used: float = Field(..., description="Margin used")
    created_at: datetime = Field(..., description="Position creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class StrategyResponse(BaseModel):
    """Strategy information response"""
    name: str = Field(..., description="Strategy name")
    enabled: bool = Field(..., description="Strategy status")
    description: Optional[str] = Field(None, description="Strategy description")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Strategy parameters")
    performance: Dict[str, float] = Field(default_factory=dict, description="Performance metrics")
    last_signal: Optional[datetime] = Field(None, description="Last signal timestamp")


class PerformanceResponse(BaseModel):
    """Performance metrics response"""
    total_return: float = Field(..., description="Total return percentage")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    max_drawdown: float = Field(..., description="Maximum drawdown percentage")
    win_rate: float = Field(..., description="Win rate percentage")
    total_trades: int = Field(..., description="Total number of trades")
    daily_pnl: float = Field(..., description="Daily P&L")
    weekly_pnl: float = Field(..., description="Weekly P&L")
    monthly_pnl: float = Field(..., description="Monthly P&L")
    volatility: Optional[float] = Field(None, description="Portfolio volatility")
    beta: Optional[float] = Field(None, description="Portfolio beta")


class MarketDataResponse(BaseModel):
    """Market data response"""
    symbol: str = Field(..., description="Trading symbol")
    timestamp: datetime = Field(..., description="Data timestamp")
    open: float = Field(..., description="Open price")
    high: float = Field(..., description="High price")
    low: float = Field(..., description="Low price")
    close: float = Field(..., description="Close price")
    volume: float = Field(..., description="Volume")


class SignalResponse(BaseModel):
    """Trading signal response"""
    signal_id: str = Field(..., description="Unique signal identifier")
    strategy: str = Field(..., description="Strategy name")
    symbol: str = Field(..., description="Trading symbol")
    signal_type: str = Field(..., description="Signal type (buy/sell/hold)")
    confidence: float = Field(..., ge=0, le=1, description="Signal confidence (0-1)")
    price: float = Field(..., description="Signal price")
    timestamp: datetime = Field(..., description="Signal timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional signal data")


class RiskMetricsResponse(BaseModel):
    """Risk metrics response"""
    var_95: float = Field(..., description="Value at Risk (95%)")
    var_99: float = Field(..., description="Value at Risk (99%)")
    expected_shortfall: float = Field(..., description="Expected Shortfall")
    max_position_size: float = Field(..., description="Maximum position size")
    current_exposure: float = Field(..., description="Current market exposure")
    leverage: float = Field(..., description="Current leverage")
    margin_ratio: float = Field(..., description="Margin utilization ratio")


class SystemStatusResponse(BaseModel):
    """System status response"""
    status: str = Field(..., description="Overall system status")
    trading_engine: str = Field(..., description="Trading engine status")
    data_feeds: str = Field(..., description="Data feeds status")
    database: str = Field(..., description="Database connection status")
    redis: str = Field(..., description="Redis connection status")
    uptime: float = Field(..., description="System uptime in seconds")
    last_heartbeat: datetime = Field(..., description="Last heartbeat timestamp")


class NewsResponse(BaseModel):
    """News item response"""
    news_id: str = Field(..., description="Unique news identifier")
    title: str = Field(..., description="News title")
    content: str = Field(..., description="News content")
    source: str = Field(..., description="News source")
    sentiment_score: float = Field(..., ge=-1, le=1, description="Sentiment score (-1 to 1)")
    impact_score: float = Field(..., ge=0, le=1, description="Market impact score (0-1)")
    symbols: List[str] = Field(default_factory=list, description="Related symbols")
    published_at: datetime = Field(..., description="Publication timestamp")
    processed_at: datetime = Field(..., description="Processing timestamp")


class BacktestRequest(BaseModel):
    """Backtest request"""
    strategy: str = Field(..., description="Strategy to backtest")
    symbol: str = Field(..., description="Trading symbol")
    start_date: datetime = Field(..., description="Backtest start date")
    end_date: datetime = Field(..., description="Backtest end date")
    initial_capital: float = Field(default=10000, gt=0, description="Initial capital")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Strategy parameters")


class BacktestResponse(BaseModel):
    """Backtest results response"""
    backtest_id: str = Field(..., description="Unique backtest identifier")
    strategy: str = Field(..., description="Strategy name")
    symbol: str = Field(..., description="Trading symbol")
    start_date: datetime = Field(..., description="Backtest start date")
    end_date: datetime = Field(..., description="Backtest end date")
    initial_capital: float = Field(..., description="Initial capital")
    final_capital: float = Field(..., description="Final capital")
    total_return: float = Field(..., description="Total return percentage")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    max_drawdown: float = Field(..., description="Maximum drawdown")
    total_trades: int = Field(..., description="Total number of trades")
    win_rate: float = Field(..., description="Win rate percentage")
    profit_factor: float = Field(..., description="Profit factor")
    created_at: datetime = Field(..., description="Backtest creation timestamp")
