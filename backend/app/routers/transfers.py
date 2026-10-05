import uuid
import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Transfer, RiskAlert
from app.schemas import TransferCreateRequest, TransferResponse
from app.services.rules import calculate_fees_and_payout, CORRIDOR_RULES
from app.services.risk import anomaly_scorer
from app.services.explain import generate_analyst_explanation

router = APIRouter(prefix="/api/v1/transfers", tags=["Transfers"])

@router.post("", response_model=TransferResponse, status_code=status.HTTP_201_CREATED)
def create_transfer(payload: TransferCreateRequest, db: Session = Depends(get_db)):
    # 0. Validate Corridor & Business Limits
    corridor_key = payload.corridor.upper()
    if corridor_key not in CORRIDOR_RULES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported corridor '{payload.corridor}'. Supported corridors: {', '.join(CORRIDOR_RULES.keys())}"
        )

    rule = CORRIDOR_RULES[corridor_key]
    if payload.amount_src < rule["min_amount"] or payload.amount_src > rule["max_amount"]:
        currency = corridor_key.split('_')[0]
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Transfer amount {payload.amount_src} is outside allowed corridor limits ({rule['min_amount']} to {rule['max_amount']} {currency})"
        )

    # 1. Calculate BDT settlement and fees
    pricing = calculate_fees_and_payout(payload.corridor, payload.amount_src)

    # 2. Check risk scoring
    risk_result = anomaly_scorer.score_transfer(
        amount_src=payload.amount_src,
        is_new_receiver=payload.simulate_anomaly or (payload.amount_src >= 5000),
        is_new_device=payload.simulate_anomaly,
        velocity_1h=3 if payload.simulate_anomaly else 1,
        simulate_anomaly=payload.simulate_anomaly
    )

    transfer_id = f"t_{uuid.uuid4().hex[:8]}"

    # 3. Create Transfer record
    transfer = Transfer(
        id=transfer_id,
        sender_id=payload.sender_id,
        receiver_id=payload.receiver_id,
        agent_id=payload.agent_id,
        corridor=payload.corridor,
        amount_src=payload.amount_src,
        amount_bdt=pricing["net_bdt"],
        fee_bdt=pricing["fee_bdt"],
        device_id=payload.device_id,
        channel=payload.channel or "app",
        status=risk_result["status"],
        risk_score=risk_result["score"]
    )
    db.add(transfer)

    # 4. If in_review, create RiskAlert record
    if risk_result["status"] == "in_review":
        alert_id = f"a_{uuid.uuid4().hex[:6]}"
        explanation_data = generate_analyst_explanation({
            "reason_codes": risk_result["reason_codes"],
            "amount_src": payload.amount_src,
            "score": risk_result["score"],
            "velocity": 3 if payload.simulate_anomaly else 1,
            "suggested_action": risk_result["suggested_action"]
        })
        
        alert = RiskAlert(
            id=alert_id,
            transfer_id=transfer_id,
            score=risk_result["score"],
            reason_codes=json.dumps(risk_result["reason_codes"]),
            explanation=f"{explanation_data['what_happened']} {explanation_data['why_risky']}",
            suggested_action=risk_result["suggested_action"],
            status="open",
            model_version=risk_result["model_version"]
        )
        db.add(alert)
        message = "Transfer routed to human safety review queue."
    else:
        message = "Transfer processed instantly."

    db.commit()

    return {
        "transfer_id": transfer_id,
        "status": risk_result["status"],
        "risk_score": risk_result["score"],
        "reason_codes": risk_result["reason_codes"],
        "message": message,
        "amount_bdt": pricing["net_bdt"],
        "fee_bdt": pricing["fee_bdt"]
    }

@router.get("")
def list_transfers(limit: int = 50, db: Session = Depends(get_db)):
    rows = db.query(Transfer).order_by(Transfer.created_at.desc()).limit(limit).all()
    return [
        {
            "id": r.id,
            "sender_id": r.sender_id,
            "receiver_id": r.receiver_id,
            "corridor": r.corridor,
            "amount_src": r.amount_src,
            "amount_bdt": r.amount_bdt,
            "fee_bdt": r.fee_bdt,
            "status": r.status,
            "risk_score": r.risk_score,
            "created_at": str(r.created_at)
        }
        for r in rows
    ]

@router.get("/{id}")
def get_transfer(id: str, db: Session = Depends(get_db)):
    trx = db.query(Transfer).filter(Transfer.id == id).first()
    if not trx:
        raise HTTPException(status_code=404, detail="Transfer not found")
    return {
        "id": trx.id,
        "sender_id": trx.sender_id,
        "receiver_id": trx.receiver_id,
        "corridor": trx.corridor,
        "amount_src": trx.amount_src,
        "amount_bdt": trx.amount_bdt,
        "fee_bdt": trx.fee_bdt,
        "status": trx.status,
        "risk_score": trx.risk_score,
        "created_at": str(trx.created_at)
    }

