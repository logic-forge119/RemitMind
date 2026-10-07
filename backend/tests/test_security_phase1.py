"""
Phase 1 Security & Normalization Test Suite
Tests:
1. JWT authentication and role-based access control (sender, analyst, admin, agent)
2. SlowAPI rate limiting with bilingual (Bangla + English) 429 response
3. ScamShield anti-evasion normalization against 14 distinct evasion strategies
4. Edge cases for risk scoring and anomaly detection
"""

import sys
from pathlib import Path
import pytest
from datetime import timedelta

# Ensure backend root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from app.main import app
from app.auth import create_access_token, decode_access_token, require_role
from app.services.normalizer import (
    strip_zero_width,
    fold_homoglyphs,
    normalize_text_for_scamshield,
    contains_scam_keyword
)
from app.services.rules import evaluate_rule_penalties, determine_status_and_action
from app.services.risk import anomaly_scorer

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_rate_limit_state():
    from app.limiter import limiter
    limiter.reset()
    yield
    limiter.reset()

# ==============================================================================
# 1. JWT & Role-Based Access Control Tests
# ==============================================================================

def test_jwt_create_and_decode():
    data = {"sub": "u_test_analyst", "role": "analyst", "name": "Test Analyst"}
    token = create_access_token(data, expires_delta=timedelta(minutes=15))
    decoded = decode_access_token(token)
    assert decoded["sub"] == "u_test_analyst"
    assert decoded["role"] == "analyst"
    assert decoded["iss"] == "remitmind-auth-service"

def test_jwt_expired_token():
    # Create token expired 1 hour ago
    data = {"sub": "u_expired", "role": "analyst"}
    token = create_access_token(data, expires_delta=timedelta(hours=-1))
    with pytest.raises(Exception) as exc_info:
        decode_access_token(token)
    assert "expired" in str(exc_info.value).lower()

def test_dev_token_issuance():
    roles = ["sender", "analyst", "admin", "agent"]
    for r in roles:
        res = client.post("/api/v1/auth/dev-token", json={"role": r, "user_id": f"u_{r}_01"})
        assert res.status_code == 200
        body = res.json()
        assert body["token_type"] == "bearer"
        assert body["role"] == r
        assert len(body["access_token"]) > 20

def test_rbac_unauthenticated_request_rejected_401():
    # Attempt accessing analyst queue without credentials
    res = client.get("/api/v1/analyst/alerts")
    assert res.status_code == 401
    err = res.json()
    assert err["detail"]["error"] == "unauthorized"
    assert "detail_bn" in err["detail"]

def test_rbac_insufficient_role_forbidden_403():
    # Obtain a sender token
    token_res = client.post("/api/v1/auth/dev-token", json={"role": "sender", "user_id": "u_sender_99"})
    assert token_res.status_code == 200
    token = token_res.json()["access_token"]

    # Sender attempts to access analyst alerts endpoint
    res = client.get("/api/v1/analyst/alerts", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403
    err = res.json()
    assert err["detail"]["error"] == "forbidden"
    assert "detail_bn" in err["detail"]
    assert "analyst" in err["detail"]["required_roles"]

def test_rbac_analyst_and_admin_authorized_200():
    # Analyst role succeeds
    a_token = client.post("/api/v1/auth/dev-token", json={"role": "analyst", "user_id": "u_analyst_2"}).json()["access_token"]
    res_a = client.get("/api/v1/analyst/alerts", headers={"Authorization": f"Bearer {a_token}"})
    assert res_a.status_code == 200

    # Admin role succeeds
    adm_token = client.post("/api/v1/auth/dev-token", json={"role": "admin", "user_id": "u_admin_1"}).json()["access_token"]
    res_adm = client.get("/api/v1/analyst/alerts", headers={"Authorization": f"Bearer {adm_token}"})
    assert res_adm.status_code == 200

# ==============================================================================
# 2. ScamShield Anti-Evasion Normalization Tests (14 Evasion Vectors)
# ==============================================================================

EVASION_TEST_CASES = [
    # 1. Zero-width spaces in English keyword
    ("Congratulations! You won the l\u200bo\u200bt\u200bt\u200be\u200br\u200by jackpot.", "lottery_fraud"),
    # 2. Cyrillic homoglyphs (Cyrillic 'о' and 'е')
    ("Claim your l\u043ett\u0435ry reward now", "lottery_fraud"),
    # 3. Fullwidth Unicode Latin letters
    ("Official ｌｏｔｔｅｒｙ disbursement fee", "lottery_fraud"),
    # 4. Dot punctuation evasion
    ("Urgent p.r.i.z.e processing fee required", "lottery_fraud"),
    # 5. Asterisk punctuation evasion
    ("Special l*o*t*t*e*r*y payout", "lottery_fraud"),
    # 6. Leet-speak alphanumeric substitutions
    ("Send fee to release l0tt3ry prize", "lottery_fraud"),
    # 7. Symbol substitution for jackpot
    ("Huge j@ckp0t win deposit", "lottery_fraud"),
    # 8. Bangla zero-width non-joiner evasion in hospital
    ("হ\u200cা\u200cস\u200cপ\u200cা\u200cত\u200cা\u200cল বিলের জন্য জরুরি টাকা", "family_emergency"),
    # 9. Bangla zero-width space in lottery
    ("আপনি ল\u200bটা\u200bরি জিতেছেন অগ্রিম ফি দিন", "lottery_fraud"),
    # 10. Cyrillic homoglyphs in government regulator
    ("Official b\u0430ngladesh b\u0430nk security audit fine", "fake_regulator"),
    # 11. Underscore-separated regulator evasion
    ("Fine for b_f_i_u clearance", "fake_regulator"),
    # 12. Soft-hyphen evasion in emergency
    ("Accident em\u00ader\u00adgency police bail", "family_emergency"),
    # 13. Reverse / refund trap with dashes
    ("r-e-f-u-n-d mistake sent please return", "accidental_refund_trap"),
    # 14. Mixed Bangla zero-width joiner in police station
    ("থ\u200dা\u200dন\u200dা থেকে বলছি জরুরি টাকা পাঠান", "family_emergency"),
]

@pytest.mark.parametrize("memo_text, expected_scam_type", EVASION_TEST_CASES)
def test_scamshield_evasion_strings(memo_text, expected_scam_type):
    payload = {
        "sender_id": "u_eval_sender",
        "receiver_id": "u_eval_receiver",
        "amount": 1200.0,
        "corridor": "AED_BDT",
        "memo": memo_text
    }
    res = client.post("/api/v1/scamshield/check", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["intercept"] is True, f"Failed to intercept evasion text: '{memo_text}'"
    assert data["scam_type"] == expected_scam_type, f"Mismatched type for: '{memo_text}'"
    assert data["cooling_off_seconds"] > 0
    assert len(data["warning_message_bn"]) > 0
    assert len(data["warning_message_en"]) > 0

def test_scamshield_legitimate_clean_memo():
    clean_payload = {
        "sender_id": "u_eval_sender",
        "receiver_id": "u_eval_receiver",
        "amount": 400.0,
        "corridor": "AED_BDT",
        "memo": "Monthly house rent and electricity utility bill"
    }
    res = client.post("/api/v1/scamshield/check", json=clean_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["intercept"] is False
    assert data["risk_level"] == "low"
    assert data["scam_type"] == "none"

# ==============================================================================
# 3. Rate Limiting Tests (Bilingual 429)
# ==============================================================================

def test_rate_limiting_auth_endpoint_bilingual_429():
    # Hit dev-token endpoint more than 5 times rapidly to exceed rate limit
    exceeded = False
    for i in range(12):
        res = client.post("/api/v1/auth/dev-token", json={"role": "sender", "user_id": f"u_limit_{i}"})
        if res.status_code == 429:
            exceeded = True
            body = res.json()
            assert body["error"] == "rate_limit_exceeded"
            assert "Rate limit exceeded" in body["detail"]
            assert "অনুরোধের সীমা অতিক্রম করেছে" in body["detail_bn"]
            assert "retry_after_seconds" in body
            assert res.headers.get("Retry-After") is not None
            break
    assert exceeded, "Rate limit of 5/min was not triggered after 12 requests"
    from app.limiter import limiter
    limiter.reset()

# ==============================================================================
# 4. Expanded Risk Scoring & Rules Edge Cases
# ==============================================================================

def test_scoring_edge_case_velocity_burst():
    # High velocity (>= 3 in 1 hour)
    bonus, reasons = evaluate_rule_penalties(
        amount_src=1000.0,
        recent_velocity=4,
        is_new_receiver=False,
        is_new_device=False,
        hour_of_day=14,
        sender_avg_amount=1000.0
    )
    assert bonus >= 22.0
    assert "VELOCITY_3X" in reasons

def test_scoring_edge_case_odd_hours_night():
    # Night hours 02:00 BST
    bonus, reasons = evaluate_rule_penalties(
        amount_src=1000.0,
        recent_velocity=1,
        is_new_receiver=False,
        is_new_device=False,
        hour_of_day=2,
        sender_avg_amount=1000.0
    )
    assert bonus >= 12.0
    assert "ODD_HOURS_NIGHT" in reasons

def test_scoring_edge_case_extreme_amount_deviation():
    # Amount 5x sender historical average
    bonus, reasons = evaluate_rule_penalties(
        amount_src=10000.0,
        recent_velocity=1,
        is_new_receiver=False,
        is_new_device=False,
        hour_of_day=14,
        sender_avg_amount=2000.0
    )
    assert bonus >= 25.0
    assert "AMOUNT_4X_DEVIATION" in reasons

def test_scoring_threshold_decisions():
    # Below review threshold (< 40)
    status_clean, action_clean = determine_status_and_action(22.0)
    assert status_clean == "completed"
    assert action_clean == "none"

    # Review threshold (40 to 69)
    status_review, action_review = determine_status_and_action(55.0)
    assert status_review == "in_review"
    assert action_review == "hold"

    # High threshold (>= 70)
    status_high, action_high = determine_status_and_action(84.0)
    assert status_high == "in_review"
    assert action_high == "escalate"
