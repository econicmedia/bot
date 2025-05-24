"""
Base Exchange Interface

Defines the common interface that all exchange integrations must implement.
This ensures consistency across different exchange implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from enum import Enum
import asyncio
from dataclasses import dataclass


class OrderSide(Enum):
    """Order side enumeration"""
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    """Order type enumeration"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderStatus(Enum):
    """Order status enumeration"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class ExchangeOrder:
    """Exchange order representation"""
    id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    average_fill_price: float = 0.0
    commission: float = 0.0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    exchange_order_id: Optional[str] = None


@dataclass
class MarketTicker:
    """Market ticker data"""
    symbol: str
    bid: float
    ask: float
    last: float
    volume: float
    high_24h: float
    low_24h: float
    change_24h: float
    change_24h_pct: float
    timestamp: datetime


@dataclass
class OrderBook:
    """Order book data"""
    symbol: str
    bids: List[List[float]]  # [price, quantity]
    asks: List[List[float]]  # [price, quantity]
    timestamp: datetime


@dataclass
class Trade:
    """Trade data"""
    id: str
    symbol: str
    side: OrderSide
    quantity: float
    price: float
    commission: float
    timestamp: datetime


class ExchangeError(Exception):
    """Base exchange error"""
    pass


class ConnectionError(ExchangeError):
    """Connection related error"""
    pass


class AuthenticationError(ExchangeError):
    """Authentication related error"""
    pass


class InsufficientFundsError(ExchangeError):
    """Insufficient funds error"""
    pass


class InvalidOrderError(ExchangeError):
    """Invalid order error"""
    pass


class BaseExchange(ABC):
    """
    Base exchange interface that all exchange implementations must inherit from.
    
    This abstract class defines the common methods that every exchange integration
    must implement to ensure consistency across different exchanges.
    """
    
    def __init__(self, api_key: str, api_secret: str, sandbox: bool = True):
        """
        Initialize exchange connection
        
        Args:
            api_key: Exchange API key
            api_secret: Exchange API secret
            sandbox: Whether to use sandbox/testnet environment
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.sandbox = sandbox
        self.is_connected = False
        self.websocket_callbacks: Dict[str, List[Callable]] = {}
        
    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish connection to the exchange
        
        Returns:
            True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the exchange"""
        pass
    
    @abstractmethod
    async def get_account_info(self) -> Dict[str, Any]:
        """
        Get account information including balances
        
        Returns:
            Dictionary containing account information
        """
        pass
    
    @abstractmethod
    async def get_ticker(self, symbol: str) -> MarketTicker:
        """
        Get market ticker for a symbol
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            
        Returns:
            MarketTicker object
        """
        pass
    
    @abstractmethod
    async def get_order_book(self, symbol: str, limit: int = 100) -> OrderBook:
        """
        Get order book for a symbol
        
        Args:
            symbol: Trading symbol
            limit: Number of price levels to return
            
        Returns:
            OrderBook object
        """
        pass
    
    @abstractmethod
    async def place_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        time_in_force: str = "GTC"
    ) -> ExchangeOrder:
        """
        Place an order on the exchange
        
        Args:
            symbol: Trading symbol
            side: Order side (buy/sell)
            order_type: Order type (market/limit/stop/stop_limit)
            quantity: Order quantity
            price: Order price (for limit orders)
            stop_price: Stop price (for stop orders)
            time_in_force: Time in force (GTC, IOC, FOK)
            
        Returns:
            ExchangeOrder object
        """
        pass
    
    @abstractmethod
    async def cancel_order(self, symbol: str, order_id: str) -> bool:
        """
        Cancel an order
        
        Args:
            symbol: Trading symbol
            order_id: Exchange order ID
            
        Returns:
            True if cancellation successful
        """
        pass
    
    @abstractmethod
    async def get_order_status(self, symbol: str, order_id: str) -> ExchangeOrder:
        """
        Get order status
        
        Args:
            symbol: Trading symbol
            order_id: Exchange order ID
            
        Returns:
            ExchangeOrder object with current status
        """
        pass
    
    @abstractmethod
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[ExchangeOrder]:
        """
        Get open orders
        
        Args:
            symbol: Trading symbol (optional, if None returns all open orders)
            
        Returns:
            List of ExchangeOrder objects
        """
        pass
    
    @abstractmethod
    async def get_trade_history(
        self,
        symbol: Optional[str] = None,
        limit: int = 100
    ) -> List[Trade]:
        """
        Get trade history
        
        Args:
            symbol: Trading symbol (optional)
            limit: Maximum number of trades to return
            
        Returns:
            List of Trade objects
        """
        pass
    
    @abstractmethod
    async def start_websocket(self, symbols: List[str]) -> None:
        """
        Start WebSocket connection for real-time data
        
        Args:
            symbols: List of symbols to subscribe to
        """
        pass
    
    @abstractmethod
    async def stop_websocket(self) -> None:
        """Stop WebSocket connection"""
        pass
    
    def add_websocket_callback(self, event_type: str, callback: Callable) -> None:
        """
        Add callback for WebSocket events
        
        Args:
            event_type: Type of event (ticker, orderbook, trade, etc.)
            callback: Callback function to execute
        """
        if event_type not in self.websocket_callbacks:
            self.websocket_callbacks[event_type] = []
        self.websocket_callbacks[event_type].append(callback)
    
    def remove_websocket_callback(self, event_type: str, callback: Callable) -> None:
        """
        Remove callback for WebSocket events
        
        Args:
            event_type: Type of event
            callback: Callback function to remove
        """
        if event_type in self.websocket_callbacks:
            try:
                self.websocket_callbacks[event_type].remove(callback)
            except ValueError:
                pass
    
    async def _notify_websocket_callbacks(self, event_type: str, data: Any) -> None:
        """
        Notify all callbacks for a specific event type
        
        Args:
            event_type: Type of event
            data: Event data
        """
        if event_type in self.websocket_callbacks:
            for callback in self.websocket_callbacks[event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    # Log error but don't stop other callbacks
                    print(f"Error in websocket callback: {e}")
