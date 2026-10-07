"""
SyndicateRadar & AegisGraph API Router
Exposes transaction network topology, Louvain syndicate community detection,
PageRank centrality profiling, and 1-click cluster quarantine.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User, Transfer
from app.services.graph import analyze_graph, build_transaction_graph, detect_communities, compute_pagerank, classify_node_role
from app.services.cloak import cloak_node_id, decloak_user_id

from app.auth import get_optional_user, require_role

router = APIRouter(prefix="/api/v1/graph", tags=["SyndicateRadar & Graph Intelligence"])

class QuarantineRequest(BaseModel):
    cluster_id: Optional[int] = None
    node_id: Optional[str] = None
    reason: Optional[str] = "Mule syndicate detected via Louvain graph analysis"

class QuarantineResponse(BaseModel):
    status: str
    target: str
    frozen_users_count: int
    frozen_transfers_count: int
    reason: str

@router.get("/network")
def get_graph_network(
    decloak: bool = Query(False, description="Display real user IDs instead of cloaked tokens"),
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None),
    limit: int = Query(500, description="Max transfers to analyze"),
    db: Session = Depends(get_db)
):
    """
    Returns full node-link graph data formatted for force-directed Canvas/SVG visualization.
    PII cloaking is enabled by default unless analyst credentials are validated.
    """
    user = get_optional_user(authorization=authorization, x_api_key=x_api_key)
    is_analyst = user is not None and user.get("role") in ("analyst", "admin")
    allow_decloak = decloak and is_analyst

    analysis = analyze_graph(db, max_transfers=limit)
    
    # Filter or cloak IDs
    nodes = []
    for n in analysis["nodes"]:
        node_copy = dict(n)
        if not allow_decloak:
            node_copy["display_id"] = n["id"]  # Cloaked WALLET-XXXX
            node_copy.pop("real_id", None)
        else:
            node_copy["display_id"] = n["real_id"]
        nodes.append(node_copy)

    links = []
    for link in analysis["links"]:
        l_copy = dict(link)
        if not allow_decloak:
            l_copy["source"] = link["source"]
            l_copy["target"] = link["target"]
            l_copy.pop("source_real_id", None)
            l_copy.pop("target_real_id", None)
        else:
            l_copy["source"] = link["source_real_id"]
            l_copy["target"] = link["target_real_id"]
        links.append(l_copy)

    return {
        "nodes": nodes,
        "links": links,
        "total_nodes": len(nodes),
        "total_links": len(links),
        "syndicates_detected": len([c for c in analysis["cluster_summaries"] if c["is_syndicate"]]),
        "clusters": analysis["cluster_summaries"]
    }

@router.get("/communities")
def get_graph_communities(db: Session = Depends(get_db)):
    """
    Returns Louvain modularity clusters and syndicate metrics.
    """
    analysis = analyze_graph(db)
    return {
        "clusters": analysis["cluster_summaries"],
        "total_clusters": len(analysis["cluster_summaries"])
    }

@router.get("/pagerank")
def get_graph_pagerank(
    limit: int = Query(25, description="Top N nodes by PageRank"),
    db: Session = Depends(get_db)
):
    """
    Returns highest centrality nodes and aggregator hubs.
    """
    analysis = analyze_graph(db)
    sorted_nodes = sorted(analysis["nodes"], key=lambda x: x["pagerank"], reverse=True)
    return {
        "top_central_nodes": sorted_nodes[:limit],
        "total_profiled": len(sorted_nodes)
    }

@router.post("/quarantine", response_model=QuarantineResponse, dependencies=[Depends(require_role("analyst", "admin"))])
def quarantine_cluster_or_node(req: QuarantineRequest, db: Session = Depends(get_db)):
    """
    1-Click Quarantine: Freezes all accounts and puts pending transfers on hold
    for all nodes in a detected syndicate cluster or specific user node.
    """
    frozen_users = 0
    frozen_transfers = 0

    if req.cluster_id is not None:
        analysis = analyze_graph(db)
        # Find all nodes in that cluster
        target_real_ids = [n["real_id"] for n in analysis["nodes"] if n["cluster_id"] == req.cluster_id]
        if not target_real_ids:
            raise HTTPException(status_code=404, detail=f"No active nodes found in cluster {req.cluster_id}")

        # Update or record quarantined users
        for uid in target_real_ids:
            u = db.query(User).filter(User.id == uid).first()
            if not u:
                u = User(id=uid, name=f"User {uid}", role="sender", is_quarantined=1, quarantine_reason=req.reason)
                db.add(u)
            else:
                u.is_quarantined = 1
                u.quarantine_reason = req.reason
            frozen_users += 1

        # Freeze transfers involving these users
        transfers = db.query(Transfer).filter(
            (Transfer.sender_id.in_(target_real_ids)) | (Transfer.receiver_id.in_(target_real_ids)),
            Transfer.status.in_(["created", "in_review", "pending"])
        ).all()
        for t in transfers:
            t.status = "held"
            frozen_transfers += 1

        db.commit()
        return QuarantineResponse(
            status="quarantined",
            target=f"Cluster {req.cluster_id}",
            frozen_users_count=frozen_users,
            frozen_transfers_count=frozen_transfers,
            reason=req.reason
        )

    elif req.node_id:
        # Single node quarantine
        node_id = req.node_id
        user = db.query(User).filter((User.id == node_id) | (User.id == node_id.replace("WALLET-", ""))).first()
        if not user:
            # Check if cloaked lookup matches
            all_users = db.query(User).all()
            for u in all_users:
                if cloak_node_id(u.id) == node_id:
                    user = u
                    break

        if not user:
            raise HTTPException(status_code=404, detail=f"User node {req.node_id} not found")

        user.is_quarantined = 1
        user.quarantine_reason = req.reason
        frozen_users = 1

        transfers = db.query(Transfer).filter(
            (Transfer.sender_id == user.id) | (Transfer.receiver_id == user.id),
            Transfer.status.in_(["created", "in_review", "pending"])
        ).all()
        for t in transfers:
            t.status = "held"
            frozen_transfers += 1

        db.commit()
        return QuarantineResponse(
            status="quarantined",
            target=f"User {user.id}",
            frozen_users_count=frozen_users,
            frozen_transfers_count=frozen_transfers,
            reason=req.reason
        )
    else:
        raise HTTPException(status_code=400, detail="Must provide either cluster_id or node_id to quarantine")

@router.get("/node/{node_id}")
def get_node_forensic_profile(node_id: str, db: Session = Depends(get_db)):
    """
    Returns forensic neighborhood and connection details for a specific node.
    """
    user = db.query(User).filter(User.id == node_id).first()
    if not user:
        # Check cloaked alias
        for u in db.query(User).all():
            if cloak_node_id(u.id) == node_id:
                user = u
                break

    if not user:
        raise HTTPException(status_code=404, detail=f"Node {node_id} not found")

    real_id = user.id
    sent = db.query(Transfer).filter(Transfer.sender_id == real_id).all()
    received = db.query(Transfer).filter(Transfer.receiver_id == real_id).all()

    counterparties = set()
    for t in sent:
        counterparties.add(t.receiver_id)
    for t in received:
        counterparties.add(t.sender_id)

    return {
        "node_id": cloak_node_id(real_id),
        "real_id": real_id,
        "role": user.role,
        "country": user.country,
        "is_quarantined": bool(getattr(user, "is_quarantined", 0)),
        "quarantine_reason": getattr(user, "quarantine_reason", ""),
        "total_sent_bdt": round(sum(t.amount_bdt for t in sent), 2),
        "total_received_bdt": round(sum(t.amount_bdt for t in received), 2),
        "sent_transfers_count": len(sent),
        "received_transfers_count": len(received),
        "unique_counterparties_count": len(counterparties)
    }
