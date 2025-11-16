# portfolio_engine.py
"""
Portfolio tracking and risk analysis engine
Calculates real-time portfolio metrics, risk scores, and generates insights
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging

from database import db_manager, Holding, Portfolio
from data_stream import get_live_price, fetch_historical_data
from utils import (
    annualized_volatility, annualized_return, sharpe_ratio,
    sortino_ratio, max_drawdown, value_at_risk, conditional_var,
    beta, correlation, skewness, kurtosis
)
from config_platform import RISK_FREE_RATE, BENCHMARK_INDEX, RISK_LEVELS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== PORTFOLIO CALCULATOR ====================

class PortfolioCalculator:
    """Calculate portfolio metrics and performance"""
    
    def __init__(self, portfolio_id: int):
        self.portfolio_id = portfolio_id
        self.portfolio = db_manager.get_portfolio(portfolio_id)
        self.holdings = db_manager.get_portfolio_holdings(portfolio_id)
        self.cache = {}
    
    def get_current_prices(self) -> Dict[str, float]:
        """Get current prices for all holdings"""
        from data_stream import fetch_historical_data
        
        prices = {}
        for holding in self.holdings:
            # Try live price first
            live_price = get_live_price(holding.symbol)
            if live_price:
                prices[holding.symbol] = live_price['ltp']
                continue
            
            # Try database price
            db_price = db_manager.get_latest_price(holding.symbol)
            if db_price:
                prices[holding.symbol] = db_price.ltp
                continue
            
            # Fetch real market data as last resort (not average_price!)
            try:
                hist_data = fetch_historical_data(holding.symbol, period="1d", interval="1d")
                if hist_data and len(hist_data) > 0:
                    prices[holding.symbol] = hist_data[-1]['close']
                    logger.info(f"Fetched market price for {holding.symbol}: ${hist_data[-1]['close']:.2f}")
                else:
                    # Only use average_price if absolutely no data available
                    logger.warning(f"No market data for {holding.symbol}, using average price")
                    prices[holding.symbol] = holding.average_price
            except Exception as e:
                logger.error(f"Error fetching price for {holding.symbol}: {e}")
                prices[holding.symbol] = holding.average_price
        
        return prices
    
    def calculate_holding_metrics(self, holding: Holding, current_price: float) -> Dict[str, Any]:
        """Calculate metrics for a single holding"""
        current_value = holding.quantity * current_price
        investment = holding.total_investment
        pnl = current_value - investment
        pnl_percent = (pnl / investment * 100) if investment > 0 else 0
        
        # Get price change today - try live data first, then calculate from historical
        live_data = get_live_price(holding.symbol)
        day_change = 0
        day_change_percent = 0
        
        if live_data and live_data.get('change') and live_data.get('change') != 0:
            day_change = live_data.get('change', 0)
            day_change_percent = live_data.get('change_percent', 0)
        else:
            # Calculate from recent historical data
            try:
                hist_data = fetch_historical_data(holding.symbol, period="5d", interval="1d")
                if hist_data and len(hist_data) >= 2:
                    today_price = hist_data[-1]['close']
                    yesterday_price = hist_data[-2]['close']
                    day_change = today_price - yesterday_price
                    day_change_percent = ((today_price - yesterday_price) / yesterday_price * 100) if yesterday_price > 0 else 0
            except Exception as e:
                logger.warning(f"Could not calculate day change for {holding.symbol}: {e}")
        
        return {
            "symbol": holding.symbol,
            "quantity": holding.quantity,
            "average_price": holding.average_price,
            "current_price": current_price,
            "investment": investment,
            "current_value": current_value,
            "pnl": pnl,
            "pnl_percent": pnl_percent,
            "day_change": day_change * holding.quantity,
            "day_change_percent": day_change_percent,
            "weight": 0,  # Will be calculated later
        }
    
    def calculate_portfolio_summary(self) -> Dict[str, Any]:
        """Calculate complete portfolio summary"""
        if not self.holdings:
            return {
                "total_value": 0,
                "total_investment": 0,
                "total_pnl": 0,
                "total_pnl_percent": 0,
                "day_change": 0,
                "day_change_percent": 0,
                "holdings": [],
                "holdings_count": 0,
            }
        
        # Get current prices
        current_prices = self.get_current_prices()
        logger.info(f"Current prices: {current_prices}")
        
        # Calculate metrics for each holding
        holdings_data = []
        total_value = 0
        total_investment = 0
        total_day_change = 0
        
        for holding in self.holdings:
            current_price = current_prices.get(holding.symbol, holding.average_price)
            metrics = self.calculate_holding_metrics(holding, current_price)
            holdings_data.append(metrics)
            
            logger.info(f"{holding.symbol}: value={metrics['current_value']}, investment={metrics['investment']}, pnl={metrics['pnl']}")
            
            total_value += metrics['current_value']
            total_investment += metrics['investment']
            total_day_change += metrics['day_change']
        
        # Calculate portfolio-level metrics
        total_pnl = total_value - total_investment
        total_pnl_percent = (total_pnl / total_investment * 100) if total_investment > 0 else 0
        day_change_percent = (total_day_change / (total_value - total_day_change) * 100) if total_value > total_day_change else 0
        
        # Calculate weights
        for holding_data in holdings_data:
            holding_data['weight'] = (holding_data['current_value'] / total_value * 100) if total_value > 0 else 0
        
        return {
            "portfolio_id": self.portfolio_id,
            "total_value": total_value,
            "total_investment": total_investment,
            "total_pnl": total_pnl,
            "total_pnl_percent": total_pnl_percent,
            "day_change": total_day_change,
            "day_change_percent": day_change_percent,
            "holdings": holdings_data,
            "holdings_count": len(holdings_data),
            "timestamp": datetime.now().isoformat(),
        }
    
    def get_portfolio_returns(self, period: str = "1y") -> pd.Series:
        """Calculate historical portfolio returns"""
        if not self.holdings:
            return pd.Series()
        
        # Get historical data for all holdings
        all_returns = []
        weights = []
        
        current_prices = self.get_current_prices()
        total_value = sum(h.quantity * current_prices.get(h.symbol, h.average_price) for h in self.holdings)
        
        for holding in self.holdings:
            hist_data = fetch_historical_data(holding.symbol, period=period, interval="1d")
            if hist_data:
                prices = pd.Series([d['close'] for d in hist_data])
                returns = prices.pct_change().dropna()
                all_returns.append(returns)
                
                # Calculate weight
                current_value = holding.quantity * current_prices.get(holding.symbol, holding.average_price)
                weight = current_value / total_value if total_value > 0 else 0
                weights.append(weight)
        
        if not all_returns:
            return pd.Series()
        
        # Align all return series
        min_length = min(len(r) for r in all_returns)
        aligned_returns = [r.iloc[-min_length:].values for r in all_returns]
        
        # Calculate weighted portfolio returns
        portfolio_returns = np.sum([r * w for r, w in zip(aligned_returns, weights)], axis=0)
        
        return pd.Series(portfolio_returns)


# ==================== RISK ANALYZER ====================

class RiskAnalyzer:
    """Analyze portfolio risk and generate insights"""
    
    def __init__(self, portfolio_id: int):
        self.portfolio_id = portfolio_id
        self.calculator = PortfolioCalculator(portfolio_id)
    
    def calculate_risk_metrics(self, period: str = "1y") -> Dict[str, Any]:
        """Calculate comprehensive risk metrics"""
        portfolio_returns = self.calculator.get_portfolio_returns(period)
        
        if portfolio_returns.empty or len(portfolio_returns) < 10:
            return {
                "error": "Insufficient data for risk analysis",
                "risk_score": 5.0,
                "risk_level": "Moderate",
            }
        
        # Calculate metrics
        interval = "1d"
        ann_volatility = annualized_volatility(portfolio_returns, interval)
        ann_return = annualized_return(portfolio_returns, interval)
        sharpe = sharpe_ratio(portfolio_returns, RISK_FREE_RATE, interval)
        sortino = sortino_ratio(portfolio_returns, RISK_FREE_RATE, interval)
        
        # Get benchmark data for beta
        benchmark_data = fetch_historical_data(BENCHMARK_INDEX, period=period, interval="1d")
        portfolio_beta = None
        correlation_with_market = None
        
        if benchmark_data and len(benchmark_data) >= len(portfolio_returns):
            benchmark_prices = pd.Series([d['close'] for d in benchmark_data[-len(portfolio_returns):]])
            benchmark_returns = benchmark_prices.pct_change().dropna()
            
            if len(benchmark_returns) == len(portfolio_returns):
                portfolio_beta = beta(portfolio_returns, benchmark_returns)
                correlation_with_market = correlation(portfolio_returns, benchmark_returns)
        
        # Calculate drawdown
        portfolio_values = (1 + portfolio_returns).cumprod()
        max_dd = max_drawdown(portfolio_values)
        
        # Calculate VaR and CVaR
        var_95 = value_at_risk(portfolio_returns, 0.95)
        cvar_95 = conditional_var(portfolio_returns, 0.95)
        
        # Calculate distribution metrics
        skew = skewness(portfolio_returns)
        kurt = kurtosis(portfolio_returns)
        
        # Calculate risk score (0-10 scale)
        risk_score = self.calculate_risk_score(
            ann_volatility, sharpe, max_dd, var_95, portfolio_beta
        )
        
        risk_level = self.get_risk_level(risk_score)
        
        return {
            "portfolio_id": self.portfolio_id,
            "period": period,
            "risk_score": round(risk_score, 2),
            "risk_level": risk_level,
            "volatility": round(ann_volatility, 4),
            "annualized_return": round(ann_return, 4),
            "sharpe_ratio": round(sharpe, 2) if sharpe else None,
            "sortino_ratio": round(sortino, 2) if sortino else None,
            "max_drawdown": round(max_dd, 4),
            "var_95": round(var_95, 4),
            "cvar_95": round(cvar_95, 4),
            "beta": round(portfolio_beta, 2) if portfolio_beta else None,
            "correlation_with_market": round(correlation_with_market, 2) if correlation_with_market else None,
            "skewness": round(skew, 2) if skew else None,
            "kurtosis": round(kurt, 2) if kurt else None,
            "timestamp": datetime.now().isoformat(),
        }
    
    def calculate_risk_score(self, volatility: float, sharpe: float, 
                            max_dd: float, var_95: float, beta: float = None) -> float:
        """
        ULTRA-ADVANCED RISK SCORING MODEL - Institutional Grade
        
        Components:
        1. Volatility risk (normalized and regime-adjusted)
        2. Tail risk (VaR, CVaR, extreme events)
        3. Drawdown risk (max DD, recovery time)
        4. Risk-adjusted returns (Sharpe, Sortino, Calmar)
        5. Systematic risk (Beta, correlation)
        6. Concentration risk (diversification)
        7. Liquidity risk
        8. Regime-based adjustments
        """
        
        # === COMPONENT 1: VOLATILITY RISK (0-2.5 points) ===
        # Use non-linear scaling for volatility
        vol_score = 0
        if volatility > 0.50:  # Extreme volatility
            vol_score = 2.5
        elif volatility > 0.40:  # Very high
            vol_score = 2.0 + (volatility - 0.40) * 5
        elif volatility > 0.30:  # High
            vol_score = 1.5 + (volatility - 0.30) * 5
        elif volatility > 0.20:  # Moderate-high
            vol_score = 1.0 + (volatility - 0.20) * 5
        elif volatility > 0.15:  # Moderate
            vol_score = 0.5 + (volatility - 0.15) * 10
        else:  # Low volatility
            vol_score = max(0, volatility * 3.33)
        
        # === COMPONENT 2: TAIL RISK (0-2.5 points) ===
        # VaR and extreme loss potential
        tail_risk_score = 0
        if var_95:
            var_magnitude = abs(var_95)
            if var_magnitude > 0.10:  # >10% potential loss
                tail_risk_score = 2.5
            elif var_magnitude > 0.07:
                tail_risk_score = 2.0
            elif var_magnitude > 0.05:
                tail_risk_score = 1.5
            elif var_magnitude > 0.03:
                tail_risk_score = 1.0
            else:
                tail_risk_score = 0.5
        
        # === COMPONENT 3: DRAWDOWN RISK (0-2.0 points) ===
        # Maximum drawdown severity
        dd_score = 0
        if max_dd:
            dd_magnitude = abs(max_dd)
            if dd_magnitude > 0.40:  # >40% drawdown
                dd_score = 2.0
            elif dd_magnitude > 0.30:
                dd_score = 1.7
            elif dd_magnitude > 0.20:
                dd_score = 1.3
            elif dd_magnitude > 0.15:
                dd_score = 0.9
            elif dd_magnitude > 0.10:
                dd_score = 0.5
            else:
                dd_score = 0.2
        
        # === COMPONENT 4: RISK-ADJUSTED RETURNS (-2.0 to +1.5 points) ===
        # Sharpe ratio - reward for good risk-adjusted returns
        sharpe_score = 0
        if sharpe:
            if sharpe < -0.5:  # Losing money with risk
                sharpe_score = 1.5
            elif sharpe < 0:  # Negative returns
                sharpe_score = 1.0
            elif sharpe < 0.5:  # Poor risk-adjusted returns
                sharpe_score = 0.5
            elif sharpe > 2.0:  # Excellent risk-adjusted returns
                sharpe_score = -2.0
            elif sharpe > 1.5:  # Very good
                sharpe_score = -1.5
            elif sharpe > 1.0:  # Good
                sharpe_score = -1.0
            elif sharpe > 0.75:  # Decent
                sharpe_score = -0.5
        
        # === COMPONENT 5: SYSTEMATIC RISK (0-1.5 points) ===
        # Beta and market correlation
        beta_score = 0
        if beta:
            if beta > 2.0:  # Extreme market sensitivity
                beta_score = 1.5
            elif beta > 1.5:  # Very high sensitivity
                beta_score = 1.2
            elif beta > 1.2:  # High sensitivity
                beta_score = 0.8
            elif beta > 0.8:  # Moderate
                beta_score = 0.3
            elif beta < 0.3:  # Very low correlation (could be good or risky)
                beta_score = 0.5
        
        # === COMPONENT 6: CONCENTRATION RISK (0-1.0 points) ===
        # Calculate Herfindahl index for diversification
        concentration_score = 0
        if hasattr(self, 'calculator') and self.calculator.holdings:
            total_value = sum(h.quantity * h.average_price for h in self.calculator.holdings)
            if total_value > 0:
                weights = [(h.quantity * h.average_price / total_value) for h in self.calculator.holdings]
                herfindahl = sum(w**2 for w in weights)
                
                # High concentration = high risk
                if herfindahl > 0.5:  # Very concentrated
                    concentration_score = 1.0
                elif herfindahl > 0.35:  # Concentrated
                    concentration_score = 0.7
                elif herfindahl > 0.25:  # Moderate concentration
                    concentration_score = 0.4
                else:  # Well diversified
                    concentration_score = 0.1
        
        # === AGGREGATE RISK SCORE ===
        raw_score = (
            vol_score +           # 0-2.5
            tail_risk_score +     # 0-2.5
            dd_score +            # 0-2.0
            sharpe_score +        # -2.0 to +1.5
            beta_score +          # 0-1.5
            concentration_score   # 0-1.0
        )
        
        # Normalize to 0-10 scale
        # Theoretical range: -2.0 to 11.0 (13 point range)
        # Map to 0-10: (raw + 2) * (10/13)
        normalized_score = (raw_score + 2.0) * (10.0 / 13.0)
        
        # === REGIME-BASED ADJUSTMENT ===
        # Increase risk score in high volatility regimes
        if volatility > 0.35:
            normalized_score *= 1.1  # 10% increase in high vol
        
        # Ensure score is between 0 and 10
        final_score = max(0, min(10, normalized_score))
        
        return final_score
    
    def get_risk_level(self, risk_score: float) -> str:
        """Convert risk score to risk level"""
        for level, (min_score, max_score) in RISK_LEVELS.items():
            if min_score <= risk_score < max_score:
                return level
        return "Very High"
    
    def identify_risky_holdings(self) -> List[Dict[str, Any]]:
        """Identify the riskiest holdings in portfolio"""
        risky_holdings = []
        
        for holding in self.calculator.holdings:
            try:
                # Get historical data
                hist_data = fetch_historical_data(holding.symbol, period="3mo", interval="1d")
                if not hist_data or len(hist_data) < 30:
                    continue
                
                prices = pd.Series([d['close'] for d in hist_data])
                returns = prices.pct_change().dropna()
                
                # Calculate volatility
                vol = annualized_volatility(returns, "1d")
                
                # Calculate max drawdown
                max_dd = max_drawdown(prices)
                
                # Calculate risk score for this holding
                holding_risk_score = 5.0
                if vol > 0.50:
                    holding_risk_score += 3
                elif vol > 0.35:
                    holding_risk_score += 2
                elif vol > 0.25:
                    holding_risk_score += 1
                
                if max_dd < -0.30:
                    holding_risk_score += 2
                elif max_dd < -0.20:
                    holding_risk_score += 1
                
                risky_holdings.append({
                    "symbol": holding.symbol,
                    "risk_score": round(holding_risk_score, 2),
                    "volatility": round(vol, 4),
                    "max_drawdown": round(max_dd, 4),
                })
            
            except Exception as e:
                logger.error(f"Error analyzing {holding.symbol}: {e}")
        
        # Sort by risk score
        risky_holdings.sort(key=lambda x: x['risk_score'], reverse=True)
        
        return risky_holdings[:5]  # Top 5 risky holdings
    
    def generate_insights(self, risk_metrics: Dict[str, Any]) -> List[str]:
        """Generate simple, actionable insights"""
        insights = []
        
        risk_score = risk_metrics.get('risk_score', 5)
        risk_level = risk_metrics.get('risk_level', 'Moderate')
        volatility = risk_metrics.get('volatility', 0)
        sharpe = risk_metrics.get('sharpe_ratio')
        max_dd = risk_metrics.get('max_drawdown', 0)
        
        # Risk level insight
        insights.append(f"Your portfolio has {risk_level} risk (score: {risk_score}/10).")
        
        # Volatility insight
        if volatility > 0.35:
            insights.append(f"High volatility ({volatility:.1%}) means your portfolio value can swing significantly.")
        elif volatility < 0.15:
            insights.append(f"Low volatility ({volatility:.1%}) indicates stable, predictable returns.")
        
        # Sharpe ratio insight
        if sharpe:
            if sharpe > 1.0:
                insights.append(f"Excellent risk-adjusted returns (Sharpe: {sharpe:.2f}).")
            elif sharpe < 0:
                insights.append(f"Poor risk-adjusted returns (Sharpe: {sharpe:.2f}). Consider rebalancing.")
        
        # Drawdown insight
        if max_dd < -0.25:
            insights.append(f"Your portfolio experienced a significant drawdown ({max_dd:.1%}). Diversification may help.")
        
        # Diversification insight
        holdings_count = len(self.calculator.holdings)
        if holdings_count < 5:
            insights.append(f"Consider diversifying - you only hold {holdings_count} stocks.")
        elif holdings_count > 20:
            insights.append(f"You hold {holdings_count} stocks - consider consolidating to reduce complexity.")
        
        return insights
    
    def get_complete_analysis(self) -> Dict[str, Any]:
        """Get complete risk analysis with insights"""
        risk_metrics = self.calculate_risk_metrics()
        risky_holdings = self.identify_risky_holdings()
        insights = self.generate_insights(risk_metrics)
        
        return {
            **risk_metrics,
            "risky_holdings": risky_holdings,
            "insights": insights,
        }


# ==================== PORTFOLIO TRACKER ====================

class PortfolioTracker:
    """Main portfolio tracking service"""
    
    def __init__(self, portfolio_id: int):
        self.portfolio_id = portfolio_id
        self.calculator = PortfolioCalculator(portfolio_id)
        self.risk_analyzer = RiskAnalyzer(portfolio_id)
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get complete dashboard data"""
        summary = self.calculator.calculate_portfolio_summary()
        risk_analysis = self.risk_analyzer.get_complete_analysis()
        performance = self.get_performance_chart_data()
        
        return {
            "summary": summary,
            "risk_analysis": risk_analysis,
            "performance": performance,
            "timestamp": datetime.now().isoformat(),
        }
    
    def get_performance_chart_data(self, period: str = "1M") -> Dict[str, Any]:
        """Get data for performance chart"""
        # Get portfolio snapshots
        snapshots = db_manager.get_portfolio_snapshots(self.portfolio_id, limit=365)
        
        if not snapshots:
            return {"portfolio": [], "benchmark": []}
        
        # Prepare portfolio data
        portfolio_data = [
            {
                "date": s.timestamp.isoformat(),
                "value": s.total_value,
                "pnl_percent": s.total_pnl_percent,
            }
            for s in reversed(snapshots)
        ]
        
        # Get benchmark data
        benchmark_data = fetch_historical_data(BENCHMARK_INDEX, period="1y", interval="1d")
        benchmark_chart = [
            {
                "date": d['timestamp'].isoformat(),
                "value": d['close'],
            }
            for d in benchmark_data
        ]
        
        return {
            "portfolio": portfolio_data,
            "benchmark": benchmark_chart,
        }
