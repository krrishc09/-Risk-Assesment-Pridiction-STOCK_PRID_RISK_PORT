# main_platform.py
"""
Real-Time Portfolio Analysis Platform - Main API
FastAPI backend with WebSocket support for live updates
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import asyncio
import json
import logging

from config_platform import API_TITLE, API_VERSION, API_DESCRIPTION, CORS_ORIGINS
from database import db_manager, User, Portfolio, Holding
from data_stream import streamer, subscribe_to_symbols, get_live_price, start_streaming, fetch_historical_data
from portfolio_engine import PortfolioTracker, PortfolioCalculator, RiskAnalyzer
from risk_models import StockRiskModel, PortfolioRiskModel
from prediction_models import StockPredictionModel, PortfolioPredictionModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== FASTAPI APP ====================

app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=API_DESCRIPTION,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== PYDANTIC MODELS ====================

class UserCreate(BaseModel):
    email: str  # Changed from EmailStr to avoid email-validator dependency
    name: str


class PortfolioCreate(BaseModel):
    name: str = "My Portfolio"
    description: Optional[str] = None


class HoldingCreate(BaseModel):
    symbol: str
    quantity: float
    average_price: float
    purchase_date: datetime


class HoldingUpdate(BaseModel):
    quantity: Optional[float] = None
    average_price: Optional[float] = None


# ==================== WEBSOCKET CONNECTION MANAGER ====================

class ConnectionManager:
    """Manage WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.portfolio_subscriptions: dict = {}  # {portfolio_id: [websockets]}
    
    async def connect(self, websocket: WebSocket, portfolio_id: int):
        await websocket.accept()
        self.active_connections.append(websocket)
        
        if portfolio_id not in self.portfolio_subscriptions:
            self.portfolio_subscriptions[portfolio_id] = []
        self.portfolio_subscriptions[portfolio_id].append(websocket)
        
        logger.info(f"Client connected to portfolio {portfolio_id}")
    
    def disconnect(self, websocket: WebSocket, portfolio_id: int):
        self.active_connections.remove(websocket)
        if portfolio_id in self.portfolio_subscriptions:
            self.portfolio_subscriptions[portfolio_id].remove(websocket)
        logger.info(f"Client disconnected from portfolio {portfolio_id}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)
    
    async def broadcast_to_portfolio(self, message: dict, portfolio_id: int):
        if portfolio_id in self.portfolio_subscriptions:
            for connection in self.portfolio_subscriptions[portfolio_id]:
                try:
                    await connection.send_json(message)
                except:
                    pass


manager = ConnectionManager()


# ==================== STARTUP/SHUTDOWN EVENTS ====================

async def populate_initial_prices():
    """Populate initial stock prices in background"""
    try:
        from database import DatabaseManager, StockPrice
        from data_stream import fetch_historical_data
        from datetime import datetime
        
        db = DatabaseManager()
        session = db.SessionLocal()
        
        try:
            # Get all unique symbols from holdings
            holdings = session.execute("SELECT DISTINCT symbol FROM holdings").fetchall()
            
            for (symbol,) in holdings:
                # Check if we have recent price data
                existing = session.query(StockPrice).filter(
                    StockPrice.symbol == symbol
                ).order_by(StockPrice.timestamp.desc()).first()
                
                # If no price or price is old (>1 day), fetch new
                if not existing or (datetime.now() - existing.timestamp).days > 0:
                    try:
                        hist_data = fetch_historical_data(symbol, period="1d", interval="1d")
                        if hist_data and len(hist_data) > 0:
                            latest = hist_data[-1]
                            
                            if existing:
                                existing.ltp = latest['close']
                                existing.open = latest['open']
                                existing.high = latest['high']
                                existing.low = latest['low']
                                existing.close = latest['close']
                                existing.volume = latest['volume']
                                existing.timestamp = datetime.now()
                            else:
                                price_data = StockPrice(
                                    symbol=symbol,
                                    ltp=latest['close'],
                                    open=latest['open'],
                                    high=latest['high'],
                                    low=latest['low'],
                                    close=latest['close'],
                                    volume=latest['volume'],
                                    timestamp=datetime.now()
                                )
                                session.add(price_data)
                            
                            logger.info(f"Updated price for {symbol}: ${latest['close']:.2f}")
                    except Exception as e:
                        logger.warning(f"Could not fetch price for {symbol}: {e}")
            
            session.commit()
            logger.info("Initial price population completed")
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Error populating initial prices: {e}")


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting up platform...")
    
    # Start data streaming in background (non-blocking)
    asyncio.create_task(streamer.start())
    
    # Start background tasks
    asyncio.create_task(populate_initial_prices())
    asyncio.create_task(periodic_portfolio_updates())
    
    logger.info("Platform started successfully!")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down platform...")
    await streamer.stop()


async def periodic_portfolio_updates():
    """Periodically update portfolio data and broadcast to connected clients"""
    while True:
        try:
            # Update all active portfolios
            for portfolio_id, connections in manager.portfolio_subscriptions.items():
                if connections:
                    try:
                        tracker = PortfolioTracker(portfolio_id)
                        dashboard_data = tracker.get_dashboard_data()
                        
                        await manager.broadcast_to_portfolio({
                            "type": "portfolio_update",
                            "data": dashboard_data
                        }, portfolio_id)
                    except Exception as e:
                        logger.error(f"Error updating portfolio {portfolio_id}: {e}")
            
            await asyncio.sleep(5)  # Update every 5 seconds
        
        except Exception as e:
            logger.error(f"Error in periodic updates: {e}")
            await asyncio.sleep(5)


# ==================== ROOT & HEALTH ENDPOINTS ====================

@app.get("/")
def root():
    return {
        "message": "Real-Time Portfolio Analysis Platform",
        "version": API_VERSION,
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "users": "/api/users",
            "portfolios": "/api/portfolios",
            "live_prices": "/api/live-prices",
            "websocket": "/ws/portfolio/{portfolio_id}",
        }
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "version": API_VERSION,
        "timestamp": datetime.now().isoformat(),
        "streaming": streamer.is_running,
        "active_connections": len(manager.active_connections),
    }


# ==================== USER ENDPOINTS ====================

@app.post("/api/users", response_model=dict)
def create_user(user: UserCreate):
    """Create a new user"""
    try:
        # Check if user exists
        existing_user = db_manager.get_user_by_email(user.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="User already exists")
        
        new_user = db_manager.create_user(user.email, user.name)
        return {
            "id": new_user.id,
            "email": new_user.email,
            "name": new_user.name,
            "created_at": new_user.created_at.isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/users/{user_id}")
def get_user(user_id: int):
    """Get user by ID"""
    user = db_manager.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "created_at": user.created_at.isoformat(),
    }


# ==================== PORTFOLIO ENDPOINTS ====================

@app.get("/api/portfolios")
def get_all_portfolios():
    """Get all portfolios"""
    try:
        session = db_manager.get_session()
        portfolios = session.query(Portfolio).all()
        return [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "created_at": p.created_at.isoformat() if p.created_at else None
            }
            for p in portfolios
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@app.post("/api/portfolios", response_model=dict)
def create_portfolio(portfolio: PortfolioCreate, user_id: int = Query(...)):
    """Create a new portfolio"""
    try:
        new_portfolio = db_manager.create_portfolio(
            user_id=user_id,
            name=portfolio.name,
            description=portfolio.description
        )
        return {
            "id": new_portfolio.id,
            "user_id": new_portfolio.user_id,
            "name": new_portfolio.name,
            "description": new_portfolio.description,
            "created_at": new_portfolio.created_at.isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/portfolios/{portfolio_id}")
def get_portfolio(portfolio_id: int):
    """Get portfolio details"""
    portfolio = db_manager.get_portfolio(portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    return {
        "id": portfolio.id,
        "user_id": portfolio.user_id,
        "name": portfolio.name,
        "description": portfolio.description,
        "created_at": portfolio.created_at.isoformat(),
        "updated_at": portfolio.updated_at.isoformat(),
    }


@app.get("/api/users/{user_id}/portfolios")
def get_user_portfolios(user_id: int):
    """Get all portfolios for a user"""
    portfolios = db_manager.get_user_portfolios(user_id)
    return [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "created_at": p.created_at.isoformat(),
        }
        for p in portfolios
    ]


# ==================== HOLDING ENDPOINTS ====================

@app.post("/api/portfolios/{portfolio_id}/holdings")
def add_holding(portfolio_id: int, holding: HoldingCreate):
    """Add a new holding to portfolio"""
    try:
        new_holding = db_manager.add_holding(
            portfolio_id=portfolio_id,
            symbol=holding.symbol.upper(),
            quantity=holding.quantity,
            average_price=holding.average_price,
            purchase_date=holding.purchase_date
        )
        
        # Subscribe to symbol for real-time updates
        subscribe_to_symbols([holding.symbol.upper()])
        
        return {
            "id": new_holding.id,
            "portfolio_id": new_holding.portfolio_id,
            "symbol": new_holding.symbol,
            "quantity": new_holding.quantity,
            "average_price": new_holding.average_price,
            "purchase_date": new_holding.purchase_date.isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/portfolios/{portfolio_id}/holdings")
def get_holdings(portfolio_id: int):
    """Get all holdings for a portfolio"""
    holdings = db_manager.get_portfolio_holdings(portfolio_id)
    return [
        {
            "id": h.id,
            "symbol": h.symbol,
            "quantity": h.quantity,
            "average_price": h.average_price,
            "purchase_date": h.purchase_date.isoformat(),
            "total_investment": h.total_investment,
        }
        for h in holdings
    ]


@app.put("/api/holdings/{holding_id}")
def update_holding(holding_id: int, holding: HoldingUpdate):
    """Update a holding"""
    updated = db_manager.update_holding(
        holding_id=holding_id,
        quantity=holding.quantity,
        average_price=holding.average_price
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Holding not found")
    
    return {
        "id": updated.id,
        "symbol": updated.symbol,
        "quantity": updated.quantity,
        "average_price": updated.average_price,
    }


@app.delete("/api/holdings/{holding_id}")
def delete_holding(holding_id: int):
    """Delete a holding"""
    success = db_manager.delete_holding(holding_id)
    if not success:
        raise HTTPException(status_code=404, detail="Holding not found")
    
    return {"message": "Holding deleted successfully"}


# ==================== DASHBOARD ENDPOINTS ====================

@app.get("/api/portfolios/{portfolio_id}/dashboard")
def get_dashboard(portfolio_id: int):
    """Get complete dashboard data for a portfolio"""
    try:
        tracker = PortfolioTracker(portfolio_id)
        return tracker.get_dashboard_data()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/portfolios/{portfolio_id}/summary")
def get_portfolio_summary(portfolio_id: int):
    """Get portfolio summary"""
    try:
        calculator = PortfolioCalculator(portfolio_id)
        return calculator.calculate_portfolio_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/portfolios/{portfolio_id}/risk-analysis")
def get_risk_analysis(portfolio_id: int, period: str = Query("1y")):
    """Get risk analysis for a portfolio"""
    try:
        analyzer = RiskAnalyzer(portfolio_id)
        return analyzer.get_complete_analysis()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/portfolios/{portfolio_id}/performance")
def get_performance_chart(portfolio_id: int, period: str = Query("1M")):
    """Get performance chart data"""
    try:
        tracker = PortfolioTracker(portfolio_id)
        return tracker.get_performance_chart_data(period)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== LIVE PRICE ENDPOINTS ====================

@app.get("/api/live-prices/{symbol}")
def get_live_price_endpoint(symbol: str):
    """Get live price for a symbol"""
    price_data = get_live_price(symbol.upper())
    if not price_data:
        raise HTTPException(status_code=404, detail="Price data not available")
    
    return price_data


@app.get("/api/live-prices")
def get_multiple_live_prices(symbols: str = Query(..., description="Comma-separated symbols")):
    """Get live prices for multiple symbols"""
    symbol_list = [s.strip().upper() for s in symbols.split(",")]
    prices = {}
    
    for symbol in symbol_list:
        price_data = get_live_price(symbol)
        if price_data:
            prices[symbol] = price_data
    
    return prices


# ==================== WEBSOCKET ENDPOINT ====================

@app.websocket("/ws/portfolio/{portfolio_id}")
async def websocket_portfolio(websocket: WebSocket, portfolio_id: int):
    """WebSocket endpoint for real-time portfolio updates"""
    await manager.connect(websocket, portfolio_id)
    
    try:
        # Subscribe to all symbols in portfolio
        holdings = db_manager.get_portfolio_holdings(portfolio_id)
        symbols = [h.symbol for h in holdings]
        subscribe_to_symbols(symbols)
        
        # Send initial data
        tracker = PortfolioTracker(portfolio_id)
        initial_data = tracker.get_dashboard_data()
        await manager.send_personal_message({
            "type": "initial_data",
            "data": initial_data
        }, websocket)
        
        # Keep connection alive and handle messages
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "ping":
                await manager.send_personal_message({"type": "pong"}, websocket)
            elif message.get("type") == "refresh":
                dashboard_data = tracker.get_dashboard_data()
                await manager.send_personal_message({
                    "type": "portfolio_update",
                    "data": dashboard_data
                }, websocket)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, portfolio_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, portfolio_id)


# ==================== RISK MODEL ENDPOINTS ====================

@app.get("/api/stock-risk/{symbol}")
def get_stock_risk_model(
    symbol: str,
    period: str = Query("1y", description="Analysis period")
):
    """Get comprehensive risk analysis for a single stock"""
    try:
        model = StockRiskModel(symbol.upper(), period)
        return model.calculate_all_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/portfolios/{portfolio_id}/risk-model")
def get_portfolio_risk_model(portfolio_id: int, period: str = Query("1y")):
    """Get comprehensive portfolio risk model"""
    try:
        # Get holdings with weights
        calculator = PortfolioCalculator(portfolio_id)
        summary = calculator.calculate_portfolio_summary()
        
        holdings_with_weights = [
            {
                "symbol": h['symbol'],
                "weight": h['weight']
            }
            for h in summary['holdings']
        ]
        
        model = PortfolioRiskModel(holdings_with_weights, period)
        return model.calculate_all_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== PREDICTION MODEL ENDPOINTS ====================

@app.get("/api/predict/{symbol}")
def predict_stock(
    symbol: str,
    period: str = Query("1y", description="Historical data period for analysis")
):
    """Get stock price predictions and trading signals"""
    try:
        model = StockPredictionModel(symbol.upper(), period)
        return model.predict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/portfolios/{portfolio_id}/predict")
def predict_portfolio(portfolio_id: int):
    """Get portfolio predictions and opportunities"""
    try:
        # Get holdings with weights
        calculator = PortfolioCalculator(portfolio_id)
        summary = calculator.calculate_portfolio_summary()
        
        holdings_with_weights = [
            {
                "symbol": h['symbol'],
                "weight": h['weight']
            }
            for h in summary['holdings']
        ]
        
        model = PortfolioPredictionModel(holdings_with_weights)
        return model.predict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== HISTORICAL DATA ENDPOINT ====================

@app.get("/api/historical/{symbol}")
def get_historical_data_endpoint(
    symbol: str,
    period: str = Query("1y", description="Period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max"),
    interval: str = Query("1d", description="Interval: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo")
):
    """Get historical data for a symbol"""
    try:
        data = fetch_historical_data(symbol.upper(), period, interval)
        return {
            "symbol": symbol.upper(),
            "period": period,
            "interval": interval,
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/prediction-accuracy/{symbol}")
def get_prediction_accuracy(symbol: str):
    """Get prediction accuracy metrics for a symbol"""
    try:
        from prediction_tracker import tracker
        accuracy = tracker.get_accuracy_metrics(symbol=symbol.upper())
        return accuracy
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/prediction-history/{symbol}")
def get_prediction_history(symbol: str, limit: int = Query(10, description="Number of records")):
    """Get recent predictions with actuals for comparison"""
    try:
        from prediction_tracker import tracker
        history = tracker.get_recent_predictions_with_actuals(symbol.upper(), limit)
        return {"symbol": symbol.upper(), "predictions": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/model-performance")
def get_model_performance():
    """Get overall model performance across all predictions"""
    try:
        from prediction_tracker import tracker
        
        # Get accuracy for each horizon
        accuracy_1d = tracker.get_accuracy_metrics(horizon_days=1)
        accuracy_5d = tracker.get_accuracy_metrics(horizon_days=5)
        accuracy_30d = tracker.get_accuracy_metrics(horizon_days=30)
        overall = tracker.get_accuracy_metrics()
        
        return {
            "overall": overall,
            "by_horizon": {
                "1_day": accuracy_1d,
                "5_day": accuracy_5d,
                "30_day": accuracy_30d
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== PORTFOLIO OPTIMIZATION ENDPOINTS ====================

@app.get("/api/portfolios/{portfolio_id}/optimize")
def get_portfolio_optimization(portfolio_id: int):
    """Get portfolio optimization recommendations"""
    try:
        from portfolio_optimizer import optimize_portfolio_endpoint
        
        logger.info(f"Optimization requested for portfolio {portfolio_id}")
        
        # Get portfolio object from database
        portfolio = db_manager.get_portfolio(portfolio_id)
        if not portfolio:
            logger.error(f"Portfolio {portfolio_id} not found")
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        holdings = portfolio.holdings
        logger.info(f"Portfolio has {len(holdings)} holdings")
        
        if not holdings or len(holdings) < 2:
            logger.warning(f"Insufficient holdings for optimization: {len(holdings)}")
            return {
                "error": f"Portfolio optimization requires at least 2 stocks. Your portfolio has {len(holdings)} stock(s). Please add more holdings."
            }
        
        symbols = [h.symbol for h in holdings]
        logger.info(f"Optimizing portfolio with symbols: {symbols}")
        
        holdings_data = [{
            'symbol': h.symbol,
            'current_value': h.quantity * h.average_price
        } for h in holdings]
        
        result = optimize_portfolio_endpoint(symbols, holdings_data)
        
        if result and 'error' in result:
            logger.warning(f"Optimization returned error: {result['error']}")
        else:
            logger.info("Optimization completed successfully")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in portfolio optimization: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/test-optimize")
def test_optimization():
    """Test optimization with sample data"""
    try:
        from portfolio_optimizer import PortfolioOptimizer
        
        # Test with common stocks
        symbols = ['AAPL', 'MSFT', 'GOOGL']
        optimizer = PortfolioOptimizer(symbols, period="1y")
        
        logger.info("Testing optimization with AAPL, MSFT, GOOGL")
        
        if not optimizer.fetch_data():
            return {"error": "Failed to fetch data for test symbols"}
        
        max_sharpe = optimizer.optimize_sharpe()
        
        if max_sharpe:
            return {
                "success": True,
                "message": "Optimization working correctly",
                "test_result": max_sharpe
            }
        else:
            return {"error": "Optimization failed"}
            
    except Exception as e:
        logger.error(f"Test optimization error: {e}", exc_info=True)
        return {"error": str(e)}


# ==================== ALERTS ENDPOINTS ====================

@app.get("/api/alerts")
def get_alerts_endpoint(unread_only: bool = Query(False), symbol: Optional[str] = None):
    """Get all alerts"""
    try:
        from alerts_system import get_alerts
        return {"alerts": get_alerts(unread_only=unread_only, symbol=symbol)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/alerts/summary")
def get_alerts_summary():
    """Get alert summary"""
    try:
        from alerts_system import get_alert_summary
        return get_alert_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/alerts/price")
def create_price_alert(
    symbol: str = Query(...),
    threshold: float = Query(...),
    alert_type: str = Query("above", description="'above' or 'below'")
):
    """Create a price alert"""
    try:
        from alerts_system import create_price_alert
        rule_id = create_price_alert(symbol, threshold, alert_type)
        return {"success": True, "rule_id": rule_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/alerts/change")
def create_change_alert(
    symbol: str = Query(...),
    threshold_percent: float = Query(5.0)
):
    """Create a percentage change alert"""
    try:
        from alerts_system import create_change_alert
        rule_id = create_change_alert(symbol, threshold_percent)
        return {"success": True, "rule_id": rule_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/alerts/{alert_id}/read")
def mark_alert_read(alert_id: str):
    """Mark alert as read"""
    try:
        from alerts_system import mark_alert_read
        success = mark_alert_read(alert_id)
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/alerts/rules")
def get_alert_rules(symbol: Optional[str] = None):
    """Get alert rules"""
    try:
        from alerts_system import alerts_manager
        rules = alerts_manager.get_alert_rules(symbol=symbol)
        return {"rules": rules}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== BACKTESTING ENDPOINTS ====================

@app.get("/api/backtest/{symbol}")
def backtest_endpoint(
    symbol: str,
    start_date: str = Query(..., description="YYYY-MM-DD"),
    end_date: str = Query(..., description="YYYY-MM-DD"),
    horizon: int = Query(1, description="Prediction horizon: 1, 5, or 30 days")
):
    """Run backtest for a symbol"""
    try:
        logger.info(f"Backtest requested: {symbol}, {start_date} to {end_date}, horizon={horizon}")
        from backtesting_engine import run_backtest
        result = run_backtest(symbol.upper(), start_date, end_date, horizon)
        
        if result and 'error' in result:
            logger.warning(f"Backtest returned error: {result['error']}")
        else:
            logger.info(f"Backtest completed: {result.get('total_predictions', 0)} predictions")
        
        return result
    except Exception as e:
        logger.error(f"Backtest error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/backtest/{symbol}/strategy")
def strategy_backtest_endpoint(
    symbol: str,
    start_date: str = Query(..., description="YYYY-MM-DD"),
    end_date: str = Query(..., description="YYYY-MM-DD"),
    initial_capital: float = Query(10000, description="Starting capital")
):
    """Run strategy backtest with simulated trading"""
    try:
        from backtesting_engine import run_strategy_backtest
        result = run_strategy_backtest(symbol.upper(), start_date, end_date, initial_capital)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
