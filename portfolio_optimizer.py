"""
Portfolio Optimization Engine
Uses Modern Portfolio Theory (MPT) to find optimal asset allocation
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime, timedelta
from data_stream import fetch_historical_data

logger = logging.getLogger(__name__)


class PortfolioOptimizer:
    """
    Portfolio optimization using Modern Portfolio Theory
    Finds optimal weights to maximize Sharpe ratio or minimize risk
    """
    
    def __init__(self, symbols: List[str], period: str = "1y"):
        self.symbols = symbols
        self.period = period
        self.returns_data = None
        self.mean_returns = None
        self.cov_matrix = None
        
    def fetch_data(self) -> bool:
        """Fetch historical data for all symbols"""
        try:
            all_returns = []
            valid_symbols = []
            
            for symbol in self.symbols:
                try:
                    hist_data = fetch_historical_data(symbol, period=self.period, interval="1d")
                    if not hist_data or len(hist_data) < 30:
                        logger.warning(f"Insufficient data for {symbol}")
                        continue
                    
                    prices = pd.Series([d['close'] for d in hist_data])
                    returns = prices.pct_change().dropna()
                    
                    if len(returns) > 0:
                        all_returns.append(returns)
                        valid_symbols.append(symbol)
                except Exception as e:
                    logger.warning(f"Error fetching data for {symbol}: {e}")
                    continue
            
            if len(all_returns) < 2:
                logger.error(f"Need at least 2 stocks for optimization, got {len(all_returns)}")
                return False
            
            # Update symbols to only valid ones
            self.symbols = valid_symbols
            
            # Align all returns to same dates
            self.returns_data = pd.DataFrame(all_returns).T
            self.returns_data.columns = self.symbols
            
            # Remove any NaN values
            self.returns_data = self.returns_data.dropna()
            
            if len(self.returns_data) < 30:
                logger.error("Insufficient overlapping data points")
                return False
            
            # Calculate statistics
            self.mean_returns = self.returns_data.mean()
            self.cov_matrix = self.returns_data.cov()
            
            logger.info(f"Successfully loaded data for {len(self.symbols)} symbols with {len(self.returns_data)} data points")
            return True
            
        except Exception as e:
            logger.error(f"Error fetching data: {e}", exc_info=True)
            return False
    
    def portfolio_performance(self, weights: np.ndarray, risk_free_rate: float = 0.02) -> tuple:
        """Calculate portfolio return, volatility, and Sharpe ratio"""
        # Annualize returns (252 trading days)
        portfolio_return = np.sum(self.mean_returns * weights) * 252
        portfolio_std = np.sqrt(np.dot(weights.T, np.dot(self.cov_matrix * 252, weights)))
        sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_std
        
        return portfolio_return, portfolio_std, sharpe_ratio
    
    def negative_sharpe(self, weights: np.ndarray, risk_free_rate: float = 0.02) -> float:
        """Negative Sharpe ratio for minimization"""
        return -self.portfolio_performance(weights, risk_free_rate)[2]
    
    def portfolio_variance(self, weights: np.ndarray) -> float:
        """Portfolio variance for minimum variance optimization"""
        return np.dot(weights.T, np.dot(self.cov_matrix * 252, weights))
    
    def optimize_sharpe(self, risk_free_rate: float = 0.02) -> Dict[str, Any]:
        """Find portfolio with maximum Sharpe ratio"""
        try:
            num_assets = len(self.symbols)
            
            # Constraints: weights sum to 1
            constraints = {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}
            
            # Bounds: each weight between 0 and 1 (long only)
            bounds = tuple((0, 1) for _ in range(num_assets))
            
            # Initial guess: equal weights
            initial_weights = np.array([1/num_assets] * num_assets)
            
            # Optimize
            result = minimize(
                self.negative_sharpe,
                initial_weights,
                args=(risk_free_rate,),
                method='SLSQP',
                bounds=bounds,
                constraints=constraints,
                options={'maxiter': 1000}
            )
            
            if not result.success:
                logger.warning("Optimization did not converge")
            
            optimal_weights = result.x
            ret, vol, sharpe = self.portfolio_performance(optimal_weights, risk_free_rate)
            
            return {
                'type': 'max_sharpe',
                'weights': {symbol: float(weight) for symbol, weight in zip(self.symbols, optimal_weights)},
                'expected_return': float(ret),
                'volatility': float(vol),
                'sharpe_ratio': float(sharpe),
                'success': result.success
            }
            
        except Exception as e:
            logger.error(f"Error in Sharpe optimization: {e}")
            return None
    
    def optimize_min_variance(self) -> Dict[str, Any]:
        """Find minimum variance portfolio"""
        try:
            num_assets = len(self.symbols)
            
            constraints = {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}
            bounds = tuple((0, 1) for _ in range(num_assets))
            initial_weights = np.array([1/num_assets] * num_assets)
            
            result = minimize(
                self.portfolio_variance,
                initial_weights,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints,
                options={'maxiter': 1000}
            )
            
            optimal_weights = result.x
            ret, vol, sharpe = self.portfolio_performance(optimal_weights)
            
            return {
                'type': 'min_variance',
                'weights': {symbol: float(weight) for symbol, weight in zip(self.symbols, optimal_weights)},
                'expected_return': float(ret),
                'volatility': float(vol),
                'sharpe_ratio': float(sharpe),
                'success': result.success
            }
            
        except Exception as e:
            logger.error(f"Error in min variance optimization: {e}")
            return None
    
    def optimize_target_return(self, target_return: float) -> Dict[str, Any]:
        """Find portfolio with target return and minimum risk"""
        try:
            num_assets = len(self.symbols)
            
            # Constraints: weights sum to 1 AND return equals target
            constraints = [
                {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
                {'type': 'eq', 'fun': lambda x: np.sum(self.mean_returns * x) * 252 - target_return}
            ]
            
            bounds = tuple((0, 1) for _ in range(num_assets))
            initial_weights = np.array([1/num_assets] * num_assets)
            
            result = minimize(
                self.portfolio_variance,
                initial_weights,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints,
                options={'maxiter': 1000}
            )
            
            if not result.success:
                logger.warning(f"Could not achieve target return {target_return}")
                return None
            
            optimal_weights = result.x
            ret, vol, sharpe = self.portfolio_performance(optimal_weights)
            
            return {
                'type': 'target_return',
                'target_return': target_return,
                'weights': {symbol: float(weight) for symbol, weight in zip(self.symbols, optimal_weights)},
                'expected_return': float(ret),
                'volatility': float(vol),
                'sharpe_ratio': float(sharpe),
                'success': result.success
            }
            
        except Exception as e:
            logger.error(f"Error in target return optimization: {e}")
            return None
    
    def efficient_frontier(self, num_portfolios: int = 50) -> List[Dict[str, Any]]:
        """Generate efficient frontier portfolios"""
        try:
            # Get min and max returns
            min_ret = float(self.mean_returns.min() * 252)
            max_ret = float(self.mean_returns.max() * 252)
            
            # Generate target returns
            target_returns = np.linspace(min_ret, max_ret, num_portfolios)
            
            frontier = []
            for target in target_returns:
                portfolio = self.optimize_target_return(target)
                if portfolio:
                    frontier.append(portfolio)
            
            return frontier
            
        except Exception as e:
            logger.error(f"Error generating efficient frontier: {e}")
            return []
    
    def get_current_allocation(self, holdings: List[Dict]) -> Dict[str, float]:
        """Get current portfolio weights"""
        total_value = sum(h['current_value'] for h in holdings)
        if total_value == 0:
            return {}
        
        return {
            h['symbol']: h['current_value'] / total_value
            for h in holdings
        }
    
    def rebalancing_recommendations(self, current_holdings: List[Dict], 
                                   optimal_weights: Dict[str, float]) -> List[Dict[str, Any]]:
        """Generate rebalancing recommendations"""
        try:
            total_value = sum(h['current_value'] for h in current_holdings)
            current_weights = self.get_current_allocation(current_holdings)
            
            recommendations = []
            
            for symbol in self.symbols:
                current_weight = current_weights.get(symbol, 0)
                optimal_weight = optimal_weights.get(symbol, 0)
                
                difference = optimal_weight - current_weight
                dollar_change = difference * total_value
                
                if abs(difference) > 0.01:  # Only recommend if >1% difference
                    action = "BUY" if difference > 0 else "SELL"
                    recommendations.append({
                        'symbol': symbol,
                        'action': action,
                        'current_weight': float(current_weight),
                        'optimal_weight': float(optimal_weight),
                        'difference_pct': float(difference * 100),
                        'dollar_amount': float(abs(dollar_change)),
                        'priority': 'High' if abs(difference) > 0.1 else 'Medium' if abs(difference) > 0.05 else 'Low'
                    })
            
            # Sort by priority
            priority_order = {'High': 0, 'Medium': 1, 'Low': 2}
            recommendations.sort(key=lambda x: (priority_order[x['priority']], -abs(x['difference_pct'])))
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []
    
    def optimize_portfolio(self, current_holdings: List[Dict] = None) -> Dict[str, Any]:
        """Complete portfolio optimization with all strategies"""
        try:
            if not self.fetch_data():
                return {'error': 'Failed to fetch data'}
            
            # Get optimal portfolios
            max_sharpe = self.optimize_sharpe()
            min_variance = self.optimize_min_variance()
            
            # Get current allocation
            current_allocation = None
            rebalancing = None
            
            if current_holdings:
                current_allocation = self.get_current_allocation(current_holdings)
                if max_sharpe:
                    rebalancing = self.rebalancing_recommendations(
                        current_holdings, 
                        max_sharpe['weights']
                    )
            
            return {
                'timestamp': datetime.now().isoformat(),
                'symbols': self.symbols,
                'max_sharpe_portfolio': max_sharpe,
                'min_variance_portfolio': min_variance,
                'current_allocation': current_allocation,
                'rebalancing_recommendations': rebalancing,
                'statistics': {
                    'mean_returns': {symbol: float(ret) for symbol, ret in self.mean_returns.items()},
                    'correlation_matrix': self.returns_data.corr().to_dict()
                }
            }
            
        except Exception as e:
            logger.error(f"Error in portfolio optimization: {e}")
            return {'error': str(e)}


def optimize_portfolio_endpoint(symbols: List[str], current_holdings: List[Dict] = None) -> Dict[str, Any]:
    """Convenience function for API endpoint"""
    optimizer = PortfolioOptimizer(symbols)
    return optimizer.optimize_portfolio(current_holdings)
