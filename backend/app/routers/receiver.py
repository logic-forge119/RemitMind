from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Transfer, Goal
from app.schemas import ReceiverSummaryResponse, SplitItem
from app.services.explain import generate_receiver_summary

router = APIRouter(prefix="/api/v1/receiver", tags=["Receiver Portal"])

@router.get("/{id}/summary", response_model=ReceiverSummaryResponse)
def get_receiver_summary(id: str, lang: str = Query("bn"), db: Session = Depends(get_db)):
    # Find latest transfer for this receiver
    trx = db.query(Transfer).filter(Transfer.receiver_id == id).order_by(Transfer.created_at.desc()).first()
    
    if trx:
        received_bdt = trx.amount_bdt
        fee_bdt = trx.fee_bdt
    else:
        received_bdt = 67780.0
        fee_bdt = 1220.0

    # Get associated goals
    goals = db.query(Goal).filter(Goal.receiver_id == id).all()
    suggested_split = []
    if goals:
        for g in goals:
            suggested_split.append(SplitItem(name=g.name, bdt=round(received_bdt * (g.share_pct / 100.0), 2)))
    else:
        suggested_split = [
            SplitItem(name="rent", bdt=round(received_bdt * 0.50, 2)),
            SplitItem(name="school", bdt=round(received_bdt * 0.30, 2)),
            SplitItem(name="savings", bdt=round(received_bdt * 0.20, 2))
        ]

    summary_text = generate_receiver_summary(received_bdt, fee_bdt, sender_name="রহিম ভাই", lang=lang)

    return {
        "received_bdt": received_bdt,
        "fee_bdt": fee_bdt,
        "summary": summary_text,
        "suggested_split": suggested_split
    }
