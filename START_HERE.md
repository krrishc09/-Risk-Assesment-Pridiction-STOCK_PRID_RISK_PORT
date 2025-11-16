# 🚀 START HERE - Quick Setup Guide

## ⚡ Super Quick Start (3 Commands)

```powershell
pip install -r requirements.txt
python -c "from database import init_database; init_database()"
python main_platform.py
```

**Done!** Platform runs at http://localhost:8000

---

## 📁 Essential Files Only

### Core Files (Don't Delete)
- `main_platform.py` - Main application ⭐
- `database.py` - Database models
- `data_stream.py` - Real-time data
- `portfolio_engine.py` - Portfolio tracking
- `risk_models.py` - Risk analysis
- `prediction_models.py` - ML predictions
- `utils.py` - Utility functions
- `config_platform.py` - Configuration
- `requirements.txt` - Dependencies ⭐

### Documentation (Read These)
- `README_COMPLETE.md` - Complete guide ⭐
- `START_HERE.md` - This file

### Testing
- `test_all.py` - Test everything ⭐

### Optional Files
- `portfolio.py` - Portfolio optimization (advanced)
- `examples.py` - Usage examples
- `.env.example` - Environment template
- `start_platform.ps1` - Windows startup script

---

## 🎯 What to Do Next

### 1. Start the Backend
```powershell
python main_platform.py
```

### 2. Start the Frontend (Optional)
```powershell
cd frontend
npm install
npm start
```

Frontend runs at: http://localhost:3000

### 3. Open API Docs
```
http://localhost:8000/docs
```

### 4. Run Tests
```powershell
python test_all.py
```

### 5. Try Examples

**Get Stock Prediction:**
```powershell
curl http://localhost:8000/api/predict/AAPL
```

**Get Stock Risk:**
```powershell
curl http://localhost:8000/api/stock-risk/AAPL
```

---

## 🗑️ Files You Can Delete

These files are duplicates or old versions:

### Old Documentation (Delete After Reading)
- `README.md` (old version)
- `README_PLATFORM.md` (merged into README_COMPLETE.md)
- `DEPLOYMENT_GUIDE.md` (merged into README_COMPLETE.md)
- `RISK_MODELS_GUIDE.md` (merged into README_COMPLETE.md)
- `PREDICTION_GUIDE.md` (merged into README_COMPLETE.md)
- `COMPLETE_FEATURES.md` (merged into README_COMPLETE.md)
- `QUICKSTART.md` (merged into README_COMPLETE.md)
- `frontend_setup.md` (optional, for later)

### Old Test Files (Delete After Using test_all.py)
- `test_platform.py` (merged into test_all.py)
- `test_risk_models.py` (merged into test_all.py)
- `test_predictions.py` (merged into test_all.py)
- `test_api.py` (old version)

### Old Config Files (Delete After Merging)
- `config.py` (merged into config_platform.py)
- `requirements_minimal.txt` (merged into requirements.txt)
- `requirements_platform.txt` (merged into requirements.txt)

### Old Main Files (Delete After Testing)
- `main.py` (old version, use main_platform.py)

---

## 📦 Minimal File Structure

After cleanup, you should have:

```
RISKMODEL/
├── main_platform.py          ⭐ Main app
├── database.py               Database
├── data_stream.py            Real-time data
├── portfolio_engine.py       Portfolio tracking
├── risk_models.py            Risk analysis
├── prediction_models.py      ML predictions
├── utils.py                  Utilities
├── config_platform.py        Configuration
├── requirements.txt          ⭐ Dependencies
├── README_COMPLETE.md        ⭐ Documentation
├── START_HERE.md             ⭐ This file
├── test_all.py               ⭐ Testing
├── .env.example              Environment template
├── portfolio_data.db         Database (auto-created)
└── .venv/                    Virtual environment
```

**Total: ~13 essential files** (down from 30+)

---

## ✅ Quick Commands

```powershell
# Install
pip install -r requirements.txt

# Initialize
python -c "from database import init_database; init_database()"

# Start
python main_platform.py

# Test
python test_all.py

# Access
# http://localhost:8000/docs
```

---

## 🆘 Troubleshooting

### "Module not found"
```powershell
pip install -r requirements.txt
```

### "Port already in use"
```powershell
netstat -ano | findstr :8000
# Kill the process or use different port
```

### "Database error"
```powershell
python -c "from database import db_manager; db_manager.drop_tables(); db_manager.create_tables()"
```

---

## 🎉 You're Ready!

1. ✅ Install: `pip install -r requirements.txt`
2. ✅ Initialize: `python -c "from database import init_database; init_database()"`
3. ✅ Start: `python main_platform.py`
4. ✅ Test: `python test_all.py`
5. ✅ Use: http://localhost:8000/docs

**Need help?** Read `README_COMPLETE.md`
