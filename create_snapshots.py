"""
Create sample portfolio snapshots for performance chart
"""
from database import db_manager, PortfolioSnapshot
from datetime import datetime, timedelta
import random

def create_sample_snapshots(portfolio_id=1, days=30):
    """Create sample portfolio snapshots for the last N days"""
    
    # Get current portfolio value
    from portfolio_engine import PortfolioCalculator
    calculator = PortfolioCalculator(portfolio_id)
    current_summary = calculator.calculate_portfolio_summary()
    
    current_value = current_summary['total_value']
    current_investment = current_summary['total_investment']
    
    print(f"Creating {days} days of sample snapshots...")
    print(f"Current value: ${current_value:.2f}")
    print(f"Investment: ${current_investment:.2f}")
    
    # Generate snapshots for past days
    for i in range(days, 0, -1):
        date = datetime.now() - timedelta(days=i)
        
        # Simulate gradual growth with some volatility
        progress = (days - i) / days  # 0 to 1
        
        # Start from investment amount and grow to current value
        value = current_investment + (current_value - current_investment) * progress
        
        # Add some random daily volatility (±2%)
        daily_change = random.uniform(-0.02, 0.02)
        value = value * (1 + daily_change)
        
        # Calculate P&L
        pnl = value - current_investment
        pnl_percent = (pnl / current_investment * 100) if current_investment > 0 else 0
        
        # Create snapshot data
        snapshot_data = {
            'timestamp': date,
            'total_value': value,
            'total_investment': current_investment,
            'total_pnl': pnl,
            'total_pnl_percent': pnl_percent,
            'day_change': value * daily_change,
            'day_change_percent': daily_change * 100
        }
        
        db_manager.save_portfolio_snapshot(portfolio_id, snapshot_data)
    
    print(f"✅ Created {days} snapshots successfully!")
    print(f"Date range: {(datetime.now() - timedelta(days=days)).date()} to {datetime.now().date()}")

if __name__ == "__main__":
    create_sample_snapshots(portfolio_id=1, days=30)
