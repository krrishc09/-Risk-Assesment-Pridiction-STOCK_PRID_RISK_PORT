"""
Script to add a new portfolio to the database
"""
import sqlite3
from datetime import datetime

def add_portfolio():
    # Connect to database
    conn = sqlite3.connect('portfolio.db')
    cursor = conn.cursor()
    
    # Check existing portfolios
    cursor.execute("SELECT id, name FROM portfolios")
    existing = cursor.fetchall()
    print("Existing portfolios:")
    for portfolio in existing:
        print(f"  ID: {portfolio[0]}, Name: {portfolio[1]}")
    
    # Add new portfolio
    new_portfolio_name = "Tech Growth Portfolio"
    cursor.execute("""
        INSERT INTO portfolios (name, description, created_at)
        VALUES (?, ?, ?)
    """, (new_portfolio_name, "Technology focused growth portfolio", datetime.now()))
    
    portfolio_id = cursor.lastrowid
    print(f"\n✅ Created new portfolio: '{new_portfolio_name}' (ID: {portfolio_id})")
    
    # Add some holdings to the new portfolio
    holdings = [
        ("TSLA", 5, 250.00),
        ("NVDA", 8, 480.00),
        ("AMD", 15, 120.00),
    ]
    
    for symbol, quantity, avg_price in holdings:
        cursor.execute("""
            INSERT INTO holdings (portfolio_id, symbol, quantity, average_price, purchase_date)
            VALUES (?, ?, ?, ?, ?)
        """, (portfolio_id, symbol, quantity, avg_price, datetime.now()))
        print(f"  Added: {quantity} shares of {symbol} @ ${avg_price}")
    
    conn.commit()
    conn.close()
    
    print("\n✅ Portfolio created successfully!")
    print(f"\nYou now have {len(existing) + 1} portfolios:")
    print("  1. My Portfolio (Original)")
    print(f"  2. {new_portfolio_name} (New)")

if __name__ == "__main__":
    add_portfolio()
