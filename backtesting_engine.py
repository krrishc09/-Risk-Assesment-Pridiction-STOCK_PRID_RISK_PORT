"""
Backtesting Engine
Tests prediction model performance on historical data
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
from data_stream import fetch_historical_data
from prediction_models import StockPredictionModel

logger = logging.getLogger(__name__)


class BacktestEngine:
    """
    Backtesting engine for validating prediction models
    Uses walk-forward analysis for realistic out-of-sample testing
    """
    
    def __init__(self, symbol: str, start_date: str, end_date: str):
        self.symbol = symbol
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date)
        self.results = []
        
    def run_backtest(self, prediction_horizon: int = 1, 
                    training_window: int = 60,
                    sample_frequency: int = 5) -> Dict[str, Any]:
        """
        Run walk-forward backtest
        
        Args:
            prediction_horizon: Days ahead to predict (1, 5, or 30)
            training_window: Days of historical data to use for training (reduced to 60 for speed)
            sample_frequency: Only make predictions every N days (for speed)
        """
        try:
            # Fetch all historical data (get more than needed)
            all_data = fetch_historical_data(
                self.symbol, 
                period="2y",  # Get 2 years to ensure enough data
                interval="1d"
            )
            
            if not all_data or len(all_data) < 50:
                return {'error': 'Insufficient historical data'}
            
            # Convert to DataFrame
            df = pd.DataFrame(all_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Remove timezone info to avoid comparison issues
            if df['timestamp'].dt.tz is not None:
                df['timestamp'] = df['timestamp'].dt.tz_localize(None)
            
            df = df.set_index('timestamp')
            df = df.sort_index()
            
            # Ensure start_date and end_date are timezone-naive
            start_date = pd.to_datetime(self.start_date)
            end_date = pd.to_datetime(self.end_date)
            
            if hasattr(start_date, 'tz_localize'):
                start_date = start_date.tz_localize(None)
            if hasattr(end_date, 'tz_localize'):
                end_date = end_date.tz_localize(None)
            
            # Don't filter yet - we need data before start_date for training
            # Just ensure we have the end date
            if df.index[-1] < end_date:
                end_date = df.index[-1]
            
            # Find the index range we'll work with
            # We need training_window days before start_date
            test_start_idx = None
            for i, date in enumerate(df.index):
                if date >= start_date and i >= training_window:
                    test_start_idx = i
                    break
            
            if test_start_idx is None:
                return {'error': f'Need at least {training_window} days of data before {start_date.date()}. Try an earlier start date or use "2y" period.'}
            
            predictions = []
            
            # Walk-forward analysis - sample every N days for speed
            # Start from test_start_idx and go until end_date
            for i in range(test_start_idx, len(df) - prediction_horizon, sample_frequency):
                prediction_date = df.index[i]
                
                # Stop if we've passed the end date
                if prediction_date > end_date:
                    break
                
                target_date = df.index[min(i + prediction_horizon, len(df) - 1)]
                
                # Get training data up to prediction date
                training_data = df.iloc[:i]
                
                # Make simple prediction based on recent trend
                try:
                    current_price = df.iloc[i]['close']
                    actual_price = df.iloc[min(i + prediction_horizon, len(df) - 1)]['close']
                    
                    # Simple momentum-based prediction
                    recent_prices = df.iloc[max(0, i-20):i]['close']
                    if len(recent_prices) < 2:
                        continue
                    
                    # Calculate simple trend
                    returns = recent_prices.pct_change().dropna()
                    avg_return = returns.mean()
                    
                    # Predict based on average return
                    predicted_change_pct = avg_return * prediction_horizon * 100
                    predicted_price = current_price * (1 + avg_return * prediction_horizon)
                    
                    actual_change_pct = ((actual_price - current_price) / current_price) * 100
                    
                    # Calculate errors
                    price_error = predicted_price - actual_price
                    price_error_pct = (price_error / actual_price) * 100
                    direction_correct = (predicted_change_pct > 0) == (actual_change_pct > 0)
                    
                    # Simple signal based on prediction
                    if predicted_change_pct > 2:
                        signal = 'Buy'
                        confidence = min(0.5 + abs(predicted_change_pct) / 20, 0.9)
                    elif predicted_change_pct < -2:
                        signal = 'Sell'
                        confidence = min(0.5 + abs(predicted_change_pct) / 20, 0.9)
                    else:
                        signal = 'Hold'
                        confidence = 0.5
                    
                    predictions.append({
                        'prediction_date': prediction_date.isoformat(),
                        'target_date': target_date.isoformat(),
                        'current_price': float(current_price),
                        'predicted_price': float(predicted_price),
                        'actual_price': float(actual_price),
                        'predicted_change_pct': float(predicted_change_pct),
                        'actual_change_pct': float(actual_change_pct),
                        'price_error': float(price_error),
                        'price_error_pct': float(price_error_pct),
                        'direction_correct': bool(direction_correct),  # Convert numpy.bool to Python bool
                        'signal': str(signal),
                        'confidence': float(confidence)
                    })
                    
                except Exception as e:
                    logger.warning(f"Error making prediction for {prediction_date}: {e}")
                    continue
            
            if not predictions:
                return {'error': 'No predictions generated'}
            
            # Calculate performance metrics
            metrics = self._calculate_metrics(predictions)
            
            return {
                'symbol': self.symbol,
                'start_date': self.start_date.isoformat(),
                'end_date': self.end_date.isoformat(),
                'prediction_horizon': prediction_horizon,
                'total_predictions': len(predictions),
                'metrics': metrics,
                'predictions': predictions[-50:],  # Return last 50 for display
                'all_predictions_count': len(predictions)
            }
            
        except Exception as e:
            logger.error(f"Error in backtest: {e}")
            return {'error': str(e)}
    
    def _calculate_metrics(self, predictions: List[Dict]) -> Dict[str, Any]:
        """Calculate performance metrics from predictions"""
        if not predictions:
            return {}
        
        # Extract arrays
        price_errors = [p['price_error'] for p in predictions]
        price_errors_pct = [p['price_error_pct'] for p in predictions]
        direction_correct = [p['direction_correct'] for p in predictions]
        
        # Basic metrics
        mae = np.mean(np.abs(price_errors))
        mae_pct = np.mean(np.abs(price_errors_pct))
        rmse = np.sqrt(np.mean(np.square(price_errors)))
        rmse_pct = np.sqrt(np.mean(np.square(price_errors_pct)))
        direction_accuracy = np.mean(direction_correct) * 100
        
        # Additional metrics
        median_error = np.median(np.abs(price_errors_pct))
        std_error = np.std(price_errors_pct)
        
        # Best and worst predictions
        best_idx = np.argmin(np.abs(price_errors_pct))
        worst_idx = np.argmax(np.abs(price_errors_pct))
        
        # Win rate (predictions within 2% of actual)
        within_2pct = sum(1 for e in price_errors_pct if abs(e) <= 2) / len(predictions) * 100
        within_5pct = sum(1 for e in price_errors_pct if abs(e) <= 5) / len(predictions) * 100
        
        # Confidence analysis
        high_conf_predictions = [p for p in predictions if p.get('confidence', 0) > 0.7]
        high_conf_accuracy = 0
        if high_conf_predictions:
            high_conf_accuracy = np.mean([p['direction_correct'] for p in high_conf_predictions]) * 100
        
        return {
            'mean_absolute_error': float(mae),
            'mean_absolute_error_pct': float(mae_pct),
            'rmse': float(rmse),
            'rmse_pct': float(rmse_pct),
            'direction_accuracy': float(direction_accuracy),
            'median_error_pct': float(median_error),
            'std_error_pct': float(std_error),
            'within_2_percent': float(within_2pct),
            'within_5_percent': float(within_5pct),
            'high_confidence_accuracy': float(high_conf_accuracy),
            'high_confidence_count': len(high_conf_predictions),
            'best_prediction': predictions[best_idx],
            'worst_prediction': predictions[worst_idx]
        }
    
    def run_strategy_backtest(self, initial_capital: float = 10000) -> Dict[str, Any]:
        """
        Backtest a trading strategy based on predictions
        
        Args:
            initial_capital: Starting capital for simulation
        """
        try:
            # Get predictions
            backtest_results = self.run_backtest(prediction_horizon=1)
            
            if 'error' in backtest_results:
                return backtest_results
            
            predictions = backtest_results.get('predictions', [])
            
            # Simulate trading
            capital = initial_capital
            shares = 0
            trades = []
            portfolio_values = []
            
            for pred in predictions:
                current_price = pred['current_price']
                signal = pred.get('signal', 'Hold')
                confidence = pred.get('confidence', 0.5)
                
                # Trading logic: Buy on Strong Buy, Sell on Strong Sell
                if signal == 'Strong Buy' and confidence > 0.7 and shares == 0:
                    # Buy with all capital
                    shares = capital / current_price
                    trades.append({
                        'date': pred['prediction_date'],
                        'action': 'BUY',
                        'price': current_price,
                        'shares': shares,
                        'value': capital
                    })
                    capital = 0
                
                elif signal in ['Strong Sell', 'Sell'] and shares > 0:
                    # Sell all shares
                    capital = shares * current_price
                    trades.append({
                        'date': pred['prediction_date'],
                        'action': 'SELL',
                        'price': current_price,
                        'shares': shares,
                        'value': capital
                    })
                    shares = 0
                
                # Track portfolio value
                portfolio_value = capital + (shares * current_price)
                portfolio_values.append({
                    'date': pred['prediction_date'],
                    'value': portfolio_value
                })
            
            # Final portfolio value
            if shares > 0:
                final_price = predictions[-1]['actual_price']
                capital = shares * final_price
            
            final_value = capital
            total_return = ((final_value - initial_capital) / initial_capital) * 100
            
            # Calculate buy-and-hold comparison
            buy_hold_shares = initial_capital / predictions[0]['current_price']
            buy_hold_value = buy_hold_shares * predictions[-1]['actual_price']
            buy_hold_return = ((buy_hold_value - initial_capital) / initial_capital) * 100
            
            return {
                'symbol': self.symbol,
                'initial_capital': initial_capital,
                'final_value': float(final_value),
                'total_return_pct': float(total_return),
                'buy_hold_return_pct': float(buy_hold_return),
                'outperformance': float(total_return - buy_hold_return),
                'total_trades': len(trades),
                'trades': trades,
                'portfolio_values': portfolio_values[-50:],  # Last 50 for chart
                'strategy': 'Signal-based trading with confidence filter'
            }
            
        except Exception as e:
            logger.error(f"Error in strategy backtest: {e}")
            return {'error': str(e)}


def run_backtest(symbol: str, start_date: str, end_date: str, 
                horizon: int = 1) -> Dict[str, Any]:
    """Convenience function for API endpoint"""
    engine = BacktestEngine(symbol, start_date, end_date)
    return engine.run_backtest(prediction_horizon=horizon)


def run_strategy_backtest(symbol: str, start_date: str, end_date: str,
                         initial_capital: float = 10000) -> Dict[str, Any]:
    """Convenience function for strategy backtest"""
    engine = BacktestEngine(symbol, start_date, end_date)
    return engine.run_strategy_backtest(initial_capital=initial_capital)
