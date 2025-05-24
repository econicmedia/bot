"""
Database-Integrated Portfolio Manager

Enhanced portfolio manager that persists all state changes to the database.
Provides data persistence, recovery, and historical tracking capabilities.
"""

import asyncio
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal

from .config import Settings
from .logger import get_trading_logger
from .portfolio_manager import Position as CorePosition, Trade as CoreTrade
from ..database import (
    get_database_manager, DatabaseManager,
    PositionRepository, TradeRepository, PortfolioRepository, PerformanceRepository
)
from ..database.models import Position as DBPosition, Trade as DBTrade, Portfolio as DBPortfolio


class DatabasePortfolioManager:
    """
    Database-integrated portfolio manager
    
    Extends the core portfolio manager with database persistence for:
    - Position tracking and history
    - Trade execution logging
    - Portfolio state snapshots
    - Performance metrics calculation
    """
    
    def __init__(self, settings: Settings, user_id: Optional[uuid.UUID] = None):
        """
        Initialize database portfolio manager
        
        Args:
            settings: Application settings
            user_id: User ID for multi-user support (defaults to system user)
        """
        self.settings = settings
        self.logger = get_trading_logger("DatabasePortfolioManager")
        
        # User identification
        self.user_id = user_id or self._get_default_user_id()
        
        # Database components
        self.db_manager: Optional[DatabaseManager] = None
        
        # Portfolio state (cached from database)
        self.initial_capital = Decimal("100000.0")
        self.cash_balance = self.initial_capital
        self.positions: Dict[str, CorePosition] = {}
        self.trades: List[CoreTrade] = []
        
        # Performance tracking
        self.total_pnl = Decimal("0.0")
        self.total_commission = Decimal("0.0")
        self.peak_portfolio_value = self.initial_capital
        self.max_drawdown = Decimal("0.0")
        
        # Statistics
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        
        # State tracking
        self.last_snapshot_time: Optional[datetime] = None
        self.snapshot_interval = timedelta(minutes=15)  # Snapshot every 15 minutes
        
        self.logger.logger.info(f"Database portfolio manager initialized for user: {self.user_id}")
    
    def _get_default_user_id(self) -> uuid.UUID:
        """Get default system user ID"""
        # For single-user deployment, use a fixed UUID
        return uuid.UUID("00000000-0000-0000-0000-000000000001")
    
    async def initialize(self) -> None:
        """Initialize database portfolio manager"""
        try:
            # Initialize database connection
            self.db_manager = await get_database_manager()
            
            # Load portfolio state from database
            await self._load_portfolio_state()
            
            # Start background tasks
            asyncio.create_task(self._portfolio_snapshot_task())
            asyncio.create_task(self._performance_calculation_task())
            
            self.logger.logger.info("Database portfolio manager initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database portfolio manager: {e}")
            raise
    
    async def _load_portfolio_state(self) -> None:
        """Load portfolio state from database"""
        try:
            async with self.db_manager.get_session() as session:
                position_repo = PositionRepository(session)
                trade_repo = TradeRepository(session)
                portfolio_repo = PortfolioRepository(session)
                
                # Load open positions
                db_positions = await position_repo.get_open_positions(self.user_id)
                for db_pos in db_positions:
                    core_pos = self._db_position_to_core(db_pos)
                    self.positions[db_pos.symbol] = core_pos
                
                # Load recent trades for statistics
                recent_trades = await trade_repo.get_trades_by_user(
                    self.user_id, 
                    start_date=datetime.utcnow() - timedelta(days=30),
                    limit=1000
                )
                
                # Calculate statistics from trades
                self.total_trades = len(recent_trades)
                self.winning_trades = len([t for t in recent_trades if self._calculate_trade_pnl(t) > 0])
                self.losing_trades = self.total_trades - self.winning_trades
                
                # Load latest portfolio snapshot
                latest_portfolio = await portfolio_repo.get_latest_portfolio(self.user_id)
                if latest_portfolio:
                    self.cash_balance = latest_portfolio.cash_balance
                    self.total_pnl = latest_portfolio.realized_pnl
                    self.peak_portfolio_value = max(self.peak_portfolio_value, latest_portfolio.total_value)
                    self.last_snapshot_time = latest_portfolio.timestamp
                
                self.logger.logger.info(f"Loaded portfolio state: {len(self.positions)} positions, {self.total_trades} trades")
                
        except Exception as e:
            self.logger.error(f"Failed to load portfolio state: {e}")
            # Continue with default values if database load fails
    
    def _db_position_to_core(self, db_pos: DBPosition) -> CorePosition:
        """Convert database position to core position object"""
        core_pos = CorePosition(
            symbol=db_pos.symbol,
            side=db_pos.side,
            quantity=float(db_pos.quantity),
            entry_price=float(db_pos.entry_price),
            entry_time=db_pos.entry_time,
            strategy=None  # Strategy info not stored in position
        )
        
        # Update with current state
        if db_pos.current_price:
            core_pos.current_price = float(db_pos.current_price)
        
        core_pos.unrealized_pnl = float(db_pos.unrealized_pnl or 0)
        core_pos.commission_paid = float(db_pos.commission_paid or 0)
        
        if db_pos.stop_loss:
            core_pos.stop_loss = float(db_pos.stop_loss)
        if db_pos.take_profit:
            core_pos.take_profit = float(db_pos.take_profit)
        
        return core_pos
    
    def _calculate_trade_pnl(self, db_trade: DBTrade) -> Decimal:
        """Calculate P&L for a database trade"""
        if db_trade.side == "buy":
            # This is a simplified calculation - in reality, we'd need to match with sell trades
            return Decimal("0")  # Placeholder
        else:
            return Decimal("0")  # Placeholder
    
    async def open_position(
        self,
        symbol: str,
        side: str,
        quantity: float,
        entry_price: float,
        strategy: Optional[str] = None,
        commission: float = 0.0
    ) -> CorePosition:
        """Open a new position with database persistence"""
        try:
            if symbol in self.positions:
                raise ValueError(f"Position already exists for {symbol}")
            
            # Create core position
            position = CorePosition(
                symbol=symbol,
                side=side,
                quantity=quantity,
                entry_price=entry_price,
                entry_time=datetime.utcnow(),
                strategy=strategy
            )
            position.commission_paid = commission
            
            # Persist to database
            async with self.db_manager.get_session() as session:
                position_repo = PositionRepository(session)
                
                position_data = {
                    "user_id": self.user_id,
                    "symbol": symbol,
                    "side": side,
                    "quantity": Decimal(str(quantity)),
                    "entry_price": Decimal(str(entry_price)),
                    "current_price": Decimal(str(entry_price)),
                    "entry_time": position.entry_time,
                    "commission_paid": Decimal(str(commission)),
                    "is_open": True
                }
                
                db_position = await position_repo.create_position(position_data)
                
                # Update local state
                self.positions[symbol] = position
                
                # Update cash balance
                position_value = entry_price * quantity
                if side == "long":
                    self.cash_balance -= Decimal(str(position_value + commission))
                else:  # short
                    self.cash_balance += Decimal(str(position_value - commission))
                
                self.total_commission += Decimal(str(commission))
                
                self.logger.logger.info(f"Opened {side} position: {symbol} {quantity}@{entry_price}")
                
                # Create portfolio snapshot
                await self._create_portfolio_snapshot()
                
                return position
                
        except Exception as e:
            self.logger.error(f"Failed to open position {symbol}: {e}")
            raise
    
    async def close_position(
        self,
        symbol: str,
        exit_price: float,
        commission: float = 0.0
    ) -> Optional[CoreTrade]:
        """Close an existing position with database persistence"""
        try:
            if symbol not in self.positions:
                self.logger.logger.warning(f"No position found for {symbol}")
                return None
            
            position = self.positions[symbol]
            exit_time = datetime.utcnow()
            
            # Create trade record
            trade = CoreTrade(
                symbol=symbol,
                side=position.side,
                quantity=position.quantity,
                entry_price=position.entry_price,
                exit_price=exit_price,
                entry_time=position.entry_time,
                exit_time=exit_time,
                strategy=position.strategy,
                commission=position.commission_paid + commission
            )
            
            # Persist to database
            async with self.db_manager.get_session() as session:
                position_repo = PositionRepository(session)
                trade_repo = TradeRepository(session)
                
                # Close position in database
                db_position = await position_repo.get_position_by_symbol(self.user_id, symbol)
                if db_position:
                    await position_repo.close_position(
                        db_position.id,
                        Decimal(str(exit_price)),
                        Decimal(str(trade.pnl))
                    )
                
                # Create trade record
                trade_data = {
                    "user_id": self.user_id,
                    "symbol": symbol,
                    "side": "sell" if position.side == "long" else "buy",  # Opposite of position side
                    "quantity": Decimal(str(position.quantity)),
                    "price": Decimal(str(exit_price)),
                    "commission": Decimal(str(commission)),
                    "executed_at": exit_time
                }
                
                await trade_repo.create_trade(trade_data)
                
                # Update local state
                self.trades.append(trade)
                self.total_pnl += Decimal(str(trade.pnl))
                self.total_commission += Decimal(str(commission))
                self.total_trades += 1
                
                if trade.pnl > 0:
                    self.winning_trades += 1
                else:
                    self.losing_trades += 1
                
                # Update cash balance
                position_value = exit_price * position.quantity
                if position.side == "long":
                    self.cash_balance += Decimal(str(position_value - commission))
                else:  # short
                    self.cash_balance -= Decimal(str(position_value + commission))
                
                # Remove position
                del self.positions[symbol]
                
                self.logger.logger.info(f"Closed position: {symbol} P&L: {trade.pnl:.2f}")
                
                # Create portfolio snapshot
                await self._create_portfolio_snapshot()
                
                return trade
                
        except Exception as e:
            self.logger.error(f"Failed to close position {symbol}: {e}")
            raise
    
    async def update_position_prices(self, price_updates: Dict[str, float]) -> None:
        """Update positions with new market prices and persist to database"""
        try:
            timestamp = datetime.utcnow()
            
            async with self.db_manager.get_session() as session:
                position_repo = PositionRepository(session)
                
                for symbol, price in price_updates.items():
                    if symbol in self.positions:
                        position = self.positions[symbol]
                        position.update_price(price, timestamp)
                        
                        # Update in database
                        db_position = await position_repo.get_position_by_symbol(self.user_id, symbol)
                        if db_position:
                            await position_repo.update_position_price(
                                db_position.id,
                                Decimal(str(price)),
                                Decimal(str(position.unrealized_pnl))
                            )
                            
        except Exception as e:
            self.logger.error(f"Failed to update position prices: {e}")
    
    async def _create_portfolio_snapshot(self) -> None:
        """Create a portfolio snapshot in the database"""
        try:
            async with self.db_manager.get_session() as session:
                portfolio_repo = PortfolioRepository(session)
                
                # Calculate current portfolio values
                positions_value = sum(Decimal(str(pos.get_market_value())) for pos in self.positions.values())
                total_value = self.cash_balance + positions_value
                unrealized_pnl = sum(Decimal(str(pos.unrealized_pnl)) for pos in self.positions.values())
                
                # Calculate returns
                total_return = ((total_value - self.initial_capital) / self.initial_capital * 100) if self.initial_capital > 0 else Decimal("0")
                
                # Calculate daily return (simplified)
                daily_return = Decimal("0")  # Would need previous day's value for accurate calculation
                
                # Update max drawdown
                if total_value > self.peak_portfolio_value:
                    self.peak_portfolio_value = total_value
                
                current_drawdown = ((self.peak_portfolio_value - total_value) / self.peak_portfolio_value * 100) if self.peak_portfolio_value > 0 else Decimal("0")
                self.max_drawdown = max(self.max_drawdown, current_drawdown)
                
                # Create snapshot
                snapshot_data = {
                    "user_id": self.user_id,
                    "total_value": total_value,
                    "cash_balance": self.cash_balance,
                    "positions_value": positions_value,
                    "unrealized_pnl": unrealized_pnl,
                    "realized_pnl": self.total_pnl,
                    "total_return": total_return,
                    "daily_return": daily_return,
                    "max_drawdown": self.max_drawdown,
                    "timestamp": datetime.utcnow()
                }
                
                await portfolio_repo.create_portfolio_snapshot(snapshot_data)
                self.last_snapshot_time = datetime.utcnow()
                
        except Exception as e:
            self.logger.error(f"Failed to create portfolio snapshot: {e}")
    
    async def _portfolio_snapshot_task(self) -> None:
        """Background task to create periodic portfolio snapshots"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                if (not self.last_snapshot_time or 
                    datetime.utcnow() - self.last_snapshot_time >= self.snapshot_interval):
                    await self._create_portfolio_snapshot()
                    
            except Exception as e:
                self.logger.error(f"Error in portfolio snapshot task: {e}")
                await asyncio.sleep(60)
    
    async def _performance_calculation_task(self) -> None:
        """Background task to calculate and store daily performance metrics"""
        while True:
            try:
                # Run once per day at midnight
                await asyncio.sleep(3600)  # Check every hour
                
                now = datetime.utcnow()
                if now.hour == 0:  # Midnight UTC
                    await self._calculate_daily_performance()
                    
            except Exception as e:
                self.logger.error(f"Error in performance calculation task: {e}")
                await asyncio.sleep(3600)
    
    async def _calculate_daily_performance(self) -> None:
        """Calculate and store daily performance metrics"""
        try:
            async with self.db_manager.get_session() as session:
                performance_repo = PerformanceRepository(session)
                trade_repo = TradeRepository(session)
                
                # Get today's date
                today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                yesterday = today - timedelta(days=1)
                
                # Get yesterday's trades
                yesterday_trades = await trade_repo.get_trades_by_user(
                    self.user_id,
                    start_date=yesterday,
                    end_date=today
                )
                
                if yesterday_trades:
                    # Calculate metrics
                    total_trades = len(yesterday_trades)
                    winning_trades = len([t for t in yesterday_trades if self._calculate_trade_pnl(t) > 0])
                    losing_trades = total_trades - winning_trades
                    win_rate = (winning_trades / total_trades) if total_trades > 0 else 0
                    
                    # Calculate P&L (simplified)
                    gross_profit = sum(max(self._calculate_trade_pnl(t), Decimal("0")) for t in yesterday_trades)
                    gross_loss = sum(min(self._calculate_trade_pnl(t), Decimal("0")) for t in yesterday_trades)
                    net_profit = gross_profit + gross_loss
                    
                    # Store metrics
                    metric_data = {
                        "total_trades": total_trades,
                        "winning_trades": winning_trades,
                        "losing_trades": losing_trades,
                        "win_rate": Decimal(str(win_rate)),
                        "gross_profit": gross_profit,
                        "gross_loss": gross_loss,
                        "net_profit": net_profit
                    }
                    
                    await performance_repo.update_daily_performance(
                        self.user_id,
                        yesterday,
                        metric_data
                    )
                    
        except Exception as e:
            self.logger.error(f"Failed to calculate daily performance: {e}")
    
    # Portfolio query methods
    def get_portfolio_value(self) -> float:
        """Get total portfolio value"""
        positions_value = sum(pos.get_market_value() for pos in self.positions.values())
        return float(self.cash_balance + Decimal(str(positions_value)))
    
    def get_unrealized_pnl(self) -> float:
        """Get total unrealized P&L"""
        return sum(pos.unrealized_pnl for pos in self.positions.values())
    
    def get_total_pnl(self) -> float:
        """Get total P&L (realized + unrealized)"""
        return float(self.total_pnl) + self.get_unrealized_pnl()
    
    def get_positions(self) -> Dict[str, CorePosition]:
        """Get current positions"""
        return self.positions.copy()
    
    def get_position(self, symbol: str) -> Optional[CorePosition]:
        """Get position for a specific symbol"""
        return self.positions.get(symbol)
    
    async def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get comprehensive portfolio summary"""
        return {
            "user_id": str(self.user_id),
            "total_value": self.get_portfolio_value(),
            "cash_balance": float(self.cash_balance),
            "positions_count": len(self.positions),
            "unrealized_pnl": self.get_unrealized_pnl(),
            "realized_pnl": float(self.total_pnl),
            "total_pnl": self.get_total_pnl(),
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "win_rate": (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0,
            "max_drawdown": float(self.max_drawdown),
            "total_commission": float(self.total_commission)
        }
