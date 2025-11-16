# utils.py
import numpy as np
import pandas as pd
import yfinance as yf


def _periods_per_year(interval: str):
    mapping = {
        "1d": 252,
        "1wk": 52,
        "1mo": 12
    }
    return mapping.get(interval, 252)


def annualized_volatility(returns, interval):
    r = np.asarray(returns)
    return float(np.std(r, ddof=1) * np.sqrt(_periods_per_year(interval)))


def annualized_return(returns, interval):
    r = np.asarray(returns)
    n = len(r)
    if n == 0:
        return 0.0
    compounded = np.prod(1 + r)
    return float(compounded ** (_periods_per_year(interval) / n) - 1)


def sharpe_ratio(returns, risk_free_rate, interval):
    r = np.asarray(returns)
    if len(r) == 0:
        return None
    mean_ann = np.mean(r) * _periods_per_year(interval)
    vol_ann = np.std(r, ddof=1) * np.sqrt(_periods_per_year(interval))
    if vol_ann == 0:
        return None
    return float((mean_ann - risk_free_rate) / vol_ann)


def max_drawdown(prices):
    p = pd.Series(prices).dropna()
    running_max = p.cummax()
    drawdown = (p - running_max) / running_max
    return float(drawdown.min())


def value_at_risk(returns, confidence=0.95):
    r = np.asarray(returns)
    alpha = 1 - confidence
    return float(np.percentile(r, alpha * 100))


def conditional_var(returns, confidence=0.95):
    """Conditional Value at Risk (CVaR) - expected loss beyond VaR"""
    r = np.asarray(returns)
    var = value_at_risk(r, confidence)
    return float(np.mean(r[r <= var]))


def sortino_ratio(returns, risk_free_rate, interval):
    """Sortino ratio - return per unit of downside risk"""
    r = np.asarray(returns)
    if len(r) == 0:
        return None
    mean_ann = np.mean(r) * _periods_per_year(interval)
    downside = r[r < 0]
    if len(downside) == 0:
        return None
    downside_std = np.std(downside, ddof=1) * np.sqrt(_periods_per_year(interval))
    if downside_std == 0:
        return None
    return float((mean_ann - risk_free_rate) / downside_std)


def beta(stock_returns, market_returns):
    """Beta - systematic risk relative to market"""
    s = np.asarray(stock_returns)
    m = np.asarray(market_returns)
    if len(s) != len(m) or len(s) == 0:
        return None
    covariance = np.cov(s, m)[0][1]
    market_variance = np.var(m, ddof=1)
    if market_variance == 0:
        return None
    return float(covariance / market_variance)


def correlation(returns1, returns2):
    """Correlation coefficient between two return series"""
    r1 = np.asarray(returns1)
    r2 = np.asarray(returns2)
    if len(r1) != len(r2) or len(r1) < 2:
        return None
    return float(np.corrcoef(r1, r2)[0][1])


def calmar_ratio(returns, max_dd, interval):
    """Calmar ratio - return per unit of maximum drawdown"""
    if max_dd >= 0:
        return None
    ann_ret = annualized_return(returns, interval)
    return float(ann_ret / abs(max_dd))


def information_ratio(returns, benchmark_returns, interval):
    """Information ratio - excess return per unit of tracking error"""
    r = np.asarray(returns)
    b = np.asarray(benchmark_returns)
    if len(r) != len(b) or len(r) == 0:
        return None
    excess = r - b
    tracking_error = np.std(excess, ddof=1) * np.sqrt(_periods_per_year(interval))
    if tracking_error == 0:
        return None
    excess_return = np.mean(excess) * _periods_per_year(interval)
    return float(excess_return / tracking_error)


def skewness(returns):
    """Skewness - asymmetry of return distribution"""
    r = np.asarray(returns)
    if len(r) < 3:
        return None
    return float(pd.Series(r).skew())


def kurtosis(returns):
    """Kurtosis - tail heaviness of return distribution"""
    r = np.asarray(returns)
    if len(r) < 4:
        return None
    return float(pd.Series(r).kurtosis())


def analyze_stock_risk(symbol: str, period="1y", interval="1d", benchmark="^GSPC"):
    """Comprehensive stock risk analysis with advanced metrics"""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)

        if df.empty:
            raise ValueError(f"No data available for symbol '{symbol}'. Please check if the ticker is valid and try again.")
    except Exception as e:
        if "No data" in str(e):
            raise
        raise ValueError(f"Error fetching data for '{symbol}': {str(e)}")

    prices = df["Close"].dropna()
    returns = prices.pct_change().dropna()
    
    # Fetch benchmark data for beta and correlation
    benchmark_data = None
    beta_val = None
    corr_val = None
    info_ratio = None
    
    try:
        benchmark_ticker = yf.Ticker(benchmark)
        benchmark_df = benchmark_ticker.history(period=period, interval=interval)
        if not benchmark_df.empty:
            benchmark_prices = benchmark_df["Close"].dropna()
            benchmark_returns = benchmark_prices.pct_change().dropna()
            
            # Align dates
            common_idx = returns.index.intersection(benchmark_returns.index)
            if len(common_idx) > 0:
                aligned_returns = returns.loc[common_idx]
                aligned_benchmark = benchmark_returns.loc[common_idx]
                beta_val = beta(aligned_returns, aligned_benchmark)
                corr_val = correlation(aligned_returns, aligned_benchmark)
                info_ratio = information_ratio(aligned_returns, aligned_benchmark, interval)
    except:
        pass  # Benchmark data optional
    
    risk_free_rate = 0.02
    max_dd = max_drawdown(prices)
    var_95 = value_at_risk(returns, 0.95)
    cvar_95 = conditional_var(returns, 0.95)

    return {
        "symbol": symbol,
        "period": period,
        "interval": interval,
        "benchmark": benchmark,
        "sample_size": len(returns),
        
        # Return metrics
        "annualized_return": annualized_return(returns, interval),
        "annualized_volatility": annualized_volatility(returns, interval),
        
        # Risk-adjusted returns
        "sharpe_ratio": sharpe_ratio(returns, risk_free_rate, interval),
        "sortino_ratio": sortino_ratio(returns, risk_free_rate, interval),
        "calmar_ratio": calmar_ratio(returns, max_dd, interval),
        "information_ratio": info_ratio,
        
        # Downside risk
        "max_drawdown": max_dd,
        "var_95": var_95,
        "cvar_95": cvar_95,
        
        # Market risk
        "beta": beta_val,
        "correlation_with_benchmark": corr_val,
        
        # Distribution statistics
        "skewness": skewness(returns),
        "kurtosis": kurtosis(returns),
        
        # Price data
        "current_price": float(prices.iloc[-1]),
        "price_52w_high": float(prices.max()),
        "price_52w_low": float(prices.min())
    }
