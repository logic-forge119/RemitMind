"""
SyndicateRadar & AegisGraph Intelligence Engine
Builds transaction graphs, executes Louvain modularity clustering for syndicate detection,
computes PageRank centrality, and classifies financial crime network roles.
"""

from typing import Dict, Any, List, Tuple
import networkx as nx
from sqlalchemy.orm import Session

from app.models import Transfer, User
from app.services.cloak import cloak_node_id

def build_transaction_graph(db: Session, max_transfers: int = 2000) -> nx.DiGraph:
    """
    Constructs a directed NetworkX graph from database transfers.
    Nodes = Senders and Receivers (with financial velocity attributes)
    Edges = Money flows with amounts and corridor metadata
    """
    G = nx.DiGraph()

    # Query transfers and users
    transfers = db.query(Transfer).order_by(Transfer.created_at.desc()).limit(max_transfers).all()
    user_ids = set()
    for t in transfers:
        if t.sender_id:
            user_ids.add(t.sender_id)
        if t.receiver_id:
            user_ids.add(t.receiver_id)

    users = db.query(User).filter(User.id.in_(user_ids)).all() if user_ids else []
    user_map = {u.id: u for u in users}

    # Add nodes with initial attributes
    for uid in user_ids:
        u = user_map.get(uid)
        role = u.role if u else "user"
        is_q = getattr(u, "is_quarantined", 0) if u else 0
        q_reason = getattr(u, "quarantine_reason", "") if u else ""
        G.add_node(
            uid,
            real_id=uid,
            cloaked_id=cloak_node_id(uid),
            role=role,
            is_quarantined=bool(is_q),
            quarantine_reason=q_reason or "",
            total_sent=0.0,
            total_received=0.0,
            tx_count=0
        )

    # Add edges
    for t in transfers:
        s_id = t.sender_id
        r_id = t.receiver_id
        if not s_id or not r_id:
            continue

        if not G.has_node(s_id):
            G.add_node(s_id, real_id=s_id, cloaked_id=cloak_node_id(s_id), role="sender", is_quarantined=False, quarantine_reason="", total_sent=0.0, total_received=0.0, tx_count=0)
        if not G.has_node(r_id):
            G.add_node(r_id, real_id=r_id, cloaked_id=cloak_node_id(r_id), role="receiver", is_quarantined=False, quarantine_reason="", total_sent=0.0, total_received=0.0, tx_count=0)

        G.nodes[s_id]["total_sent"] += t.amount_bdt
        G.nodes[s_id]["tx_count"] += 1
        G.nodes[r_id]["total_received"] += t.amount_bdt
        G.nodes[r_id]["tx_count"] += 1

        G.add_edge(
            s_id,
            r_id,
            transfer_id=t.id,
            amount_bdt=t.amount_bdt,
            corridor=t.corridor,
            status=t.status,
            created_at=str(t.created_at) if t.created_at else ""
        )

    return G

def detect_communities(G: nx.DiGraph) -> Dict[str, int]:
    """
    Applies Louvain community partition algorithm to detect money mule rings and syndicates.
    Falls back gracefully to greedy modularity communities if needed.
    """
    if len(G) == 0:
        return {}

    G_undirected = G.to_undirected()

    try:
        import community as community_louvain
        partition = community_louvain.best_partition(G_undirected)
        return partition
    except Exception:
        # Fallback to networkx community detection
        try:
            import networkx.algorithms.community as nx_comm
            comms = list(nx_comm.greedy_modularity_communities(G_undirected))
            partition = {}
            for cid, cset in enumerate(comms):
                for node in cset:
                    partition[node] = cid
            return partition
        except Exception:
            # Trivial connected components fallback
            components = list(nx.connected_components(G_undirected))
            partition = {}
            for cid, comp in enumerate(components):
                for node in comp:
                    partition[node] = cid
            return partition

def compute_pagerank(G: nx.DiGraph) -> Dict[str, float]:
    """
    Computes PageRank centrality to identify high-velocity hubs and aggregator accounts.
    """
    if len(G) == 0:
        return {}
    try:
        return nx.pagerank(G, alpha=0.85, max_iter=200)
    except Exception:
        # Degree centrality fallback
        return nx.degree_centrality(G)

def classify_node_role(node_id: str, G: nx.DiGraph, pagerank_val: float) -> str:
    """
    Classifies node role in financial crime topologies:
    - 'mastermind': High fan-out funding multiple accounts
    - 'mule_cashout': High in-degree, low or zero forward outbound transfers
    - 'layering': Rapid pass-through with balanced in/out degree
    - 'normal': Low volume, standard bilateral remittance
    """
    in_deg = G.in_degree(node_id)
    out_deg = G.out_degree(node_id)
    
    if in_deg >= 3 and out_deg <= 1:
        return "mule_cashout"
    if in_deg >= 2 and out_deg >= 2:
        return "layering"
    if out_deg >= 3 and in_deg <= 1:
        return "mastermind"
    if pagerank_val > 0.05 and (in_deg + out_deg >= 4):
        return "syndicate_hub"
    return "normal"

def analyze_graph(db: Session, max_transfers: int = 2000) -> Dict[str, Any]:
    """
    Executes full graph analysis pipeline and returns unified topology data.
    """
    G = build_transaction_graph(db, max_transfers=max_transfers)
    if len(G) == 0:
        return {
            "nodes": [],
            "links": [],
            "communities": {},
            "pagerank": {},
            "cluster_summaries": []
        }

    communities = detect_communities(G)
    pagerank = compute_pagerank(G)

    # Classify roles & prepare node list
    nodes = []
    cluster_stats: Dict[int, Dict[str, Any]] = {}

    for node_id, data in G.nodes(data=True):
        pr = pagerank.get(node_id, 0.0)
        c_id = communities.get(node_id, 0)
        role = classify_node_role(node_id, G, pr)

        node_entry = {
            "id": data.get("cloaked_id", node_id),
            "real_id": node_id,
            "role": role,
            "cluster_id": c_id,
            "pagerank": round(pr, 4),
            "in_degree": G.in_degree(node_id),
            "out_degree": G.out_degree(node_id),
            "total_sent": round(data.get("total_sent", 0.0), 2),
            "total_received": round(data.get("total_received", 0.0), 2),
            "is_quarantined": data.get("is_quarantined", False),
            "quarantine_reason": data.get("quarantine_reason", "")
        }
        nodes.append(node_entry)

        # Aggregate cluster metrics
        if c_id not in cluster_stats:
            cluster_stats[c_id] = {
                "cluster_id": c_id,
                "node_count": 0,
                "total_volume_bdt": 0.0,
                "mule_count": 0,
                "layering_count": 0,
                "nodes": [],
                "quarantined_count": 0
            }
        cs = cluster_stats[c_id]
        cs["node_count"] += 1
        cs["total_volume_bdt"] += data.get("total_sent", 0.0) + data.get("total_received", 0.0)
        if role == "mule_cashout":
            cs["mule_count"] += 1
        elif role == "layering":
            cs["layering_count"] += 1
        if data.get("is_quarantined"):
            cs["quarantined_count"] += 1
        cs["nodes"].append(node_id)

    # Prepare links
    links = []
    for u, v, edata in G.edges(data=True):
        links.append({
            "source": G.nodes[u].get("cloaked_id", u),
            "target": G.nodes[v].get("cloaked_id", v),
            "source_real_id": u,
            "target_real_id": v,
            "amount_bdt": round(edata.get("amount_bdt", 0.0), 2),
            "transfer_id": edata.get("transfer_id", ""),
            "status": edata.get("status", "completed"),
            "corridor": edata.get("corridor", "AED_BDT")
        })

    # Cluster summaries with threat score
    cluster_summaries = []
    for cid, stats in cluster_stats.items():
        is_syndicate = (stats["mule_count"] >= 1 or stats["layering_count"] >= 1 or stats["node_count"] >= 4)
        threat_level = "critical" if stats["mule_count"] >= 2 else ("high" if is_syndicate else "low")
        cluster_summaries.append({
            "cluster_id": cid,
            "member_count": stats["node_count"],
            "total_volume_bdt": round(stats["total_volume_bdt"], 2),
            "mules_detected": stats["mule_count"],
            "layering_nodes": stats["layering_count"],
            "threat_level": threat_level,
            "is_syndicate": is_syndicate,
            "quarantined_members": stats["quarantined_count"]
        })

    cluster_summaries.sort(key=lambda x: (x["mules_detected"], x["total_volume_bdt"]), reverse=True)

    return {
        "nodes": nodes,
        "links": links,
        "communities": communities,
        "pagerank": {k: round(v, 4) for k, v in pagerank.items()},
        "cluster_summaries": cluster_summaries
    }
