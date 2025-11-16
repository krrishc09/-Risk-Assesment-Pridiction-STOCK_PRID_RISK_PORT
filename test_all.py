# test_all.py
"""
Unified test suite for the entire platform
Tests: Platform, Risk Models, and Predictions
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def print_section(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

# ==================== PLATFORM TESTS ====================

def test_health():
    print_section("1. HEALTH CHECK")
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        print("✅ Server is healthy")
        return True
    print("❌ Server is not responding")
    return False

def create_test_data():
    print_section("2. CREATING TEST DATA")
    
    # Create user
    user_data = {"email": f"test_{int(time.time())}@example.com", "name": "Test User"}
    user_response = requests.post(f"{BASE_URL}/api/users", json=user_data)
    
    if user_response.status_code != 200:
        print("❌ Failed to create user")
        return None, None
    
    user_id = user_response.json()['id']
    print(f"✅ User created (ID: {user_id})")
    
    # Create portfolio
    portfolio_data = {"name": "Test Portfolio"}
    portfolio_response = requests.post(
        f"{BASE_URL}/api/portfolios",
        params={"user_id": user_id},
        json=portfolio_data
    )
    
    if portfolio_response.status_code != 200:
        print("❌ Failed to create portfolio")
        return user_id, None
    
    portfolio_id = portfolio_response.json()['id']
    print(f"✅ Portfolio created (ID: {portfolio_id})")
    
    # Add holdings
    holdings = [
        {"symbol": "AAPL", "quantity": 10, "average_price": 150.00},
        {"symbol": "MSFT", "quantity": 5, "average_price": 350.00},
        {"symbol": "GOOGL", "quantity": 3, "average_price": 140.00},
    ]
    
    for holding in holdings:
        from datetime import datetime, timedelta
        holding["purchase_date"] = (datetime.now() - timedelta(days=180)).isoformat()
        response = requests.post(
            f"{BASE_URL}/api/portfolios/{portfolio_id}/holdings",
            json=holding
        )
        if response.status_code == 200:
            print(f"✅ Added {holding['symbol']}")
    
    print("\n⏳ Waiting 10 seconds for data to load...")
    time.sleep(10)
    
    return user_id, portfolio_id

def test_dashboard(portfolio_id):
    print_section("3. DASHBOARD TEST")
    response = requests.get(f"{BASE_URL}/api/portfolios/{portfolio_id}/dashboard")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Dashboard loaded")
        print(f"   Total Value: ${data['summary']['total_value']:,.2f}")
        print(f"   P&L: {data['summary']['total_pnl_percent']:+.2f}%")
        print(f"   Holdings: {data['summary']['holdings_count']}")
        return True
    print("❌ Dashboard failed")
    return False

# ==================== RISK MODEL TESTS ====================

def test_stock_risk():
    print_section("4. STOCK RISK MODEL TEST")
    
    symbols = ["AAPL", "MSFT"]
    for symbol in symbols:
        response = requests.get(f"{BASE_URL}/api/stock-risk/{symbol}")
        if response.status_code == 200:
            risk = response.json()
            if 'error' not in risk:
                print(f"✅ {symbol}: Risk Score {risk['risk_score']:.1f}/10 ({risk['risk_level']})")
            else:
                print(f"⚠️ {symbol}: {risk['error']}")
        else:
            print(f"❌ {symbol}: Failed")

def test_portfolio_risk(portfolio_id):
    print_section("5. PORTFOLIO RISK MODEL TEST")
    response = requests.get(f"{BASE_URL}/api/portfolios/{portfolio_id}/risk-model")
    
    if response.status_code == 200:
        risk = response.json()
        if 'error' not in risk:
            print(f"✅ Portfolio Risk: {risk['risk_level']} ({risk['risk_score']:.1f}/10)")
            print(f"   Concentration: {risk['concentration_risk']:.1f}%")
            print(f"   Volatility: {risk['weighted_volatility']:.2%}")
            return True
        else:
            print(f"⚠️ {risk['error']}")
    print("❌ Portfolio risk failed")
    return False

# ==================== PREDICTION TESTS ====================

def test_stock_prediction():
    print_section("6. STOCK PREDICTION TEST")
    
    symbols = ["AAPL", "MSFT"]
    for symbol in symbols:
        response = requests.get(f"{BASE_URL}/api/predict/{symbol}")
        if response.status_code == 200:
            pred = response.json()
            if 'error' not in pred:
                print(f"✅ {symbol}:")
                print(f"   Current: ${pred['current_price']:.2f}")
                print(f"   30d Pred: ${pred['predicted_price_30d']:.2f} ({pred['price_change_30d_pct']:+.2f}%)")
                print(f"   Signal: {pred['signal']}")
                print(f"   Trend: {pred['trend']}")
            else:
                print(f"⚠️ {symbol}: {pred['error']}")
        else:
            print(f"❌ {symbol}: Failed")

def test_portfolio_prediction(portfolio_id):
    print_section("7. PORTFOLIO PREDICTION TEST")
    response = requests.get(f"{BASE_URL}/api/portfolios/{portfolio_id}/predict")
    
    if response.status_code == 200:
        pred = response.json()
        if 'error' not in pred:
            print(f"✅ Portfolio Predictions:")
            print(f"   30d Forecast: {pred['predicted_return_30d']:+.2f}%")
            print(f"   Outlook: {pred['overall_outlook']}")
            print(f"   Buy Signals: {pred['buy_signals']}")
            print(f"   Sell Signals: {pred['sell_signals']}")
            return True
        else:
            print(f"⚠️ {pred['error']}")
    print("❌ Portfolio prediction failed")
    return False

# ==================== MAIN TEST RUNNER ====================

def run_all_tests():
    print("\n" + "🎯"*35)
    print("  COMPLETE PLATFORM TEST SUITE")
    print("🎯"*35)
    
    try:
        # Test 1: Health check
        if not test_health():
            print("\n❌ Server is not running!")
            print("   Start with: python main_platform.py")
            return
        
        # Test 2: Create test data
        user_id, portfolio_id = create_test_data()
        if not portfolio_id:
            print("\n❌ Failed to create test data")
            return
        
        # Test 3: Dashboard
        test_dashboard(portfolio_id)
        
        # Test 4-5: Risk models
        test_stock_risk()
        test_portfolio_risk(portfolio_id)
        
        # Test 6-7: Predictions
        test_stock_prediction()
        test_portfolio_prediction(portfolio_id)
        
        # Summary
        print_section("TEST SUMMARY")
        print("✅ All tests completed!")
        print(f"\n📝 Test Results:")
        print(f"   User ID: {user_id}")
        print(f"   Portfolio ID: {portfolio_id}")
        print(f"\n🌐 Access your data:")
        print(f"   Dashboard: {BASE_URL}/api/portfolios/{portfolio_id}/dashboard")
        print(f"   Risk Model: {BASE_URL}/api/portfolios/{portfolio_id}/risk-model")
        print(f"   Predictions: {BASE_URL}/api/portfolios/{portfolio_id}/predict")
        print(f"   API Docs: {BASE_URL}/docs")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to server!")
        print("   Make sure the server is running:")
        print("   python main_platform.py")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_all_tests()
