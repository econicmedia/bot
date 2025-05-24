"""
Binance Exchange Client

Implements the Binance exchange integration using the python-binance library.
Provides both REST API and WebSocket functionality for real-time trading.
"""

import asyncio
import hmac
import hashlib
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import aiohttp
import json
from decimal import Decimal

from ..base import (
    BaseExchange, ExchangeOrder, MarketTicker, OrderBook, Trade,
    OrderSide, OrderType, OrderStatus, ExchangeError, ConnectionError,
    AuthenticationError, InsufficientFundsError, InvalidOrderError
)
from .websocket import BinanceWebSocket


class BinanceExchange(BaseExchange):
    """
    Binance exchange implementation

    Provides integration with Binance Spot trading API including:
    - Order placement and management
    - Market data retrieval
    - Account information
    - Real-time WebSocket data streams
    """

    def __init__(self, api_key: str, api_secret: str, sandbox: bool = True):
        """
        Initialize Binance exchange client

        Args:
            api_key: Binance API key
            api_secret: Binance API secret
            sandbox: Whether to use testnet (True) or mainnet (False)
        """
        super().__init__(api_key, api_secret, sandbox)

        # API endpoints
        if sandbox:
            self.base_url = "https://testnet.binance.vision"
            self.ws_base_url = "wss://testnet.binance.vision"
        else:
            self.base_url = "https://api.binance.com"
            self.ws_base_url = "wss://stream.binance.com:9443"

        # HTTP session
        self.session: Optional[aiohttp.ClientSession] = None

        # WebSocket client
        self.websocket: Optional[BinanceWebSocket] = None

        # Rate limiting
        self.last_request_time = 0
        self.request_interval = 0.1  # 100ms between requests

        # Symbol info cache
        self.symbol_info: Dict[str, Dict] = {}

    async def connect(self) -> bool:
        """
        Establish connection to Binance

        Returns:
            True if connection successful
        """
        try:
            # Create HTTP session with timeout
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            self.session = aiohttp.ClientSession(timeout=timeout)

            # Test connectivity
            await self._test_connectivity()

            # Get exchange info to cache symbol data
            await self._load_exchange_info()

            # Test authentication if not using demo credentials
            if not self._is_demo_credentials():
                await self._test_authentication()
            else:
                print("⚠️  Using demo credentials - authentication test skipped")

            self.is_connected = True
            return True

        except Exception as e:
            if self.session:
                await self.session.close()
                self.session = None
            raise ConnectionError(f"Failed to connect to Binance: {str(e)}")

    def _is_demo_credentials(self) -> bool:
        """Check if using demo/test credentials"""
        demo_keys = ["demo_api_key", "test_key", "your-binance-api-key", ""]
        return self.api_key in demo_keys or self.api_secret in ["demo_api_secret", "test_secret", "your-binance-api-secret", ""]

    async def disconnect(self) -> None:
        """Disconnect from Binance"""
        try:
            # Stop WebSocket if running
            if self.websocket:
                await self.websocket.stop()
                self.websocket = None

            # Close HTTP session
            if self.session:
                await self.session.close()
                self.session = None

            self.is_connected = False

        except Exception as e:
            print(f"Error during disconnect: {e}")

    async def _test_connectivity(self) -> None:
        """Test basic connectivity to Binance"""
        url = f"{self.base_url}/api/v3/ping"
        async with self.session.get(url) as response:
            if response.status != 200:
                raise ConnectionError("Failed to ping Binance API")

    async def _test_authentication(self) -> None:
        """Test API key authentication"""
        try:
            await self.get_account_info()
        except Exception as e:
            raise AuthenticationError(f"Authentication failed: {str(e)}")

    async def _load_exchange_info(self) -> None:
        """Load exchange information and symbol data"""
        url = f"{self.base_url}/api/v3/exchangeInfo"
        async with self.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                for symbol_data in data.get('symbols', []):
                    symbol = symbol_data['symbol']
                    self.symbol_info[symbol] = symbol_data

    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """Generate HMAC SHA256 signature for authenticated requests"""
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        signed: bool = False
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Binance API

        Args:
            method: HTTP method (GET, POST, DELETE)
            endpoint: API endpoint
            params: Request parameters
            signed: Whether request requires signature

        Returns:
            Response data as dictionary
        """
        if not self.session:
            raise ConnectionError("Not connected to exchange")

        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.request_interval:
            await asyncio.sleep(self.request_interval - time_since_last)

        url = f"{self.base_url}{endpoint}"
        headers = {"X-MBX-APIKEY": self.api_key}

        if params is None:
            params = {}

        if signed:
            params['timestamp'] = int(time.time() * 1000)
            params['signature'] = self._generate_signature(params)

        self.last_request_time = time.time()

        try:
            if method == "GET":
                async with self.session.get(url, params=params, headers=headers) as response:
                    return await self._handle_response(response)
            elif method == "POST":
                async with self.session.post(url, data=params, headers=headers) as response:
                    return await self._handle_response(response)
            elif method == "DELETE":
                async with self.session.delete(url, params=params, headers=headers) as response:
                    return await self._handle_response(response)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

        except aiohttp.ClientError as e:
            raise ConnectionError(f"Request failed: {str(e)}")

    async def _handle_response(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """Handle HTTP response and check for errors"""
        data = await response.json()

        if response.status == 200:
            return data
        elif response.status == 400:
            error_msg = data.get('msg', 'Bad request')
            if 'insufficient' in error_msg.lower():
                raise InsufficientFundsError(error_msg)
            else:
                raise InvalidOrderError(error_msg)
        elif response.status == 401:
            raise AuthenticationError(data.get('msg', 'Unauthorized'))
        else:
            raise ExchangeError(f"API error {response.status}: {data.get('msg', 'Unknown error')}")

    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information including balances"""
        data = await self._make_request("GET", "/api/v3/account", signed=True)

        # Format balances
        balances = {}
        for balance in data.get('balances', []):
            asset = balance['asset']
            free = float(balance['free'])
            locked = float(balance['locked'])
            if free > 0 or locked > 0:
                balances[asset] = {
                    'free': free,
                    'locked': locked,
                    'total': free + locked
                }

        return {
            'balances': balances,
            'can_trade': data.get('canTrade', False),
            'can_withdraw': data.get('canWithdraw', False),
            'can_deposit': data.get('canDeposit', False),
            'update_time': datetime.fromtimestamp(data.get('updateTime', 0) / 1000)
        }

    async def get_ticker(self, symbol: str) -> MarketTicker:
        """Get 24hr ticker price change statistics"""
        params = {'symbol': symbol.upper()}
        data = await self._make_request("GET", "/api/v3/ticker/24hr", params)

        return MarketTicker(
            symbol=data['symbol'],
            bid=float(data.get('bidPrice', 0)),
            ask=float(data.get('askPrice', 0)),
            last=float(data['lastPrice']),
            volume=float(data['volume']),
            high_24h=float(data['highPrice']),
            low_24h=float(data['lowPrice']),
            change_24h=float(data['priceChange']),
            change_24h_pct=float(data['priceChangePercent']),
            timestamp=datetime.fromtimestamp(int(data['closeTime']) / 1000)
        )

    async def get_order_book(self, symbol: str, limit: int = 100) -> OrderBook:
        """Get order book for a symbol"""
        params = {'symbol': symbol.upper(), 'limit': min(limit, 5000)}
        data = await self._make_request("GET", "/api/v3/depth", params)

        bids = [[float(price), float(qty)] for price, qty in data['bids']]
        asks = [[float(price), float(qty)] for price, qty in data['asks']]

        return OrderBook(
            symbol=symbol.upper(),
            bids=bids,
            asks=asks,
            timestamp=datetime.fromtimestamp(int(data['lastUpdateId']) / 1000)
        )

    def _convert_order_side(self, side: OrderSide) -> str:
        """Convert internal order side to Binance format"""
        return "BUY" if side == OrderSide.BUY else "SELL"

    def _convert_order_type(self, order_type: OrderType) -> str:
        """Convert internal order type to Binance format"""
        mapping = {
            OrderType.MARKET: "MARKET",
            OrderType.LIMIT: "LIMIT",
            OrderType.STOP: "STOP_LOSS",
            OrderType.STOP_LIMIT: "STOP_LOSS_LIMIT"
        }
        return mapping.get(order_type, "MARKET")

    def _convert_order_status(self, status: str) -> OrderStatus:
        """Convert Binance order status to internal format"""
        mapping = {
            "NEW": OrderStatus.SUBMITTED,
            "PARTIALLY_FILLED": OrderStatus.PARTIALLY_FILLED,
            "FILLED": OrderStatus.FILLED,
            "CANCELED": OrderStatus.CANCELLED,
            "REJECTED": OrderStatus.REJECTED,
            "EXPIRED": OrderStatus.EXPIRED
        }
        return mapping.get(status, OrderStatus.PENDING)

    def _format_quantity(self, symbol: str, quantity: float) -> str:
        """Format quantity according to symbol precision"""
        if symbol in self.symbol_info:
            for filter_info in self.symbol_info[symbol].get('filters', []):
                if filter_info['filterType'] == 'LOT_SIZE':
                    step_size = float(filter_info['stepSize'])
                    precision = len(str(step_size).split('.')[-1].rstrip('0'))
                    return f"{quantity:.{precision}f}"
        return str(quantity)

    def _format_price(self, symbol: str, price: float) -> str:
        """Format price according to symbol precision"""
        if symbol in self.symbol_info:
            for filter_info in self.symbol_info[symbol].get('filters', []):
                if filter_info['filterType'] == 'PRICE_FILTER':
                    tick_size = float(filter_info['tickSize'])
                    precision = len(str(tick_size).split('.')[-1].rstrip('0'))
                    return f"{price:.{precision}f}"
        return str(price)

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
        """Place an order on Binance"""
        symbol = symbol.upper()

        params = {
            'symbol': symbol,
            'side': self._convert_order_side(side),
            'type': self._convert_order_type(order_type),
            'quantity': self._format_quantity(symbol, quantity),
            'timeInForce': time_in_force
        }

        # Add price for limit orders
        if order_type in [OrderType.LIMIT, OrderType.STOP_LIMIT] and price:
            params['price'] = self._format_price(symbol, price)

        # Add stop price for stop orders
        if order_type in [OrderType.STOP, OrderType.STOP_LIMIT] and stop_price:
            params['stopPrice'] = self._format_price(symbol, stop_price)

        data = await self._make_request("POST", "/api/v3/order", params, signed=True)

        return self._create_exchange_order(data)

    def _create_exchange_order(self, data: Dict[str, Any]) -> ExchangeOrder:
        """Create ExchangeOrder object from Binance response"""
        return ExchangeOrder(
            id=str(data['clientOrderId']),
            symbol=data['symbol'],
            side=OrderSide.BUY if data['side'] == 'BUY' else OrderSide.SELL,
            order_type=self._parse_order_type(data['type']),
            quantity=float(data['origQty']),
            price=float(data['price']) if data.get('price') else None,
            stop_price=float(data['stopPrice']) if data.get('stopPrice') else None,
            status=self._convert_order_status(data['status']),
            filled_quantity=float(data.get('executedQty', 0)),
            average_fill_price=float(data.get('cummulativeQuoteQty', 0)) / float(data.get('executedQty', 1)),
            commission=0.0,  # Will be calculated from fills
            created_at=datetime.fromtimestamp(int(data['transactTime']) / 1000),
            exchange_order_id=str(data['orderId'])
        )

    def _parse_order_type(self, binance_type: str) -> OrderType:
        """Parse Binance order type to internal format"""
        mapping = {
            "MARKET": OrderType.MARKET,
            "LIMIT": OrderType.LIMIT,
            "STOP_LOSS": OrderType.STOP,
            "STOP_LOSS_LIMIT": OrderType.STOP_LIMIT
        }
        return mapping.get(binance_type, OrderType.MARKET)

    async def cancel_order(self, symbol: str, order_id: str) -> bool:
        """Cancel an order"""
        params = {
            'symbol': symbol.upper(),
            'origClientOrderId': order_id
        }

        try:
            await self._make_request("DELETE", "/api/v3/order", params, signed=True)
            return True
        except Exception:
            return False

    async def get_order_status(self, symbol: str, order_id: str) -> ExchangeOrder:
        """Get order status"""
        params = {
            'symbol': symbol.upper(),
            'origClientOrderId': order_id
        }

        data = await self._make_request("GET", "/api/v3/order", params, signed=True)
        return self._create_exchange_order(data)

    async def get_open_orders(self, symbol: Optional[str] = None) -> List[ExchangeOrder]:
        """Get open orders"""
        params = {}
        if symbol:
            params['symbol'] = symbol.upper()

        data = await self._make_request("GET", "/api/v3/openOrders", params, signed=True)
        return [self._create_exchange_order(order_data) for order_data in data]

    async def get_trade_history(
        self,
        symbol: Optional[str] = None,
        limit: int = 100
    ) -> List[Trade]:
        """Get trade history"""
        if not symbol:
            raise ValueError("Symbol is required for Binance trade history")

        params = {
            'symbol': symbol.upper(),
            'limit': min(limit, 1000)
        }

        data = await self._make_request("GET", "/api/v3/myTrades", params, signed=True)

        trades = []
        for trade_data in data:
            trades.append(Trade(
                id=str(trade_data['id']),
                symbol=trade_data['symbol'],
                side=OrderSide.BUY if trade_data['isBuyer'] else OrderSide.SELL,
                quantity=float(trade_data['qty']),
                price=float(trade_data['price']),
                commission=float(trade_data['commission']),
                timestamp=datetime.fromtimestamp(int(trade_data['time']) / 1000)
            ))

        return trades

    async def start_websocket(self, symbols: List[str]) -> None:
        """Start WebSocket connection for real-time data"""
        if not self.websocket:
            self.websocket = BinanceWebSocket(
                base_url=self.ws_base_url,
                callbacks=self.websocket_callbacks
            )

        await self.websocket.start(symbols)

    async def stop_websocket(self) -> None:
        """Stop WebSocket connection"""
        if self.websocket:
            await self.websocket.stop()
            self.websocket = None
