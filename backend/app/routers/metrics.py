from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Transfer
from app.schemas import FairnessMetricsResponse, FairnessMetricItem

router = APIRouter(prefix="/api/v1/metrics", tags=["Fairness & Audit"])

@router.get("/fairness", response_model=FairnessMetricsResponse)
def get_fairness_audit(db: Session = Depends(get_db)):
    transfers = db.query(Transfer).all()
    total_count = len(transfers)

    corridors = ["AED_BDT", "SAR_BDT", "MYR_BDT", "EUR_BDT", "USD_BDT"]
    amount_bands = [
        ("< 50k BDT", 0, 50000),
        ("50k-150k BDT", 50000, 150000),
        ("> 150k BDT", 150000, 999999999)
    ]

    metric_items = []
    overall_flagged = 0

    for c in corridors:
        c_transfers = [t for t in transfers if t.corridor == c]
        for band_name, low, high in amount_bands:
            band_transfers = [t for t in c_transfers if low <= (t.amount_bdt or 0) < high]
            count = len(band_transfers)
            flagged = len([t for t in band_transfers if t.status in ["in_review", "held", "escalated"]])
            rate = round((flagged / count * 100), 1) if count > 0 else 0.0

            metric_items.append(FairnessMetricItem(
                corridor=c,
                amount_band=band_name,
                total_transfers=count,
                flagged_count=flagged,
                alert_rate_pct=rate
            ))

    total_flagged = len([t for t in transfers if t.status in ["in_review", "held", "escalated"]])
    overall_rate = round((total_flagged / total_count * 100), 1) if total_count > 0 else 0.0

    return FairnessMetricsResponse(
        metrics=metric_items,
        overall_alert_rate_pct=overall_rate,
        audited_at=datetime.now().isoformat(),
        notes="Disaggregated alert rate monitored across geographic corridors and ticket amount bands to ensure equitable anomaly thresholds without regional discrimination."
    )
