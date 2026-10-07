"""
Phase 3 Platform and Intelligence Test Suite
Tests:
1. YAML policy engine (config/policy.yaml) with hot reload, admin-only updates, presets, and audit_events logging.
2. Alembic migration verification and database indexes on hot query paths.
3. Authenticated WebSocket /ws/alerts live stream, handshake, rejection of unauthenticated clients, and status.
4. Agent structuring intelligence (volume z-score, BDT 45k-50k CTR smurfing share, night share, cash-out ratio).
5. Evidence IDs (TXN-, RULE-, FACTOR-) and BM25 regulatory SOP retrieval over docs/sop/.
6. Verification that STR output contains ONLY Evidence IDs that exist in the database.
7. Analyst KPI endpoint (/api/v1/analyst/kpis) operations metrics.
"""

import sys
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure backend root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.main import app
from app.db import SessionLocal
from app.models import AuditEvent, Transfer, RiskAlert, Agent
from app.auth import create_access_token
from app.services.sop_retrieval import sop_retriever, build_evidence_ids, validate_evidence_ids_in_db
from app.services.policy import policy_engine

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_rate_limit_state():
    from app.limiter import limiter
    limiter.reset()

# -----------------------------------------------------------------------------
# 1. YAML Policy Engine & Audit Events
# -----------------------------------------------------------------------------

def test_get_policy_returns_weights_and_presets():
    """Verify authenticated user can retrieve active policy configuration."""
    token = create_access_token({"sub": "u_sender_01", "role": "sender"})
    headers = {"Authorization": f"Bearer {token}"}
    res = client.get("/api/v1/policy", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "weights" in data
    assert "supervised_ml" in data["weights"]
    assert "presets" in data
    assert "nocturnal_guard" in data["presets"]
    assert "mule_syndicate_strike" in data["presets"]
    assert "thresholds" in data

def test_policy_update_requires_admin_role():
    """Verify non-admin users cannot update policy."""
    analyst_token = create_access_token({"sub": "u_analyst_01", "role": "analyst"})
    headers = {"Authorization": f"Bearer {analyst_token}"}
    
    payload = {"preset": "nocturnal_guard"}
    res = client.put("/api/v1/policy", json=payload, headers=headers)
    assert res.status_code == 403

def test_admin_updates_policy_and_writes_audit_event():
    """Verify admin can apply preset or update weights, persisting an audit event."""
    admin_token = create_access_token({"sub": "u_admin_root", "role": "admin"})
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    payload = {
        "preset": "mule_syndicate_strike"
    }
    res = client.put("/api/v1/policy", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "diff" in data
    audit_id = data["audit_event_id"]
    
    # Verify in DB
    db = SessionLocal()
    audit_record = db.query(AuditEvent).filter(AuditEvent.id == audit_id).first()
    assert audit_record is not None
    assert audit_record.event_type == "policy_update"
    assert audit_record.actor_id == "u_admin_root"
    db.close()
    
    # Reset back to standard preset
    reset_res = client.put("/api/v1/policy", json={"preset": "standard"}, headers=headers)
    assert reset_res.status_code == 200

def test_policy_audit_log_endpoint():
    """Verify analyst or admin can retrieve policy modification audit trail."""
    analyst_token = create_access_token({"sub": "u_analyst_01", "role": "analyst"})
    headers = {"Authorization": f"Bearer {analyst_token}"}
    res = client.get("/api/v1/policy/audit", headers=headers)
    assert res.status_code == 200
    events = res.json()
    assert isinstance(events, list)
    assert len(events) > 0
    assert "event_type" in events[0]
    assert events[0]["event_type"] == "policy_update"

# -----------------------------------------------------------------------------
# 2. Database & Alembic Migration Indexes
# -----------------------------------------------------------------------------

def test_audit_events_table_and_indexes_exist():
    """Verify audit_events table and performance indexes are live in database."""
    from sqlalchemy import inspect
    from app.db import engine
    inspector = inspect(engine)
    
    tables = inspector.get_table_names()
    assert "audit_events" in tables
    assert "transfers" in tables
    assert "risk_alerts" in tables
    
    # Check index names
    transfer_indexes = [idx["name"] for idx in inspector.get_indexes("transfers")]
    assert any("sender" in name for name in transfer_indexes)
    assert any("receiver" in name for name in transfer_indexes)
    
    audit_indexes = [idx["name"] for idx in inspector.get_indexes("audit_events")]
    assert any("event_type" in name or "type" in name for name in audit_indexes)

# -----------------------------------------------------------------------------
# 3. WebSocket Live Alert Stream
# -----------------------------------------------------------------------------

def test_websocket_status_endpoint():
    """Verify polling fallback status endpoint returns online."""
    res = client.get("/api/v1/ws/status")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"
    assert data["fallback"] == "polling"

def test_websocket_connection_with_valid_token():
    """Verify analyst can establish live WebSocket stream and receive handshake."""
    token = create_access_token({"sub": "u_analyst_ws", "role": "analyst"})
    with client.websocket_connect(f"/ws/alerts?token={token}") as ws:
        init_msg = ws.receive_json()
        assert init_msg["type"] == "CONNECTED"
        assert init_msg["role"] == "analyst"
        
        # Test ping-pong keep-alive
        ws.send_text("ping")
        pong = ws.receive_text()
        assert pong == "pong"

def test_websocket_rejects_unauthenticated_connection():
    """Verify connection without token is rejected."""
    with pytest.raises(Exception):
        with client.websocket_connect("/ws/alerts") as ws:
            pass

def test_websocket_rejects_insufficient_role():
    """Verify sender role cannot connect to analyst live alerts."""
    sender_token = create_access_token({"sub": "u_sender_ws", "role": "sender"})
    with pytest.raises(Exception):
        with client.websocket_connect(f"/ws/alerts?token={sender_token}") as ws:
            pass

# -----------------------------------------------------------------------------
# 4. Agent Structuring Intelligence
# -----------------------------------------------------------------------------

def test_agent_structuring_risk_endpoint():
    """Verify agent structuring intelligence returns peer z-scores, CTR evasion, and nocturnal ratios."""
    token = create_access_token({"sub": "u_analyst_01", "role": "analyst"})
    headers = {"Authorization": f"Bearer {token}"}
    
    res = client.get("/api/v1/agents/structuring-risk", headers=headers)
    assert res.status_code == 200
    data = res.json()
    
    assert "agents" in data
    assert isinstance(data["agents"], list)
    assert len(data["agents"]) > 0
    assert "audited_at" in data
    
    first = data["agents"][0]
    assert "agent_id" in first
    assert "district" in first
    assert "volume_zscore" in first
    assert "near_threshold_share_pct" in first
    assert "night_share_pct" in first
    assert "cashout_ratio" in first
    assert first["risk_level"] in ["low", "medium", "high"]
    assert isinstance(first["structuring_flags"], list)

# -----------------------------------------------------------------------------
# 5. Evidence IDs & BM25 SOP Regulatory Retrieval
# -----------------------------------------------------------------------------

def test_bm25_sop_retrieval_finds_relevant_sections():
    """Verify BM25 retrieval finds accurate BFIU SOP clauses for given fraud scenarios."""
    results = sop_retriever.retrieve("mule account rapid velocity pass through", top_k=2)
    assert len(results) > 0
    assert any("BFIU-SOP" in r["id"] for r in results)
    
    smurfing_results = sop_retriever.retrieve("smurfing near threshold 50000 CTR evasion", top_k=2)
    assert len(smurfing_results) > 0
    assert any("4.2" in r["id"] or "STRUC" in r["id"] or "SEC" in r["id"] for r in smurfing_results)

def test_evidence_id_generation_and_db_validation():
    """Verify Evidence IDs format and validate against database."""
    db = SessionLocal()
    first_tx = db.query(Transfer).first()
    assert first_tx is not None, "Need at least one transfer in DB for test"
    
    e_ids = build_evidence_ids(
        transfer_id=first_tx.id,
        reason_codes=["VELOCITY_3X", "NEW_DEVICE"],
        factors=[{"name": "Hardware_Trust"}]
    )
    
    assert f"TXN-{first_tx.id}" in e_ids
    assert "RULE-VELOCITY_3X" in e_ids
    assert "FACTOR-Hardware_Trust" in e_ids
    
    # Test DB validation passes for real transaction
    val_res = validate_evidence_ids_in_db(e_ids, db)
    assert val_res["valid"] is True
    assert first_tx.id in val_res["verified_txns"]
    
    # Test DB validation catches fake transaction ID
    fake_e_ids = ["TXN-t_nonexistent_xyz999"]
    fake_val = validate_evidence_ids_in_db(fake_e_ids, db)
    assert fake_val["valid"] is False
    assert "t_nonexistent_xyz999" in fake_val["missing_txns"]
    db.close()

def test_str_output_contains_only_db_verified_evidence_ids():
    """
    Critical requirement: Verify BFIU Form 2 STR output contains ONLY
    Evidence IDs whose underlying transactions exist in the database.
    """
    db = SessionLocal()
    # 1. Trigger or find an alert
    alert = db.query(RiskAlert).first()
    if not alert:
        # Create transfer and alert
        tx_payload = {
            "sender_id": "u_str_test_sender",
            "receiver_id": "u_str_test_receiver",
            "corridor": "AED_BDT",
            "amount_src": 8500.0
        }
        res_tx = client.post("/api/v1/transfers", json=tx_payload)
        assert res_tx.status_code == 201
        alert = db.query(RiskAlert).order_by(RiskAlert.created_at.desc()).first()
    
    assert alert is not None
    
    # 2. Generate STR
    payload = {
        "alert_id": alert.id,
        "analyst_id": "u_analyst_lead"
    }
    res_str = client.post("/api/v1/compliance/generate-str", json=payload)
    assert res_str.status_code == 200
    data = res_str.json()
    
    assert "evidence_ids" in data
    assert isinstance(data["evidence_ids"], list)
    assert len(data["evidence_ids"]) > 0
    
    # 3. Validate ALL TXN Evidence IDs against DB
    val = validate_evidence_ids_in_db(data["evidence_ids"], db)
    assert val["valid"] is True, f"Found unregistered evidence IDs: {val['missing_txns']}"
    
    # 4. Check that narrative cites BM25 retrieved SOP clause
    assert "Evidence IDs" in data["narrative"]
    assert "BFIU-SOP" in data["narrative"]
    db.close()

# -----------------------------------------------------------------------------
# 6. Analyst Operations KPIs
# -----------------------------------------------------------------------------

def test_analyst_kpi_endpoint():
    """Verify /api/v1/analyst/kpis returns operational metrics."""
    analyst_token = create_access_token({"sub": "u_analyst_lead", "role": "analyst"})
    headers = {"Authorization": f"Bearer {analyst_token}"}
    
    res = client.get("/api/v1/analyst/kpis", headers=headers)
    assert res.status_code == 200
    data = res.json()
    
    assert "open_today" in data
    assert "closed_today" in data
    assert "avg_review_time_seconds" in data
    assert "false_positive_trend" in data
    assert "7d_fp_rate_pct" in data["false_positive_trend"]
    assert "30d_fp_rate_pct" in data["false_positive_trend"]
    assert "top_5_risky_corridors" in data
    assert isinstance(data["top_5_risky_corridors"], list)
    assert len(data["top_5_risky_corridors"]) > 0
    assert "fraud_caught_vs_missed" in data
    assert "caught" in data["fraud_caught_vs_missed"]
    assert "generated_at" in data
