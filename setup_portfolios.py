"""
Setup portfolios in the database
"""
import sqlite3
from datetime import datetime

def setup_portfolios():
    # Try both database files
    db_files = ['portfolio.db', 'portfolio_data.db']
    
    for db_file in db_files:
        print(f"\n{'='*50}")
        print(f"Checking {db_file}...")
        print('='*50)
        
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            # Check existing tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"Existing tables: {[t[0] for t in tables]}")
            
            # Create portfolios table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS portfolios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Check if we have any portfolios
            cursor.execute("SELECT COUNT(*) FROM portfolios")
            count = cursor.fetchone()[0]
            
            if count == 0:
                print("No portfolios found. Creating default portfolios...")
                
                # Create default portfolio
                cursor.execute("""
                    INSERT INTO portfolios (name, description, created_at)
                    VALUES (?, ?, ?)
                """, ("My Portfolio", "Default investment portfolio", datetime.now()))
                portfolio1_id = cursor.lastrowid
                print(f"✅ Created: 'My Portfolio' (ID: {portfolio1_id})")
                
                # Create second portfolio
                cursor.execute("""
                    INSERT INTO portfolios (name, description, created_at)
                    VALUES (?, ?, ?)
                """, ("Tech Growth Portfolio", "Technology focused growth portfolio", datetime.now()))
                portfolio2_id = cursor.lastrowid
                print(f"✅ Created: 'Tech Growth Portfolio' (ID: {portfolio2_id})")
                
                # If holdings table exists, assign holdings to portfolios
                if 'holdings' in [t[0] for t in tables]:
                    # Check if holdings have portfolio_id column
                    cursor.execute("PRAGMA table_info(holdings)")
                    columns = [col[1] for col in cursor.fetchall()]
                    
                    if 'portfolio_id' not in columns:
                        print("Adding portfolio_id column to holdings...")
                        cursor.execute("ALTER TABLE holdings ADD COLUMN portfolio_id INTEGER DEFAULT 1")
                    
                    # Assign existing holdings to portfolio 1
                    cursor.execute("UPDATE holdings SET portfolio_id = ? WHERE portfolio_id IS NULL", (portfolio1_id,))
                    
                    # Add some holdings to portfolio 2
                    holdings_2 = [
                        ("TSLA", 5, 250.00),
                        ("NVDA", 8, 480.00),
                    ]
                    
                    for symbol, quantity, avg_price in holdings_2:
                        cursor.execute("""
                            INSERT INTO holdings (portfolio_id, symbol, quantity, average_price, purchase_date)
                            VALUES (?, ?, ?, ?, ?)
                        """, (portfolio2_id, symbol, quantity, avg_price, datetime.now()))
                        print(f"  Added to Tech Portfolio: {quantity} shares of {symbol} @ ${avg_price}")
                
                conn.commit()
                print(f"\n✅ Successfully set up portfolios in {db_file}!")
            else:
                print(f"Found {count} existing portfolio(s)")
                cursor.execute("SELECT id, name FROM portfolios")
                for pid, name in cursor.fetchall():
                    print(f"  - ID {pid}: {name}")
            
            conn.close()
            
        except Exception as e:
            print(f"Error with {db_file}: {e}")
            continue
    
    print("\n" + "="*50)
    print("Setup complete! Restart your backend server.")
    print("="*50)

if __name__ == "__main__":
    setup_portfolios()
