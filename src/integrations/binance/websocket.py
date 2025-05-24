"""
Binance WebSocket Client

Provides real-time market data streaming from Binance via WebSocket connections.
Supports multiple data streams including ticker, order book, and trade data.
"""

import asyncio
import json
import websockets
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import logging


class BinanceWebSocket:
    """
    Binance WebSocket client for real-time market data
    
    Supports streaming of:
    - 24hr ticker statistics
    - Order book updates
    - Trade data
    - Kline/candlestick data
    """
    
    def __init__(self, base_url: str, callbacks: Dict[str, List[Callable]]):
        """
        Initialize Binance WebSocket client
        
        Args:
            base_url: WebSocket base URL
            callbacks: Dictionary of event callbacks
        """
        self.base_url = base_url
        self.callbacks = callbacks
        self.websocket = None
        self.is_running = False
        self.subscribed_streams = []
        self.logger = logging.getLogger(__name__)
        
    async def start(self, symbols: List[str]) -> None:
        """
        Start WebSocket connection and subscribe to symbols
        
        Args:
            symbols: List of trading symbols to subscribe to
        """
        try:
            # Create stream names for multiple data types
            streams = []
            for symbol in symbols:
                symbol_lower = symbol.lower()
                streams.extend([
                    f"{symbol_lower}@ticker",      # 24hr ticker
                    f"{symbol_lower}@depth20",     # Order book (20 levels)
                    f"{symbol_lower}@trade",       # Trade data
                    f"{symbol_lower}@kline_1m"     # 1-minute klines
                ])
            
            self.subscribed_streams = streams
            
            # Build WebSocket URL
            stream_names = "/".join(streams)
            ws_url = f"{self.base_url}/ws/{stream_names}"
            
            # Connect to WebSocket
            self.websocket = await websockets.connect(ws_url)
            self.is_running = True
            
            self.logger.info(f"Connected to Binance WebSocket: {len(symbols)} symbols")
            
            # Start message processing
            asyncio.create_task(self._process_messages())
            
        except Exception as e:
            self.logger.error(f"Failed to start WebSocket: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop WebSocket connection"""
        try:
            self.is_running = False
            
            if self.websocket:
                await self.websocket.close()
                self.websocket = None
            
            self.logger.info("Binance WebSocket disconnected")
            
        except Exception as e:
            self.logger.error(f"Error stopping WebSocket: {e}")
    
    async def _process_messages(self) -> None:
        """Process incoming WebSocket messages"""
        try:
            while self.is_running and self.websocket:
                try:
                    # Receive message with timeout
                    message = await asyncio.wait_for(
                        self.websocket.recv(),
                        timeout=30.0
                    )
                    
                    # Parse JSON message
                    data = json.loads(message)
                    
                    # Process based on stream type
                    await self._handle_message(data)
                    
                except asyncio.TimeoutError:
                    # Send ping to keep connection alive
                    if self.websocket:
                        await self.websocket.ping()
                    continue
                    
                except websockets.exceptions.ConnectionClosed:
                    self.logger.warning("WebSocket connection closed")
                    break
                    
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse WebSocket message: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error in message processing: {e}")
        finally:
            self.is_running = False
    
    async def _handle_message(self, data: Dict[str, Any]) -> None:
        """
        Handle incoming WebSocket message based on stream type
        
        Args:
            data: Parsed message data
        """
        try:
            stream = data.get('stream', '')
            event_data = data.get('data', {})
            
            if '@ticker' in stream:
                await self._handle_ticker_data(event_data)
            elif '@depth' in stream:
                await self._handle_orderbook_data(event_data)
            elif '@trade' in stream:
                await self._handle_trade_data(event_data)
            elif '@kline' in stream:
                await self._handle_kline_data(event_data)
            else:
                self.logger.debug(f"Unknown stream type: {stream}")
                
        except Exception as e:
            self.logger.error(f"Error handling message: {e}")
    
    async def _handle_ticker_data(self, data: Dict[str, Any]) -> None:
        """Handle 24hr ticker data"""
        ticker_data = {
            'symbol': data['s'],
            'price': float(data['c']),
            'bid': float(data['b']),
            'ask': float(data['a']),
            'volume': float(data['v']),
            'high_24h': float(data['h']),
            'low_24h': float(data['l']),
            'change_24h': float(data['P']),
            'timestamp': datetime.fromtimestamp(int(data['E']) / 1000)
        }
        
        await self._notify_callbacks('ticker', ticker_data)
    
    async def _handle_orderbook_data(self, data: Dict[str, Any]) -> None:
        """Handle order book depth data"""
        orderbook_data = {
            'symbol': data['s'],
            'bids': [[float(price), float(qty)] for price, qty in data['bids']],
            'asks': [[float(price), float(qty)] for price, qty in data['asks']],
            'timestamp': datetime.fromtimestamp(int(data['E']) / 1000)
        }
        
        await self._notify_callbacks('orderbook', orderbook_data)
    
    async def _handle_trade_data(self, data: Dict[str, Any]) -> None:
        """Handle individual trade data"""
        trade_data = {
            'symbol': data['s'],
            'price': float(data['p']),
            'quantity': float(data['q']),
            'side': 'buy' if data['m'] else 'sell',  # m = true if buyer is market maker
            'timestamp': datetime.fromtimestamp(int(data['T']) / 1000)
        }
        
        await self._notify_callbacks('trade', trade_data)
    
    async def _handle_kline_data(self, data: Dict[str, Any]) -> None:
        """Handle kline/candlestick data"""
        kline = data['k']
        
        # Only process closed klines
        if kline['x']:  # x = true if kline is closed
            kline_data = {
                'symbol': kline['s'],
                'open_time': datetime.fromtimestamp(int(kline['t']) / 1000),
                'close_time': datetime.fromtimestamp(int(kline['T']) / 1000),
                'open': float(kline['o']),
                'high': float(kline['h']),
                'low': float(kline['l']),
                'close': float(kline['c']),
                'volume': float(kline['v']),
                'trades': int(kline['n'])
            }
            
            await self._notify_callbacks('kline', kline_data)
    
    async def _notify_callbacks(self, event_type: str, data: Any) -> None:
        """
        Notify all registered callbacks for an event type
        
        Args:
            event_type: Type of event (ticker, orderbook, trade, kline)
            data: Event data
        """
        if event_type in self.callbacks:
            for callback in self.callbacks[event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    self.logger.error(f"Error in {event_type} callback: {e}")
    
    def add_callback(self, event_type: str, callback: Callable) -> None:
        """
        Add callback for specific event type
        
        Args:
            event_type: Type of event
            callback: Callback function
        """
        if event_type not in self.callbacks:
            self.callbacks[event_type] = []
        self.callbacks[event_type].append(callback)
    
    def remove_callback(self, event_type: str, callback: Callable) -> None:
        """
        Remove callback for specific event type
        
        Args:
            event_type: Type of event
            callback: Callback function to remove
        """
        if event_type in self.callbacks:
            try:
                self.callbacks[event_type].remove(callback)
            except ValueError:
                pass
    
    @property
    def is_connected(self) -> bool:
        """Check if WebSocket is connected"""
        return self.is_running and self.websocket is not None
    
    def get_subscribed_symbols(self) -> List[str]:
        """Get list of subscribed symbols"""
        symbols = set()
        for stream in self.subscribed_streams:
            symbol = stream.split('@')[0].upper()
            symbols.add(symbol)
        return list(symbols)
