"""
Phase 2 Machine Learning, TreeSHAP & Conformal Prediction Test Suite
Tests:
1. Supervised LightGBM + Platt Calibration scoring and TreeSHAP attribution extraction.
2. Inductive Conformal Prediction set generation, empirical doubt handling, and zero-auto-block compliance.
3. False Positive Rate (FPR) guarantee on legitimate high-value remittance transactions.
4. Graceful fallback to Isolation Forest if supervised artifacts are unavailable.
5. End-to-end API integration for /api/v1/transfers and /api/v1/analyst/alerts/{id} returning conformal & SHAP fields.
"""

import sys
from pathlib import Path
import pytest
from unittest.mock import patch

# Ensure backend root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from app.main import app
from app.services.risk import AnomalyScorer, anomaly_scorer
from app.auth import create_access_token

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_rate_limit_state():
    from app.limiter import limiter
    limiter.reset()

# -----------------------------------------------------------------------------
# 1. LightGBM & TreeSHAP Verification
# -----------------------------------------------------------------------------

def test_supervised_model_initialization():
    """Verify that the AnomalyScorer initializes with LightGBM and Platt calibration."""
    assert anomaly_scorer.lgbm_model is not None, "LightGBM model should be loaded"
    assert anomaly_scorer.calibrator is not None, "Platt calibrator should be loaded"
    assert anomaly_scorer.model_version == "risk-v2.0-lgbm"
    assert anomaly_scorer.q_hat > 0.0 and anomaly_scorer.q_hat < 0.5
    assert len(anomaly_scorer.feature_columns) > 10

def test_treeshap_feature_attributions_on_anomaly():
    """Verify TreeSHAP attributions identify top risk drivers for anomalous transactions."""
    result = anomaly_scorer.score_transfer(
        amount_src=9500.0,
        is_new_receiver=True,
        is_new_device=True,
        velocity_1h=5,
        simulate_anomaly=True
    )
    
    assert result["score"] >= 50.0
    assert result["status"] == "in_review"
    assert "factors" in result
    assert isinstance(result["factors"], list)
    assert len(result["factors"]) > 0
    
    # Check factor schema and non-empty contributions
    for f in result["factors"]:
        assert "name" in f and len(f["name"]) > 0
        assert "contribution_pct" in f and f["contribution_pct"] > 0
        assert f["impact"] == "elevates_risk"
    
    # Verify top factors sum to <= 100%
    total_pct = sum(f["contribution_pct"] for f in result["factors"])
    assert total_pct <= 100.1

def test_benign_transfer_scoring():
    """Verify standard legitimate remittance transfers receive low risk scores and 'completed' status."""
    result = anomaly_scorer.score_transfer(
        amount_src=1200.0,
        sender_avg=1200.0,
        sender_std=200.0,
        velocity_1h=1,
        frequency_7d=1,
        frequency_30d=2,
        time_since_last_txn_hours=140.0,
        device_age_days=240,
        accounts_per_device=1,
        sim_swap_recent=False,
        country_jump=False,
        is_new_receiver=False,
        is_new_device=False,
        hour_of_day=14,
        distinct_senders_24h=1,
        corridor="AED_BDT",
        simulate_anomaly=False
    )
    
    assert result["score"] < 40.0
    assert result["status"] == "completed"
    assert result["suggested_action"] == "none"
    assert "LEGITIMATE" in result["prediction_set"]

# -----------------------------------------------------------------------------
# 2. Conformal Prediction & Zero Auto-Block Compliance
# -----------------------------------------------------------------------------

def test_conformal_prediction_set_structure():
    """Verify conformal prediction set format and non-empty guarantees."""
    result = anomaly_scorer.score_transfer(amount_src=2000.0)
    
    pset = result["prediction_set"]
    assert isinstance(pset, list)
    assert len(pset) >= 1
    for label in pset:
        assert label in ["LEGITIMATE", "SCAM"]
    assert isinstance(result["is_doubt"], bool)
    assert isinstance(result["q_hat"], float)
    assert result["q_hat"] > 0.0

def test_doubt_routing_never_auto_blocks():
    """Verify that when conformal uncertainty (doubt) occurs, the system routes to OTP step-up, NEVER hard blocking."""
    # Test scoring directly under simulated doubt
    scorer = AnomalyScorer()
    with patch.object(scorer.calibrator, "predict_proba", return_value=[[0.50, 0.50]]):
        res = scorer.score_transfer(amount_src=3000.0)
        assert res["is_doubt"] is True
        assert "LEGITIMATE" in res["prediction_set"]
        assert "SCAM" in res["prediction_set"]
        # Mandatory zero auto-blocking requirement:
        assert res["status"] == "in_review"
        assert res["suggested_action"] == "otp_step_up"
        assert res["status"] != "blocked"
        assert "CONFORMAL_DOUBT_FLAG" in res["reason_codes"]

# -----------------------------------------------------------------------------
# 3. High-Value Legitimate FPR Verification
# -----------------------------------------------------------------------------

def test_legitimate_high_value_transfers_do_not_flag_false_positives():
    """Verify that legitimate high-value remittance transfers (Eid gifts / business savings) are not falsely blocked."""
    high_value_amounts = [5000.0, 7500.0, 10000.0, 15000.0]
    
    for amount in high_value_amounts:
        res = anomaly_scorer.score_transfer(
            amount_src=amount,
            sender_avg=amount,
            sender_std=1000.0,
            velocity_1h=1,
            frequency_7d=1,
            frequency_30d=2,
            time_since_last_txn_hours=200.0,
            device_age_days=300,
            accounts_per_device=1,
            sim_swap_recent=False,
            country_jump=False,
            is_new_receiver=False,
            is_new_device=False,
            hour_of_day=15,
            distinct_senders_24h=1,
            corridor="AED_BDT",
            simulate_anomaly=False
        )
        # Must not be flagged as severe fraud, and never blocked
        assert res["status"] in ["completed", "in_review"], f"High value {amount} had unexpected status {res['status']}"
        assert res["status"] != "blocked"
        # Calibrated scam probability should remain low
        assert res["calibrated_prob"] < 0.40

# -----------------------------------------------------------------------------
# 4. Isolation Forest Fallback Verification
# -----------------------------------------------------------------------------

def test_fallback_to_isolation_forest():
    """Verify that AnomalyScorer falls back gracefully to Isolation Forest if supervised artifacts are unavailable."""
    fallback_scorer = AnomalyScorer()
    # Simulate missing supervised model
    fallback_scorer.lgbm_model = None
    fallback_scorer.calibrator = None
    fallback_scorer.model_version = "risk-v1.0-iforest"
    
    # Normal transaction scoring with fallback
    res_normal = fallback_scorer.score_transfer(amount_src=1500.0, simulate_anomaly=False)
    assert 0.0 <= res_normal["score"] <= 100.0
    assert res_normal["status"] in ["completed", "in_review"]
    assert res_normal["model_version"] == "risk-v1.0-iforest"
    assert res_normal["status"] != "blocked"
    
    # Anomaly scoring with fallback
    res_anomaly = fallback_scorer.score_transfer(amount_src=8000.0, simulate_anomaly=True)
    assert res_anomaly["score"] >= 50.0
    assert res_anomaly["status"] == "in_review"
    assert res_anomaly["model_version"] == "risk-v1.0-iforest"

# -----------------------------------------------------------------------------
# 5. API Endpoints Contract Integration
# -----------------------------------------------------------------------------

def test_api_create_transfer_returns_conformal_and_shap_fields():
    """Verify /api/v1/transfers returns factors, prediction_set, is_doubt, q_hat, suggested_action."""
    payload = {
        "sender_id": "u_send_phase2_01",
        "receiver_id": "u_recv_phase2_01",
        "corridor": "AED_BDT",
        "amount_src": 6500.0,
        "simulate_anomaly": True
    }
    res = client.post("/api/v1/transfers", json=payload)
    assert res.status_code == 201
    data = res.json()
    
    assert "transfer_id" in data
    assert "status" in data
    assert "risk_score" in data
    assert "factors" in data
    assert isinstance(data["factors"], list)
    assert len(data["factors"]) > 0
    assert "prediction_set" in data
    assert isinstance(data["prediction_set"], list)
    assert "is_doubt" in data
    assert isinstance(data["is_doubt"], bool)
    assert "q_hat" in data
    assert isinstance(data["q_hat"], float)
    assert "suggested_action" in data
    assert data["status"] != "blocked"

def test_api_analyst_alert_detail_returns_conformal_and_shap_fields():
    """Verify /api/v1/analyst/alerts/{id} returns enriched factors and conformal fields."""
    token = create_access_token({"sub": "u_analyst_01", "role": "analyst"})
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Trigger an alert via transfer
    t_payload = {
        "sender_id": "u_send_phase2_02",
        "receiver_id": "u_recv_phase2_02",
        "corridor": "AED_BDT",
        "amount_src": 8500.0,
        "simulate_anomaly": True
    }
    t_res = client.post("/api/v1/transfers", json=t_payload)
    assert t_res.status_code == 201
    
    # 2. Get open alerts
    res = client.get("/api/v1/analyst/alerts?status=open", headers=headers)
    assert res.status_code == 200
    alerts = res.json()
    assert len(alerts) > 0
    
    # 3. Check alert detail
    alert_id = alerts[0]["alert_id"]
    det_res = client.get(f"/api/v1/analyst/alerts/{alert_id}", headers=headers)
    assert det_res.status_code == 200
    det = det_res.json()
    
    assert det["alert_id"] == alert_id
    assert "factors" in det
    assert isinstance(det["factors"], list)
    assert "prediction_set" in det
    assert "is_doubt" in det
    assert "q_hat" in det
