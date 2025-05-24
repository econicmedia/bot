"""
Database Repositories

Data access layer providing high-level operations for trading bot entities.
Implements repository pattern for clean separation of data access logic.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, desc, asc, func
from sqlalchemy.orm import selectinload

from .models import User, Strategy, Order, Trade, Position, Portfolio, PerformanceMetric, TradingSession
from core.logger import get_trading_logger


class BaseRepository:
    """Base repository with common operations"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = get_trading_logger(self.__class__.__name__)


class OrderRepository(BaseRepository):
    """Repository for order operations"""

    async def create_order(self, order_data: Dict[str, Any]) -> Order:
        """Create a new order"""
        order = Order(**order_data)
        self.session.add(order)
        await self.session.flush()
        return order

    async def get_order_by_id(self, order_id: uuid.UUID) -> Optional[Order]:
        """Get order by ID"""
        result = await self.session.execute(
            select(Order).where(Order.id == order_id)
        )
        return result.scalar_one_or_none()

    async def get_orders_by_user(
        self,
        user_id: uuid.UUID,
        symbol: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Order]:
        """Get orders for a user with optional filters"""
        query = select(Order).where(Order.user_id == user_id)

        if symbol:
            query = query.where(Order.symbol == symbol)

        if status:
            query = query.where(Order.status == status)

        query = query.order_by(desc(Order.created_at)).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_active_orders(self, user_id: uuid.UUID) -> List[Order]:
        """Get active orders for a user"""
        result = await self.session.execute(
            select(Order).where(
                and_(
                    Order.user_id == user_id,
                    Order.status.in_(["pending", "submitted", "partially_filled"])
                )
            ).order_by(desc(Order.created_at))
        )
        return result.scalars().all()

    async def update_order_status(
        self,
        order_id: uuid.UUID,
        status: str,
        filled_quantity: Optional[Decimal] = None,
        average_fill_price: Optional[Decimal] = None,
        commission: Optional[Decimal] = None
    ) -> bool:
        """Update order status and fill information"""
        update_data = {"status": status, "updated_at": datetime.utcnow()}

        if filled_quantity is not None:
            update_data["filled_quantity"] = filled_quantity

        if average_fill_price is not None:
            update_data["average_fill_price"] = average_fill_price

        if commission is not None:
            update_data["commission"] = commission

        if status == "filled":
            update_data["filled_at"] = datetime.utcnow()
        elif status == "cancelled":
            update_data["cancelled_at"] = datetime.utcnow()

        result = await self.session.execute(
            update(Order).where(Order.id == order_id).values(**update_data)
        )

        return result.rowcount > 0

    async def get_order_statistics(self, user_id: uuid.UUID, days: int = 30) -> Dict[str, Any]:
        """Get order statistics for a user"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Total orders
        total_result = await self.session.execute(
            select(func.count(Order.id)).where(
                and_(Order.user_id == user_id, Order.created_at >= cutoff_date)
            )
        )
        total_orders = total_result.scalar()

        # Orders by status
        status_result = await self.session.execute(
            select(Order.status, func.count(Order.id)).where(
                and_(Order.user_id == user_id, Order.created_at >= cutoff_date)
            ).group_by(Order.status)
        )
        status_counts = dict(status_result.all())

        return {
            "total_orders": total_orders,
            "status_breakdown": status_counts,
            "period_days": days
        }


class TradeRepository(BaseRepository):
    """Repository for trade operations"""

    async def create_trade(self, trade_data: Dict[str, Any]) -> Trade:
        """Create a new trade"""
        trade = Trade(**trade_data)
        self.session.add(trade)
        await self.session.flush()
        return trade

    async def get_trade_by_id(self, trade_id: uuid.UUID) -> Optional[Trade]:
        """Get trade by ID"""
        result = await self.session.execute(
            select(Trade).where(Trade.id == trade_id)
        )
        return result.scalar_one_or_none()

    async def get_trades_by_user(
        self,
        user_id: uuid.UUID,
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Trade]:
        """Get trades for a user with optional filters"""
        query = select(Trade).where(Trade.user_id == user_id)

        if symbol:
            query = query.where(Trade.symbol == symbol)

        if start_date:
            query = query.where(Trade.executed_at >= start_date)

        if end_date:
            query = query.where(Trade.executed_at <= end_date)

        query = query.order_by(desc(Trade.executed_at)).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_trade_summary(
        self,
        user_id: uuid.UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get trade summary statistics"""
        query = select(Trade).where(Trade.user_id == user_id)

        if start_date:
            query = query.where(Trade.executed_at >= start_date)

        if end_date:
            query = query.where(Trade.executed_at <= end_date)

        # Get all trades for calculations
        result = await self.session.execute(query)
        trades = result.scalars().all()

        if not trades:
            return {
                "total_trades": 0,
                "total_volume": Decimal("0"),
                "total_commission": Decimal("0"),
                "symbols_traded": []
            }

        total_volume = sum(trade.quantity * trade.price for trade in trades)
        total_commission = sum(trade.commission for trade in trades)
        symbols_traded = list(set(trade.symbol for trade in trades))

        return {
            "total_trades": len(trades),
            "total_volume": total_volume,
            "total_commission": total_commission,
            "symbols_traded": symbols_traded,
            "first_trade": min(trade.executed_at for trade in trades),
            "last_trade": max(trade.executed_at for trade in trades)
        }


class PositionRepository(BaseRepository):
    """Repository for position operations"""

    async def create_position(self, position_data: Dict[str, Any]) -> Position:
        """Create a new position"""
        position = Position(**position_data)
        self.session.add(position)
        await self.session.flush()
        return position

    async def get_position_by_id(self, position_id: uuid.UUID) -> Optional[Position]:
        """Get position by ID"""
        result = await self.session.execute(
            select(Position).where(Position.id == position_id)
        )
        return result.scalar_one_or_none()

    async def get_position_by_symbol(self, user_id: uuid.UUID, symbol: str) -> Optional[Position]:
        """Get open position for a symbol"""
        result = await self.session.execute(
            select(Position).where(
                and_(
                    Position.user_id == user_id,
                    Position.symbol == symbol,
                    Position.is_open == True
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_open_positions(self, user_id: uuid.UUID) -> List[Position]:
        """Get all open positions for a user"""
        result = await self.session.execute(
            select(Position).where(
                and_(Position.user_id == user_id, Position.is_open == True)
            ).order_by(desc(Position.entry_time))
        )
        return result.scalars().all()

    async def update_position_price(
        self,
        position_id: uuid.UUID,
        current_price: Decimal,
        unrealized_pnl: Decimal
    ) -> bool:
        """Update position current price and unrealized P&L"""
        result = await self.session.execute(
            update(Position).where(Position.id == position_id).values(
                current_price=current_price,
                unrealized_pnl=unrealized_pnl,
                updated_at=datetime.utcnow()
            )
        )
        return result.rowcount > 0

    async def close_position(
        self,
        position_id: uuid.UUID,
        exit_price: Decimal,
        realized_pnl: Decimal
    ) -> bool:
        """Close a position"""
        result = await self.session.execute(
            update(Position).where(Position.id == position_id).values(
                current_price=exit_price,
                realized_pnl=realized_pnl,
                is_open=False,
                exit_time=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        )
        return result.rowcount > 0

    async def get_position_history(
        self,
        user_id: uuid.UUID,
        symbol: Optional[str] = None,
        limit: int = 100
    ) -> List[Position]:
        """Get position history for a user"""
        query = select(Position).where(Position.user_id == user_id)

        if symbol:
            query = query.where(Position.symbol == symbol)

        query = query.order_by(desc(Position.entry_time)).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()


class PortfolioRepository(BaseRepository):
    """Repository for portfolio operations"""

    async def create_portfolio_snapshot(self, portfolio_data: Dict[str, Any]) -> Portfolio:
        """Create a portfolio snapshot"""
        portfolio = Portfolio(**portfolio_data)
        self.session.add(portfolio)
        await self.session.flush()
        return portfolio

    async def get_latest_portfolio(self, user_id: uuid.UUID) -> Optional[Portfolio]:
        """Get the latest portfolio snapshot for a user"""
        result = await self.session.execute(
            select(Portfolio).where(Portfolio.user_id == user_id)
            .order_by(desc(Portfolio.timestamp)).limit(1)
        )
        return result.scalar_one_or_none()

    async def get_portfolio_history(
        self,
        user_id: uuid.UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Portfolio]:
        """Get portfolio history for a user"""
        query = select(Portfolio).where(Portfolio.user_id == user_id)

        if start_date:
            query = query.where(Portfolio.timestamp >= start_date)

        if end_date:
            query = query.where(Portfolio.timestamp <= end_date)

        query = query.order_by(desc(Portfolio.timestamp)).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_portfolio_performance(
        self,
        user_id: uuid.UUID,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get portfolio performance metrics"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        result = await self.session.execute(
            select(Portfolio).where(
                and_(Portfolio.user_id == user_id, Portfolio.timestamp >= cutoff_date)
            ).order_by(asc(Portfolio.timestamp))
        )
        snapshots = result.scalars().all()

        if not snapshots:
            return {"error": "No portfolio data available"}

        first_snapshot = snapshots[0]
        last_snapshot = snapshots[-1]

        total_return = ((last_snapshot.total_value - first_snapshot.total_value) /
                       first_snapshot.total_value * 100)

        # Calculate max drawdown
        peak_value = first_snapshot.total_value
        max_drawdown = 0

        for snapshot in snapshots:
            if snapshot.total_value > peak_value:
                peak_value = snapshot.total_value

            drawdown = (peak_value - snapshot.total_value) / peak_value * 100
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        return {
            "period_days": days,
            "starting_value": first_snapshot.total_value,
            "ending_value": last_snapshot.total_value,
            "total_return_pct": round(total_return, 2),
            "max_drawdown_pct": round(max_drawdown, 2),
            "current_unrealized_pnl": last_snapshot.unrealized_pnl,
            "current_realized_pnl": last_snapshot.realized_pnl,
            "snapshots_count": len(snapshots)
        }


class PerformanceRepository(BaseRepository):
    """Repository for performance metrics operations"""

    async def create_performance_metric(self, metric_data: Dict[str, Any]) -> PerformanceMetric:
        """Create a performance metric record"""
        metric = PerformanceMetric(**metric_data)
        self.session.add(metric)
        await self.session.flush()
        return metric

    async def get_performance_by_date(
        self,
        user_id: uuid.UUID,
        date: datetime
    ) -> Optional[PerformanceMetric]:
        """Get performance metrics for a specific date"""
        result = await self.session.execute(
            select(PerformanceMetric).where(
                and_(
                    PerformanceMetric.user_id == user_id,
                    func.date(PerformanceMetric.date) == date.date()
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_performance_history(
        self,
        user_id: uuid.UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[PerformanceMetric]:
        """Get performance history for a user"""
        query = select(PerformanceMetric).where(PerformanceMetric.user_id == user_id)

        if start_date:
            query = query.where(PerformanceMetric.date >= start_date)

        if end_date:
            query = query.where(PerformanceMetric.date <= end_date)

        query = query.order_by(desc(PerformanceMetric.date)).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def update_daily_performance(
        self,
        user_id: uuid.UUID,
        date: datetime,
        metric_updates: Dict[str, Any]
    ) -> bool:
        """Update or create daily performance metrics"""
        # Try to update existing record
        result = await self.session.execute(
            update(PerformanceMetric).where(
                and_(
                    PerformanceMetric.user_id == user_id,
                    func.date(PerformanceMetric.date) == date.date()
                )
            ).values(**metric_updates, updated_at=datetime.utcnow())
        )

        if result.rowcount == 0:
            # Create new record if none exists
            metric_data = {
                "user_id": user_id,
                "date": date,
                **metric_updates
            }
            await self.create_performance_metric(metric_data)

        return True
