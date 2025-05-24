"""
Data Manager - Handles market data ingestion and processing
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from collections import defaultdict, deque
import json

from .config import Settings
from .logger import get_trading_logger


class DataType(str):
    """Data type constants"""
    TICK = "tick"
    CANDLE = "candle"
    ORDER_BOOK = "order_book"
    TRADE = "trade"


class Timeframe(str):
    """Timeframe constants"""
    TICK = "tick"
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"


class MarketData:
    """Market data container"""

    def __init__(self, symbol: str, data_type: str, timestamp: datetime, data: Dict[str, Any]):
        self.symbol = symbol
        self.data_type = data_type
        self.timestamp = timestamp
        self.data = data

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "symbol": self.symbol,
            "data_type": self.data_type,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data
        }


class Candle:
    """OHLCV candle data"""

    def __init__(
        self,
        symbol: str,
        timeframe: str,
        timestamp: datetime,
        open_price: float,
        high_price: float,
        low_price: float,
        close_price: float,
        volume: float
    ):
        self.symbol = symbol
        self.timeframe = timeframe
        self.timestamp = timestamp
        self.open = open_price
        self.high = high_price
        self.low = low_price
        self.close = close_price
        self.volume = volume

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "timestamp": self.timestamp.isoformat(),
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume
        }


class DataSubscription:
    """Data subscription configuration"""

    def __init__(
        self,
        symbol: str,
        data_type: str,
        timeframe: Optional[str] = None,
        callback: Optional[Callable[[MarketData], None]] = None
    ):
        self.symbol = symbol
        self.data_type = data_type
        self.timeframe = timeframe
        self.callback = callback
        self.active = True
        self.created_at = datetime.utcnow()


class DataManager:
    """Manages market data ingestion and processing"""

    def __init__(self, settings: Settings):
        """Initialize data manager"""
        self.settings = settings
        self.logger = get_trading_logger("DataManager")

        # Data storage
        self.candle_data: Dict[str, Dict[str, deque]] = defaultdict(lambda: defaultdict(deque))
        self.tick_data: Dict[str, deque] = defaultdict(deque)
        self.order_book_data: Dict[str, Dict[str, Any]] = {}

        # Subscriptions
        self.subscriptions: List[DataSubscription] = []
        self.data_callbacks: List[Callable[[MarketData], None]] = []

        # Data sources
        self.data_sources: Dict[str, Any] = {}
        self.primary_source = settings.data_sources.primary
        self.backup_source = settings.data_sources.backup

        # Configuration
        self.max_candles_per_timeframe = 1000
        self.max_ticks_per_symbol = 10000

        # State
        self.is_running = False
        self.last_heartbeat = datetime.utcnow()

        self.logger.logger.info("Data manager initialized")

    async def start(self) -> None:
        """Start data collection"""
        if not self.is_running:
            await self.initialize()
        self.logger.logger.info("Data manager started")

    async def initialize(self) -> None:
        """Initialize data manager"""
        try:
            # Initialize data sources
            await self._initialize_data_sources()

            # Start data processing tasks
            await self._start_data_tasks()

            self.is_running = True
            self.logger.logger.info("Data manager initialized successfully")

        except Exception as e:
            self.logger.error("Failed to initialize data manager", e)
            raise

    async def _initialize_data_sources(self) -> None:
        """Initialize data source connections"""
        # TODO: Initialize actual data source connections (Binance, Coinbase, etc.)
        # For now, just simulate initialization
        self.data_sources[self.primary_source] = {"status": "connected", "type": "simulated"}
        self.data_sources[self.backup_source] = {"status": "connected", "type": "simulated"}

        self.logger.logger.info(f"Initialized data sources: {list(self.data_sources.keys())}")

    async def _start_data_tasks(self) -> None:
        """Start background data processing tasks"""
        # Start heartbeat task
        asyncio.create_task(self._heartbeat_task())

        # Start data simulation task (for testing)
        if self.settings.app.debug:
            asyncio.create_task(self._simulate_data_task())

    async def _heartbeat_task(self) -> None:
        """Heartbeat task to track data manager health"""
        while self.is_running:
            self.last_heartbeat = datetime.utcnow()
            await asyncio.sleep(30)  # Heartbeat every 30 seconds

    async def _simulate_data_task(self) -> None:
        """Simulate market data for testing"""
        import random

        symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
        base_prices = {"BTCUSDT": 50000, "ETHUSDT": 3000, "ADAUSDT": 1.5}

        while self.is_running:
            for symbol in symbols:
                # Generate simulated candle data
                base_price = base_prices[symbol]
                price_change = random.uniform(-0.02, 0.02)  # ±2% change

                open_price = base_price * (1 + price_change)
                high_price = open_price * (1 + random.uniform(0, 0.01))
                low_price = open_price * (1 - random.uniform(0, 0.01))
                close_price = open_price + random.uniform(-0.005, 0.005) * open_price
                volume = random.uniform(100, 1000)

                candle = Candle(
                    symbol=symbol,
                    timeframe=Timeframe.M1,
                    timestamp=datetime.utcnow(),
                    open_price=open_price,
                    high_price=high_price,
                    low_price=low_price,
                    close_price=close_price,
                    volume=volume
                )

                await self.process_candle_data(candle)

                # Update base price for next iteration
                base_prices[symbol] = close_price

            await asyncio.sleep(5)  # Generate data every 5 seconds

    def subscribe(
        self,
        symbol: str,
        data_type: str,
        timeframe: Optional[str] = None,
        callback: Optional[Callable[[MarketData], None]] = None
    ) -> str:
        """Subscribe to market data"""
        subscription = DataSubscription(symbol, data_type, timeframe, callback)
        self.subscriptions.append(subscription)

        self.logger.logger.info(f"Subscribed to {data_type} data for {symbol}")
        return f"{symbol}_{data_type}_{timeframe or 'all'}"

    def unsubscribe(self, symbol: str, data_type: str, timeframe: Optional[str] = None) -> bool:
        """Unsubscribe from market data"""
        for i, sub in enumerate(self.subscriptions):
            if (sub.symbol == symbol and
                sub.data_type == data_type and
                sub.timeframe == timeframe):
                sub.active = False
                self.logger.logger.info(f"Unsubscribed from {data_type} data for {symbol}")
                return True
        return False

    def add_data_callback(self, callback: Callable[[MarketData], None]) -> None:
        """Add a global data callback"""
        self.data_callbacks.append(callback)

    async def process_candle_data(self, candle: Candle) -> None:
        """Process incoming candle data"""
        # Store candle data
        symbol_data = self.candle_data[candle.symbol]
        timeframe_data = symbol_data[candle.timeframe]

        timeframe_data.append(candle)

        # Maintain maximum size
        if len(timeframe_data) > self.max_candles_per_timeframe:
            timeframe_data.popleft()

        # Create market data object
        market_data = MarketData(
            symbol=candle.symbol,
            data_type=DataType.CANDLE,
            timestamp=candle.timestamp,
            data=candle.to_dict()
        )

        # Notify subscribers
        await self._notify_subscribers(market_data)

    async def process_tick_data(self, symbol: str, price: float, volume: float, timestamp: datetime) -> None:
        """Process incoming tick data"""
        tick_data = {
            "price": price,
            "volume": volume,
            "timestamp": timestamp.isoformat()
        }

        # Store tick data
        symbol_ticks = self.tick_data[symbol]
        symbol_ticks.append(tick_data)

        # Maintain maximum size
        if len(symbol_ticks) > self.max_ticks_per_symbol:
            symbol_ticks.popleft()

        # Create market data object
        market_data = MarketData(
            symbol=symbol,
            data_type=DataType.TICK,
            timestamp=timestamp,
            data=tick_data
        )

        # Notify subscribers
        await self._notify_subscribers(market_data)

    async def _notify_subscribers(self, market_data: MarketData) -> None:
        """Notify all relevant subscribers"""
        # Notify specific subscribers
        for subscription in self.subscriptions:
            if (subscription.active and
                subscription.symbol == market_data.symbol and
                subscription.data_type == market_data.data_type):

                if subscription.callback:
                    try:
                        subscription.callback(market_data)
                    except Exception as e:
                        self.logger.error(f"Error in subscription callback: {e}")

        # Notify global callbacks
        for callback in self.data_callbacks:
            try:
                callback(market_data)
            except Exception as e:
                self.logger.error(f"Error in global data callback: {e}")

    def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: Optional[int] = None
    ) -> List[Candle]:
        """Get historical candle data"""
        if symbol not in self.candle_data or timeframe not in self.candle_data[symbol]:
            return []

        candles = list(self.candle_data[symbol][timeframe])

        if limit:
            candles = candles[-limit:]

        return candles

    def get_latest_candle(self, symbol: str, timeframe: str) -> Optional[Candle]:
        """Get the latest candle for a symbol and timeframe"""
        candles = self.get_candles(symbol, timeframe, limit=1)
        return candles[0] if candles else None

    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get the latest price for a symbol"""
        # Try to get from latest candle
        latest_candle = self.get_latest_candle(symbol, Timeframe.M1)
        if latest_candle:
            return latest_candle.close

        # Try to get from tick data
        if symbol in self.tick_data and self.tick_data[symbol]:
            latest_tick = self.tick_data[symbol][-1]
            return latest_tick["price"]

        return None

    async def get_latest_market_data(self) -> Optional[Dict[str, Any]]:
        """Get the latest market data for all tracked symbols"""
        market_data = {}

        # Get latest candles for all symbols
        for symbol in self.candle_data.keys():
            latest_candle = self.get_latest_candle(symbol, Timeframe.M1)
            if latest_candle:
                market_data[symbol] = {
                    "symbol": symbol,
                    "price": latest_candle.close_price,
                    "timestamp": latest_candle.timestamp,
                    "candle": latest_candle.to_dict()
                }

        return market_data if market_data else None

    def get_data_status(self) -> Dict[str, Any]:
        """Get data manager status"""
        return {
            "is_running": self.is_running,
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "subscriptions": len([s for s in self.subscriptions if s.active]),
            "symbols_tracked": len(self.candle_data),
            "data_sources": {
                source: info["status"] for source, info in self.data_sources.items()
            },
            "candle_data_count": {
                symbol: {tf: len(data) for tf, data in timeframes.items()}
                for symbol, timeframes in self.candle_data.items()
            }
        }

    async def stop(self) -> None:
        """Stop the data manager"""
        self.is_running = False

        # Close data source connections
        for source_name, source in self.data_sources.items():
            try:
                # TODO: Close actual connections
                self.logger.logger.info(f"Closed connection to {source_name}")
            except Exception as e:
                self.logger.error(f"Error closing {source_name}: {e}")

        self.logger.logger.info("Data manager stopped")
