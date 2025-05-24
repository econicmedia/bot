# Database Setup Guide

This guide helps you set up PostgreSQL for the AI Trading Bot in different environments.

## Option 1: Docker Setup (Recommended)

### Prerequisites
- Docker Desktop installed and running
- Docker Compose available

### Steps
1. **Start PostgreSQL with Docker:**
   ```bash
   docker compose up postgres -d
   ```

2. **Verify PostgreSQL is running:**
   ```bash
   docker ps
   ```
   You should see `trading-postgres` container running.

3. **Test database connection:**
   ```bash
   python setup_database.py
   ```

### Database Details
- **Host:** localhost
- **Port:** 5432
- **Database:** trading_db
- **Username:** trading_user
- **Password:** trading_pass

## Option 2: Local PostgreSQL Installation

### Windows Installation

1. **Download PostgreSQL:**
   - Go to https://www.postgresql.org/download/windows/
   - Download PostgreSQL 15+ installer
   - Run the installer with default settings

2. **Create Database and User:**
   ```sql
   -- Connect to PostgreSQL as postgres user
   psql -U postgres

   -- Create database
   CREATE DATABASE trading_db;

   -- Create user
   CREATE USER trading_user WITH PASSWORD 'trading_pass';

   -- Grant privileges
   GRANT ALL PRIVILEGES ON DATABASE trading_db TO trading_user;
   GRANT ALL ON SCHEMA public TO trading_user;

   -- Exit
   \q
   ```

3. **Initialize Database Schema:**
   ```bash
   psql -U trading_user -d trading_db -f sql/init.sql
   ```

### macOS Installation

1. **Install with Homebrew:**
   ```bash
   brew install postgresql@15
   brew services start postgresql@15
   ```

2. **Create Database and User:**
   ```bash
   createdb trading_db
   psql trading_db
   ```
   
   Then run the SQL commands from the Windows section.

### Linux Installation

1. **Ubuntu/Debian:**
   ```bash
   sudo apt update
   sudo apt install postgresql postgresql-contrib
   sudo systemctl start postgresql
   sudo systemctl enable postgresql
   ```

2. **CentOS/RHEL:**
   ```bash
   sudo yum install postgresql-server postgresql-contrib
   sudo postgresql-setup initdb
   sudo systemctl start postgresql
   sudo systemctl enable postgresql
   ```

3. **Create Database and User:**
   ```bash
   sudo -u postgres psql
   ```
   
   Then run the SQL commands from the Windows section.

## Testing the Setup

### 1. Run Database Setup Script
```bash
python setup_database.py
```

This script will:
- Test database connectivity
- Verify table creation
- Test basic operations

### 2. Run Paper Trading Tests
```bash
python test_paper_trading.py
```

This script will:
- Create test trading data
- Test order management
- Test position tracking
- Calculate performance metrics

### 3. Start the Trading Bot
```bash
python src/main.py
```

## Troubleshooting

### Connection Issues

1. **Check PostgreSQL is running:**
   ```bash
   # Docker
   docker ps | grep postgres
   
   # Local installation
   sudo systemctl status postgresql  # Linux
   brew services list | grep postgresql  # macOS
   ```

2. **Check connection settings in .env file:**
   ```
   DATABASE_URL=postgresql://trading_user:trading_pass@localhost:5432/trading_db
   ```

3. **Test connection manually:**
   ```bash
   psql -U trading_user -h localhost -d trading_db
   ```

### Permission Issues

1. **Grant proper permissions:**
   ```sql
   GRANT ALL PRIVILEGES ON DATABASE trading_db TO trading_user;
   GRANT ALL ON SCHEMA public TO trading_user;
   GRANT ALL ON ALL TABLES IN SCHEMA trading TO trading_user;
   GRANT ALL ON ALL SEQUENCES IN SCHEMA trading TO trading_user;
   ```

### Schema Issues

1. **Recreate database schema:**
   ```bash
   psql -U trading_user -d trading_db -f sql/init.sql
   ```

2. **Check if tables exist:**
   ```sql
   \dt trading.*
   ```

## Environment Configuration

### Development (.env)
```
DATABASE_URL=postgresql://trading_user:trading_pass@localhost:5432/trading_db
TRADING_MODE=paper
APP_DEBUG=true
```

### Production
- Use strong passwords
- Enable SSL connections
- Use connection pooling
- Set up backups
- Monitor performance

## Next Steps

1. **Configure Exchange APIs** (for live data)
2. **Set up monitoring** (Grafana/Prometheus)
3. **Configure alerts** (Discord/Telegram)
4. **Run backtests** with historical data
5. **Start paper trading** to validate strategies

## Support

If you encounter issues:
1. Check the logs in `logs/` directory
2. Run diagnostic scripts
3. Verify environment configuration
4. Check database permissions
