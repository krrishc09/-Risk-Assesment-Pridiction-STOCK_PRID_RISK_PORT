# examples.py
"""
Example usage of the Stock Risk Analysis API
Run the server first: uvicorn main:app --reload
"""

import requests
import json

BASE_URL = "http://localhost:8000"


def example_single_stock_analysis():
    """Example: Analyze a single stock"""
    print("\n" + "="*60)
    print("EXAMPLE 1: Single Stock Analysis")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/analyze", params={
        "symbol": "AAPL",
        "period": "1y",
        "interval": "1d"
    })
    
    data = response.json()
    print(f"\nStock: {data['symbol']}")
    print(f"Annualized Return: {data['annualized_return']:.2%}")
    print(f"Annualized Volatility: {data['annualized_volatility']:.2%}")
    print(f"Sharpe Ratio: {data['sharpe_ratio']:.2f}")
    print(f"Sortino Ratio: {data['sortino_ratio']:.2f}")
    print(f"Max Drawdown: {data['max_drawdown']:.2%}")
    print(f"Beta: {data['beta']:.2f}")
    print(f"VaR (95%): {data['var_95']:.2%}")


def example_batch_analysis():
    """Example: Batch analyze multiple stocks"""
    print("\n" + "="*60)
    print("EXAMPLE 2: Batch Analysis")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/batch", params={
        "symbols": "AAPL,MSFT,GOOGL,AMZN",
        "period": "1y"
    })
    
    data = response.json()
    
    print("\nComparison Table:")
    print(f"{'Symbol':<10} {'Return':<12} {'Volatility':<12} {'Sharpe':<10} {'Beta':<10}")
    print("-" * 60)
    
    for symbol, metrics in data.items():
        if "error" not in metrics:
            print(f"{symbol:<10} "
                  f"{metrics['annualized_return']:>10.2%}  "
                  f"{metrics['annualized_volatility']:>10.2%}  "
                  f"{metrics['sharpe_ratio']:>8.2f}  "
                  f"{metrics['beta']:>8.2f}")


def example_portfolio_analysis():
    """Example: Analyze a portfolio"""
    print("\n" + "="*60)
    print("EXAMPLE 3: Portfolio Analysis")
    print("="*60)
    
    payload = {
        "symbols": ["AAPL", "MSFT", "GOOGL"],
        "weights": [0.4, 0.3, 0.3],
        "period": "1y",
        "interval": "1d"
    }
    
    response = requests.post(f"{BASE_URL}/portfolio/analyze", json=payload)
    data = response.json()
    
    print("\nPortfolio Composition:")
    for symbol, weight in zip(data['symbols'], data['weights']):
        print(f"  {symbol}: {weight:.1%}")
    
    print("\nPortfolio Metrics:")
    print(f"Annualized Return: {data['annualized_return']:.2%}")
    print(f"Annualized Volatility: {data['annualized_volatility']:.2%}")
    print(f"Sharpe Ratio: {data['sharpe_ratio']:.2f}")
    
    print("\nIndividual Contributions:")
    for symbol, contrib in data['contributions'].items():
        print(f"  {symbol}:")
        print(f"    Weight: {contrib['weight']:.1%}")
        print(f"    Return Contribution: {contrib['contribution_to_return']:.2%}")
        print(f"    Risk Contribution: {contrib['contribution_to_risk']:.2%}")


def example_portfolio_optimization():
    """Example: Optimize portfolio weights"""
    print("\n" + "="*60)
    print("EXAMPLE 4: Portfolio Optimization")
    print("="*60)
    
    payload = {
        "symbols": ["AAPL", "MSFT", "GOOGL", "AMZN"],
        "period": "1y",
        "target": "sharpe"
    }
    
    response = requests.post(f"{BASE_URL}/portfolio/optimize", json=payload)
    data = response.json()
    
    print(f"\nOptimization Target: Maximize {data['optimization_target'].upper()}")
    print("\nOptimal Weights:")
    for symbol, weight in zip(data['symbols'], data['optimal_weights']):
        print(f"  {symbol}: {weight:.1%}")
    
    print("\nExpected Performance:")
    print(f"Expected Return: {data['expected_return']:.2%}")
    print(f"Expected Volatility: {data['expected_volatility']:.2%}")
    print(f"Expected Sharpe: {data['expected_sharpe']:.2f}")


def example_compare_stocks():
    """Example: Compare multiple stocks"""
    print("\n" + "="*60)
    print("EXAMPLE 5: Stock Comparison")
    print("="*60)
    
    payload = {
        "symbols": ["AAPL", "MSFT", "GOOGL"],
        "period": "1y"
    }
    
    response = requests.post(f"{BASE_URL}/compare", json=payload)
    data = response.json()
    
    print("\nDetailed Comparison:")
    for symbol, metrics in data.items():
        print(f"\n{symbol}:")
        print(f"  Return: {metrics['annualized_return']:.2%}")
        print(f"  Volatility: {metrics['annualized_volatility']:.2%}")
        print(f"  Sharpe: {metrics['sharpe_ratio']:.2f}")
        print(f"  Sortino: {metrics['sortino_ratio']:.2f}")
        print(f"  Max Drawdown: {metrics['max_drawdown']:.2%}")
        print(f"  Beta: {metrics['beta']:.2f}")


def example_efficient_frontier():
    """Example: Generate efficient frontier"""
    print("\n" + "="*60)
    print("EXAMPLE 6: Efficient Frontier")
    print("="*60)
    
    payload = {
        "symbols": ["AAPL", "MSFT", "GOOGL"],
        "period": "1y"
    }
    
    response = requests.post(f"{BASE_URL}/portfolio/frontier", json=payload)
    data = response.json()
    
    print("\nEfficient Frontier Points:")
    print(f"{'Return':<12} {'Volatility':<12} {'Sharpe':<10}")
    print("-" * 40)
    
    for point in data['frontier'][:10]:  # Show first 10 points
        sharpe = point['sharpe'] if point['sharpe'] else 0
        print(f"{point['return']:>10.2%}  {point['volatility']:>10.2%}  {sharpe:>8.2f}")


def run_all_examples():
    """Run all examples"""
    try:
        # Check if server is running
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("Error: Server is not running!")
            print("Start the server with: uvicorn main:app --reload")
            return
        
        print("\n" + "="*60)
        print("STOCK RISK ANALYSIS API - EXAMPLES")
        print("="*60)
        
        example_single_stock_analysis()
        example_batch_analysis()
        example_portfolio_analysis()
        example_portfolio_optimization()
        example_compare_stocks()
        example_efficient_frontier()
        
        print("\n" + "="*60)
        print("All examples completed successfully!")
        print("="*60 + "\n")
        
    except requests.exceptions.ConnectionError:
        print("\nError: Cannot connect to the API server!")
        print("Make sure the server is running:")
        print("  uvicorn main:app --reload")
        print("\nThen run this script again.")
    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    run_all_examples()
