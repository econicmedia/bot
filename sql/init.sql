-- AI Trading Bot Database Initialization

-- Create database if not exists
-- This is handled by docker-compose environment variables

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS trading;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS logs;

-- Create users table
CREATE TABLE IF NOT EXISTS trading.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create strategies table
CREATE TABLE IF NOT EXISTS trading.strategies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    parameters JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create orders table
CREATE TABLE IF NOT EXISTS trading.orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES trading.users(id),
    strategy_id UUID REFERENCES trading.strategies(id),
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL CHECK (side IN ('buy', 'sell')),
    order_type VARCHAR(20) NOT NULL,
    quantity DECIMAL(20, 8) NOT NULL,
    price DECIMAL(20, 8),
    stop_price DECIMAL(20, 8),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    exchange_order_id VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create trades table
CREATE TABLE IF NOT EXISTS trading.trades (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID REFERENCES trading.orders(id),
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,
    quantity DECIMAL(20, 8) NOT NULL,
    price DECIMAL(20, 8) NOT NULL,
    commission DECIMAL(20, 8) DEFAULT 0,
    exchange_trade_id VARCHAR(100),
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create positions table
CREATE TABLE IF NOT EXISTS trading.positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES trading.users(id),
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL CHECK (side IN ('long', 'short')),
    quantity DECIMAL(20, 8) NOT NULL,
    entry_price DECIMAL(20, 8) NOT NULL,
    current_price DECIMAL(20, 8),
    unrealized_pnl DECIMAL(20, 8) DEFAULT 0,
    realized_pnl DECIMAL(20, 8) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, symbol, side)
);

-- Create performance metrics table
CREATE TABLE IF NOT EXISTS analytics.performance_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES trading.users(id),
    strategy_id UUID REFERENCES trading.strategies(id),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(20, 8) NOT NULL,
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON trading.orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_symbol ON trading.orders(symbol);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON trading.orders(created_at);
CREATE INDEX IF NOT EXISTS idx_trades_order_id ON trading.trades(order_id);
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trading.trades(symbol);
CREATE INDEX IF NOT EXISTS idx_trades_executed_at ON trading.trades(executed_at);
CREATE INDEX IF NOT EXISTS idx_positions_user_id ON trading.positions(user_id);
CREATE INDEX IF NOT EXISTS idx_positions_symbol ON trading.positions(symbol);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_user_id ON analytics.performance_metrics(user_id);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_strategy_id ON analytics.performance_metrics(strategy_id);

-- Insert default admin user (password: admin123 - change in production!)
INSERT INTO trading.users (username, email, password_hash) 
VALUES ('admin', 'admin@tradingbot.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6hsxq9w5KS')
ON CONFLICT (username) DO NOTHING;

-- Insert default strategies
INSERT INTO trading.strategies (name, description, parameters) VALUES
('ICT', 'Inner Circle Trader strategy based on market structure and order blocks', '{"timeframes": ["1m", "5m", "15m"], "risk_per_trade": 0.02}'),
('SMC', 'Smart Money Concept strategy focusing on supply and demand zones', '{"timeframes": ["5m", "15m", "1h"], "confluence_required": 3}'),
('Scalping', 'High-frequency scalping strategy for quick profits', '{"timeframe": "1m", "max_trade_duration": 300}'),
('Swing', 'Medium-term swing trading strategy', '{"timeframes": ["4h", "1d"], "min_trade_duration": 3600}')
ON CONFLICT DO NOTHING;
