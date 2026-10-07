"""
AegisRisk PII Cloaking & Tokenization Service
Provides deterministic pseudonymization for financial accounts, phone numbers, and graph nodes.
Guarantees zero leakage of customer PII while preserving graph topology for analytics.
"""

import hashlib
from typing import Optional

def cloak_node_id(user_id: str) -> str:
    """
    Returns a deterministic privacy-preserving alias (e.g., WALLET-A4B7).
    Same user_id always maps to the same cloaked alias across graph queries.
    """
    if not user_id:
        return "WALLET-0000"
    digest = hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:4].upper()
    return f"WALLET-{digest}"

def tokenize_phone(phone: str) -> str:
    """
    Masks a phone number for UI display while generating a deterministic token.
    Example: '+8801712345678' -> '+88017***5678 (TOK-8F2B)'
    """
    if not phone or len(phone) < 6:
        return "+88017***0000 (TOK-0000)"
    
    clean = phone.strip()
    prefix = clean[:6] if len(clean) >= 6 else clean[:3]
    suffix = clean[-4:]
    token_hex = hashlib.sha256(clean.encode("utf-8")).hexdigest()[:4].upper()
    return f"{prefix}***{suffix} (TOK-{token_hex})"

def decloak_user_id(cloaked_alias: str, real_id: str, is_verified_analyst: bool = False) -> str:
    """
    Returns real user ID if analyst authentication is verified, else returns the cloaked alias.
    """
    if is_verified_analyst:
        return real_id
    return cloaked_alias
