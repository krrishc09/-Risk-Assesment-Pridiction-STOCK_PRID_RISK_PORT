# portfolio.py
import numpy as np
import pandas as pd
import yfinance as yf
from typing import List, Dict
from scipy.optimize import minimize


def get_portfolio_data(symbols: List[str], period="1y", interval="1d"):
    """Fetch historical data for multiple stocks"""
    data = {}
    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            if not df.empty:
                data[symbol] = df["Close"]
        except:
            continue
    
    if not data:
        raise ValueError("No valid data for any symbols")
    
    return pd.DataFrame(data).dropna()


def portfolio_returns(prices_df: pd.DataFrame, weights: List[float]):
    """Calculate portfolio returns given prices and weights"""
    returns = prices_df.pct_change().dropna()
    portfolio_ret = (returns * weights).sum(axis=1)
    return portfolio_ret


def portfolio_metrics(symbols: List[str], weights: List[float], period="1y", interval="1d"):
    """Calculate comprehensive portfolio metrics"""
    if len(symbols) != len(weights):
        raise ValueError("Number of symbols must match number of weights")
    
    if not np.isclose(sum(weights), 1.0):
        raise ValueError("Weights must sum to 1.0")
    
    # Get data
    prices = get_portfolio_data(symbols, period, interval)
    returns = prices.pct_change().dropna()
    
    # Portfolio returns
    portfolio_ret = (returns * weights).sum(axis=1)
    
    # Annualization factor
    periods_per_year = {"1d": 252, "1wk": 52, "1mo": 12}.get(interval, 252)
    
    # Calculate metrics
    ann_return = float(np.mean(portfolio_ret) * periods_per_year)
    ann_volatility = float(np.std(portfolio_ret, ddof=1) * np.sqrt(periods_per_year))
    
    # Sharpe ratio
    risk_free_rate = 0.02
    sharpe = (ann_return - risk_free_rate) / ann_volatility if ann_volatility > 0 else None
    
    # Correlation matrix
    corr_matrix = returns.corr().to_dict()
    
    # Individual stock contributions
    contributions = {}
    for i, symbol in enumerate(symbols):
        contributions[symbol] = {
            "weight": weights[i],
            "contribution_to_return": float(np.mean(returns[symbol]) * weights[i] * periods_per_year),
            "contribution_to_risk": float(np.std(returns[symbol], ddof=1) * weights[i] * np.sqrt(periods_per_year))
        }
    
    return {
        "symbols": symbols,
        "weights": weights,
        "period": period,
        "interval": interval,
        "annualized_return": ann_return,
        "annualized_volatility": ann_volatility,
        "sharpe_ratio": sharpe,
        "correlation_matrix": corr_matrix,
        "contributions": contributions
    }


def optimize_portfolio(symbols: List[str], period="1y", interval="1d", target="sharpe"):
    """
    Optimize portfolio weights
    target: 'sharpe' (maximize Sharpe ratio) or 'min_vol' (minimize volatility)
    """
    prices = get_portfolio_data(symbols, period, interval)
    returns = prices.pct_change().dropna()
    
    periods_per_year = {"1d": 252, "1wk": 52, "1mo": 12}.get(interval, 252)
    mean_returns = returns.mean() * periods_per_year
    cov_matrix = returns.cov() * periods_per_year
    
    n_assets = len(symbols)
    
    def portfolio_stats(weights):
        portfolio_return = np.dot(weights, mean_returns)
        portfolio_std = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        return portfolio_return, portfolio_std
    
    def neg_sharpe(weights):
        ret, std = portfolio_stats(weights)
        return -(ret - 0.02) / std if std > 0 else 1e10
    
    def portfolio_volatility(weights):
        _, std = portfolio_stats(weights)
        return std
    
    # Constraints and bounds
    constraints = {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}
    bounds = tuple((0, 1) for _ in range(n_assets))
    initial_weights = np.array([1/n_assets] * n_assets)
    
    # Optimize
    if target == "sharpe":
        result = minimize(neg_sharpe, initial_weights, method='SLSQP', 
                         bounds=bounds, constraints=constraints)
    else:  # min_vol
        result = minimize(portfolio_volatility, initial_weights, method='SLSQP',
                         bounds=bounds, constraints=constraints)
    
    if not result.success:
        raise ValueError("Optimization failed")
    
    optimal_weights = result.x.tolist()
    opt_return, opt_std = portfolio_stats(result.x)
    opt_sharpe = (opt_return - 0.02) / opt_std if opt_std > 0 else None
    
    return {
        "symbols": symbols,
        "optimal_weights": optimal_weights,
        "optimization_target": target,
        "expected_return": float(opt_return),
        "expected_volatility": float(opt_std),
        "expected_sharpe": float(opt_sharpe) if opt_sharpe else None
    }


def efficient_frontier(symbols: List[str], period="1y", interval="1d", n_points=20):
    """Generate efficient frontier points"""
    prices = get_portfolio_data(symbols, period, interval)
    returns = prices.pct_change().dropna()
    
    periods_per_year = {"1d": 252, "1wk": 52, "1mo": 12}.get(interval, 252)
    mean_returns = returns.mean() * periods_per_year
    cov_matrix = returns.cov() * periods_per_year
    
    n_assets = len(symbols)
    
    def portfolio_stats(weights):
        portfolio_return = np.dot(weights, mean_returns)
        portfolio_std = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        return portfolio_return, portfolio_std
    
    def portfolio_volatility(weights):
        _, std = portfolio_stats(weights)
        return std
    
    # Get min and max returns
    min_ret = mean_returns.min()
    max_ret = mean_returns.max()
    target_returns = np.linspace(min_ret, max_ret, n_points)
    
    frontier_points = []
    
    for target_ret in target_returns:
        constraints = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
            {'type': 'eq', 'fun': lambda x: np.dot(x, mean_returns) - target_ret}
        ]
        bounds = tuple((0, 1) for _ in range(n_assets))
        initial_weights = np.array([1/n_assets] * n_assets)
        
        result = minimize(portfolio_volatility, initial_weights, method='SLSQP',
                         bounds=bounds, constraints=constraints)
        
        if result.success:
            ret, vol = portfolio_stats(result.x)
            frontier_points.append({
                "return": float(ret),
                "volatility": float(vol),
                "sharpe": float((ret - 0.02) / vol) if vol > 0 else None
            })
    
    return {
        "symbols": symbols,
        "frontier": frontier_points
    }
