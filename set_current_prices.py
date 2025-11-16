"""
Set current market prices in the database so P&L shows correctly
"""
from database import DatabaseManager, StockPrice
from datetime import datetime

db = DatabaseManager()
session = db.SessionLocal()

try:
    # Set current market prices (higher than average to show profit)
    current_prices = {
        'AAPL': 150.0,   # 11% higher than avg of 135
        'MSFT': 350.0,   # 11% higher than avg of 315
        'GOOGL': 140.0   # 11% higher than avg of 126
    }
    
    print("Setting current market prices...")
    
    for symbol, price in current_prices.items():
        # Check if price data exists
        existing = session.query(StockPrice).filter(
            StockPrice.symbol == symbol
        ).order_by(StockPrice.timestamp.desc()).first()
        
        if existing:
            # Update existing
            existing.ltp = price
            existing.timestamp = datetime.now()
            print(f"Updated {symbol}: ${price}")
        else:
            # Create new
            price_data = StockPrice(
                symbol=symbol,
                ltp=price,
                open=price * 0.99,
                high=price * 1.01,
                low=price * 0.98,
                close=price,
                volume=1000000,
                timestamp=datetime.now()
            )
            session.add(price_data)
            print(f"Created {symbol}: ${price}")
    
    session.commit()
    print("\n✅ Current prices set! Restart backend and refresh to see P&L.")
    
finally:
    session.close()
