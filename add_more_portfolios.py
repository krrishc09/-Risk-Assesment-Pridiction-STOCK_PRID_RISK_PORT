"""
Add more portfolios to portfolio_data.db
"""
import sqlite3

def add_portfolios():
    conn = sqlite3.connect('portfolio_data.db')
    cursor = conn.cursor()
    
    # Check existing portfolios
    cursor.execute("SELECT id, name FROM portfolios")
    existing = cursor.fetchall()
    print("Existing portfolios:")
    for pid, name in existing:
        print(f"  ID {pid}: {name}")
    
    # Add Tech Growth Portfolio
    cursor.execute("""
        INSERT INTO portfolios (name, description)
        VALUES (?, ?)
    """, ("Tech Growth Portfolio", "Technology focused growth portfolio"))
    tech_id = cursor.lastrowid
    print(f"\n✅ Created: Tech Growth Portfolio (ID: {tech_id})")
    
    # Add holdings for Tech Growth Portfolio
    tech_holdings = [
        ("TSLA", 5.0, 250.00),
        ("NVDA", 8.0, 480.00),
        ("AMD", 15.0, 120.00),
    ]
    
    for symbol, qty, price in tech_holdings:
        cursor.execute("""
            INSERT INTO holdings (portfolio_id, symbol, quantity, average_price)
            VALUES (?, ?, ?, ?)
        """, (tech_id, symbol, qty, price))
        print(f"  Added: {qty} shares of {symbol} @ ${price:.2f}")
    
    # Add Value Investment Portfolio
    cursor.execute("""
        INSERT INTO portfolios (name, description)
        VALUES (?, ?)
    """, ("Value Investment Portfolio", "Long-term value investment strategy"))
    value_id = cursor.lastrowid
    print(f"\n✅ Created: Value Investment Portfolio (ID: {value_id})")
    
    # Add holdings for Value Investment Portfolio
    value_holdings = [
        ("BRK.B", 10.0, 350.00),
        ("JPM", 20.0, 150.00),
        ("JNJ", 15.0, 160.00),
    ]
    
    for symbol, qty, price in value_holdings:
        cursor.execute("""
            INSERT INTO holdings (portfolio_id, symbol, quantity, average_price)
            VALUES (?, ?, ?, ?)
        """, (value_id, symbol, qty, price))
        print(f"  Added: {qty} shares of {symbol} @ ${price:.2f}")
    
    conn.commit()
    conn.close()
    
    print("\n" + "="*60)
    print("✅ Successfully added 2 new portfolios!")
    print("="*60)
    print("\nYou now have 3 portfolios:")
    print("  1. Test Portfolio (AAPL, MSFT, GOOGL)")
    print("  2. Tech Growth Portfolio (TSLA, NVDA, AMD)")
    print("  3. Value Investment Portfolio (BRK.B, JPM, JNJ)")
    print("\n🚀 Restart your backend and refresh the frontend to see all portfolios!")

if __name__ == "__main__":
    add_portfolios()
