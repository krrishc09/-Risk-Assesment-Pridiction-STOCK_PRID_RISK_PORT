"""
Prediction Tracking and Accuracy Measurement System
Stores predictions, compares with actuals, and calculates model accuracy
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from database import DatabaseManager
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()


class PredictionRecord(Base):
    """Store prediction records for accuracy tracking"""
    __tablename__ = 'prediction_records'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(10), nullable=False, index=True)
    prediction_date = Column(DateTime, nullable=False, index=True)
    target_date = Column(DateTime, nullable=False, index=True)
    horizon_days = Column(Integer, nullable=False)  # 1, 5, 30
    
    # Prediction values
    predicted_price = Column(Float, nullable=False)
    predicted_change_pct = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    
    # Actual values (filled later)
    actual_price = Column(Float, nullable=True)
    actual_change_pct = Column(Float, nullable=True)
    
    # Accuracy metrics
    is_resolved = Column(Boolean, default=False)
    price_error = Column(Float, nullable=True)
    price_error_pct = Column(Float, nullable=True)
    direction_correct = Column(Boolean, nullable=True)
    
    # Model metadata
    model_version = Column(String(50), default='v1.0')
    confidence_score = Column(Float, nullable=True)


class PredictionTracker:
    """Track predictions and measure accuracy"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self._ensure_table_exists()
    
    def _ensure_table_exists(self):
        """Create prediction_records table if it doesn't exist"""
        try:
            from sqlalchemy import create_engine
            engine = create_engine('sqlite:///portfolio_data.db')
            Base.metadata.create_all(engine)
            logger.info("Prediction tracking table created/verified")
        except Exception as e:
            logger.error(f"Error creating prediction table: {e}")
    
    def store_prediction(self, symbol: str, prediction_data: Dict[str, Any]) -> None:
        """
        Store a prediction for future accuracy tracking
        
        Args:
            symbol: Stock symbol
            prediction_data: Dict with predicted_price_1d, predicted_price_5d, predicted_price_30d, current_price
        """
        try:
            session = next(self.db.get_session())
            prediction_date = datetime.now()
            current_price = prediction_data.get('current_price', 0)
            
            # Store 1-day prediction
            if 'predicted_price_1d' in prediction_data:
                pred_1d = PredictionRecord(
                    symbol=symbol,
                    prediction_date=prediction_date,
                    target_date=prediction_date + timedelta(days=1),
                    horizon_days=1,
                    predicted_price=prediction_data['predicted_price_1d'],
                    predicted_change_pct=prediction_data.get('price_change_1d_pct', 0),
                    current_price=current_price,
                    model_version='v2.0_advanced'
                )
                session.add(pred_1d)
            
            # Store 5-day prediction
            if 'predicted_price_5d' in prediction_data:
                pred_5d = PredictionRecord(
                    symbol=symbol,
                    prediction_date=prediction_date,
                    target_date=prediction_date + timedelta(days=5),
                    horizon_days=5,
                    predicted_price=prediction_data['predicted_price_5d'],
                    predicted_change_pct=prediction_data.get('price_change_5d_pct', 0),
                    current_price=current_price,
                    model_version='v2.0_advanced'
                )
                session.add(pred_5d)
            
            # Store 30-day prediction
            if 'predicted_price_30d' in prediction_data:
                pred_30d = PredictionRecord(
                    symbol=symbol,
                    prediction_date=prediction_date,
                    target_date=prediction_date + timedelta(days=30),
                    horizon_days=30,
                    predicted_price=prediction_data['predicted_price_30d'],
                    predicted_change_pct=prediction_data.get('price_change_30d_pct', 0),
                    current_price=current_price,
                    model_version='v2.0_advanced'
                )
                session.add(pred_30d)
            
            session.commit()
            logger.info(f"Stored predictions for {symbol}")
            
        except Exception as e:
            logger.error(f"Error storing prediction: {e}")
            session.rollback()
        finally:
            session.close()
    
    def update_with_actuals(self, symbol: str, actual_price: float) -> None:
        """
        Update predictions with actual prices and calculate accuracy
        
        Args:
            symbol: Stock symbol
            actual_price: Current actual price
        """
        try:
            session = next(self.db.get_session())
            now = datetime.now()
            
            # Find unresolved predictions that have reached their target date
            unresolved = session.query(PredictionRecord).filter(
                PredictionRecord.symbol == symbol,
                PredictionRecord.is_resolved == False,
                PredictionRecord.target_date <= now
            ).all()
            
            for pred in unresolved:
                # Calculate actual change
                actual_change_pct = ((actual_price - pred.current_price) / pred.current_price) * 100
                
                # Calculate errors
                price_error = actual_price - pred.predicted_price
                price_error_pct = (price_error / pred.current_price) * 100
                
                # Check direction correctness
                predicted_direction = pred.predicted_change_pct > 0
                actual_direction = actual_change_pct > 0
                direction_correct = predicted_direction == actual_direction
                
                # Update record
                pred.actual_price = actual_price
                pred.actual_change_pct = actual_change_pct
                pred.price_error = price_error
                pred.price_error_pct = price_error_pct
                pred.direction_correct = direction_correct
                pred.is_resolved = True
            
            session.commit()
            logger.info(f"Updated {len(unresolved)} predictions for {symbol}")
            
        except Exception as e:
            logger.error(f"Error updating actuals: {e}")
            session.rollback()
        finally:
            session.close()
    
    def get_accuracy_metrics(self, symbol: Optional[str] = None, horizon_days: Optional[int] = None) -> Dict[str, Any]:
        """
        Calculate accuracy metrics for predictions
        
        Args:
            symbol: Optional symbol filter
            horizon_days: Optional horizon filter (1, 5, 30)
        
        Returns:
            Dict with accuracy metrics
        """
        try:
            session = next(self.db.get_session())
            
            # Build query
            query = session.query(PredictionRecord).filter(
                PredictionRecord.is_resolved == True
            )
            
            if symbol:
                query = query.filter(PredictionRecord.symbol == symbol)
            if horizon_days:
                query = query.filter(PredictionRecord.horizon_days == horizon_days)
            
            predictions = query.all()
            
            if not predictions:
                return {
                    "total_predictions": 0,
                    "message": "No resolved predictions yet"
                }
            
            # Calculate metrics
            total = len(predictions)
            direction_correct = sum(1 for p in predictions if p.direction_correct)
            direction_accuracy = (direction_correct / total) * 100
            
            price_errors = [abs(p.price_error_pct) for p in predictions]
            mean_absolute_error = np.mean(price_errors)
            median_absolute_error = np.median(price_errors)
            
            # Calculate RMSE
            squared_errors = [p.price_error_pct ** 2 for p in predictions]
            rmse = np.sqrt(np.mean(squared_errors))
            
            # Calculate within bounds (±2 std dev)
            std_dev = np.std(price_errors)
            within_bounds = sum(1 for e in price_errors if e <= 2 * std_dev)
            within_bounds_pct = (within_bounds / total) * 100
            
            return {
                "total_predictions": total,
                "direction_accuracy": round(direction_accuracy, 2),
                "mean_absolute_error_pct": round(mean_absolute_error, 2),
                "median_absolute_error_pct": round(median_absolute_error, 2),
                "rmse_pct": round(rmse, 2),
                "within_bounds_pct": round(within_bounds_pct, 2),
                "std_dev": round(std_dev, 2),
                "best_prediction": min(price_errors),
                "worst_prediction": max(price_errors)
            }
            
        except Exception as e:
            logger.error(f"Error calculating accuracy: {e}")
            return {"error": str(e)}
        finally:
            session.close()
    
    def get_recent_predictions_with_actuals(self, symbol: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent resolved predictions with comparison"""
        try:
            session = next(self.db.get_session())
            
            predictions = session.query(PredictionRecord).filter(
                PredictionRecord.symbol == symbol,
                PredictionRecord.is_resolved == True
            ).order_by(
                PredictionRecord.prediction_date.desc()
            ).limit(limit).all()
            
            results = []
            for pred in predictions:
                results.append({
                    "prediction_date": pred.prediction_date.isoformat(),
                    "target_date": pred.target_date.isoformat(),
                    "horizon_days": pred.horizon_days,
                    "predicted_price": pred.predicted_price,
                    "actual_price": pred.actual_price,
                    "predicted_change_pct": pred.predicted_change_pct,
                    "actual_change_pct": pred.actual_change_pct,
                    "error_pct": pred.price_error_pct,
                    "direction_correct": pred.direction_correct
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting predictions: {e}")
            return []
        finally:
            session.close()


# Global tracker instance
tracker = PredictionTracker()
