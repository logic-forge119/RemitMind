import pytest
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_divisions():
    res = client.get("/api/v1/resilience/divisions")
    assert res.status_code == 200
    data = res.json()
    assert "divisions" in data
    assert data["total_divisions"] == 8
    first = data["divisions"][0]
    assert "risk_index" in first
    assert "coordinates" in first
    assert "total_division_cash_bdt" in first

def test_stress_test_flash_flood():
    payload = {
        "scenario": "flash_flood",
        "severity": 0.85,
        "affected_divisions": ["Sylhet", "Chittagong"],
        "duration_hours": 48
    }
    res = client.post("/api/v1/resilience/stress-test", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["scenario"] == "flash_flood"
    assert "division_health" in data
    assert len(data["division_health"]) == 8
    assert "emergency_injection_schedule" in data
    assert "resilience_index" in data

    # Verify Sylhet is stressed
    sylhet_health = next(d for d in data["division_health"] if d["name"] == "Sylhet")
    assert sylhet_health["drain_rate_pct_per_hour"] > 0

def test_stress_test_grid_blackout():
    payload = {
        "scenario": "grid_blackout",
        "severity": 0.6,
        "affected_divisions": ["Dhaka", "Barisal"],
        "duration_hours": 24
    }
    res = client.post("/api/v1/resilience/stress-test", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["scenario"] == "grid_blackout"
    assert data["resilience_index"] > 0

def test_rebalance_schedule():
    res = client.get("/api/v1/resilience/rebalance")
    assert res.status_code == 200
    data = res.json()
    assert "transfers" in data
    assert len(data["transfers"]) > 0
    assert data["total_rebalanced_bdt"] > 0
    assert "network_stability_score" in data
