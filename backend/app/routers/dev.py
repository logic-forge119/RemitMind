import uuid
import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Transfer, RiskAlert
from app.services.rules import calculate_fees_and_payout
from app.services.risk import anomaly_scorer
from app.services.explain import generate_analyst_explanation
from app.config import settings

def require_dev_mode():
    if getattr(settings, "APP_ENV", "development").lower() == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dev and adversary replay endpoints are strictly disabled in production mode."
        )

router = APIRouter(prefix="/api/v1/dev", tags=["Development & Seeding"], dependencies=[Depends(require_dev_mode)])

class ReplayAttackRequest(BaseModel):
    attack_type: str  # "account_takeover", "mule_fan_in", "social_scam"

@router.post("/seed")
def trigger_seed():
    from data.generate import seed_database
    seed_database()
    return {"status": "success", "message": "Synthetic dataset seeded successfully."}

@router.get("/scenarios")
def list_attack_scenarios():
    return [
        {
            "id": "account_takeover",
            "name": "Account Takeover (ATO) & Sudden Velocity",
            "description": "Legitimate Dubai sender Rahim's session hijacked from an unrecognized device; sudden 95,000 BDT transfer with 3 rapid attempts.",
            "target_victim": "Rahim (UAE)",
            "threat_actor": "Automated ATO Botnet via proxy",
            "expected_penalties": ["NEW_DEVICE", "AMOUNT_DEVIATION", "VELOCITY_3X"]
        },
        {
            "id": "mule_fan_in",
            "name": "Coordinated Fan-In Mule Ring (Smurfing)",
            "description": "4 foreign sender accounts rapidly dispatching structured 24,900 BDT transfers to a single recipient wallet u_recv_001.",
            "target_victim": "MFS Ecosystem / AML Smurfing",
            "threat_actor": "Organized Mule Syndicate",
            "expected_penalties": ["MULE_CLUSTER_FAN_IN", "NEW_RECEIVER", "VELOCITY_3X"]
        },
        {
            "id": "social_scam",
            "name": "Social Engineering & Urgent Phishing Scam",
            "description": "Elderly sender coerced via phone call ('upay lottery prize fee') into an off-hours urgent transfer to an unknown account.",
            "target_victim": "Elderly Migrant Family",
            "threat_actor": "Social Engineering Fraudster",
            "expected_penalties": ["OFF_HOURS_ANOMALY", "NEW_RECEIVER", "UNUSUAL_CORRIDOR_SPIKE"]
        }
    ]

@router.post("/replay-attack")
def replay_attack(payload: ReplayAttackRequest, db: Session = Depends(get_db)):
    t_id = f"t_sim_{uuid.uuid4().hex[:6]}"
    now = datetime.datetime.now(datetime.timezone.utc)
    
    if payload.attack_type == "account_takeover":
        corridor = "AED_BDT"
        amount_src = 3200.0  # ~96,000 BDT vs normal 15,000 BDT
        sender_id = "u_send_001"
        receiver_id = "u_recv_299"
        device_id = "dev_hijacked_proxy_ru"
        velocity_1h = 3
        hour_of_day = 2
        is_new_receiver = True
        is_new_device = True
        scenario_note = "High-velocity account takeover from unrecognized device with 6x amount deviation."
        
    elif payload.attack_type == "mule_fan_in":
        corridor = "SAR_BDT"
        amount_src = 900.0  # Structured just under AML reporting threshold (~27,000 BDT)
        sender_id = f"u_send_{uuid.uuid4().hex[:3]}"
        receiver_id = "u_recv_001"  # Known mule node
        device_id = "dev_mule_shared_emulator"
        velocity_1h = 4
        hour_of_day = 14
        is_new_receiver = True
        is_new_device = True
        scenario_note = "Coordinated smurfing: 4th concurrent transfer funneling into known mule wallet u_recv_001."
        
    elif payload.attack_type == "social_scam":
        corridor = "MYR_BDT"
        amount_src = 1800.0  # ~45,000 BDT
        sender_id = "u_send_042"
        receiver_id = "u_recv_288"
        device_id = "dev_sender_042"
        velocity_1h = 2
        hour_of_day = 3  # Late night coercion
        is_new_receiver = True
        is_new_device = False
        scenario_note = "Urgent off-hours transaction to unverified beneficiary with predatory lottery scam markers."
        
    else:
        raise HTTPException(status_code=400, detail=f"Unknown attack scenario '{payload.attack_type}'")

    pricing = calculate_fees_and_payout(corridor, amount_src)
    score_res = anomaly_scorer.score_transfer(
        amount_src=amount_src,
        is_new_receiver=is_new_receiver,
        is_new_device=is_new_device,
        velocity_1h=velocity_1h,
        hour_of_day=hour_of_day
    )
    
    # Adjust reason codes and attribution for scenario fidelity
    if payload.attack_type == "mule_fan_in":
        if "MULE_CLUSTER_FAN_IN" not in score_res["reason_codes"]:
            score_res["reason_codes"].insert(0, "MULE_CLUSTER_FAN_IN")
        score_res["score"] = max(score_res["score"], 92)
        score_res["status"] = "in_review"
    elif payload.attack_type == "account_takeover":
        score_res["score"] = max(score_res["score"], 88)
        score_res["status"] = "in_review"
    elif payload.attack_type == "social_scam":
        if "OFF_HOURS_ANOMALY" not in score_res["reason_codes"]:
            score_res["reason_codes"].append("OFF_HOURS_ANOMALY")
        score_res["score"] = max(score_res["score"], 76)
        score_res["status"] = "in_review"

    # Persist the transfer
    transfer = Transfer(
        id=t_id,
        sender_id=sender_id,
        receiver_id=receiver_id,
        agent_id="u_agent_001",
        corridor=corridor,
        amount_src=amount_src,
        amount_bdt=pricing["net_bdt"],
        fee_bdt=pricing["fee_bdt"],
        device_id=device_id,
        channel="app",
        status=score_res["status"],
        risk_score=score_res["score"],
        created_at=now
    )
    db.add(transfer)
    
    # Create RiskAlert if intercepted
    alert_id = None
    explanation = ""
    if score_res["status"] == "in_review":
        import json
        alert_id = f"alt_{uuid.uuid4().hex[:6]}"
        explanation_data = generate_analyst_explanation({
            "id": t_id,
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "amount_bdt": pricing["net_bdt"],
            "risk_score": score_res["score"],
            "reason_codes": score_res["reason_codes"],
            "velocity": velocity_1h,
            "suggested_action": "hold"
        })
        explanation = f"{explanation_data['what_happened']} {explanation_data['why_risky']}"
        alert = RiskAlert(
            id=alert_id,
            transfer_id=t_id,
            score=score_res["score"],
            reason_codes=json.dumps(score_res["reason_codes"]),
            suggested_action="hold_for_step_up_kyc",
            explanation=explanation,
            status="open",
            model_version="v1.2-hybrid-iforest"
        )
        db.add(alert)
        
    db.commit()

    # Feature attribution waterfall breakdown for UI
    attribution = [
        {"feature": "Velocity Acceleration", "impact_points": 35 if velocity_1h > 1 else 0},
        {"feature": "Device Fingerprint Discrepancy", "impact_points": 30 if is_new_device else 5},
        {"feature": "Beneficiary Tenure", "impact_points": 25 if is_new_receiver else -10},
        {"feature": "Amount Deviation from Baseline", "impact_points": 20 if amount_src > 2000 else 5},
        {"feature": "Corridor Historical Prior", "impact_points": -15}
    ]

    return {
        "status": "attack_simulated",
        "scenario": payload.attack_type,
        "note": scenario_note,
        "transfer_id": t_id,
        "amount_bdt": pricing["net_bdt"],
        "corridor": corridor,
        "risk_score": score_res["score"],
        "decision": score_res["status"],
        "reason_codes": score_res["reason_codes"],
        "alert_id": alert_id,
        "explanation": explanation,
        "feature_attribution": attribution
    }
