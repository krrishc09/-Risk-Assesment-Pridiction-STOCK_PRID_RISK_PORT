# risk_models.py
"""
Advanced Risk Models for Portfolio and Individual Stocks
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any
import logging

from utils import annualized_volatility, annualized_return, sharpe_ratio, max_drawdown, value_at_risk, conditional_var, beta
from data_stream import fetch_historical_data

logger = logging.getLogger(__name__)


class StockRiskModel:
    """Comprehensive risk assessment for individual stocks"""
    
    def __init__(self, symbol: str, period: str = "1y"):
        self.symbol = symbol
        self.period = period
        
    def calculate_all_metrics(self) -> Dict[str, Any]:
        """Calculate all risk metrics"""
        try:
            hist_data = fetch_historical_data(self.symbol, period=self.period, interval="1d")
            if not hist_data or len(hist_data) < 30:
                return {"error": "Insufficient data"}
            
            prices = pd.Series([d['close'] for d in hist_data])
            returns = prices.pct_change().dropna()
            
            # Calculate metrics
            volatility = annualized_volatility(returns, "1d")
            ann_return = annualized_return(returns, "1d")
            max_dd = max_drawdown(prices)
            var_95 = value_at_risk(returns, 0.95)
            cvar_95 = conditional_var(returns, 0.95)
            
            # Risk score calculation
            risk_score = self._calculate_risk_score(volatility, max_dd, var_95)
            risk_level = self._get_risk_level(risk_score)
            
            return {
                "symbol": self.symbol,
                "volatility": float(volatility),
                "annualized_return": float(ann_return),
                "max_drawdown": float(max_dd),
                "var_95": float(var_95),
                "cvar_95": float(cvar_95),
                "risk_score": float(risk_score),
                "risk_level": risk_level,
                "risk_factors": self._identify_risk_factors(volatility, max_dd, var_95),
                "recommendations": self._generate_recommendations(risk_score, volatility, max_dd)
            }
        except Exception as e:
            logger.error(f"Error: {e}")
            return {"error": str(e)}
    
    def _calculate_risk_score(self, vol: float, max_dd: float, var: float) -> float:
        """Calculate 0-10 risk score"""
        score = 5.0
        if vol > 0.40: score += 2.5
        elif vol > 0.30: score += 1.5
        elif vol > 0.20: score += 0.5
        
        if max_dd < -0.30: score += 2
        elif max_dd < -0.20: score += 1
        
        if var < -0.04: score += 1.5
        elif var < -0.03: score += 1
        
        return max(0, min(10, score))
    
    def _get_risk_level(self, score: float) -> str:
        """Convert score to risk level"""
        if score < 3: return "Low"
        elif score < 6: return "Moderate"
        elif score < 8: return "High"
        else: return "Very High"
    
    def _identify_risk_factors(self, vol: float, max_dd: float, var: float) -> List[str]:
        """Identify key risk factors"""
        factors = []
        if vol > 0.35:
            factors.append(f"High volatility ({vol:.1%})")
        if max_dd < -0.25:
            factors.append(f"Large drawdown ({max_dd:.1%})")
        if var < -0.04:
            factors.append(f"High VaR ({var:.1%})")
        return factors or ["No major risk factors"]
    
    def _generate_recommendations(self, score: float, vol: float, max_dd: float) -> List[str]:
        """Generate recommendations"""
        recs = []
        if score > 7:
            recs.append("⚠️ High risk - consider reducing position size")
        if vol > 0.35:
            recs.append("📊 High volatility - use stop-loss orders")
        if max_dd < -0.30:
            recs.append("📉 Large drawdowns - requires long-term horizon")
        return recs or ["✅ Acceptable risk profile"]


class PortfolioRiskModel:
    """Comprehensive portfolio risk assessment"""
    
    def __init__(self, holdings: List[Dict[str, Any]], period: str = "1y"):
        self.holdings = holdings
        self.period = period
    
    def calculate_all_metrics(self) -> Dict[str, Any]:
        """Calculate portfolio risk metrics"""
        try:
            if not self.holdings:
                return {"error": "No holdings"}
            
            # Get individual stock metrics
            stock_metrics = []
            for holding in self.holdings:
                model = StockRiskModel(holding['symbol'], self.period)
                metrics = model.calculate_all_metrics()
                if 'error' not in metrics:
                    metrics['weight'] = holding.get('weight', 0)
                    stock_metrics.append(metrics)
            
            # Portfolio metrics
            concentration = max([h.get('weight', 0) for h in self.holdings])
            weighted_vol = sum(m['volatility'] * m['weight'] / 100 for m in stock_metrics)
            weighted_var = sum(m['var_95'] * m['weight'] / 100 for m in stock_metrics)
            
            # Risk score
            risk_score = self._calculate_portfolio_risk_score(
                len(self.holdings), concentration, weighted_vol
            )
            risk_level = self._get_risk_level(risk_score)
            
            # Identify risky stocks
            high_risk = [m for m in stock_metrics if m['risk_score'] >= 6.5]
            
            return {
                "holdings_count": len(self.holdings),
                "concentration_risk": float(concentration),
                "weighted_volatility": float(weighted_vol),
                "weighted_var_95": float(weighted_var),
                "risk_score": float(risk_score),
                "risk_level": risk_level,
                "high_risk_stocks": [{"symbol": s['symbol'], "risk_score": s['risk_score']} for s in high_risk],
                "risk_factors": self._identify_portfolio_risks(len(self.holdings), concentration, weighted_vol),
                "recommendations": self._generate_portfolio_recommendations(risk_score, len(self.holdings), concentration)
            }
        except Exception as e:
            logger.error(f"Error: {e}")
            return {"error": str(e)}
    
    def _calculate_portfolio_risk_score(self, n_holdings: int, concentration: float, weighted_vol: float) -> float:
        """Calculate portfolio risk score"""
        score = 5.0
        
        if concentration > 35: score += 2
        elif concentration > 25: score += 1
        
        if n_holdings < 5: score += 1.5
        elif n_holdings < 10: score += 0.5
        
        if weighted_vol > 0.30: score += 2
        elif weighted_vol > 0.20: score += 1
        
        return max(0, min(10, score))
    
    def _get_risk_level(self, score: float) -> str:
        """Convert score to risk level"""
        if score < 3: return "Low"
        elif score < 6: return "Moderate"
        elif score < 8: return "High"
        else: return "Very High"
    
    def _identify_portfolio_risks(self, n_holdings: int, concentration: float, weighted_vol: float) -> List[str]:
        """Identify portfolio risk factors"""
        factors = []
        if concentration > 30:
            factors.append(f"High concentration ({concentration:.1f}% in largest position)")
        if n_holdings < 5:
            factors.append(f"Limited diversification ({n_holdings} holdings)")
        if weighted_vol > 0.25:
            factors.append(f"High portfolio volatility ({weighted_vol:.1%})")
        return factors or ["Well-diversified portfolio"]
    
    def _generate_portfolio_recommendations(self, score: float, n_holdings: int, concentration: float) -> List[str]:
        """Generate portfolio recommendations"""
        recs = []
        if score > 7:
            recs.append("⚠️ High portfolio risk - consider rebalancing")
        if n_holdings < 8:
            recs.append("📊 Add more holdings for better diversification")
        if concentration > 30:
            recs.append("💡 Reduce concentration in largest positions")
        return recs or ["✅ Portfolio is well-balanced"]
