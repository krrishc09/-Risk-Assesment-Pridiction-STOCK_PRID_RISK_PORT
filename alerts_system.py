"""
Real-Time Alerts System
Monitors portfolio and sends notifications for important events
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json

logger = logging.getLogger(__name__)


class AlertType(Enum):
    """Types of alerts"""
    PRICE_THRESHOLD = "price_threshold"
    PRICE_CHANGE = "price_change"
    PREDICTION_CONFIDENCE = "prediction_confidence"
    RISK_LEVEL = "risk_level"
    PORTFOLIO_VALUE = "portfolio_value"
    REBALANCE_NEEDED = "rebalance_needed"
    SIGNAL_CHANGE = "signal_change"


class AlertPriority(Enum):
    """Alert priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Alert data structure"""
    id: str
    type: AlertType
    priority: AlertPriority
    symbol: Optional[str]
    title: str
    message: str
    timestamp: datetime
    data: Dict[str, Any]
    read: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'type': self.type.value,
            'priority': self.priority.value,
            'symbol': self.symbol,
            'title': self.title,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'data': self.data,
            'read': self.read
        }


class AlertsManager:
    """Manages alerts and notifications"""
    
    def __init__(self):
        self.alerts: List[Alert] = []
        self.alert_rules: List[Dict] = []
        self.alert_counter = 0
        
    def add_alert_rule(self, rule: Dict[str, Any]) -> str:
        """Add a new alert rule"""
        rule_id = f"rule_{len(self.alert_rules) + 1}"
        rule['id'] = rule_id
        rule['created_at'] = datetime.now().isoformat()
        rule['enabled'] = True
        self.alert_rules.append(rule)
        logger.info(f"Added alert rule: {rule_id}")
        return rule_id
    
    def remove_alert_rule(self, rule_id: str) -> bool:
        """Remove an alert rule"""
        self.alert_rules = [r for r in self.alert_rules if r['id'] != rule_id]
        return True
    
    def get_alert_rules(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get all alert rules, optionally filtered by symbol"""
        if symbol:
            return [r for r in self.alert_rules if r.get('symbol') == symbol]
        return self.alert_rules
    
    def create_alert(self, alert_type: AlertType, priority: AlertPriority,
                    title: str, message: str, symbol: Optional[str] = None,
                    data: Dict[str, Any] = None) -> Alert:
        """Create a new alert"""
        self.alert_counter += 1
        alert = Alert(
            id=f"alert_{self.alert_counter}",
            type=alert_type,
            priority=priority,
            symbol=symbol,
            title=title,
            message=message,
            timestamp=datetime.now(),
            data=data or {}
        )
        self.alerts.append(alert)
        logger.info(f"Created alert: {title} ({priority.value})")
        return alert
    
    def get_alerts(self, unread_only: bool = False, 
                  symbol: Optional[str] = None,
                  limit: int = 50) -> List[Dict]:
        """Get alerts"""
        filtered = self.alerts
        
        if unread_only:
            filtered = [a for a in filtered if not a.read]
        
        if symbol:
            filtered = [a for a in filtered if a.symbol == symbol]
        
        # Sort by timestamp descending
        filtered.sort(key=lambda x: x.timestamp, reverse=True)
        
        return [a.to_dict() for a in filtered[:limit]]
    
    def mark_as_read(self, alert_id: str) -> bool:
        """Mark alert as read"""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.read = True
                return True
        return False
    
    def mark_all_as_read(self, symbol: Optional[str] = None) -> int:
        """Mark all alerts as read"""
        count = 0
        for alert in self.alerts:
            if not alert.read and (symbol is None or alert.symbol == symbol):
                alert.read = True
                count += 1
        return count
    
    def check_price_alerts(self, symbol: str, current_price: float, 
                          previous_price: float) -> List[Alert]:
        """Check price-based alert rules"""
        alerts = []
        
        for rule in self.alert_rules:
            if not rule.get('enabled') or rule.get('symbol') != symbol:
                continue
            
            rule_type = rule.get('type')
            
            # Price threshold alerts
            if rule_type == 'price_above' and current_price > rule.get('threshold'):
                alert = self.create_alert(
                    AlertType.PRICE_THRESHOLD,
                    AlertPriority.HIGH,
                    f"{symbol} Price Alert",
                    f"{symbol} is now ${current_price:.2f}, above your threshold of ${rule.get('threshold'):.2f}",
                    symbol=symbol,
                    data={'current_price': current_price, 'threshold': rule.get('threshold')}
                )
                alerts.append(alert)
                rule['enabled'] = False  # Disable after triggering
            
            elif rule_type == 'price_below' and current_price < rule.get('threshold'):
                alert = self.create_alert(
                    AlertType.PRICE_THRESHOLD,
                    AlertPriority.HIGH,
                    f"{symbol} Price Alert",
                    f"{symbol} is now ${current_price:.2f}, below your threshold of ${rule.get('threshold'):.2f}",
                    symbol=symbol,
                    data={'current_price': current_price, 'threshold': rule.get('threshold')}
                )
                alerts.append(alert)
                rule['enabled'] = False
            
            # Percentage change alerts
            elif rule_type == 'change_percent':
                change_pct = ((current_price - previous_price) / previous_price) * 100
                threshold = rule.get('threshold', 5)
                
                if abs(change_pct) >= threshold:
                    priority = AlertPriority.CRITICAL if abs(change_pct) >= 10 else AlertPriority.HIGH
                    alert = self.create_alert(
                        AlertType.PRICE_CHANGE,
                        priority,
                        f"{symbol} Large Price Movement",
                        f"{symbol} {'gained' if change_pct > 0 else 'dropped'} {abs(change_pct):.2f}% to ${current_price:.2f}",
                        symbol=symbol,
                        data={'change_percent': change_pct, 'current_price': current_price}
                    )
                    alerts.append(alert)
        
        return alerts
    
    def check_prediction_alerts(self, symbol: str, prediction_data: Dict) -> List[Alert]:
        """Check prediction-based alerts"""
        alerts = []
        
        confidence = prediction_data.get('signal_confidence', 0)
        signal = prediction_data.get('signal', '')
        
        # High confidence prediction
        if confidence > 0.8:
            alert = self.create_alert(
                AlertType.PREDICTION_CONFIDENCE,
                AlertPriority.HIGH,
                f"{symbol} High Confidence Signal",
                f"{symbol} has a {signal} signal with {confidence*100:.0f}% confidence",
                symbol=symbol,
                data={'signal': signal, 'confidence': confidence}
            )
            alerts.append(alert)
        
        # Strong buy/sell signals
        if signal in ['Strong Buy', 'Strong Sell']:
            alert = self.create_alert(
                AlertType.SIGNAL_CHANGE,
                AlertPriority.HIGH,
                f"{symbol} {signal} Signal",
                f"Model predicts {signal} for {symbol}",
                symbol=symbol,
                data={'signal': signal}
            )
            alerts.append(alert)
        
        return alerts
    
    def check_risk_alerts(self, symbol: str, risk_score: float) -> List[Alert]:
        """Check risk-based alerts"""
        alerts = []
        
        if risk_score >= 8:
            alert = self.create_alert(
                AlertType.RISK_LEVEL,
                AlertPriority.CRITICAL,
                f"{symbol} High Risk Warning",
                f"{symbol} risk score is {risk_score:.1f}/10 - Consider reviewing position",
                symbol=symbol,
                data={'risk_score': risk_score}
            )
            alerts.append(alert)
        elif risk_score >= 7:
            alert = self.create_alert(
                AlertType.RISK_LEVEL,
                AlertPriority.HIGH,
                f"{symbol} Elevated Risk",
                f"{symbol} risk score is {risk_score:.1f}/10",
                symbol=symbol,
                data={'risk_score': risk_score}
            )
            alerts.append(alert)
        
        return alerts
    
    def check_portfolio_alerts(self, portfolio_data: Dict) -> List[Alert]:
        """Check portfolio-level alerts"""
        alerts = []
        
        total_value = portfolio_data.get('total_value', 0)
        day_change = portfolio_data.get('day_change', 0)
        day_change_pct = portfolio_data.get('day_change_percent', 0)
        
        # Large portfolio movement
        if abs(day_change_pct) >= 5:
            priority = AlertPriority.CRITICAL if abs(day_change_pct) >= 10 else AlertPriority.HIGH
            alert = self.create_alert(
                AlertType.PORTFOLIO_VALUE,
                priority,
                "Portfolio Large Movement",
                f"Your portfolio {'gained' if day_change > 0 else 'lost'} {abs(day_change_pct):.2f}% (${abs(day_change):.2f}) today",
                data={'day_change': day_change, 'day_change_pct': day_change_pct}
            )
            alerts.append(alert)
        
        return alerts
    
    def check_rebalancing_alerts(self, rebalancing_recs: List[Dict]) -> List[Alert]:
        """Check if rebalancing is needed"""
        alerts = []
        
        high_priority_recs = [r for r in rebalancing_recs if r.get('priority') == 'High']
        
        if len(high_priority_recs) >= 2:
            alert = self.create_alert(
                AlertType.REBALANCE_NEEDED,
                AlertPriority.MEDIUM,
                "Portfolio Rebalancing Recommended",
                f"{len(high_priority_recs)} positions significantly deviate from optimal allocation",
                data={'recommendations': high_priority_recs}
            )
            alerts.append(alert)
        
        return alerts
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of alerts"""
        unread = [a for a in self.alerts if not a.read]
        
        return {
            'total_alerts': len(self.alerts),
            'unread_count': len(unread),
            'by_priority': {
                'critical': len([a for a in unread if a.priority == AlertPriority.CRITICAL]),
                'high': len([a for a in unread if a.priority == AlertPriority.HIGH]),
                'medium': len([a for a in unread if a.priority == AlertPriority.MEDIUM]),
                'low': len([a for a in unread if a.priority == AlertPriority.LOW])
            },
            'by_type': {
                alert_type.value: len([a for a in unread if a.type == alert_type])
                for alert_type in AlertType
            },
            'active_rules': len([r for r in self.alert_rules if r.get('enabled')])
        }


# Global alerts manager instance
alerts_manager = AlertsManager()


# Convenience functions for API
def create_price_alert(symbol: str, threshold: float, alert_type: str = 'above') -> str:
    """Create a price alert rule"""
    rule = {
        'type': f'price_{alert_type}',
        'symbol': symbol,
        'threshold': threshold
    }
    return alerts_manager.add_alert_rule(rule)


def create_change_alert(symbol: str, threshold_percent: float = 5.0) -> str:
    """Create a percentage change alert"""
    rule = {
        'type': 'change_percent',
        'symbol': symbol,
        'threshold': threshold_percent
    }
    return alerts_manager.add_alert_rule(rule)


def get_alerts(unread_only: bool = False, symbol: Optional[str] = None) -> List[Dict]:
    """Get alerts"""
    return alerts_manager.get_alerts(unread_only=unread_only, symbol=symbol)


def mark_alert_read(alert_id: str) -> bool:
    """Mark alert as read"""
    return alerts_manager.mark_as_read(alert_id)


def get_alert_summary() -> Dict[str, Any]:
    """Get alert summary"""
    return alerts_manager.get_alert_summary()
