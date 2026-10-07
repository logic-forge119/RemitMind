"""
Agent Structuring Intelligence Service
Analyzes agent transaction distributions for BFIU threshold evasion (smurfing),
district peer volume z-scores, nocturnal transaction spikes, and float exhaustion ratios.
"""

from datetime import datetime, timezone
from typing import List, Dict, Any
from sqlalchemy.orm import Session
import numpy as np

from app.models import Agent, Transfer

def calculate_agent_structuring_metrics(db: Session) -> Dict[str, Any]:
    """
    Computes structuring and AML compliance metrics for all network agents:
    - Volume Z-Score relative to district peers
    - Near-Threshold (BDT 45k-49.9k) CTR evasion share
    - Nocturnal off-hours share (00:00 - 06:00 BST)
    - Cash-out to cash-in turnover ratio
    """
    agents = db.query(Agent).all()
    if not agents:
        return {
            "agents": [],
            "flagged_agent_count": 0,
            "high_risk_count": 0,
            "audited_at": datetime.now(timezone.utc).isoformat()
        }

    # Fetch transfers grouped by agent
    transfers = db.query(Transfer).all()
    transfers_by_agent: Dict[str, List[Transfer]] = {}
    for t in transfers:
        if t.agent_id:
            transfers_by_agent.setdefault(t.agent_id, []).append(t)

    # Calculate agent volumes and group by district for peer normalization
    agent_volumes: Dict[str, float] = {}
    district_volumes: Dict[str, List[float]] = {}

    for ag in agents:
        ag_txns = transfers_by_agent.get(ag.id, [])
        vol = sum(t.amount_bdt for t in ag_txns) if ag_txns else 0.0
        agent_volumes[ag.id] = vol
        dist = ag.district or "Unknown"
        district_volumes.setdefault(dist, []).append(vol)

    # Compute district peer statistics (mean & std)
    district_stats: Dict[str, Dict[str, float]] = {}
    for dist, vols in district_volumes.items():
        arr = np.array(vols, dtype=float)
        mean_v = float(np.mean(arr)) if len(arr) > 0 else 0.0
        std_v = float(np.std(arr)) if len(arr) > 1 else 0.0
        district_stats[dist] = {"mean": mean_v, "std": std_v if std_v > 0 else 1.0}

    metric_list = []
    flagged_count = 0
    high_risk_count = 0

    for ag in agents:
        ag_txns = transfers_by_agent.get(ag.id, [])
        n_txns = len(ag_txns)
        vol = agent_volumes[ag.id]
        dist = ag.district or "Unknown"
        stats = district_stats.get(dist, {"mean": vol, "std": 1.0})

        z_score = (vol - stats["mean"]) / stats["std"] if stats["std"] > 0 else 0.0

        # Near-Threshold CTR Structuring (BDT 45,000 to 49,999)
        near_thresh_count = sum(1 for t in ag_txns if 45000.0 <= t.amount_bdt <= 49999.0)
        near_thresh_share = (near_thresh_count / n_txns * 100.0) if n_txns > 0 else 0.0

        # Nocturnal Transactions (00:00 - 06:00 BST)
        night_count = sum(
            1 for t in ag_txns
            if t.created_at and (t.created_at.hour <= 6 or t.created_at.hour >= 23)
        )
        night_share = (night_count / n_txns * 100.0) if n_txns > 0 else 0.0

        # Float Cash-Out Ratio
        cash_in = max(50000.0, float(ag.cash_on_hand or 100000.0))
        cashout_ratio = vol / cash_in if cash_in > 0 else 1.0

        # Structuring Risk Rules
        flags = []
        if near_thresh_share >= 10.0 or near_thresh_count >= 5:
            flags.append("SMURFING_NEAR_50K_CTR_THRESHOLD")
        if z_score >= 2.0:
            flags.append("DISTRICT_PEER_VOLUME_ANOMALY")
        if night_share >= 20.0:
            flags.append("ELEVATED_NOCTURNAL_VOLUME")
        if cashout_ratio >= 3.0:
            flags.append("RAPID_FLOAT_DEPLETION_RISK")

        # Determine overall Risk Level
        if len(flags) >= 2 or near_thresh_share >= 15.0 or z_score >= 2.5:
            risk_level = "high"
            high_risk_count += 1
            flagged_count += 1
        elif len(flags) >= 1 or near_thresh_share >= 5.0 or z_score >= 1.5:
            risk_level = "medium"
            flagged_count += 1
        else:
            risk_level = "low"

        metric_list.append({
            "agent_id": ag.id,
            "district": dist,
            "total_transfers_30d": n_txns,
            "total_volume_bdt": round(vol, 2),
            "volume_zscore": round(float(z_score), 2),
            "near_threshold_count": near_thresh_count,
            "near_threshold_share_pct": round(near_thresh_share, 1),
            "night_count": night_count,
            "night_share_pct": round(night_share, 1),
            "cashout_bdt": round(vol, 2),
            "cashin_bdt": round(cash_in, 2),
            "cashout_ratio": round(cashout_ratio, 2),
            "risk_level": risk_level,
            "structuring_flags": flags
        })

    # Sort so high-risk agents appear first
    metric_list.sort(key=lambda m: (m["risk_level"] == "high", m["risk_level"] == "medium", m["volume_zscore"]), reverse=True)

    return {
        "agents": metric_list,
        "flagged_agent_count": flagged_count,
        "high_risk_count": high_risk_count,
        "audited_at": datetime.now(timezone.utc).isoformat()
    }
