# 🎨 Frontend Setup Guide

## Overview

Modern React frontend with:
- ✅ Real-time portfolio dashboard
- ✅ Risk analysis visualization
- ✅ ML predictions display
- ✅ Performance charts
- ✅ Responsive design (Tailwind CSS)
- ✅ Beautiful UI with Lucide icons

---

## 🚀 Quick Start

### 1. Install Dependencies

```powershell
cd frontend
npm install
```

### 2. Start Backend (Required)

In the main project directory:
```powershell
python main_platform.py
```

Backend runs at: http://localhost:8000

### 3. Start Frontend

In the frontend directory:
```powershell
npm start
```

Frontend runs at: http://localhost:3000

---

## 📁 Project Structure

```
frontend/
├── public/
│   └── index.html              # HTML template
├── src/
│   ├── components/
│   │   ├── Dashboard.js        # Main dashboard
│   │   ├── PortfolioSummary.js # Summary cards
│   │   ├── HoldingsList.js     # Holdings table
│   │   ├── RiskAnalysis.js     # Risk visualization
│   │   ├── PredictionPanel.js  # Predictions display
│   │   ├── PerformanceChart.js # Performance charts
│   │   └── PortfolioList.js    # Portfolio selector
│   ├── App.js                  # Main app component
│   ├── index.js                # Entry point
│   └── index.css               # Tailwind styles
├── package.json                # Dependencies
├── tailwind.config.js          # Tailwind config
└── postcss.config.js           # PostCSS config
```

---

## 🎯 Features

### 1. **Portfolio Dashboard**
- Real-time portfolio value
- Total P&L with percentage
- Today's change
- Holdings count
- Auto-refresh every 30 seconds

### 2. **Holdings View**
- Complete holdings table
- Current prices
- P&L per stock
- Day change
- Portfolio weight

### 3. **Risk Analysis**
- Risk score (0-10)
- Risk level (Low/Moderate/High/Very High)
- Concentration risk
- Volatility metrics
- Risk factors
- Recommendations
- High-risk stocks alert

### 4. **Predictions**
- Overall outlook (Bullish/Bearish/Neutral)
- 1-day, 5-day, 30-day forecasts
- Signal distribution (Buy/Hold/Sell)
- Buy opportunities
- Sell recommendations
- Individual stock predictions
- Insights

### 5. **Performance Charts**
- Portfolio value over time
- P&L percentage chart
- Interactive tooltips
- Responsive design

---

## 🎨 UI Components

### Color Scheme
- **Primary**: Blue (#3b82f6)
- **Success**: Green (#10b981)
- **Danger**: Red (#ef4444)
- **Warning**: Yellow (#f59e0b)

### Icons
Using **Lucide React** for modern, clean icons:
- Activity, TrendingUp, TrendingDown
- DollarSign, Percent, PieChart
- Shield, AlertTriangle, Target
- Lightbulb, ShoppingCart, AlertCircle

---

## 🔧 Configuration

### API Proxy

The frontend is configured to proxy API requests to the backend:

```json
// package.json
"proxy": "http://localhost:8000"
```

This means:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API calls from frontend automatically proxy to backend

### Environment Variables (Optional)

Create `.env` in frontend directory:

```env
REACT_APP_API_URL=http://localhost:8000
```

---

## 📊 Data Flow

```
Backend (Port 8000)
    ↓
API Endpoints
    ↓
Frontend (Port 3000)
    ↓
React Components
    ↓
User Interface
```

### API Calls

```javascript
// Dashboard data
GET /api/portfolios/1/dashboard

// Risk analysis
GET /api/portfolios/1/risk-model

// Predictions
GET /api/portfolios/1/predict
```

---

## 🧪 Testing

### 1. Test Backend First

```powershell
# Start backend
python main_platform.py

# Test API
curl http://localhost:8000/health
```

### 2. Create Test Data

```powershell
python test_all.py
```

### 3. Start Frontend

```powershell
cd frontend
npm start
```

### 4. Access Dashboard

Open: http://localhost:3000

You should see:
- Portfolio summary cards
- Holdings table
- Risk analysis
- Predictions
- Performance charts

---

## 🎯 Usage Examples

### View Portfolio

1. Frontend loads automatically with Portfolio ID 1
2. Dashboard shows real-time data
3. Auto-refreshes every 30 seconds

### Switch Tabs

- **Overview**: Holdings table
- **Risk**: Risk analysis and metrics
- **Predictions**: ML predictions and signals
- **Performance**: Charts and graphs

### Interpret Data

**Risk Levels:**
- 🟢 Low (0-3): Safe
- 🟡 Moderate (3-6): Normal
- 🟠 High (6-8): Caution
- 🔴 Very High (8-10): Alert

**Trading Signals:**
- 🟢 Strong Buy / Buy: Consider buying
- ⚪ Hold: Maintain position
- 🔴 Sell / Strong Sell: Consider selling

---

## 🚀 Production Build

### Build for Production

```powershell
cd frontend
npm run build
```

This creates an optimized production build in `frontend/build/`

### Serve Production Build

```powershell
# Install serve globally
npm install -g serve

# Serve the build
serve -s build -p 3000
```

---

## 🐛 Troubleshooting

### "Cannot connect to backend"

**Solution:**
```powershell
# Make sure backend is running
python main_platform.py
```

### "Module not found"

**Solution:**
```powershell
cd frontend
npm install
```

### "Port 3000 already in use"

**Solution:**
```powershell
# Use different port
set PORT=3001 && npm start
```

### "No data displayed"

**Solution:**
```powershell
# Create test data
python test_all.py

# Refresh frontend
# Press Ctrl+R in browser
```

### CSS warnings about @tailwind

**Note:** These warnings are normal during development. They disappear once you run `npm start` and Tailwind processes the CSS.

---

## 📱 Responsive Design

The frontend is fully responsive:

- **Desktop** (1024px+): Full layout with all features
- **Tablet** (768px-1023px): Adjusted grid layouts
- **Mobile** (< 768px): Stacked layout, mobile-optimized

---

## 🎨 Customization

### Change Colors

Edit `tailwind.config.js`:

```javascript
theme: {
  extend: {
    colors: {
      primary: '#your-color',
      success: '#your-color',
      danger: '#your-color',
    },
  },
}
```

### Add New Components

1. Create file in `src/components/`
2. Import in `Dashboard.js` or `App.js`
3. Use in JSX

### Modify Refresh Rate

Edit `Dashboard.js`:

```javascript
// Change from 30000 (30 sec) to desired milliseconds
const interval = setInterval(loadDashboardData, 60000); // 1 minute
```

---

## 📦 Dependencies

### Core
- `react` - UI framework
- `react-dom` - React DOM rendering
- `react-scripts` - Build tools

### UI
- `tailwindcss` - Utility-first CSS
- `lucide-react` - Icon library

### Data & Charts
- `axios` - HTTP client
- `recharts` - Charting library

---

## ✅ Checklist

- [ ] Backend running on port 8000
- [ ] Test data created
- [ ] Dependencies installed (`npm install`)
- [ ] Frontend started (`npm start`)
- [ ] Dashboard loads at http://localhost:3000
- [ ] Data displays correctly
- [ ] Charts render properly
- [ ] Tabs work
- [ ] Auto-refresh working

---

## 🎉 You're Ready!

Your modern React frontend is ready to use!

**Access:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

**Features:**
- ✅ Real-time portfolio tracking
- ✅ Risk analysis visualization
- ✅ ML predictions display
- ✅ Performance charts
- ✅ Responsive design
- ✅ Auto-refresh

Enjoy your portfolio analysis platform! 🚀
