# database.py
"""
Database models and operations for Portfolio Analysis Platform
Supports SQLite (local), Firebase (cloud), and PostgreSQL (production)
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from typing import List, Dict, Any, Optional
import json

Base = declarative_base()


# ==================== DATABASE MODELS ====================

class User(Base):
    """User account information"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    portfolios = relationship("Portfolio", back_populates="user")


class Portfolio(Base):
    """User's portfolio container"""
    __tablename__ = "portfolios"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False, default="My Portfolio")
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="portfolios")
    holdings = relationship("Holding", back_populates="portfolio", cascade="all, delete-orphan")
    snapshots = relationship("PortfolioSnapshot", back_populates="portfolio", cascade="all, delete-orphan")


class Holding(Base):
    """Individual stock holdings in a portfolio"""
    __tablename__ = "holdings"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    symbol = Column(String, nullable=False, index=True)
    quantity = Column(Float, nullable=False)
    average_price = Column(Float, nullable=False)
    purchase_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="holdings")
    
    @property
    def total_investment(self) -> float:
        """Calculate total investment amount"""
        return self.quantity * self.average_price


class StockPrice(Base):
    """Real-time and historical stock price data"""
    __tablename__ = "stock_prices"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    open = Column(Float, nullable=True)
    high = Column(Float, nullable=True)
    low = Column(Float, nullable=True)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=True)
    ltp = Column(Float, nullable=False)  # Last Traded Price
    change_percent = Column(Float, nullable=True)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "ltp": self.ltp,
            "change_percent": self.change_percent,
        }


class StockFundamentals(Base):
    """Fundamental data for stocks"""
    __tablename__ = "stock_fundamentals"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, nullable=False, index=True)
    company_name = Column(String, nullable=True)
    sector = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    market_cap = Column(Float, nullable=True)
    pe_ratio = Column(Float, nullable=True)
    pb_ratio = Column(Float, nullable=True)
    dividend_yield = Column(Float, nullable=True)
    beta = Column(Float, nullable=True)
    week_52_high = Column(Float, nullable=True)
    week_52_low = Column(Float, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "company_name": self.company_name,
            "sector": self.sector,
            "industry": self.industry,
            "market_cap": self.market_cap,
            "pe_ratio": self.pe_ratio,
            "pb_ratio": self.pb_ratio,
            "dividend_yield": self.dividend_yield,
            "beta": self.beta,
            "week_52_high": self.week_52_high,
            "week_52_low": self.week_52_low,
        }


class PortfolioSnapshot(Base):
    """Daily snapshots of portfolio performance"""
    __tablename__ = "portfolio_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    total_value = Column(Float, nullable=False)
    total_investment = Column(Float, nullable=False)
    total_pnl = Column(Float, nullable=False)
    total_pnl_percent = Column(Float, nullable=False)
    day_change = Column(Float, nullable=True)
    day_change_percent = Column(Float, nullable=True)
    risk_score = Column(Float, nullable=True)
    sharpe_ratio = Column(Float, nullable=True)
    volatility = Column(Float, nullable=True)
    beta = Column(Float, nullable=True)
    holdings_data = Column(Text, nullable=True)  # JSON string of holdings details
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="snapshots")
    
    def get_holdings_data(self) -> Dict[str, Any]:
        """Parse holdings data from JSON"""
        if self.holdings_data:
            return json.loads(self.holdings_data)
        return {}
    
    def set_holdings_data(self, data: Dict[str, Any]):
        """Store holdings data as JSON"""
        self.holdings_data = json.dumps(data)


class RiskAnalysis(Base):
    """Risk analysis results for portfolios"""
    __tablename__ = "risk_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    risk_score = Column(Float, nullable=False)  # 0-10 scale
    risk_level = Column(String, nullable=False)  # Very Low, Low, Moderate, High, Very High
    volatility = Column(Float, nullable=False)
    sharpe_ratio = Column(Float, nullable=True)
    sortino_ratio = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)
    var_95 = Column(Float, nullable=True)
    cvar_95 = Column(Float, nullable=True)
    beta = Column(Float, nullable=True)
    correlation_matrix = Column(Text, nullable=True)  # JSON
    top_risks = Column(Text, nullable=True)  # JSON array of risky stocks
    recommendations = Column(Text, nullable=True)  # JSON array of recommendations


# ==================== DATABASE MANAGER ====================

class DatabaseManager:
    """Manages database connections and operations"""
    
    def __init__(self, database_url: str = "sqlite:///portfolio_data.db"):
        # Configure connection pool to prevent exhaustion
        self.engine = create_engine(
            database_url, 
            echo=False,
            pool_size=20,  # Increase pool size
            max_overflow=40,  # Allow more overflow connections
            pool_timeout=60,  # Increase timeout
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=3600  # Recycle connections after 1 hour
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        """Get a database session"""
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()
    
    def create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(bind=self.engine)
    
    def drop_tables(self):
        """Drop all database tables"""
        Base.metadata.drop_all(bind=self.engine)
    
    # ==================== USER OPERATIONS ====================
    
    def create_user(self, email: str, name: str) -> User:
        """Create a new user"""
        session = next(self.get_session())
        user = User(email=email, name=name)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    
    def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        session = next(self.get_session())
        return session.query(User).filter(User.id == user_id).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        session = next(self.get_session())
        return session.query(User).filter(User.email == email).first()
    
    # ==================== PORTFOLIO OPERATIONS ====================
    
    def create_portfolio(self, user_id: int, name: str = "My Portfolio", description: str = None) -> Portfolio:
        """Create a new portfolio"""
        session = next(self.get_session())
        portfolio = Portfolio(user_id=user_id, name=name, description=description)
        session.add(portfolio)
        session.commit()
        session.refresh(portfolio)
        return portfolio
    
    def get_portfolio(self, portfolio_id: int) -> Optional[Portfolio]:
        """Get portfolio by ID"""
        session = next(self.get_session())
        return session.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    
    def get_user_portfolios(self, user_id: int) -> List[Portfolio]:
        """Get all portfolios for a user"""
        session = next(self.get_session())
        return session.query(Portfolio).filter(Portfolio.user_id == user_id, Portfolio.is_active == True).all()
    
    # ==================== HOLDING OPERATIONS ====================
    
    def add_holding(self, portfolio_id: int, symbol: str, quantity: float, 
                   average_price: float, purchase_date: datetime) -> Holding:
        """Add a new holding to portfolio"""
        session = next(self.get_session())
        holding = Holding(
            portfolio_id=portfolio_id,
            symbol=symbol,
            quantity=quantity,
            average_price=average_price,
            purchase_date=purchase_date
        )
        session.add(holding)
        session.commit()
        session.refresh(holding)
        return holding
    
    def get_portfolio_holdings(self, portfolio_id: int) -> List[Holding]:
        """Get all holdings for a portfolio"""
        session = next(self.get_session())
        return session.query(Holding).filter(
            Holding.portfolio_id == portfolio_id,
            Holding.is_active == True
        ).all()
    
    def update_holding(self, holding_id: int, quantity: float = None, 
                      average_price: float = None) -> Optional[Holding]:
        """Update a holding"""
        session = next(self.get_session())
        holding = session.query(Holding).filter(Holding.id == holding_id).first()
        if holding:
            if quantity is not None:
                holding.quantity = quantity
            if average_price is not None:
                holding.average_price = average_price
            holding.updated_at = datetime.utcnow()
            session.commit()
            session.refresh(holding)
        return holding
    
    def delete_holding(self, holding_id: int) -> bool:
        """Delete a holding"""
        session = next(self.get_session())
        holding = session.query(Holding).filter(Holding.id == holding_id).first()
        if holding:
            holding.is_active = False
            session.commit()
            return True
        return False
    
    # ==================== PRICE OPERATIONS ====================
    
    def save_stock_price(self, symbol: str, price_data: Dict[str, Any]) -> StockPrice:
        """Save stock price data"""
        session = next(self.get_session())
        price = StockPrice(
            symbol=symbol,
            timestamp=price_data.get("timestamp", datetime.utcnow()),
            open=price_data.get("open"),
            high=price_data.get("high"),
            low=price_data.get("low"),
            close=price_data.get("close"),
            volume=price_data.get("volume"),
            ltp=price_data.get("ltp", price_data.get("close")),
            change_percent=price_data.get("change_percent")
        )
        session.add(price)
        session.commit()
        session.refresh(price)
        return price
    
    def get_latest_price(self, symbol: str) -> Optional[StockPrice]:
        """Get latest price for a symbol"""
        session = next(self.get_session())
        return session.query(StockPrice).filter(
            StockPrice.symbol == symbol
        ).order_by(StockPrice.timestamp.desc()).first()
    
    def get_historical_prices(self, symbol: str, start_date: datetime, 
                            end_date: datetime = None) -> List[StockPrice]:
        """Get historical prices for a symbol"""
        session = next(self.get_session())
        query = session.query(StockPrice).filter(
            StockPrice.symbol == symbol,
            StockPrice.timestamp >= start_date
        )
        if end_date:
            query = query.filter(StockPrice.timestamp <= end_date)
        return query.order_by(StockPrice.timestamp).all()
    
    # ==================== SNAPSHOT OPERATIONS ====================
    
    def save_portfolio_snapshot(self, portfolio_id: int, snapshot_data: Dict[str, Any]) -> PortfolioSnapshot:
        """Save portfolio snapshot"""
        session = next(self.get_session())
        snapshot = PortfolioSnapshot(
            portfolio_id=portfolio_id,
            timestamp=snapshot_data.get("timestamp", datetime.utcnow()),
            total_value=snapshot_data["total_value"],
            total_investment=snapshot_data["total_investment"],
            total_pnl=snapshot_data["total_pnl"],
            total_pnl_percent=snapshot_data["total_pnl_percent"],
            day_change=snapshot_data.get("day_change"),
            day_change_percent=snapshot_data.get("day_change_percent"),
            risk_score=snapshot_data.get("risk_score"),
            sharpe_ratio=snapshot_data.get("sharpe_ratio"),
            volatility=snapshot_data.get("volatility"),
            beta=snapshot_data.get("beta"),
        )
        if "holdings_data" in snapshot_data:
            snapshot.set_holdings_data(snapshot_data["holdings_data"])
        session.add(snapshot)
        session.commit()
        session.refresh(snapshot)
        return snapshot
    
    def get_portfolio_snapshots(self, portfolio_id: int, limit: int = 365) -> List[PortfolioSnapshot]:
        """Get portfolio snapshots"""
        session = next(self.get_session())
        return session.query(PortfolioSnapshot).filter(
            PortfolioSnapshot.portfolio_id == portfolio_id
        ).order_by(PortfolioSnapshot.timestamp.desc()).limit(limit).all()


# ==================== INITIALIZE DATABASE ====================

def init_database(database_url: str = "sqlite:///portfolio_data.db") -> DatabaseManager:
    """Initialize database and return manager"""
    db_manager = DatabaseManager(database_url)
    db_manager.create_tables()
    return db_manager


# Global database manager instance
db_manager = init_database()
