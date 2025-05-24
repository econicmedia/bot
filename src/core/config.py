"""
Configuration management for the trading bot
"""

import os
from functools import lru_cache
from typing import List, Optional

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class DatabaseConfig(BaseModel):
    """Database configuration"""
    host: str = "localhost"
    port: int = 5432
    database: str = "trading_db"
    username: str = "trading_user"
    password: str = "trading_pass"
    pool_size: int = 10
    max_overflow: int = 20


class InfluxDBConfig(BaseModel):
    """InfluxDB configuration"""
    url: str = "http://localhost:8086"
    token: str = ""
    org: str = "trading-org"
    bucket: str = "market-data"


class RedisConfig(BaseModel):
    """Redis configuration"""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None


class RiskConfig(BaseModel):
    """Risk management configuration"""
    max_position_size: float = 0.02
    max_daily_loss: float = 0.05
    max_drawdown: float = 0.15
    stop_loss_pct: float = 0.02
    take_profit_pct: float = 0.04


class TradingConfig(BaseModel):
    """Trading configuration"""
    mode: str = "paper"  # paper, live
    default_currency: str = "USD"
    max_positions: int = 10
    max_daily_trades: int = 100
    risk: RiskConfig = RiskConfig()


class StrategyConfig(BaseModel):
    """Strategy configuration"""
    enabled: bool = True
    timeframes: List[str] = ["1m", "5m", "15m", "1h", "4h", "1d"]


class ICTConfig(StrategyConfig):
    """ICT strategy configuration"""
    kill_zones: dict = {
        "london": ["02:00", "05:00"],
        "new_york": ["07:00", "10:00"],
        "asian": ["20:00", "23:00"]
    }


class SMCConfig(StrategyConfig):
    """SMC strategy configuration"""
    confluence_required: int = 3


class ScalpingConfig(StrategyConfig):
    """Scalping strategy configuration"""
    timeframe: str = "1m"
    max_trade_duration: int = 300


class SwingConfig(StrategyConfig):
    """Swing strategy configuration"""
    min_trade_duration: int = 3600


class StrategiesConfig(BaseModel):
    """All strategies configuration"""
    ict: ICTConfig = ICTConfig()
    smc: SMCConfig = SMCConfig()
    scalping: ScalpingConfig = ScalpingConfig()
    swing: SwingConfig = SwingConfig()


class ExchangeConfig(BaseModel):
    """Exchange configuration"""
    api_key: str = ""
    api_secret: str = ""
    sandbox: bool = True


class DataSourcesConfig(BaseModel):
    """Data sources configuration"""
    primary: str = "binance"
    backup: str = "coinbase"
    binance: ExchangeConfig = ExchangeConfig()
    coinbase: ExchangeConfig = ExchangeConfig()


class TradingViewConfig(BaseModel):
    """TradingView integration configuration"""
    username: str = ""
    password: str = ""
    webhook_url: str = ""


class FusionTradingConfig(BaseModel):
    """Fusion Trading integration configuration"""
    api_key: str = ""
    api_secret: str = ""
    base_url: str = "https://api.fusiontrading.com"


class IntegrationsConfig(BaseModel):
    """External integrations configuration"""
    tradingview: TradingViewConfig = TradingViewConfig()
    fusion_trading: FusionTradingConfig = FusionTradingConfig()


class NewsConfig(BaseModel):
    """News and sentiment configuration"""
    sources: List[str] = ["reuters", "bloomberg", "cnbc", "marketwatch"]
    sentiment_model: str = "finbert"
    sentiment_threshold: float = 0.7
    update_interval: int = 300


class MLModelConfig(BaseModel):
    """Machine learning model configuration"""
    type: str
    lookback_window: Optional[int] = None
    prediction_horizon: Optional[int] = None
    retrain_interval: Optional[int] = None


class MLConfig(BaseModel):
    """Machine learning configuration"""
    price_prediction: MLModelConfig = MLModelConfig(type="lstm", lookback_window=60)
    sentiment_analysis: MLModelConfig = MLModelConfig(type="transformer")
    pattern_recognition: MLModelConfig = MLModelConfig(type="cnn")


class AlertConfig(BaseModel):
    """Alert configuration"""
    enabled: bool = False
    smtp_server: Optional[str] = None
    smtp_port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    webhook_url: Optional[str] = None
    bot_token: Optional[str] = None
    chat_id: Optional[str] = None


class MonitoringConfig(BaseModel):
    """Monitoring configuration"""
    prometheus_enabled: bool = True
    prometheus_port: int = 9090
    grafana_enabled: bool = True
    grafana_port: int = 3000
    email: AlertConfig = AlertConfig()
    discord: AlertConfig = AlertConfig()
    telegram: AlertConfig = AlertConfig()


class BacktestingConfig(BaseModel):
    """Backtesting configuration"""
    start_date: str = "2020-01-01"
    end_date: str = "2023-12-31"
    initial_capital: float = 10000
    commission: float = 0.001
    slippage: float = 0.0005


class APIConfig(BaseModel):
    """API configuration"""
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    rate_limit: int = 100


class SecurityConfig(BaseModel):
    """Security configuration"""
    jwt_secret: str = "your-jwt-secret-key"
    jwt_expiration: int = 3600
    api_key_header: str = "X-API-Key"


class LoggingConfig(BaseModel):
    """Logging configuration"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: str = "logs/trading_bot.log"
    max_size: str = "10MB"
    backup_count: int = 5


class AppConfig(BaseModel):
    """Application configuration"""
    name: str = "AI Trading Bot"
    version: str = "1.0.0"
    debug: bool = True
    log_level: str = "INFO"


class Settings(BaseSettings):
    """Main settings class"""
    app: AppConfig = AppConfig()
    database: DatabaseConfig = DatabaseConfig()
    influxdb: InfluxDBConfig = InfluxDBConfig()
    redis: RedisConfig = RedisConfig()
    trading: TradingConfig = TradingConfig()
    strategies: StrategiesConfig = StrategiesConfig()
    data_sources: DataSourcesConfig = DataSourcesConfig()
    integrations: IntegrationsConfig = IntegrationsConfig()
    news: NewsConfig = NewsConfig()
    ml: MLConfig = MLConfig()
    monitoring: MonitoringConfig = MonitoringConfig()
    backtesting: BacktestingConfig = BacktestingConfig()
    api: APIConfig = APIConfig()
    security: SecurityConfig = SecurityConfig()
    logging: LoggingConfig = LoggingConfig()

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"  # Ignore extra fields from .env
    }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    # Load from YAML file if exists
    config_file = os.getenv("CONFIG_FILE", "config/settings.yaml")

    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            config_data = yaml.safe_load(f)
        return Settings(**config_data)

    # Create settings with environment variable overrides
    settings = Settings()

    # Parse DATABASE_URL if provided
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        # Parse postgresql://user:pass@host:port/db
        if database_url.startswith("postgresql://"):
            import re
            match = re.match(r"postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)", database_url)
            if match:
                username, password, host, port, database = match.groups()
                settings.database.username = username
                settings.database.password = password
                settings.database.host = host
                settings.database.port = int(port)
                settings.database.database = database

    # Override other settings from environment
    if os.getenv("TRADING_MODE"):
        settings.trading.mode = os.getenv("TRADING_MODE")

    if os.getenv("APP_DEBUG"):
        settings.app.debug = os.getenv("APP_DEBUG").lower() == "true"

    if os.getenv("LOG_LEVEL"):
        settings.app.log_level = os.getenv("LOG_LEVEL")
        settings.logging.level = os.getenv("LOG_LEVEL")

    return settings
