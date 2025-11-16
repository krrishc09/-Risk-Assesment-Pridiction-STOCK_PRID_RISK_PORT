# 🚀 Real-Time Portfolio Analysis Platform - Complete Guide

A comprehensive, production-ready platform for real-time portfolio tracking, risk analysis, and ML-based stock predictions.

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Features](#features)
3. [Installation](#installation)
4. [API Endpoints](#api-endpoints)
5. [Risk Models](#risk-models)
6. [Prediction Models](#prediction-models)
7. [Usage Examples](#usage-examples)
8. [Testing](#testing)
9. [Deployment](#deployment)
10. [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

### Installation (3 Steps)

```powershell
# 1. Install dependencies
pip install -r requirements.txt

# 2. Initialize database
python -c "from database import init_database; init_database()"

# 3. Start platform
python main_platform.py
```

**Platform runs at:** http://localhost:8000  
**API Docs:** http://localhost:8000/docs

### Quick Test

```powershell
# In new terminal
python test_all.py
```

---

## ✨ Features

### Core Capabilities

1. **Real-Time Portfolio Tracking**
   - Live price updates (5-second refresh)
   - Real-time P&L calculation
   - WebSocket streaming
   - Historical performance charts

2. **Risk Analysis**
   - Stock risk model (20+ metrics)
   - Portfolio risk model
   - Risk scores (0-10 scale)
   - Concentration analysis

3. **ML-Based Predictions**
   - Price forecasts (1d, 5d, 30d)
   - Trading signals (Buy/Sell/Hold)
   - Trend analysis
   - Technical indicators (RSI, MACD, etc.)

4. **Portfolio Management**
   - Multi-portfolio support
   - Holdings tracking
   - Performance monitoring
   - Rebalancing suggestions

---

## 📦 Installation

### Prerequisites
- Python 3.8+
- Virtual environment
- Internet connection

### Step-by-Step

```powershell
# 1. Activate virtual environment
.venv\Scripts\Activate.ps1

# 2. Install packages
pip install -r requirements.txt

# 3. Initialize database
python -c "from database import init_database; init_database()"

# 4. Start server
python main_platform.py
```

---

## 🌐 API Endpoints

### Portfolio Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/users` | POST | Create user |
| `/api/portfolios` | POST | Create portfolio |
| `/api/portfolios/{id}/holdings` | POST | Add holding |
| `/api/portfolios/{id}/holdings` | GET | List holdings |

### Dashboard & Analytics

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/portfolios/{id}/dashboard` | GET | Complete dashboard |
| `/api/portfolios/{id}/summary` | GET | Portfolio summary |
| `/api/portfolios/{id}/performance` | GET | Performance chart |

### Risk Models

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/stock-risk/{symbol}` | GET | Stock risk analysis |
| `/api/portfolios/{id}/risk-model` | GET | Portfolio risk model |

### Prediction Models

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/predict/{symbol}` | GET | Stock predictions |
| `/api/portfolios/{id}/predict` | GET | Portfolio predictions |

### Live Data

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/live-prices/{symbol}` | GET | Get live price |
| `/api/historical/{symbol}` | GET | Historical data |

### WebSocket

| Endpoint | Protocol | Description |
|----------|----------|-------------|
| `/ws/portfolio/{id}` | WebSocket | Real-time updates |

---

## 📊 Risk Models

### Stock Risk Model

**Metrics Calculated:**
- Volatility, Max Drawdown, VaR, CVaR
- Sharpe, Sortino, Calmar ratios
- Beta, Correlation, Alpha
- Risk score (0-10)

**Example:**
```python
import requests

risk = requests.get("http://localhost:8000/api/stock-risk/AAPL").json()
print(f"Risk Score: {risk['risk_score']}/10")
print(f"Risk Level: {risk['risk_level']}")
```

### Portfolio Risk Model

**Metrics Calculated:**
- Concentration risk
- Weighted volatility
- Diversification ratio
- High-risk stock identification

**Example:**
```python
risk = requests.get("http://localhost:8000/api/portfolios/1/risk-model").json()
print(f"Portfolio Risk: {risk['risk_level']}")
print(f"Concentration: {risk['concentration_risk']:.1f}%")
```

---

## 🔮 Prediction Models

### Stock Predictions

**Features:**
- Price forecasts (1d, 5d, 30d)
- Trading signals (Strong Buy → Strong Sell)
- Trend analysis (Uptrend/Downtrend/Sideways)
- Technical indicators (RSI, MACD, Bollinger Bands)

**Example:**
```python
pred = requests.get("http://localhost:8000/api/predict/AAPL").json()
print(f"Current: ${pred['current_price']:.2f}")
print(f"Predicted (30d): ${pred['predicted_price_30d']:.2f}")
print(f"Signal: {pred['signal']}")
print(f"Trend: {pred['trend']}")
```

### Portfolio Predictions

**Features:**
- Portfolio return forecasts
- Buy/sell opportunities
- Overall outlook (Bullish/Bearish/Neutral)

**Example:**
```python
pred = requests.get("http://localhost:8000/api/portfolios/1/predict").json()
print(f"30d Forecast: {pred['predicted_return_30d']:+.2f}%")
print(f"Outlook: {pred['overall_outlook']}")
```

---

## 💡 Usage Examples

### Example 1: Daily Portfolio Check

```python
import requests

BASE_URL = "http://localhost:8000"

# Get dashboard
dashboard = requests.get(f"{BASE_URL}/api/portfolios/1/dashboard").json()
print(f"Value: ${dashboard['summary']['total_value']:,.2f}")
print(f"P&L: {dashboard['summary']['total_pnl_percent']:+.2f}%")

# Check risk
risk = requests.get(f"{BASE_URL}/api/portfolios/1/risk-model").json()
print(f"Risk: {risk['risk_level']}")

# Get predictions
pred = requests.get(f"{BASE_URL}/api/portfolios/1/predict").json()
print(f"Forecast: {pred['predicted_return_30d']:+.2f}%")
```

### Example 2: Stock Analysis

```python
symbol = "AAPL"

# Get live price
price = requests.get(f"{BASE_URL}/api/live-prices/{symbol}").json()
print(f"Price: ${price['ltp']:.2f}")

# Check risk
risk = requests.get(f"{BASE_URL}/api/stock-risk/{symbol}").json()
print(f"Risk: {risk['risk_score']}/10")

# Get prediction
pred = requests.get(f"{BASE_URL}/api/predict/{symbol}").json()
print(f"Signal: {pred['signal']}")
print(f"Predicted: {pred['price_change_30d_pct']:+.2f}%")
```

### Example 3: Trading Decision

```python
symbol = "AAPL"

# Get prediction
pred = requests.get(f"{BASE_URL}/api/predict/{symbol}").json()

# Get risk
risk = requests.get(f"{BASE_URL}/api/stock-risk/{symbol}").json()

# Decision logic
if pred['signal'] in ['Strong Buy', 'Buy'] and risk['risk_score'] < 7:
    print(f"✅ BUY {symbol}")
elif pred['signal'] in ['Strong Sell', 'Sell']:
    print(f"⚠️ SELL {symbol}")
else:
    print(f"📊 HOLD {symbol}")
```

---

## 🧪 Testing

### Run All Tests

```powershell
python test_all.py
```

### Test Individual Components

```powershell
# Test platform
python test_platform.py

# Test risk models
python test_risk_models.py

# Test predictions
python test_predictions.py
```

### Manual Testing

```powershell
# Health check
curl http://localhost:8000/health

# Get dashboard
curl http://localhost:8000/api/portfolios/1/dashboard

# Stock prediction
curl http://localhost:8000/api/predict/AAPL
```

---

## 🚀 Deployment

### Local Development

```powershell
python main_platform.py
```

### Production (Docker)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "main_platform.py"]
```

```powershell
docker build -t portfolio-platform .
docker run -p 8000:8000 portfolio-platform
```

### Environment Variables

Create `.env` file:
```env
# Database
DATABASE_TYPE=sqlite  # or postgresql

# Broker (optional)
BROKER=yfinance

# Security
SECRET_KEY=your-secret-key-here
```

---

## 🐛 Troubleshooting

### Server won't start

```powershell
# Check port
netstat -ano | findstr :8000

# Use different port
python main_platform.py --port 8001
```

### Module not found

```powershell
pip install -r requirements.txt
```

### No price data

```powershell
# Check internet connection
curl https://finance.yahoo.com

# Verify symbol
curl http://localhost:8000/api/live-prices/AAPL
```

### Database errors

```powershell
# Reinitialize
python -c "from database import db_manager; db_manager.drop_tables(); db_manager.create_tables()"
```

---

## 📊 Key Metrics Explained

### Risk Scores (0-10)
- **0-3**: Low risk
- **3-6**: Moderate risk
- **6-8**: High risk
- **8-10**: Very high risk

### Trading Signals
- **Strong Buy**: Very bullish
- **Buy**: Bullish
- **Hold**: Neutral
- **Sell**: Bearish
- **Strong Sell**: Very bearish

### Technical Indicators
- **RSI < 30**: Oversold (buy)
- **RSI > 70**: Overbought (sell)
- **MACD > 0**: Bullish
- **Price > SMA**: Uptrend

---

## 📞 Support

- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Logs**: `platform.log`

---

## ✅ Quick Reference

### Start Server
```powershell
python main_platform.py
```

### Test Everything
```powershell
python test_all.py
```

### Access Platform
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

### Key Endpoints
- Dashboard: `/api/portfolios/1/dashboard`
- Risk: `/api/portfolios/1/risk-model`
- Predict: `/api/portfolios/1/predict`
- Stock Risk: `/api/stock-risk/AAPL`
- Stock Predict: `/api/predict/AAPL`

---

## 🎉 You're Ready!

Your complete portfolio analysis platform with real-time tracking, risk assessment, and ML predictions is ready to use!

**Start now:** `python main_platform.py`
