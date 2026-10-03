import pytest
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["service"] == "RemitMind API"

def test_frontend_routes():
    res_landing = client.get("/")
    assert res_landing.status_code == 200
    assert "RemitMind" in res_landing.text

    res_app = client.get("/app")
    assert res_app.status_code == 200
    assert "RemitMind Portal" in res_app.text


def test_plan_recommend():
    payload = {
        "sender_id": "u_test_sender",
        "receiver_id": "u_test_receiver",
        "corridor": "AED_BDT",
        "amount_src": 2000.0,
        "goals": [
            {"name": "rent", "share_pct": 50},
            {"name": "school", "share_pct": 30},
            {"name": "savings", "share_pct": 20}
        ]
    }
    res = client.post("/api/v1/plans/recommend", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "best_day" in data
    assert data["expected_saving_bdt"] > 0
    assert len(data["split"]) == 3
    assert data["confidence"] > 0.5

def test_create_transfer_normal():
    payload = {
        "sender_id": "u_send_001",
        "receiver_id": "u_recv_001",
        "corridor": "AED_BDT",
        "amount_src": 1500.0,
        "device_id": "dev_trusted_user",
        "channel": "app"
    }
    res = client.post("/api/v1/transfers", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["status"] in ["completed", "in_review"]
    assert "transfer_id" in data
    assert data["amount_bdt"] > 0

def test_create_transfer_anomaly():
    payload = {
        "sender_id": "u_send_002",
        "receiver_id": "u_recv_999",
        "corridor": "AED_BDT",
        "amount_src": 8500.0,
        "simulate_anomaly": True
    }
    res = client.post("/api/v1/transfers", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "in_review"
    assert data["risk_score"] >= 40.0
    assert len(data["reason_codes"]) > 0

def test_analyst_alerts_and_decision():
    # 1. Fetch alerts
    res = client.get("/api/v1/analyst/alerts?status=open")
    assert res.status_code == 200
    alerts = res.json()
    assert isinstance(alerts, list)

    if len(alerts) > 0:
        alert_id = alerts[0]["alert_id"]
        # 2. Get detail
        res_det = client.get(f"/api/v1/analyst/alerts/{alert_id}")
        assert res_det.status_code == 200
        det = res_det.json()
        assert det["alert_id"] == alert_id
        assert "what_happened" in det

        # 3. Post decision
        dec_payload = {
            "decision": "approve",
            "note": "Verified legit family remittance",
            "is_fraud": False
        }
        res_dec = client.post(f"/api/v1/analyst/alerts/{alert_id}/decision", json=dec_payload)
        assert res_dec.status_code == 200
        dec_data = res_dec.json()
        assert dec_data["status"] == "closed"
        assert dec_data["transfer_status"] == "completed"

def test_receiver_summary():
    res = client.get("/api/v1/receiver/u_recv_001/summary?lang=bn")
    assert res.status_code == 200
    data = res.json()
    assert data["received_bdt"] > 0
    assert "টাকা" in data["summary"]

def test_agent_forecast():
    res = client.get("/api/v1/agents/ag_01/forecast")
    assert res.status_code == 200
    data = res.json()
    assert len(data["days"]) == 7
    assert data["festival_flag"] is True

def test_fairness_metrics():
    res = client.get("/api/v1/metrics/fairness")
    assert res.status_code == 200
    data = res.json()
    assert "overall_alert_rate_pct" in data
    assert len(data["metrics"]) > 0

def test_dev_scenarios_and_replay_attack():
    # 1. Fetch available attack scenarios
    res = client.get("/api/v1/dev/scenarios")
    assert res.status_code == 200
    scenarios = res.json()
    assert len(scenarios) == 3
    scenario_ids = [s["id"] for s in scenarios]
    assert "account_takeover" in scenario_ids
    assert "mule_fan_in" in scenario_ids
    assert "social_scam" in scenario_ids

    # 2. Replay account takeover attack
    res_ato = client.post("/api/v1/dev/replay-attack", json={"attack_type": "account_takeover"})
    assert res_ato.status_code == 200
    data_ato = res_ato.json()
    assert data_ato["status"] == "attack_simulated"
    assert data_ato["risk_score"] >= 70
    assert data_ato["decision"] == "in_review"
    assert len(data_ato["feature_attribution"]) > 0
    assert data_ato["alert_id"] is not None

    # 3. Replay mule fan-in smurfing attack
    res_mule = client.post("/api/v1/dev/replay-attack", json={"attack_type": "mule_fan_in"})
    assert res_mule.status_code == 200
    data_mule = res_mule.json()
    assert "MULE_CLUSTER_FAN_IN" in data_mule["reason_codes"]
    assert data_mule["risk_score"] >= 90

def test_ai_endpoints():
    # 1. Models catalog
    res_models = client.get("/api/v1/ai/models")
    assert res_models.status_code == 200
    models = res_models.json()
    assert len(models) >= 3

    # 2. Chat copilot
    res_chat = client.post("/api/v1/ai/chat", json={
        "message": "When is the best day to send money to Bangladesh from Dubai?",
        "model": "gemini-1.5-flash",
        "language": "en"
    })
    assert res_chat.status_code == 200
    chat_data = res_chat.json()
    assert "reply" in chat_data
    assert len(chat_data["grounded_facts"]) > 0

    # 3. Risk explain forensic SAR
    res_explain = client.post("/api/v1/ai/explain-risk", json={
        "transfer_id": "TRX-TEST-01",
        "score": 88.0,
        "reason_codes": ["NEW_RECEIVER", "VELOCITY_3X", "NEW_DEVICE"],
        "corridor": "AED_BDT",
        "amount_bdt": 95000.0
    })
    assert res_explain.status_code == 200
    exp_data = res_explain.json()
    assert "narrative" in exp_data
    assert exp_data["recommended_action"] in ["HOLD_24H", "ESCALATE"]

    # 4. Receiver advice in Bangla
    res_rcv = client.post("/api/v1/ai/receiver-advice", json={
        "sender_name": "Rahim",
        "receiver_name": "Amina",
        "amount_bdt": 67780.0,
        "language": "bn"
    })
    assert res_rcv.status_code == 200
    rcv_data = res_rcv.json()
    assert "টাকা" in rcv_data["text"]

    # 5. Agent liquidity planning
    res_liq = client.post("/api/v1/ai/agent-liquidity", json={
        "agent_id": "AG-05",
        "location": "Balaganj",
        "current_cash": 250000.0,
        "peak_demand": 420000.0
    })
    assert res_liq.status_code == 200
    liq_data = res_liq.json()
    assert liq_data["deficit"] == 170000.0
    assert "advice_plan" in liq_data

