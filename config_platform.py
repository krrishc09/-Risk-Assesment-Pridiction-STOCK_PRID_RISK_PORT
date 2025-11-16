# config_platform.py
"""
Configuration for Real-Time Portfolio Analysis Platform
Supports multiple broker APIs: Upstox, Zerodha Kite, ICICIDIRECT Breeze
"""

import os
from typing import Dict, Any

# ==================== BROKER API CONFIGURATION ====================
# Choose your broker: 'upstox', 'zerodha', 'breeze', or 'yfinance' (fallback)
BROKER = os.getenv("BROKER", "yfinance")  # Default to yfinance for demo

# Upstox Configuration
UPSTOX_CONFIG = {
    "api_key": os.getenv("UPSTOX_API_KEY", ""),
    "api_secret": os.getenv("UPSTOX_API_SECRET", ""),
    "redirect_uri": os.getenv("UPSTOX_REDIRECT_URI", "http://localhost:8000/callback"),
}

# Zerodha Kite Configuration
ZERODHA_CONFIG = {
    "api_key": os.getenv("ZERODHA_API_KEY", ""),
    "api_secret": os.getenv("ZERODHA_API_SECRET", ""),
    "redirect_uri": os.getenv("ZERODHA_REDIRECT_URI", "http://localhost:8000/callback"),
}

# ICICIDIRECT Breeze Configuration
BREEZE_CONFIG = {
    "api_key": os.getenv("BREEZE_API_KEY", ""),
    "api_secret": os.getenv("BREEZE_API_SECRET", ""),
    "session_token": os.getenv("BREEZE_SESSION_TOKEN", ""),
}

# ==================== DATABASE CONFIGURATION ====================
# Database type: 'sqlite' (local), 'firebase' (cloud), 'postgresql' (production)
DATABASE_TYPE = os.getenv("DATABASE_TYPE", "sqlite")

# SQLite Configuration (Local Development)
SQLITE_DB_PATH = "portfolio_data.db"

# Firebase Configuration (Cloud)
FIREBASE_CONFIG = {
    "credentials_path": os.getenv("FIREBASE_CREDENTIALS", "firebase-credentials.json"),
    "project_id": os.getenv("FIREBASE_PROJECT_ID", ""),
}

# PostgreSQL Configuration (Production)
POSTGRES_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "database": os.getenv("POSTGRES_DB", "portfolio_db"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", ""),
}

# ==================== PLATFORM SETTINGS ====================
# Market Settings
MARKET_TIMEZONE = "Asia/Kolkata"
MARKET_OPEN_TIME = "09:15"
MARKET_CLOSE_TIME = "15:30"
MARKET_DAYS = [0, 1, 2, 3, 4]  # Monday to Friday

# Data Update Frequencies
REALTIME_UPDATE_INTERVAL = 5  # seconds (WebSocket push)
PRICE_CACHE_INTERVAL = 60  # seconds (database update)
EOD_SNAPSHOT_TIME = "15:35"  # End of day snapshot time
HISTORICAL_DATA_REFRESH = 86400  # 24 hours

# Risk Analysis Settings
RISK_FREE_RATE = 0.065  # 6.5% (Indian 10-year G-Sec rate)
BENCHMARK_INDEX = "^NSEI"  # Nifty 50
RISK_LEVELS = {
    "Very Low": (0, 2),
    "Low": (2, 4),
    "Moderate": (4, 6),
    "High": (6, 8),
    "Very High": (8, 10),
}

# Portfolio Metrics
LOOKBACK_PERIODS = {
    "1D": 1,
    "1W": 7,
    "1M": 30,
    "3M": 90,
    "6M": 180,
    "1Y": 365,
    "YTD": "ytd",
    "ALL": "max",
}

# ==================== API SETTINGS ====================
API_TITLE = "Real-Time Portfolio Analysis Platform"
API_VERSION = "3.0"
API_DESCRIPTION = "Comprehensive portfolio tracking, risk analysis, and investment insights"

# CORS Settings
CORS_ORIGINS = [
    "http://localhost:3000",  # React dev server
    "http://localhost:8000",  # FastAPI server
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
]

# WebSocket Settings
WS_HEARTBEAT_INTERVAL = 30  # seconds
WS_RECONNECT_DELAY = 5  # seconds
WS_MAX_RECONNECT_ATTEMPTS = 10

# ==================== CACHE SETTINGS ====================
CACHE_ENABLED = True
CACHE_TYPE = "memory"  # 'memory', 'redis'
CACHE_TTL = {
    "realtime_prices": 5,
    "portfolio_summary": 30,
    "risk_analysis": 300,
    "historical_data": 3600,
}

# Redis Configuration (if using Redis cache)
REDIS_CONFIG = {
    "host": os.getenv("REDIS_HOST", "localhost"),
    "port": int(os.getenv("REDIS_PORT", "6379")),
    "db": int(os.getenv("REDIS_DB", "0")),
    "password": os.getenv("REDIS_PASSWORD", None),
}

# ==================== LOGGING SETTINGS ====================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = "platform.log"

# ==================== SECURITY SETTINGS ====================
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION = 3600  # 1 hour

# ==================== RISK ANALYSIS SETTINGS (from config.py) ====================
# Annualization Factors
PERIODS_PER_YEAR_MAPPING = {
    "1d": 252,   # Trading days per year
    "1wk": 52,   # Weeks per year
    "1mo": 12    # Months per year
}

# Valid Periods and Intervals
VALID_PERIODS = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]
VALID_INTERVALS = ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"]

# Popular Benchmarks
BENCHMARKS_DICT = {
    "SP500": "^GSPC",
    "NASDAQ": "^IXIC",
    "DOW": "^DJI",
    "RUSSELL2000": "^RUT",
    "NIFTY50": "^NSEI",
}

# ==================== HELPER FUNCTIONS ====================
def get_broker_config() -> Dict[str, Any]:
    """Get the active broker configuration"""
    configs = {
        "upstox": UPSTOX_CONFIG,
        "zerodha": ZERODHA_CONFIG,
        "breeze": BREEZE_CONFIG,
    }
    return configs.get(BROKER, {})


def is_market_open() -> bool:
    """Check if market is currently open"""
    from datetime import datetime
    import pytz
    
    tz = pytz.timezone(MARKET_TIMEZONE)
    now = datetime.now(tz)
    
    # Check if it's a trading day
    if now.weekday() not in MARKET_DAYS:
        return False
    
    # Check if it's within trading hours
    market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
    
    return market_open <= now <= market_close


def get_database_url() -> str:
    """Get database connection URL based on configuration"""
    if DATABASE_TYPE == "sqlite":
        return f"sqlite:///{SQLITE_DB_PATH}"
    elif DATABASE_TYPE == "postgresql":
        return f"postgresql://{POSTGRES_CONFIG['user']}:{POSTGRES_CONFIG['password']}@{POSTGRES_CONFIG['host']}:{POSTGRES_CONFIG['port']}/{POSTGRES_CONFIG['database']}"
    return ""
