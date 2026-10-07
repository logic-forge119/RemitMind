"""
BM25 SOP Regulatory Retrieval & Evidence ID Service
Indexes BFIU/AML regulatory circulars in docs/sop/ using BM25Okapi.
Generates, formats, and validates forensic Evidence IDs (TXN-, RULE-, FACTOR-)
for regulatory filing and STR groundings.
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
from sqlalchemy.orm import Session

from app.models import Transfer

SOP_DIR = Path(__file__).resolve().parent.parent.parent.parent / "docs" / "sop"

class BM25SOPRetriever:
    def __init__(self, sop_dir: Path = SOP_DIR):
        self.sop_dir = sop_dir
        self.documents: List[Dict[str, str]] = []
        self.tokenized_corpus: List[List[str]] = []
        self.bm25: Optional[BM25Okapi] = None
        self._index_sop_documents()

    def _tokenize(self, text: str) -> List[str]:
        """Simple alphanumeric tokenizer."""
        return re.findall(r"\b[a-zA-Z0-9_\-\.]+\b", text.lower())

    def _index_sop_documents(self):
        """Reads markdown files in docs/sop/ and creates BM25 index on clauses."""
        self.documents = []
        self.tokenized_corpus = []

        if not self.sop_dir.exists():
            return

        for filepath in self.sop_dir.glob("*.md"):
            try:
                content = filepath.read_text(encoding="utf-8")
                # Split clauses by ### header
                sections = re.split(r"(?=###\s+BFIU-SOP-)", content)
                for sec in sections:
                    sec_clean = sec.strip()
                    if not sec_clean or not sec_clean.startswith("###"):
                        continue
                    
                    lines = sec_clean.split("\n")
                    header_line = lines[0].replace("###", "").strip()
                    
                    # Extract SOP ID e.g. BFIU-SOP-SEC-25.1
                    id_match = re.search(r"BFIU-SOP-[A-Z0-9\.\-]+", header_line)
                    sop_id = id_match.group(0) if id_match else f"SOP-{len(self.documents)+1}"

                    doc_entry = {
                        "id": sop_id,
                        "header": header_line,
                        "content": sec_clean,
                        "source_file": filepath.name
                    }
                    self.documents.append(doc_entry)
                    self.tokenized_corpus.append(self._tokenize(sec_clean))
            except Exception as e:
                pass

        if self.tokenized_corpus:
            self.bm25 = BM25Okapi(self.tokenized_corpus)

    def retrieve(self, query: str, top_k: int = 2) -> List[Dict[str, str]]:
        """Retrieves top-k most relevant BFIU SOP clauses using BM25."""
        if not self.bm25 or not self.documents:
            self._index_sop_documents()
            if not self.bm25:
                return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return self.documents[:top_k]

        scores = self.bm25.get_scores(query_tokens)
        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

        results = []
        for idx in ranked_indices[:top_k]:
            results.append({
                "id": self.documents[idx]["id"],
                "header": self.documents[idx]["header"],
                "content": self.documents[idx]["content"],
                "score": round(float(scores[idx]), 3)
            })
        return results

sop_retriever = BM25SOPRetriever()

# -----------------------------------------------------------------------------
# Evidence ID Helpers
# -----------------------------------------------------------------------------

def format_evidence_id(category: str, identifier: str) -> str:
    """Formats standardized Evidence IDs: TXN-, RULE-, FACTOR-."""
    cat = category.upper().strip()
    clean_id = str(identifier).strip()
    if cat == "TXN":
        # Ensure clean TXN- prefix
        if clean_id.startswith("TXN-"):
            return clean_id
        return f"TXN-{clean_id}"
    elif cat == "RULE":
        rule_name = clean_id.upper().replace(" ", "_")
        return f"RULE-{rule_name}"
    elif cat == "FACTOR":
        factor_name = clean_id.replace(" ", "_")
        return f"FACTOR-{factor_name}"
    return f"{cat}-{clean_id}"

def build_evidence_ids(
    transfer_id: str,
    reason_codes: Optional[List[str]] = None,
    factors: Optional[List[Dict[str, Any]]] = None
) -> List[str]:
    """Builds authoritative list of evidence IDs for an alert or transfer."""
    evidence_ids = []
    
    # 1. Transaction Evidence ID
    if transfer_id:
        evidence_ids.append(format_evidence_id("TXN", transfer_id))

    # 2. Rule Indicator Evidence IDs
    if reason_codes:
        for r in reason_codes:
            if r:
                evidence_ids.append(format_evidence_id("RULE", r))

    # 3. Model Attribution Factor Evidence IDs
    if factors:
        for f in factors:
            name = f.get("name") if isinstance(f, dict) else str(f)
            if name:
                evidence_ids.append(format_evidence_id("FACTOR", name))

    return evidence_ids

def validate_evidence_ids_in_db(evidence_ids: List[str], db: Session) -> Dict[str, Any]:
    """
    Validates that every TXN- evidence ID references an existing transfer in the database.
    Returns status and list of verified vs missing transaction IDs.
    """
    txn_ids = []
    for eid in evidence_ids:
        if eid.startswith("TXN-"):
            raw_id = eid[4:]
            txn_ids.append(raw_id)

    if not txn_ids:
        return {"valid": True, "verified_txns": [], "missing_txns": []}

    found_txns = db.query(Transfer.id).filter(Transfer.id.in_(txn_ids)).all()
    found_set = {r[0] for r in found_txns}
    missing = [t for t in txn_ids if t not in found_set]

    return {
        "valid": len(missing) == 0,
        "verified_txns": list(found_set),
        "missing_txns": missing
    }
