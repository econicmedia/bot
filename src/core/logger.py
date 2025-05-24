"""
Logging configuration for the trading bot
"""

import logging
import logging.handlers
import os
import sys
from typing import Optional

# Simplified imports - remove external dependencies for now
try:
    import structlog
    from pythonjsonlogger import jsonlogger
    ADVANCED_LOGGING = True
except ImportError:
    ADVANCED_LOGGING = False

# Avoid circular import by importing settings only when needed


def setup_logging(log_level: Optional[str] = None) -> None:
    """Setup logging configuration"""
    # Import here to avoid circular imports
    try:
        from .config import get_settings
        settings = get_settings()
        level = log_level or settings.logging.level
        log_file = settings.logging.file
        log_format = settings.logging.format
        max_size = settings.logging.max_size
        backup_count = settings.logging.backup_count
    except Exception:
        # Fallback to simple configuration
        level = log_level or "INFO"
        log_file = "logs/trading.log"
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        max_size = "10MB"
        backup_count = 5

    log_level_num = getattr(logging, level.upper(), logging.INFO)

    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    os.makedirs(log_dir, exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level_num)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level_num)

    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=_parse_size(max_size),
        backupCount=backup_count
    )
    file_handler.setLevel(log_level_num)

    # Simple formatter for both console and file
    formatter = logging.Formatter(
        fmt=log_format,
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Set formatters
    console_handler.setFormatter(formatter)

    # Use JSON formatter if available, otherwise simple formatter
    if ADVANCED_LOGGING:
        json_formatter = jsonlogger.JsonFormatter(
            fmt='%(asctime)s %(name)s %(levelname)s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(json_formatter)
    else:
        file_handler.setFormatter(formatter)

    # Add handlers to root logger
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Configure structlog if available
    if ADVANCED_LOGGING:
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("kafka").setLevel(logging.WARNING)
    logging.getLogger("websockets").setLevel(logging.WARNING)


def _parse_size(size_str: str) -> int:
    """Parse size string like '10MB' to bytes"""
    size_str = size_str.upper()

    if size_str.endswith('KB'):
        return int(size_str[:-2]) * 1024
    elif size_str.endswith('MB'):
        return int(size_str[:-2]) * 1024 * 1024
    elif size_str.endswith('GB'):
        return int(size_str[:-2]) * 1024 * 1024 * 1024
    else:
        return int(size_str)


class TradingLogger:
    """Specialized logger for trading operations"""

    def __init__(self, name: str):
        if ADVANCED_LOGGING:
            self.logger = structlog.get_logger(name)
        else:
            self.logger = logging.getLogger(name)

    # Basic logging methods
    def info(self, message: str, **kwargs):
        """Log info message"""
        if ADVANCED_LOGGING and kwargs:
            self.logger.info(message, **kwargs)
        else:
            self.logger.info(message)

    def warning(self, message: str, **kwargs):
        """Log warning message"""
        if ADVANCED_LOGGING and kwargs:
            self.logger.warning(message, **kwargs)
        else:
            self.logger.warning(message)

    def error(self, message: str, error: Exception = None, **kwargs):
        """Log error message"""
        if error:
            if ADVANCED_LOGGING:
                self.logger.error(
                    message,
                    error=str(error),
                    error_type=type(error).__name__,
                    **kwargs
                )
            else:
                self.logger.error(f"{message}: {error}")
        else:
            if ADVANCED_LOGGING and kwargs:
                self.logger.error(message, **kwargs)
            else:
                self.logger.error(message)

    def debug(self, message: str, **kwargs):
        """Log debug message"""
        if ADVANCED_LOGGING and kwargs:
            self.logger.debug(message, **kwargs)
        else:
            self.logger.debug(message)

    def trade_executed(self, symbol: str, side: str, quantity: float, price: float, order_id: str):
        """Log trade execution"""
        if ADVANCED_LOGGING:
            self.logger.info(
                "Trade executed",
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                order_id=order_id,
                event_type="trade_executed"
            )
        else:
            self.logger.info(
                f"Trade executed: {symbol} {side} {quantity}@{price} (order: {order_id})"
            )

    def order_placed(self, symbol: str, side: str, quantity: float, price: float, order_type: str, order_id: str):
        """Log order placement"""
        self.logger.info(
            "Order placed",
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
            order_type=order_type,
            order_id=order_id,
            event_type="order_placed"
        )

    def order_cancelled(self, order_id: str, reason: str):
        """Log order cancellation"""
        self.logger.info(
            "Order cancelled",
            order_id=order_id,
            reason=reason,
            event_type="order_cancelled"
        )

    def strategy_signal(self, strategy: str, symbol: str, signal: str, confidence: float, data: dict):
        """Log strategy signal"""
        self.logger.info(
            "Strategy signal generated",
            strategy=strategy,
            symbol=symbol,
            signal=signal,
            confidence=confidence,
            data=data,
            event_type="strategy_signal"
        )

    def risk_event(self, event_type: str, symbol: str, current_value: float, limit: float, action: str):
        """Log risk management event"""
        self.logger.warning(
            "Risk management event",
            risk_event_type=event_type,
            symbol=symbol,
            current_value=current_value,
            limit=limit,
            action=action,
            event_type="risk_event"
        )



    def performance_metric(self, metric_name: str, value: float, symbol: str = None, strategy: str = None):
        """Log performance metric"""
        self.logger.info(
            "Performance metric",
            metric_name=metric_name,
            value=value,
            symbol=symbol,
            strategy=strategy,
            event_type="performance_metric"
        )


def get_trading_logger(name: str) -> TradingLogger:
    """Get a trading logger instance"""
    return TradingLogger(name)
