"""
AegisRisk In-App Documentation Hub Router
Serves project specifications, architecture blueprints, data models, and ML specs as markdown resources.
"""

from pathlib import Path
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/v1/docs", tags=["Documentation Hub"])

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent

DOCS_MAP = {
    "prd": {"filename": "01_PRD.md", "title": "Product Requirements Document (PRD)"},
    "trd": {"filename": "02_TRD.md", "title": "Technical Requirements Document (TRD)"},
    "flow": {"filename": "03_APP_FLOW.md", "title": "System Architecture & App Flow"},
    "schema": {"filename": "04_DATABASE_SCHEMA.md", "title": "Relational Database Schema"},
    "api": {"filename": "05_API_DOCS.md", "title": "REST API Reference"},
    "ml": {"filename": "06_ML_SPEC.md", "title": "Machine Learning & Anomaly Detection Spec"},
    "synthetic": {"filename": "07_SYNTHETIC_DATA_SPEC.md", "title": "Synthetic Data Generation Spec"},
    "responsible_ai": {"filename": "08_RESPONSIBLE_AI.md", "title": "Responsible AI & Fairness Governance"},
    "checklist": {"filename": "09_SUBMISSION_CHECKLIST.md", "title": "Submission & Compliance Checklist"},
    "showcase": {"filename": "SUBMISSION_SHOWCASE.md", "title": "Platform Showcase & Executive Brief"}
}

@router.get("")
def list_available_docs():
    """
    Returns list of all available specification documents for in-app viewing.
    """
    items = []
    for slug, meta in DOCS_MAP.items():
        file_path = ROOT_DIR / meta["filename"]
        items.append({
            "slug": slug,
            "title": meta["title"],
            "filename": meta["filename"],
            "available": file_path.exists(),
            "size_bytes": file_path.stat().st_size if file_path.exists() else 0
        })
    return {"documents": items}

@router.get("/{slug}")
def get_doc_by_slug(slug: str):
    """
    Retrieves the raw markdown contents of a requested specification document.
    """
    meta = DOCS_MAP.get(slug.lower())
    if not meta:
        raise HTTPException(
            status_code=404,
            detail=f"Document '{slug}' not found. Available slugs: {list(DOCS_MAP.keys())}"
        )

    file_path = ROOT_DIR / meta["filename"]
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File {meta['filename']} not found on disk")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    return {
        "slug": slug,
        "title": meta["title"],
        "filename": meta["filename"],
        "content": content
    }
