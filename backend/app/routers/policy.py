import uuid
import json
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import AuditEvent
from app.schemas import PolicyResponse, PolicyUpdateRequest
from app.services.policy import policy_engine
from app.auth import require_role

router = APIRouter(prefix="/api/v1/policy", tags=["Risk Policy Engine"])

@router.get("", response_model=PolicyResponse)
def get_active_policy(current_user: dict = Depends(require_role("sender", "analyst", "admin", "agent"))):
    """
    Retrieves currently active policy configuration, including
    normalized model component weights, decision thresholds, and presets.
    """
    data = policy_engine.get_policy()
    return {
        "version": data.get("version", "1.0.0"),
        "active_preset": data.get("active_preset", "standard"),
        "updated_at": data.get("updated_at", "2026-10-07T00:00:00Z"),
        "updated_by": data.get("updated_by", "system"),
        "weights": data.get("weights", {}),
        "thresholds": data.get("thresholds", {}),
        "presets": data.get("presets", {})
    }

@router.get("/presets")
def list_policy_presets(current_user: dict = Depends(require_role("analyst", "admin"))):
    """Lists available operational policy presets."""
    policy = policy_engine.get_policy()
    return policy.get("presets", {})

@router.put("", dependencies=[Depends(require_role("admin"))])
def update_policy(
    request: Request,
    payload: PolicyUpdateRequest,
    current_user: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """
    Updates active policy weights or applies a named operational preset.
    Restricted to admin role.
    Every update is transactionally recorded in the audit_events table.
    """
    actor_id = current_user.get("sub", "admin_user")
    client_ip = request.client.host if request.client else "127.0.0.1"

    try:
        diff_result = policy_engine.update_policy(
            new_weights=payload.weights,
            preset_name=payload.preset,
            new_thresholds=payload.thresholds,
            actor_id=actor_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Record persistent audit event
    audit = AuditEvent(
        id=f"audit_{uuid.uuid4().hex[:8]}",
        event_type="policy_update",
        actor_id=actor_id,
        details=json.dumps({
            "preset": payload.preset,
            "weights": payload.weights,
            "thresholds": payload.thresholds,
            "diff": diff_result
        }),
        ip_address=client_ip
    )
    db.add(audit)
    db.commit()

    return {
        "status": "success",
        "message": f"Policy updated successfully to preset '{diff_result['after']['active_preset']}'.",
        "diff": diff_result,
        "audit_event_id": audit.id
    }

@router.get("/audit", dependencies=[Depends(require_role("analyst", "admin"))])
def get_policy_audit_log(limit: int = 50, db: Session = Depends(get_db)):
    """Retrieves chronological policy modification audit trail."""
    events = (
        db.query(AuditEvent)
        .filter(AuditEvent.event_type == "policy_update")
        .order_by(AuditEvent.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": e.id,
            "event_type": e.event_type,
            "actor_id": e.actor_id,
            "details": json.loads(e.details) if e.details else {},
            "ip_address": e.ip_address,
            "created_at": str(e.created_at)
        }
        for e in events
    ]
