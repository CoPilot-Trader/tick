"""
Alerts API Router.

Provides REST endpoints for:
- Alert management
- Alert rules configuration
- Alert history
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

# Import agents
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.alert_agent.agent import AlertAgent, AlertType, AlertPriority

router = APIRouter(prefix="/api/v1/alerts", tags=["Alerts"])

# Global agent instance
_alert_agent: Optional[AlertAgent] = None


def get_alert_agent() -> AlertAgent:
    """Get or create Alert Agent instance."""
    global _alert_agent
    if _alert_agent is None:
        _alert_agent = AlertAgent()
        _alert_agent.initialize()
    return _alert_agent


# ============================================================================
# Request/Response Models
# ============================================================================

class CheckAlertsRequest(BaseModel):
    """Request model for checking alerts."""
    ticker: str = Field(..., description="Stock symbol")
    signal: Optional[str] = Field(None, description="Trading signal (BUY/SELL/HOLD)")
    confidence: Optional[float] = Field(None, ge=0, le=1, description="Signal confidence")
    fused_score: Optional[float] = Field(None, ge=-1, le=1, description="Fused score")
    current_price: Optional[float] = Field(None, description="Current price")
    sentiment_impact: Optional[str] = Field(None, description="Sentiment impact (High/Medium/Low)")
    drawdown_pct: Optional[float] = Field(None, description="Current drawdown percentage")
    price_thresholds: Optional[Dict[str, str]] = Field(None, description="Price thresholds to check")


class RuleRequest(BaseModel):
    """Request model for creating/updating alert rules."""
    id: str = Field(..., description="Rule ID")
    name: str = Field(..., description="Rule name")
    type: str = Field(..., description="Alert type (signal, price, risk, performance)")
    priority: str = Field(default="medium", description="Alert priority")
    enabled: bool = Field(default=True)
    cooldown_minutes: int = Field(default=60, ge=1)


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/health")
async def health_check():
    """Check Alert Agent health."""
    agent = get_alert_agent()
    return agent.health_check()


@router.post("/check/{ticker}")
async def check_alerts(ticker: str, request: CheckAlertsRequest) -> Dict[str, Any]:
    """
    Check alert conditions for a ticker.

    Pass trading signal data and the agent will check all rules
    and trigger alerts as appropriate.

    Returns:
        List of triggered alerts.
    """
    try:
        agent = get_alert_agent()

        params = {
            "signal": request.signal,
            "confidence": request.confidence,
            "fused_score": request.fused_score,
            "current_price": request.current_price,
            "sentiment_impact": request.sentiment_impact,
            "drawdown_pct": request.drawdown_pct,
            "price_thresholds": request.price_thresholds
        }

        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}

        result = agent.process(ticker, params)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
async def get_alerts(
    ticker: Optional[str] = Query(None, description="Filter by ticker"),
    alert_type: Optional[str] = Query(None, description="Filter by type"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    unacknowledged_only: bool = Query(False, description="Only unacknowledged"),
    limit: int = Query(100, ge=1, le=500)
) -> Dict[str, Any]:
    """
    Get alert history with optional filters.

    Returns:
        List of alerts matching filters.
    """
    try:
        agent = get_alert_agent()

        # Convert string to enum if provided
        type_enum = None
        if alert_type:
            try:
                type_enum = AlertType(alert_type)
            except ValueError:
                pass

        priority_enum = None
        if priority:
            try:
                priority_enum = AlertPriority(priority)
            except ValueError:
                pass

        alerts = agent.get_alerts(
            symbol=ticker,
            alert_type=type_enum,
            priority=priority_enum,
            unacknowledged_only=unacknowledged_only,
            limit=limit
        )

        return {
            "status": "success",
            "count": len(alerts),
            "alerts": alerts
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str) -> Dict[str, Any]:
    """Acknowledge a specific alert."""
    try:
        agent = get_alert_agent()
        success = agent.acknowledge_alert(alert_id)

        if success:
            return {"status": "success", "message": f"Alert {alert_id} acknowledged"}
        else:
            raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/acknowledge-all")
async def acknowledge_all_alerts(
    ticker: Optional[str] = Query(None, description="Only for this ticker")
) -> Dict[str, Any]:
    """Acknowledge all alerts, optionally for a specific ticker."""
    try:
        agent = get_alert_agent()
        count = agent.acknowledge_all(ticker)

        return {
            "status": "success",
            "message": f"Acknowledged {count} alerts",
            "acknowledged_count": count
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("")
async def clear_alerts(
    ticker: Optional[str] = Query(None, description="Only for this ticker")
) -> Dict[str, Any]:
    """Clear alerts, optionally for a specific ticker."""
    try:
        agent = get_alert_agent()
        count = agent.clear_alerts(ticker)

        return {
            "status": "success",
            "message": f"Cleared {count} alerts",
            "cleared_count": count
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rules")
async def get_rules() -> Dict[str, Any]:
    """Get all alert rules."""
    try:
        agent = get_alert_agent()
        rules = agent.get_rules()

        return {
            "status": "success",
            "count": len(rules),
            "rules": rules
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rules/{rule_id}/enable")
async def enable_rule(rule_id: str) -> Dict[str, Any]:
    """Enable an alert rule."""
    try:
        agent = get_alert_agent()
        success = agent.enable_rule(rule_id)

        if success:
            return {"status": "success", "message": f"Rule {rule_id} enabled"}
        else:
            raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rules/{rule_id}/disable")
async def disable_rule(rule_id: str) -> Dict[str, Any]:
    """Disable an alert rule."""
    try:
        agent = get_alert_agent()
        success = agent.disable_rule(rule_id)

        if success:
            return {"status": "success", "message": f"Rule {rule_id} disabled"}
        else:
            raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/rules/{rule_id}")
async def delete_rule(rule_id: str) -> Dict[str, Any]:
    """Delete an alert rule."""
    try:
        agent = get_alert_agent()
        success = agent.unregister_rule(rule_id)

        if success:
            return {"status": "success", "message": f"Rule {rule_id} deleted"}
        else:
            raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_alerts_summary() -> Dict[str, Any]:
    """Get summary of current alert status."""
    try:
        agent = get_alert_agent()
        health = agent.health_check()

        # Count by type
        alerts = agent.alerts
        by_type = {}
        by_priority = {}
        by_symbol = {}

        for alert in alerts:
            # By type
            type_key = alert.type.value
            by_type[type_key] = by_type.get(type_key, 0) + 1

            # By priority
            priority_key = alert.priority.value
            by_priority[priority_key] = by_priority.get(priority_key, 0) + 1

            # By symbol
            if alert.symbol:
                by_symbol[alert.symbol] = by_symbol.get(alert.symbol, 0) + 1

        return {
            "status": "success",
            "total_alerts": health.get("total_alerts", 0),
            "unacknowledged": health.get("unacknowledged_alerts", 0),
            "active_rules": health.get("enabled_rules", 0),
            "by_type": by_type,
            "by_priority": by_priority,
            "by_symbol": by_symbol
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
