"""
Update holdings with lower average prices to show P&L
"""
from database import DatabaseManager, Holding

db = DatabaseManager()

# Create a session
session = db.SessionLocal()

try:
    # Query holdings directly in this session
    holdings = session.query(Holding).filter(Holding.portfolio_id == 1).all()
    
    if not holdings:
        print("No holdings found")
        exit()

    print(f"Holdings: {len(holdings)}")

    # Manually set lower average prices (90% of current to show 10% profit)
    price_adjustments = {
        'AAPL': 135.0,   # Current is 150, so 10% profit
        'MSFT': 315.0,   # Current is 350, so 10% profit  
        'GOOGL': 126.0   # Current is 140, so 10% profit
    }

    # Update each holding with a lower average price (simulate buying cheaper)
    for holding in holdings:
        if holding.symbol in price_adjustments:
            old_avg_price = holding.average_price
            new_avg_price = price_adjustments[holding.symbol]
            
            holding.average_price = new_avg_price
            
            print(f"\n{holding.symbol}:")
            print(f"  Old avg price: ${old_avg_price:.2f}")
            print(f"  New avg price: ${new_avg_price:.2f}")
            print(f"  Quantity: {holding.quantity}")
            print(f"  Old Investment: ${old_avg_price * holding.quantity:.2f}")
            print(f"  New Investment: ${holding.total_investment:.2f}")

    # Commit all changes
    session.commit()
    print("\n✅ Holdings updated! Restart backend and refresh dashboard to see ~10% P&L.")

finally:
    session.close()
