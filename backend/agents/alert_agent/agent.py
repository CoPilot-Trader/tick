"""
Alert Agent - Main agent implementation.

Provides alerting and notification capabilities for trading signals.

Developer: Lead Developer
Milestone: M4 - Backtesting & Integration
Version: 1.0.0
"""

import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from core.interfaces.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class AlertType(Enum):
    """Types of alerts."""
    SIGNAL = "signal"           # Trading signal alerts (BUY/SELL)
    PRICE = "price"             # Price threshold alerts
    RISK = "risk"               # Risk management alerts
    PERFORMANCE = "performance" # Performance-related alerts
    SYSTEM = "system"           # System/operational alerts


class AlertPriority(Enum):
    """Alert priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Represents an alert."""
    id: str
    type: AlertType
    priority: AlertPriority
    symbol: Optional[str]
    title: str
    message: str
    data: Dict[str, Any]
    created_at: datetime
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None


@dataclass
class AlertRule:
    """Defines an alert rule/condition."""
    id: str
    name: str
    type: AlertType
    condition: Callable[[Dict[str, Any]], bool]
    priority: AlertPriority
    enabled: bool = True
    cooldown_minutes: int = 60  # Minimum time between alerts
    last_triggered: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class AlertAgent(BaseAgent):
    """
    Alert Agent for trading notifications and monitoring.

    This agent:
    1. Monitors trading signals for alert conditions
    2. Tracks price thresholds
    3. Monitors risk limits
    4. Sends notifications (extensible)

    Features:
    - Multiple alert types (signal, price, risk, performance)
    - Configurable alert rules
    - Alert cooldown to prevent spam
    - Alert history and acknowledgment
    - Extensible notification handlers

    Developer: Lead Developer
    Milestone: M4 - Backtesting & Integration
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Alert Agent."""
        super().__init__(name="alert_agent", config=config)
        self.version = "1.0.0"

        # Alert configuration
        self.max_alerts_history = self.config.get("max_alerts_history", 1000)
        self.default_cooldown = self.config.get("default_cooldown_minutes", 60)

        # State
        self.alerts: List[Alert] = []
        self.rules: Dict[str, AlertRule] = {}
        self.notification_handlers: List[Callable[[Alert], None]] = []

        # Alert counter for ID generation
        self._alert_counter = 0

    def initialize(self) -> bool:
        """
        Initialize the Alert Agent.

        Sets up:
        - Default alert rules
        - Notification handlers
        """
        try:
            # Register default alert rules
            self._register_default_rules()

            # Add console notification handler by default
            self.add_notification_handler(self._console_handler)

            self.initialized = True
            logger.info(f"AlertAgent v{self.version} initialized with {len(self.rules)} rules")
            return True

        except Exception as e:
            logger.error(f"Error initializing Alert Agent: {e}", exc_info=True)
            self.initialized = False
            return False

    def _register_default_rules(self) -> None:
        """Register default alert rules."""

        # Rule 1: High confidence BUY signal
        self.register_rule(AlertRule(
            id="high_conf_buy",
            name="High Confidence BUY Signal",
            type=AlertType.SIGNAL,
            condition=lambda d: (
                d.get("signal") == "BUY" and
                d.get("confidence", 0) >= 0.7
            ),
            priority=AlertPriority.HIGH,
            cooldown_minutes=30
        ))

        # Rule 2: High confidence SELL signal
        self.register_rule(AlertRule(
            id="high_conf_sell",
            name="High Confidence SELL Signal",
            type=AlertType.SIGNAL,
            condition=lambda d: (
                d.get("signal") == "SELL" and
                d.get("confidence", 0) >= 0.7
            ),
            priority=AlertPriority.HIGH,
            cooldown_minutes=30
        ))

        # Rule 3: Strong bullish agreement
        self.register_rule(AlertRule(
            id="strong_bullish",
            name="Strong Bullish Agreement",
            type=AlertType.SIGNAL,
            condition=lambda d: (
                d.get("fused_score", 0) >= 0.6 and
                d.get("confidence", 0) >= 0.6
            ),
            priority=AlertPriority.MEDIUM
        ))

        # Rule 4: Strong bearish agreement
        self.register_rule(AlertRule(
            id="strong_bearish",
            name="Strong Bearish Agreement",
            type=AlertType.SIGNAL,
            condition=lambda d: (
                d.get("fused_score", 0) <= -0.6 and
                d.get("confidence", 0) >= 0.6
            ),
            priority=AlertPriority.MEDIUM
        ))

        # Rule 5: High impact sentiment
        self.register_rule(AlertRule(
            id="high_impact_sentiment",
            name="High Impact Sentiment",
            type=AlertType.SIGNAL,
            condition=lambda d: d.get("sentiment_impact") == "High",
            priority=AlertPriority.MEDIUM,
            cooldown_minutes=120
        ))

        # Rule 6: Large drawdown warning
        self.register_rule(AlertRule(
            id="large_drawdown",
            name="Large Drawdown Warning",
            type=AlertType.RISK,
            condition=lambda d: d.get("drawdown_pct", 0) >= 10,
            priority=AlertPriority.HIGH,
            cooldown_minutes=240
        ))

        # Rule 7: Position limit reached
        self.register_rule(AlertRule(
            id="position_limit",
            name="Position Limit Reached",
            type=AlertType.RISK,
            condition=lambda d: d.get("positions_at_limit", False),
            priority=AlertPriority.MEDIUM
        ))

    def process(self, symbol: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process data and check for alert conditions.

        Args:
            symbol: Stock symbol (or "SYSTEM" for system alerts)
            params: Data to check against alert rules:
                   - signal: Trading signal (BUY/SELL/HOLD)
                   - confidence: Signal confidence
                   - fused_score: Fusion score
                   - current_price: Current price
                   - price_thresholds: Dict of threshold -> direction
                   - drawdown_pct: Current drawdown percentage
                   - etc.

        Returns:
            Dictionary with triggered alerts
        """
        if not self.initialized:
            return {
                "symbol": symbol,
                "status": "error",
                "message": "Agent not initialized"
            }

        params = params or {}
        params["symbol"] = symbol
        triggered_alerts = []

        # Check each enabled rule
        for rule_id, rule in self.rules.items():
            if not rule.enabled:
                continue

            # Check cooldown
            if rule.last_triggered:
                cooldown_delta = timedelta(minutes=rule.cooldown_minutes)
                if datetime.utcnow() - rule.last_triggered < cooldown_delta:
                    continue

            # Check condition
            try:
                if rule.condition(params):
                    alert = self._create_alert(rule, params, symbol)
                    triggered_alerts.append(alert)
                    rule.last_triggered = datetime.utcnow()
            except Exception as e:
                logger.error(f"Error checking rule {rule_id}: {e}")

        # Check custom price thresholds
        price_alerts = self._check_price_thresholds(symbol, params)
        triggered_alerts.extend(price_alerts)

        return {
            "symbol": symbol,
            "status": "success",
            "alerts_triggered": len(triggered_alerts),
            "alerts": [self._alert_to_dict(a) for a in triggered_alerts]
        }

    def _create_alert(
        self,
        rule: AlertRule,
        data: Dict[str, Any],
        symbol: str
    ) -> Alert:
        """Create and store an alert."""
        self._alert_counter += 1
        alert_id = f"alert_{self._alert_counter}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        # Generate message based on rule type
        if rule.type == AlertType.SIGNAL:
            signal = data.get("signal", "UNKNOWN")
            confidence = data.get("confidence", 0)
            message = f"{signal} signal for {symbol} with {confidence*100:.1f}% confidence"
        elif rule.type == AlertType.RISK:
            message = f"Risk alert for {symbol}: {rule.name}"
        else:
            message = f"{rule.name} triggered for {symbol}"

        alert = Alert(
            id=alert_id,
            type=rule.type,
            priority=rule.priority,
            symbol=symbol,
            title=rule.name,
            message=message,
            data=data.copy(),
            created_at=datetime.utcnow()
        )

        # Store alert
        self.alerts.append(alert)
        self._trim_alert_history()

        # Send notifications
        self._send_notifications(alert)

        logger.info(f"Alert triggered: {alert.title} for {symbol}")
        return alert

    def _check_price_thresholds(
        self,
        symbol: str,
        params: Dict[str, Any]
    ) -> List[Alert]:
        """Check custom price threshold alerts."""
        alerts = []
        current_price = params.get("current_price")
        thresholds = params.get("price_thresholds", {})

        if not current_price or not thresholds:
            return alerts

        for threshold, direction in thresholds.items():
            threshold = float(threshold)
            triggered = False

            if direction == "above" and current_price >= threshold:
                triggered = True
                message = f"{symbol} crossed above ${threshold:.2f} (current: ${current_price:.2f})"
            elif direction == "below" and current_price <= threshold:
                triggered = True
                message = f"{symbol} crossed below ${threshold:.2f} (current: ${current_price:.2f})"

            if triggered:
                self._alert_counter += 1
                alert = Alert(
                    id=f"price_{self._alert_counter}",
                    type=AlertType.PRICE,
                    priority=AlertPriority.MEDIUM,
                    symbol=symbol,
                    title=f"Price Threshold Alert",
                    message=message,
                    data={"threshold": threshold, "direction": direction, "price": current_price},
                    created_at=datetime.utcnow()
                )
                alerts.append(alert)
                self.alerts.append(alert)
                self._send_notifications(alert)

        return alerts

    def register_rule(self, rule: AlertRule) -> bool:
        """
        Register an alert rule.

        Args:
            rule: AlertRule to register

        Returns:
            True if successful
        """
        self.rules[rule.id] = rule
        logger.info(f"Registered alert rule: {rule.name}")
        return True

    def unregister_rule(self, rule_id: str) -> bool:
        """Remove an alert rule."""
        if rule_id in self.rules:
            del self.rules[rule_id]
            return True
        return False

    def enable_rule(self, rule_id: str) -> bool:
        """Enable an alert rule."""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = True
            return True
        return False

    def disable_rule(self, rule_id: str) -> bool:
        """Disable an alert rule."""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = False
            return True
        return False

    def add_notification_handler(self, handler: Callable[[Alert], None]) -> None:
        """Add a notification handler."""
        self.notification_handlers.append(handler)

    def _send_notifications(self, alert: Alert) -> None:
        """Send alert to all registered handlers."""
        for handler in self.notification_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Notification handler error: {e}")

    def _console_handler(self, alert: Alert) -> None:
        """Default console notification handler."""
        priority_emoji = {
            AlertPriority.LOW: "",
            AlertPriority.MEDIUM: "[!]",
            AlertPriority.HIGH: "[!!]",
            AlertPriority.CRITICAL: "[!!!]"
        }
        emoji = priority_emoji.get(alert.priority, "")
        logger.warning(f"ALERT {emoji} {alert.title}: {alert.message}")

    def _trim_alert_history(self) -> None:
        """Trim alert history to max size."""
        if len(self.alerts) > self.max_alerts_history:
            self.alerts = self.alerts[-self.max_alerts_history:]

    def get_alerts(
        self,
        symbol: Optional[str] = None,
        alert_type: Optional[AlertType] = None,
        priority: Optional[AlertPriority] = None,
        unacknowledged_only: bool = False,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get filtered alerts.

        Args:
            symbol: Filter by symbol
            alert_type: Filter by type
            priority: Filter by priority
            unacknowledged_only: Only unacknowledged alerts
            limit: Maximum alerts to return

        Returns:
            List of alert dictionaries
        """
        filtered = self.alerts.copy()

        if symbol:
            filtered = [a for a in filtered if a.symbol == symbol]
        if alert_type:
            filtered = [a for a in filtered if a.type == alert_type]
        if priority:
            filtered = [a for a in filtered if a.priority == priority]
        if unacknowledged_only:
            filtered = [a for a in filtered if not a.acknowledged]

        # Sort by created_at descending
        filtered.sort(key=lambda a: a.created_at, reverse=True)

        return [self._alert_to_dict(a) for a in filtered[:limit]]

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert."""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                alert.acknowledged_at = datetime.utcnow()
                return True
        return False

    def acknowledge_all(self, symbol: Optional[str] = None) -> int:
        """Acknowledge all alerts, optionally for a specific symbol."""
        count = 0
        for alert in self.alerts:
            if not alert.acknowledged:
                if symbol is None or alert.symbol == symbol:
                    alert.acknowledged = True
                    alert.acknowledged_at = datetime.utcnow()
                    count += 1
        return count

    def get_rules(self) -> List[Dict[str, Any]]:
        """Get all alert rules."""
        return [
            {
                "id": r.id,
                "name": r.name,
                "type": r.type.value,
                "priority": r.priority.value,
                "enabled": r.enabled,
                "cooldown_minutes": r.cooldown_minutes,
                "last_triggered": r.last_triggered.isoformat() if r.last_triggered else None
            }
            for r in self.rules.values()
        ]

    def _alert_to_dict(self, alert: Alert) -> Dict[str, Any]:
        """Convert Alert to dictionary."""
        return {
            "id": alert.id,
            "type": alert.type.value,
            "priority": alert.priority.value,
            "symbol": alert.symbol,
            "title": alert.title,
            "message": alert.message,
            "data": alert.data,
            "created_at": alert.created_at.isoformat() + "Z",
            "acknowledged": alert.acknowledged,
            "acknowledged_at": alert.acknowledged_at.isoformat() + "Z" if alert.acknowledged_at else None
        }

    def clear_alerts(self, symbol: Optional[str] = None) -> int:
        """Clear alerts, optionally for a specific symbol."""
        if symbol:
            before = len(self.alerts)
            self.alerts = [a for a in self.alerts if a.symbol != symbol]
            return before - len(self.alerts)
        else:
            count = len(self.alerts)
            self.alerts = []
            return count

    def health_check(self) -> Dict[str, Any]:
        """Check Alert Agent health."""
        unacked = sum(1 for a in self.alerts if not a.acknowledged)
        return {
            "status": "healthy" if self.initialized else "not_initialized",
            "agent": self.name,
            "version": self.version,
            "rules_count": len(self.rules),
            "enabled_rules": sum(1 for r in self.rules.values() if r.enabled),
            "total_alerts": len(self.alerts),
            "unacknowledged_alerts": unacked,
            "notification_handlers": len(self.notification_handlers)
        }
