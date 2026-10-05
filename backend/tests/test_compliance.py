import pytest
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_generate_bfiu_str():
    payload = {
        "alert_id": "a_test_alert_99",
        "analyst_id": "u_analyst_01"
    }
    res = client.post("/api/v1/compliance/generate-str", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["str_reference"].startswith("BFIU-STR-2026-")
    assert "upay Bangladesh" in data["reporting_entity"]
    assert "sha256_hash" in data
    assert len(data["sha256_hash"]) == 64
    assert data["status"] == "ready_for_submission"
    assert data["transaction_amount_bdt"] > 0
    assert len(data["anomaly_indicators"]) > 0

def test_demographic_parity_endpoint():
    res = client.get("/api/v1/metrics/demographic-parity")
    assert res.status_code == 200
    data = res.json()
    assert "reference_group" in data
    assert "reference_alert_rate_pct" in data
    assert "groups" in data
    assert len(data["groups"]) > 0
    first_group = data["groups"][0]
    assert "category" in first_group
    assert "disparate_impact_ratio" in first_group
    assert "parity_status" in first_group

def test_ai_copilot_sop_grounding():
    payload = {
        "message": "What is the protocol for velocity rapid transfers and BFIU filing?",
        "model": "remitmind-local"
    }
    res = client.post("/api/v1/ai/chat", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "reply" in data
    reply = data["reply"]
    # Check that SOP citation was prepended
    assert "[SOP-001" in reply or "[SOP-004" in reply
