"""
Order Manager - Handles order lifecycle and execution
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from enum import Enum

from .config import Settings
from .logger import get_trading_logger


class OrderType(str, Enum):
    """Order type enumeration"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderSide(str, Enum):
    """Order side enumeration"""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(str, Enum):
    """Order status enumeration"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class TimeInForce(str, Enum):
    """Time in force enumeration"""
    GTC = "gtc"  # Good Till Cancelled
    IOC = "ioc"  # Immediate Or Cancel
    FOK = "fok"  # Fill Or Kill
    DAY = "day"  # Day order


class Order:
    """Order object representing a trading order"""

    def __init__(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        time_in_force: TimeInForce = TimeInForce.GTC,
        strategy: Optional[str] = None
    ):
        """Initialize order"""
        self.id = str(uuid.uuid4())
        self.symbol = symbol
        self.side = side
        self.order_type = order_type
        self.quantity = quantity
        self.price = price
        self.stop_price = stop_price
        self.time_in_force = time_in_force
        self.strategy = strategy

        # Order state
        self.status = OrderStatus.PENDING
        self.filled_quantity = 0.0
        self.remaining_quantity = quantity
        self.average_fill_price = 0.0
        self.commission = 0.0
        self.fills: List[Dict[str, Any]] = []

        # Timestamps
        self.created_at = datetime.utcnow()
        self.submitted_at: Optional[datetime] = None
        self.filled_at: Optional[datetime] = None
        self.cancelled_at: Optional[datetime] = None

        # Exchange information
        self.exchange_order_id: Optional[str] = None
        self.exchange: Optional[str] = None

        # Error information
        self.error_message: Optional[str] = None

    def add_fill(self, fill_quantity: float, fill_price: float, commission: float = 0.0) -> None:
        """Add a fill to the order"""
        fill = {
            "quantity": fill_quantity,
            "price": fill_price,
            "commission": commission,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.fills.append(fill)

        # Update order state
        self.filled_quantity += fill_quantity
        self.remaining_quantity = self.quantity - self.filled_quantity
        self.commission += commission

        # Calculate average fill price
        total_value = sum(f["quantity"] * f["price"] for f in self.fills)
        self.average_fill_price = total_value / self.filled_quantity if self.filled_quantity > 0 else 0.0

        # Update status
        if self.remaining_quantity <= 0:
            self.status = OrderStatus.FILLED
            self.filled_at = datetime.utcnow()
        elif self.filled_quantity > 0:
            self.status = OrderStatus.PARTIALLY_FILLED

    def cancel(self, reason: str = "User cancelled") -> None:
        """Cancel the order"""
        if self.status in [OrderStatus.PENDING, OrderStatus.SUBMITTED, OrderStatus.PARTIALLY_FILLED]:
            self.status = OrderStatus.CANCELLED
            self.cancelled_at = datetime.utcnow()
            self.error_message = reason

    def reject(self, reason: str) -> None:
        """Reject the order"""
        self.status = OrderStatus.REJECTED
        self.error_message = reason

    def to_dict(self) -> Dict[str, Any]:
        """Convert order to dictionary"""
        return {
            "id": self.id,
            "symbol": self.symbol,
            "side": self.side.value,
            "order_type": self.order_type.value,
            "quantity": self.quantity,
            "price": self.price,
            "stop_price": self.stop_price,
            "time_in_force": self.time_in_force.value,
            "strategy": self.strategy,
            "status": self.status.value,
            "filled_quantity": self.filled_quantity,
            "remaining_quantity": self.remaining_quantity,
            "average_fill_price": self.average_fill_price,
            "commission": self.commission,
            "fills": self.fills,
            "created_at": self.created_at.isoformat(),
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "filled_at": self.filled_at.isoformat() if self.filled_at else None,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
            "exchange_order_id": self.exchange_order_id,
            "exchange": self.exchange,
            "error_message": self.error_message
        }


class OrderManager:
    """Manages order lifecycle and execution"""

    def __init__(self, settings: Settings, user_id: Optional[uuid.UUID] = None):
        """Initialize order manager"""
        self.settings = settings
        self.logger = get_trading_logger("OrderManager")

        # User identification for database operations
        self.user_id = user_id or self._get_default_user_id()

        # Order storage
        self.orders: Dict[str, Order] = {}
        self.active_orders: Dict[str, Order] = {}

        # Callbacks
        self.fill_callbacks: List[Callable[[Order], None]] = []
        self.status_callbacks: List[Callable[[Order], None]] = []

        # Exchange connections (will be set by integrations)
        self.exchanges: Dict[str, Any] = {}

        # Database components
        self.db_manager = None
        self.enable_database = settings.database.enabled if hasattr(settings.database, 'enabled') else True

        # Paper trading mode
        self.paper_trading = settings.trading.mode == "paper"

        self.logger.logger.info(f"Order manager initialized (mode: {settings.trading.mode})")

    async def start(self) -> None:
        """Start the order manager"""
        await self.initialize()
        self.logger.logger.info("Order manager started")

    def _get_default_user_id(self) -> uuid.UUID:
        """Get default system user ID"""
        return uuid.UUID("00000000-0000-0000-0000-000000000001")

    async def initialize(self) -> None:
        """Initialize order manager"""
        try:
            # Initialize database connection if enabled
            if self.enable_database:
                await self._initialize_database()

            # Initialize exchange connections if not in paper mode
            if not self.paper_trading:
                await self._initialize_exchanges()

            # Load existing orders from database
            if self.enable_database:
                await self._load_orders_from_database()

            self.logger.logger.info("Order manager initialized successfully")
        except Exception as e:
            self.logger.error("Failed to initialize order manager", e)
            raise

    async def _initialize_database(self) -> None:
        """Initialize database connection"""
        try:
            from ..database import get_database_manager
            self.db_manager = await get_database_manager()
            self.logger.logger.info("Database connection initialized for order manager")
        except Exception as e:
            self.logger.error("Failed to initialize database", e)
            # Continue without database if it fails
            self.enable_database = False

    async def _load_orders_from_database(self) -> None:
        """Load existing orders from database"""
        try:
            if not self.db_manager:
                return

            from ..database.repositories import OrderRepository

            async with self.db_manager.get_session() as session:
                order_repo = OrderRepository(session)

                # Load active orders
                db_orders = await order_repo.get_active_orders(self.user_id)

                for db_order in db_orders:
                    # Convert database order to core order
                    order = self._db_order_to_core(db_order)
                    self.orders[order.id] = order
                    self.active_orders[order.id] = order

                self.logger.logger.info(f"Loaded {len(db_orders)} active orders from database")

        except Exception as e:
            self.logger.error("Failed to load orders from database", e)

    def _db_order_to_core(self, db_order) -> Order:
        """Convert database order to core order object"""
        # Create core order
        order = Order(
            symbol=db_order.symbol,
            side=OrderSide(db_order.side),
            order_type=OrderType(db_order.order_type),
            quantity=float(db_order.quantity),
            price=float(db_order.price) if db_order.price else None,
            stop_price=float(db_order.stop_price) if db_order.stop_price else None,
            time_in_force=TimeInForce(db_order.time_in_force),
            strategy=None  # Strategy info not stored in order
        )

        # Update with database state
        order.id = str(db_order.id)
        order.status = OrderStatus(db_order.status)
        order.filled_quantity = float(db_order.filled_quantity or 0)
        order.remaining_quantity = float(db_order.remaining_quantity or db_order.quantity)
        order.average_fill_price = float(db_order.average_fill_price or 0)
        order.commission = float(db_order.commission or 0)
        order.created_at = db_order.created_at
        order.submitted_at = db_order.submitted_at
        order.filled_at = db_order.filled_at
        order.cancelled_at = db_order.cancelled_at
        order.exchange_order_id = db_order.exchange_order_id
        order.exchange = db_order.exchange
        order.error_message = db_order.error_message

        return order

    async def _initialize_exchanges(self) -> None:
        """Initialize exchange connections"""
        try:
            from ..integrations import BinanceExchange

            # Initialize Binance exchange if configured
            binance_config = self.settings.data_sources.binance
            if binance_config.api_key and binance_config.api_secret:
                binance = BinanceExchange(
                    api_key=binance_config.api_key,
                    api_secret=binance_config.api_secret,
                    sandbox=binance_config.sandbox
                )

                # Connect to exchange
                if await binance.connect():
                    self.exchanges["binance"] = binance
                    self.logger.logger.info("Binance exchange connected successfully")
                else:
                    self.logger.logger.warning("Failed to connect to Binance exchange")
            else:
                self.logger.logger.warning("Binance API credentials not configured")

        except Exception as e:
            self.logger.error("Failed to initialize exchanges", e)
            raise

    def add_fill_callback(self, callback: Callable[[Order], None]) -> None:
        """Add a callback for order fills"""
        self.fill_callbacks.append(callback)

    def add_status_callback(self, callback: Callable[[Order], None]) -> None:
        """Add a callback for order status changes"""
        self.status_callbacks.append(callback)

    async def submit_order(self, order: Order) -> str:
        """Submit an order for execution"""
        try:
            # Store the order
            self.orders[order.id] = order
            self.active_orders[order.id] = order

            # Update status
            order.status = OrderStatus.SUBMITTED
            order.submitted_at = datetime.utcnow()

            # Persist to database
            if self.enable_database and self.db_manager:
                await self._persist_order_to_database(order)

            self.logger.logger.info(f"Submitted order: {order.id} ({order.symbol} {order.side.value} {order.quantity})")

            # Execute based on mode
            if self.paper_trading:
                await self._execute_paper_order(order)
            else:
                await self._execute_live_order(order)

            # Update database with execution results
            if self.enable_database and self.db_manager:
                await self._update_order_in_database(order)

            # Notify callbacks
            for callback in self.status_callbacks:
                try:
                    callback(order)
                except Exception as e:
                    self.logger.error("Error in status callback", e)

            return order.id

        except Exception as e:
            order.reject(f"Submission failed: {str(e)}")

            # Update database with error
            if self.enable_database and self.db_manager:
                try:
                    await self._update_order_in_database(order)
                except Exception as db_error:
                    self.logger.error("Failed to update order in database", db_error)

            self.logger.error(f"Failed to submit order {order.id}", e)
            raise

    async def _persist_order_to_database(self, order: Order) -> None:
        """Persist order to database"""
        try:
            from ..database.repositories import OrderRepository
            from decimal import Decimal

            async with self.db_manager.get_session() as session:
                order_repo = OrderRepository(session)

                order_data = {
                    "id": uuid.UUID(order.id),
                    "user_id": self.user_id,
                    "symbol": order.symbol,
                    "side": order.side.value,
                    "order_type": order.order_type.value,
                    "quantity": Decimal(str(order.quantity)),
                    "price": Decimal(str(order.price)) if order.price else None,
                    "stop_price": Decimal(str(order.stop_price)) if order.stop_price else None,
                    "time_in_force": order.time_in_force.value,
                    "status": order.status.value,
                    "filled_quantity": Decimal(str(order.filled_quantity)),
                    "remaining_quantity": Decimal(str(order.remaining_quantity)),
                    "average_fill_price": Decimal(str(order.average_fill_price)),
                    "commission": Decimal(str(order.commission)),
                    "created_at": order.created_at,
                    "submitted_at": order.submitted_at,
                    "exchange": order.exchange,
                    "exchange_order_id": order.exchange_order_id,
                    "error_message": order.error_message
                }

                await order_repo.create_order(order_data)

        except Exception as e:
            self.logger.error("Failed to persist order to database", e)
            # Don't raise - continue with order execution

    async def _update_order_in_database(self, order: Order) -> None:
        """Update order in database"""
        try:
            from ..database.repositories import OrderRepository
            from decimal import Decimal

            async with self.db_manager.get_session() as session:
                order_repo = OrderRepository(session)

                await order_repo.update_order_status(
                    uuid.UUID(order.id),
                    order.status.value,
                    Decimal(str(order.filled_quantity)) if order.filled_quantity > 0 else None,
                    Decimal(str(order.average_fill_price)) if order.average_fill_price > 0 else None,
                    Decimal(str(order.commission)) if order.commission > 0 else None
                )

        except Exception as e:
            self.logger.error("Failed to update order in database", e)
            # Don't raise - continue with order processing

    async def _execute_paper_order(self, order: Order) -> None:
        """Execute order in paper trading mode"""
        # Simulate order execution with a small delay
        await asyncio.sleep(0.1)

        # For paper trading, assume orders are filled immediately at the requested price
        fill_price = order.price if order.price else 100.0  # Default price for market orders
        commission = fill_price * order.quantity * 0.001  # 0.1% commission

        order.add_fill(order.quantity, fill_price, commission)

        # Remove from active orders
        if order.id in self.active_orders:
            del self.active_orders[order.id]

        self.logger.logger.info(f"Paper order filled: {order.id} at {fill_price}")

        # Notify fill callbacks
        for callback in self.fill_callbacks:
            try:
                callback(order)
            except Exception as e:
                self.logger.error("Error in fill callback", e)

    async def _execute_live_order(self, order: Order) -> None:
        """Execute order on live exchange"""
        try:
            # Determine which exchange to use (default to binance for now)
            exchange_name = "binance"  # Could be configurable per symbol

            if exchange_name not in self.exchanges:
                raise ValueError(f"Exchange {exchange_name} not available")

            exchange = self.exchanges[exchange_name]

            # Convert internal order types to exchange format
            from ..integrations.base import OrderSide as ExchangeOrderSide, OrderType as ExchangeOrderType

            # Map order sides
            exchange_side = ExchangeOrderSide.BUY if order.side == OrderSide.BUY else ExchangeOrderSide.SELL

            # Map order types
            order_type_mapping = {
                OrderType.MARKET: ExchangeOrderType.MARKET,
                OrderType.LIMIT: ExchangeOrderType.LIMIT,
                OrderType.STOP: ExchangeOrderType.STOP,
                OrderType.STOP_LIMIT: ExchangeOrderType.STOP_LIMIT
            }
            exchange_order_type = order_type_mapping.get(order.order_type, ExchangeOrderType.MARKET)

            # Place order on exchange
            exchange_order = await exchange.place_order(
                symbol=order.symbol,
                side=exchange_side,
                order_type=exchange_order_type,
                quantity=order.quantity,
                price=order.price,
                stop_price=order.stop_price,
                time_in_force=order.time_in_force.value
            )

            # Update order with exchange information
            order.exchange_order_id = exchange_order.exchange_order_id
            order.exchange = exchange_name

            # Update order status based on exchange response
            self._update_order_from_exchange(order, exchange_order)

            # Remove from active orders if filled
            if order.status in [OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED]:
                if order.id in self.active_orders:
                    del self.active_orders[order.id]

            self.logger.logger.info(f"Live order executed: {order.id} on {exchange_name}")

            # Notify fill callbacks if order was filled
            if order.status in [OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED]:
                for callback in self.fill_callbacks:
                    try:
                        callback(order)
                    except Exception as e:
                        self.logger.error("Error in fill callback", e)

        except Exception as e:
            order.reject(f"Live execution failed: {str(e)}")
            self.logger.error(f"Failed to execute live order {order.id}", e)

            # Remove from active orders
            if order.id in self.active_orders:
                del self.active_orders[order.id]
            raise

    def _update_order_from_exchange(self, order: Order, exchange_order) -> None:
        """Update internal order with exchange order data"""
        # Map exchange status to internal status
        status_mapping = {
            "PENDING": OrderStatus.PENDING,
            "SUBMITTED": OrderStatus.SUBMITTED,
            "PARTIALLY_FILLED": OrderStatus.PARTIALLY_FILLED,
            "FILLED": OrderStatus.FILLED,
            "CANCELLED": OrderStatus.CANCELLED,
            "REJECTED": OrderStatus.REJECTED,
            "EXPIRED": OrderStatus.EXPIRED
        }

        # Update order status
        if hasattr(exchange_order, 'status'):
            order.status = status_mapping.get(exchange_order.status.value, OrderStatus.PENDING)

        # Update fill information
        if hasattr(exchange_order, 'filled_quantity') and exchange_order.filled_quantity > 0:
            # Calculate new fill
            new_fill_quantity = exchange_order.filled_quantity - order.filled_quantity
            if new_fill_quantity > 0:
                order.add_fill(
                    new_fill_quantity,
                    exchange_order.average_fill_price,
                    exchange_order.commission
                )

    async def cancel_order(self, order_id: str, reason: str = "User cancelled") -> bool:
        """Cancel an order"""
        if order_id not in self.orders:
            self.logger.logger.warning(f"Order {order_id} not found for cancellation")
            return False

        order = self.orders[order_id]

        if order.status not in [OrderStatus.PENDING, OrderStatus.SUBMITTED, OrderStatus.PARTIALLY_FILLED]:
            self.logger.logger.warning(f"Cannot cancel order {order_id} with status {order.status}")
            return False

        try:
            # Cancel on exchange if live trading
            if not self.paper_trading and order.exchange_order_id and order.exchange:
                exchange = self.exchanges.get(order.exchange)
                if exchange:
                    success = await exchange.cancel_order(order.symbol, order.exchange_order_id)
                    if not success:
                        self.logger.logger.warning(f"Failed to cancel order {order_id} on exchange")
                        return False

            # Update order status
            order.cancel(reason)

            # Remove from active orders
            if order_id in self.active_orders:
                del self.active_orders[order_id]

            self.logger.logger.info(f"Cancelled order: {order_id}")

            # Notify callbacks
            for callback in self.status_callbacks:
                try:
                    callback(order)
                except Exception as e:
                    self.logger.error("Error in status callback", e)

            return True

        except Exception as e:
            self.logger.error(f"Failed to cancel order {order_id}", e)
            return False

    async def cancel_all_orders(self, symbol: Optional[str] = None) -> int:
        """Cancel all active orders, optionally filtered by symbol"""
        cancelled_count = 0
        orders_to_cancel = []

        for order in self.active_orders.values():
            if symbol is None or order.symbol == symbol:
                orders_to_cancel.append(order.id)

        for order_id in orders_to_cancel:
            if await self.cancel_order(order_id, "Bulk cancellation"):
                cancelled_count += 1

        self.logger.logger.info(f"Cancelled {cancelled_count} orders")
        return cancelled_count

    def get_order(self, order_id: str) -> Optional[Order]:
        """Get an order by ID"""
        return self.orders.get(order_id)

    def get_orders(
        self,
        symbol: Optional[str] = None,
        status: Optional[OrderStatus] = None,
        strategy: Optional[str] = None
    ) -> List[Order]:
        """Get orders with optional filtering"""
        orders = list(self.orders.values())

        if symbol:
            orders = [o for o in orders if o.symbol == symbol]

        if status:
            orders = [o for o in orders if o.status == status]

        if strategy:
            orders = [o for o in orders if o.strategy == strategy]

        return orders

    def get_active_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """Get active orders"""
        orders = list(self.active_orders.values())

        if symbol:
            orders = [o for o in orders if o.symbol == symbol]

        return orders

    def get_order_status(self) -> Dict[str, Any]:
        """Get order manager status"""
        return {
            "total_orders": len(self.orders),
            "active_orders": len(self.active_orders),
            "paper_trading": self.paper_trading,
            "exchanges_connected": len(self.exchanges)
        }
