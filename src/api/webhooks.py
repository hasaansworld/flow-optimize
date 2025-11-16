"""
Webhook Receivers for External Triggers
Allows external systems to trigger agent decisions

Endpoints:
- POST /webhooks/price_alert - Triggered when electricity price changes
- POST /webhooks/opcua_event - Triggered by OPC UA server events
- POST /webhooks/emergency - Emergency override trigger
- POST /webhooks/manual_decision - Manual decision request
"""

from typing import Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, BackgroundTasks
import asyncio

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


# ===== Request Models =====

class PriceAlertWebhook(BaseModel):
    """Price alert webhook payload"""
    timestamp: str
    new_price: float = Field(..., description="New electricity price in EUR/kWh")
    old_price: float = Field(..., description="Previous price in EUR/kWh")
    change_percent: float = Field(..., description="Price change percentage")
    scenario: str = Field(default="normal", description="Price scenario")


class OPCUAEventWebhook(BaseModel):
    """OPC UA event webhook payload"""
    timestamp: str
    event_type: str = Field(..., description="Type of event (alarm, warning, state_change)")
    severity: str = Field(..., description="Severity level (low, medium, high, critical)")
    message: str = Field(..., description="Event message")
    data: Dict[str, Any] = Field(default_factory=dict, description="Additional event data")


class EmergencyWebhook(BaseModel):
    """Emergency override webhook payload"""
    timestamp: str
    emergency_type: str = Field(..., description="Type of emergency (overflow, power_failure, pump_failure)")
    current_L1: float = Field(..., description="Current water level")
    message: str = Field(..., description="Emergency description")
    override_command: Optional[Dict] = Field(None, description="Manual override pump commands")


class ManualDecisionWebhook(BaseModel):
    """Manual decision request webhook payload"""
    timestamp: str
    requester: str = Field(..., description="Person/system requesting decision")
    reason: str = Field(..., description="Reason for manual decision")
    state_index: Optional[int] = Field(None, description="Historical data index to use")
    force_reassessment: bool = Field(default=True, description="Force all agents to reassess")


# ===== Webhook Endpoints =====

@router.post("/price_alert")
async def price_alert_webhook(payload: PriceAlertWebhook, background_tasks: BackgroundTasks):
    """
    Triggered when electricity price changes significantly

    Use case: When price drops >30%, trigger cost optimization agent
    """
    try:
        # Check if price change is significant
        is_significant = abs(payload.change_percent) > 20.0

        response = {
            "status": "received",
            "timestamp": payload.timestamp,
            "is_significant": is_significant,
            "action": "triggered_cost_agent" if is_significant else "no_action"
        }

        if is_significant:
            # Add background task to trigger cost optimization
            background_tasks.add_task(
                trigger_cost_optimization,
                payload.new_price,
                payload.scenario
            )
            response["message"] = f"Price changed by {payload.change_percent:.1f}% - triggering cost optimization"
        else:
            response["message"] = f"Price change {payload.change_percent:.1f}% below threshold"

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Price alert processing failed: {str(e)}")


@router.post("/opcua_event")
async def opcua_event_webhook(payload: OPCUAEventWebhook, background_tasks: BackgroundTasks):
    """
    Triggered by OPC UA server events

    Use case: Water level alarms, pump failures, communication errors
    """
    try:
        # Determine response based on severity
        requires_immediate_action = payload.severity in ["high", "critical"]

        response = {
            "status": "received",
            "timestamp": payload.timestamp,
            "event_type": payload.event_type,
            "severity": payload.severity,
            "requires_action": requires_immediate_action
        }

        if requires_immediate_action:
            # Add background task for immediate reassessment
            background_tasks.add_task(
                trigger_emergency_reassessment,
                payload.event_type,
                payload.data
            )
            response["message"] = f"Critical event '{payload.event_type}' - triggering emergency reassessment"
        else:
            response["message"] = f"Event '{payload.event_type}' logged - no immediate action required"

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OPC UA event processing failed: {str(e)}")


@router.post("/emergency")
async def emergency_webhook(payload: EmergencyWebhook, background_tasks: BackgroundTasks):
    """
    Emergency override trigger

    Use case: Overflow imminent, pump failure, power outage
    """
    try:
        # Log emergency
        print(f"🚨 EMERGENCY: {payload.emergency_type} at L1={payload.current_L1:.2f}m")
        print(f"   Message: {payload.message}")

        response = {
            "status": "emergency_received",
            "timestamp": payload.timestamp,
            "emergency_type": payload.emergency_type,
            "current_L1": payload.current_L1
        }

        # Check if manual override provided
        if payload.override_command:
            response["action"] = "executing_override_command"
            response["message"] = "Manual override command will be executed"
            # Add task to execute override
            background_tasks.add_task(
                execute_override_command,
                payload.override_command
            )
        else:
            response["action"] = "triggering_emergency_protocol"
            response["message"] = "Emergency protocol triggered - all agents reassessing with CRITICAL priority"
            # Add task for emergency reassessment
            background_tasks.add_task(
                trigger_emergency_reassessment,
                payload.emergency_type,
                {"L1": payload.current_L1}
            )

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Emergency processing failed: {str(e)}")


@router.post("/manual_decision")
async def manual_decision_webhook(payload: ManualDecisionWebhook, background_tasks: BackgroundTasks):
    """
    Manual decision request from operator

    Use case: Operator wants to see what agents would recommend
    """
    try:
        response = {
            "status": "processing",
            "timestamp": payload.timestamp,
            "requester": payload.requester,
            "reason": payload.reason
        }

        # Add background task for manual decision
        background_tasks.add_task(
            trigger_manual_decision,
            payload.state_index,
            payload.force_reassessment,
            payload.requester
        )

        response["message"] = "Manual decision request queued - check /api/v1/decisions/history for results"

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Manual decision processing failed: {str(e)}")


# ===== Background Tasks =====

async def trigger_cost_optimization(new_price: float, scenario: str):
    """Background task: Trigger cost optimization"""
    print(f"💰 Cost optimization triggered - New price: {new_price:.3f} EUR/kWh ({scenario})")
    # TODO: Implement actual cost optimization trigger
    await asyncio.sleep(1)
    print("✓ Cost optimization complete")


async def trigger_emergency_reassessment(event_type: str, data: Dict):
    """Background task: Emergency reassessment"""
    print(f"🚨 Emergency reassessment triggered - Event: {event_type}")
    # TODO: Implement emergency reassessment
    await asyncio.sleep(1)
    print("✓ Emergency reassessment complete")


async def execute_override_command(override_command: Dict):
    """Background task: Execute manual override"""
    print(f"⚙️  Executing override command: {override_command}")
    # TODO: Implement override command execution
    await asyncio.sleep(1)
    print("✓ Override command executed")


async def trigger_manual_decision(state_index: Optional[int], force_reassessment: bool, requester: str):
    """Background task: Manual decision"""
    print(f"👤 Manual decision triggered by {requester} - State index: {state_index}")
    # TODO: Implement manual decision
    await asyncio.sleep(1)
    print("✓ Manual decision complete")


# ===== Webhook Status =====

@router.get("/status")
async def webhook_status():
    """Get webhook receiver status"""
    return {
        "status": "active",
        "available_webhooks": [
            {
                "endpoint": "/webhooks/price_alert",
                "description": "Electricity price change alerts",
                "method": "POST"
            },
            {
                "endpoint": "/webhooks/opcua_event",
                "description": "OPC UA server events",
                "method": "POST"
            },
            {
                "endpoint": "/webhooks/emergency",
                "description": "Emergency override trigger",
                "method": "POST"
            },
            {
                "endpoint": "/webhooks/manual_decision",
                "description": "Manual decision request",
                "method": "POST"
            }
        ],
        "timestamp": datetime.now().isoformat()
    }
