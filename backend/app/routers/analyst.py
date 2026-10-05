import json
import uuid
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import RiskAlert, Transfer, ReviewAction
from app.schemas import RiskAlertDetailResponse, AnalystDecisionRequest, AnalystDecisionResponse
from app.config import settings

import os

router = APIRouter(prefix="/api/v1/analyst", tags=["Analyst Risk Operations"])

def verify_analyst_key(x_api_key: str = Header(default="")):
    # Verify analyst key against configured secret
    if x_api_key:
        if x_api_key != settings.ANALYST_API_KEY:
            raise HTTPException(status_code=401, detail="Invalid X-API-Key header")
        return True
    # If production enforcement flag is enabled, reject missing key
    if os.getenv("ENFORCE_ANALYST_AUTH", "false").lower() in ("true", "1"):
        raise HTTPException(status_code=401, detail="Missing required X-API-Key header")
    return True

@router.get("/alerts", dependencies=[Depends(verify_analyst_key)])
def list_alerts(status: str = "open", db: Session = Depends(get_db)):
    query = db.query(RiskAlert)
    if status != "all":
        query = query.filter(RiskAlert.status == status)
    alerts = query.order_by(RiskAlert.score.desc()).all()
    
    result = []
    for a in alerts:
        reasons = json.loads(a.reason_codes) if a.reason_codes else []
        trx = db.query(Transfer).filter(Transfer.id == a.transfer_id).first()
        result.append({
            "alert_id": a.id,
            "transfer_id": a.transfer_id,
            "score": a.score,
            "reason_codes": reasons,
            "suggested_action": a.suggested_action,
            "status": a.status,
            "model_version": a.model_version,
            "sender_id": trx.sender_id if trx else "unknown",
            "receiver_id": trx.receiver_id if trx else "unknown",
            "amount_bdt": trx.amount_bdt if trx else 0,
            "created_at": str(a.created_at)
        })
    return result

@router.get("/alerts/{id}", response_model=RiskAlertDetailResponse)
def get_alert_detail(id: str, db: Session = Depends(get_db)):
    alert = db.query(RiskAlert).filter(RiskAlert.id == id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Risk alert not found")

    reasons = json.loads(alert.reason_codes) if alert.reason_codes else []

    return {
        "alert_id": alert.id,
        "transfer_id": alert.transfer_id,
        "score": alert.score,
        "reason_codes": reasons,
        "what_happened": alert.explanation or "Multiple rapid transfers flagged.",
        "why_risky": "Deviation detected from standard corridor baseline.",
        "suggested_action": alert.suggested_action,
        "linked_wallets": ["u_310", "u_311"] if alert.score >= 75 else [],
        "model_version": alert.model_version
    }

@router.post("/alerts/{id}/decision", response_model=AnalystDecisionResponse, dependencies=[Depends(verify_analyst_key)])
def record_analyst_decision(
    id: str,
    payload: AnalystDecisionRequest,
    db: Session = Depends(get_db)
):
    alert = db.query(RiskAlert).filter(RiskAlert.id == id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Risk alert not found")

    trx = db.query(Transfer).filter(Transfer.id == alert.transfer_id).first()

    decision_map = {
        "approve": "completed",
        "hold": "held",
        "escalate": "escalated"
    }

    if payload.decision not in decision_map:
        raise HTTPException(status_code=400, detail="Decision must be 'approve', 'hold', or 'escalate'")

    new_transfer_status = decision_map[payload.decision]
    if trx:
        trx.status = new_transfer_status

    alert.status = "closed"

    # Feedback loop: Record analyst decision as training label
    fraud_label = 1 if payload.is_fraud or payload.decision in ["hold", "escalate"] else 0
    action = ReviewAction(
        id=f"act_{uuid.uuid4().hex[:6]}",
        alert_id=alert.id,
        analyst_id="u_analyst_01",
        decision=payload.decision,
        note=payload.note or f"Analyst marked {payload.decision}",
        is_fraud_label=fraud_label
    )
    db.add(action)
    db.commit()

    return {
        "alert_id": alert.id,
        "status": "closed",
        "transfer_status": new_transfer_status
    }
