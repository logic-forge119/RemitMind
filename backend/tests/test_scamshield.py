import pytest
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_scamshield_normal_transfer():
    payload = {
        "sender_id": "u_test_sender_01",
        "receiver_id": "u_test_receiver_01",
        "amount": 500.0,
        "corridor": "AED_BDT",
        "memo": "Monthly family allowance for groceries"
    }
    res = client.post("/api/v1/scamshield/check", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["intercept"] is False
    assert data["risk_level"] == "low"
    assert data["cooling_off_seconds"] == 0
    assert len(data["warning_message_en"]) > 0
    assert len(data["warning_message_bn"]) > 0

def test_scamshield_lottery_fraud():
    payload = {
        "sender_id": "u_test_sender_02",
        "receiver_id": "u_unknown_mule",
        "amount": 2500.0,
        "corridor": "AED_BDT",
        "memo": "Payment for lottery prize release and winning processing fee"
    }
    res = client.post("/api/v1/scamshield/check", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["intercept"] is True
    assert data["risk_level"] == "critical"
    assert data["scam_type"] == "lottery_fraud"
    assert data["cooling_off_seconds"] == 30
    assert "SUSPECTED_ADVANCE_FEE_LOTTERY_SCAM" in data["reasons"]
    assert "লটারি" in data["warning_message_bn"] or "পুরস্কার" in data["warning_message_bn"]

def test_scamshield_emergency_impersonation():
    payload = {
        "sender_id": "u_test_sender_03",
        "receiver_id": "u_unknown_mule",
        "amount": 1500.0,
        "corridor": "AED_BDT",
        "memo": "Hospital surgery urgent emergency ICU fee"
    }
    res = client.post("/api/v1/scamshield/check", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["intercept"] is True
    assert data["scam_type"] == "family_emergency"
    assert data["cooling_off_seconds"] == 30
    assert "SUSPECTED_EMERGENCY_IMPERSONATION" in data["reasons"]

def test_scamshield_regulator_impersonation_bilingual():
    payload = {
        "sender_id": "u_test_sender_04",
        "receiver_id": "u_unknown_regulator_scam",
        "amount": 5000.0,
        "corridor": "AED_BDT",
        "memo": "BFIU Bangladesh Bank fine to unfreeze wallet"
    }
    res = client.post("/api/v1/scamshield/check", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["intercept"] is True
    assert data["risk_level"] == "critical"
    assert data["scam_type"] == "fake_regulator"
    assert "বিএফআইইউ" in data["warning_message_bn"] or "বাংলাদেশ ব্যাংক" in data["warning_message_bn"]
    assert "Bangladesh Bank" in data["warning_message_en"]
