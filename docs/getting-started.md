# Getting Started Guide

## 1. Prerequisites

### System Requirements
- **Operating System**: Windows 10/11, macOS 10.15+, or Linux Ubuntu 18.04+
- **Python**: Version 3.11 or higher
- **Memory**: Minimum 8GB RAM (16GB recommended)
- **Storage**: 50GB free space for data and logs
- **Network**: Stable internet connection for real-time data

### Required Software
- **Docker**: For containerized deployment
- **Git**: For version control
- **Node.js**: For frontend development (v18+)
- **PostgreSQL**: Database (if not using Docker)
- **Redis**: Caching layer (if not using Docker)

## 2. Installation

### Option 1: Docker Setup (Recommended)

1. **Clone the Repository**
```bash
git clone https://github.com/your-username/ai-trading-bot.git
cd ai-trading-bot
```

2. **Environment Configuration**
```bash
# Copy environment template
cp .env.example .env

# Edit configuration
notepad .env  # Windows
nano .env     # Linux/macOS
```

3. **Start Services**
```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f trading-bot
```

### Option 2: Local Development Setup

1. **Python Environment**
```bash
# Create virtual environment
python -m venv venv

# Activate environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

2. **Database Setup**
```bash
# Install PostgreSQL and Redis locally
# Create database
createdb trading_db

# Run migrations
alembic upgrade head
```

3. **Start Application**
```bash
# Start the trading bot
python src/main.py

# Or with uvicorn directly
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

## 3. Configuration

### API Keys Setup

1. **Exchange APIs**
   - Create accounts on supported exchanges (Binance, Coinbase)
   - Generate API keys with trading permissions
   - Add keys to `config/settings.yaml` or environment variables

2. **TradingView Integration**
   - Set up TradingView account
   - Configure webhook URLs
   - Add credentials to configuration

3. **News Sources**
   - Register for news API access (Alpha Vantage, NewsAPI)
   - Configure API keys in settings

### Configuration Files

**Main Configuration**: `config/settings.yaml`
```yaml
# Trading mode: paper or live
trading:
  mode: "paper"
  
# Exchange configuration
data_sources:
  binance:
    api_key: "your-api-key"
    api_secret: "your-api-secret"
    sandbox: true
```

**Environment Variables**: `.env`
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/trading_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
JWT_SECRET=your-secret-key
```

## 4. First Run

### 1. Health Check
```bash
# Check if services are running
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "trading_engine": "initialized",
  "database": "connected",
  "redis": "connected"
}
```

### 2. Access Dashboard
- Open browser: `http://localhost:8000`
- Default login: admin/admin (change immediately)
- Explore the dashboard interface

### 3. Paper Trading Test
```bash
# Start paper trading
curl -X POST http://localhost:8000/api/v1/trading/start \
  -H "Content-Type: application/json" \
  -d '{"mode": "paper"}'

# Check positions
curl http://localhost:8000/api/v1/positions
```

## 5. Basic Usage

### Strategy Management

1. **Enable Strategies**
```python
# Via API
import requests

response = requests.post(
    "http://localhost:8000/api/v1/strategies/enable",
    json={"strategy": "ict", "enabled": True}
)
```

2. **Monitor Performance**
```bash
# Get strategy performance
curl http://localhost:8000/api/v1/strategies/performance

# Get trade history
curl http://localhost:8000/api/v1/trades?limit=10
```

### Data Management

1. **Historical Data Import**
```bash
# Import historical data
python scripts/import_historical_data.py --symbol BTCUSDT --days 365
```

2. **Real-time Data**
```bash
# Start real-time data feeds
curl -X POST http://localhost:8000/api/v1/data/start-feeds
```

## 6. Monitoring & Debugging

### Logs
```bash
# Application logs
tail -f logs/trading_bot.log

# Trading-specific logs
tail -f logs/trading/trades.log

# Error logs
tail -f logs/application/errors.log
```

### Metrics Dashboard
- **Grafana**: `http://localhost:3000` (admin/admin)
- **Prometheus**: `http://localhost:9090`
- **Trading Dashboard**: `http://localhost:8000/dashboard`

### Common Issues

1. **Database Connection Error**
```bash
# Check PostgreSQL status
docker-compose ps postgres

# Restart database
docker-compose restart postgres
```

2. **API Rate Limits**
```bash
# Check rate limit status
curl http://localhost:8000/api/v1/status/rate-limits
```

3. **Memory Issues**
```bash
# Monitor memory usage
docker stats trading-bot-app

# Restart if needed
docker-compose restart trading-bot
```

## 7. Development Workflow

### Code Structure
```
src/
├── core/           # Core engine and utilities
├── strategies/     # Trading strategies
├── analysis/       # Technical analysis
├── data/          # Data management
├── integrations/  # External APIs
├── ui/            # User interface
└── utils/         # Helper functions
```

### Testing
```bash
# Run all tests
pytest

# Run specific test category
pytest tests/unit/
pytest tests/integration/

# Run with coverage
pytest --cov=src tests/
```

### Code Quality
```bash
# Format code
black src/

# Lint code
flake8 src/

# Type checking
mypy src/
```

## 8. Production Deployment

### AWS Deployment
```bash
# Deploy infrastructure
cd terraform/
terraform init
terraform plan
terraform apply

# Deploy application
docker build -t trading-bot .
docker tag trading-bot:latest your-ecr-repo/trading-bot:latest
docker push your-ecr-repo/trading-bot:latest
```

### Environment Setup
1. **Production Configuration**
   - Use environment-specific config files
   - Enable SSL/TLS encryption
   - Configure monitoring and alerting

2. **Security Checklist**
   - Change default passwords
   - Enable API authentication
   - Configure firewall rules
   - Set up backup procedures

## 9. Support & Resources

### Documentation
- [API Documentation](api.md)
- [Trading Concepts](trading-concepts.md)
- [Architecture Guide](architecture.md)
- [Troubleshooting](troubleshooting.md)

### Community
- GitHub Issues: Report bugs and feature requests
- Discord Server: Real-time community support
- Documentation Wiki: Community-contributed guides

### Professional Support
- Email: support@trading-bot.com
- Priority Support: Available for enterprise users
- Custom Development: Contact for custom features

## 10. Next Steps

1. **Complete Configuration**
   - Set up all required API keys
   - Configure risk management parameters
   - Test paper trading functionality

2. **Strategy Development**
   - Study ICT and SMC concepts
   - Backtest strategies with historical data
   - Optimize strategy parameters

3. **Live Trading Preparation**
   - Extensive paper trading
   - Risk management validation
   - Performance monitoring setup

4. **Continuous Improvement**
   - Monitor strategy performance
   - Analyze trade results
   - Refine and optimize strategies
