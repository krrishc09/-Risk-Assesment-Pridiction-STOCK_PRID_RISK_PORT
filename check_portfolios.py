"""
Check portfolios in the correct database
"""
import sqlite3

def check_portfolios():
    print("\n" + "="*60)
    print("CHECKING portfolio_data.db (Backend Database)")
    print("="*60)
    
    conn = sqlite3.connect('portfolio_data.db')
    cursor = conn.cursor()
    
    # Check portfolios
    cursor.execute("SELECT id, name, description FROM portfolios")
    portfolios = cursor.fetchall()
    
    print(f"\n✅ Found {len(portfolios)} portfolio(s):\n")
    for pid, name, desc in portfolios:
        print(f"  📊 ID {pid}: {name}")
        if desc:
            print(f"     Description: {desc}")
        
        # Check holdings for this portfolio
        cursor.execute("SELECT symbol, quantity, average_price FROM holdings WHERE portfolio_id = ?", (pid,))
        holdings = cursor.fetchall()
        
        if holdings:
            print(f"     Holdings:")
            for symbol, qty, price in holdings:
                print(f"       • {symbol}: {qty} shares @ ${price:.2f}")
        else:
            print(f"     Holdings: None")
        print()
    
    conn.close()
    
    print("="*60)
    print("✅ Your portfolios are ready!")
    print("="*60)
    print("\n📝 To test the portfolio selector:")
    print("   1. Make sure backend is running: python main_platform.py")
    print("   2. Open frontend: http://localhost:3000")
    print("   3. Click the portfolio dropdown in the header")
    print(f"   4. You should see {len(portfolios)} portfolio(s) to choose from\n")

if __name__ == "__main__":
    check_portfolios()
