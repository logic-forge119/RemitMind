import pytest
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from app.main import app
from app.services.cloak import cloak_node_id, tokenize_phone

client = TestClient(app)

def test_pii_cloaking_service():
    token = cloak_node_id("u_sender_12345")
    assert token.startswith("WALLET-")
    assert len(token) == 11
    
    # Determinism check
    assert cloak_node_id("u_sender_12345") == token

    masked_phone = tokenize_phone("+8801712345678")
    assert "+88017***5678" in masked_phone
    assert "TOK-" in masked_phone

def test_graph_network_endpoint_cloaked():
    res = client.get("/api/v1/graph/network")
    assert res.status_code == 200
    data = res.json()
    assert "nodes" in data
    assert "links" in data
    assert "total_nodes" in data
    assert data["total_nodes"] > 0
    # Verify cloaked IDs by default
    first_node = data["nodes"][0]
    assert "display_id" in first_node
    assert first_node["display_id"].startswith("WALLET-")
    assert "real_id" not in first_node

def test_graph_network_decloak_analyst():
    # Attempt decloak without key
    res_unauth = client.get("/api/v1/graph/network?decloak=true")
    assert res_unauth.status_code == 200
    first_node_unauth = res_unauth.json()["nodes"][0]
    assert first_node_unauth["display_id"].startswith("WALLET-")

    # Decloak with valid analyst key
    res_auth = client.get("/api/v1/graph/network?decloak=true", headers={"X-API-Key": "upay-risk-secret"})
    assert res_auth.status_code == 200
    first_node_auth = res_auth.json()["nodes"][0]
    assert "real_id" in first_node_auth
    assert first_node_auth["display_id"] == first_node_auth["real_id"]

def test_graph_communities_louvain():
    res = client.get("/api/v1/graph/communities")
    assert res.status_code == 200
    data = res.json()
    assert "clusters" in data
    assert data["total_clusters"] > 0
    first_cluster = data["clusters"][0]
    assert "cluster_id" in first_cluster
    assert "member_count" in first_cluster
    assert "total_volume_bdt" in first_cluster

def test_graph_pagerank():
    res = client.get("/api/v1/graph/pagerank?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert "top_central_nodes" in data
    assert len(data["top_central_nodes"]) > 0
    assert "pagerank" in data["top_central_nodes"][0]

def test_quarantine_cluster():
    # Fetch clusters first
    comm_res = client.get("/api/v1/graph/communities")
    assert comm_res.status_code == 200
    clusters = comm_res.json()["clusters"]
    assert len(clusters) > 0
    target_cluster_id = clusters[0]["cluster_id"]

    # Quarantine cluster
    payload = {
        "cluster_id": target_cluster_id,
        "reason": "Suspected synthetic mule ring automated freeze"
    }
    q_res = client.post("/api/v1/graph/quarantine", json=payload)
    assert q_res.status_code == 200
    data = q_res.json()
    assert data["status"] == "quarantined"
    assert data["frozen_users_count"] > 0

def test_node_forensic_profile():
    # Fetch a node ID
    net_res = client.get("/api/v1/graph/network")
    nodes = net_res.json()["nodes"]
    assert len(nodes) > 0
    sample_id = nodes[0]["display_id"]

    res = client.get(f"/api/v1/graph/node/{sample_id}")
    assert res.status_code == 200
    data = res.json()
    assert "node_id" in data
    assert "total_sent_bdt" in data
    assert "unique_counterparties_count" in data
