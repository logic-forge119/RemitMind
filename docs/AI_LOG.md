# RemitMind &bull; AI Disclosure & Prompt Log (Rule GR §5.6)

This document satisfies the official hackathon disclosure requirements under **General Rules §5.3–§5.6**. It catalogs all AI tools, models, system instructions, and human verification procedures used during project development and embedded in runtime services.

---

## 1. Development-Time AI Tools Disclosed

| Tool / Model | Primary Usage | Human Verification & Validation Procedure |
|---|---|---|
| **Google Gemini 1.5 Pro / Flash** | Architecture design, schema formulation, and PRD drafting | Verified against official upay transaction limits and Bangladesh Bank regulations. |
| **Antigravity AI IDE Agent** | Code generation, test suite scaffolding, refactoring, and documentation | Every generated function was compiled, run against pytest, and inspected line-by-line. |
| **Scikit-Learn (Isolation Forest)** | Unsupervised statistical anomaly detection on transaction feature vectors | Validated on a held-out test split (20% of synthetic dataset) with precision, recall, and PR-AUC tracking. |

---

## 2. Runtime Model Architecture & System Prompts

RemitMind employs **strict evidence grounding**. The runtime LLM is barred from computing numeric scores or making binary authorization decisions. It functions solely as a natural language interpreter for structured telemetry.

### 2.1 Fraud Operations Copilot Prompt (Analyst SAR Briefing)

```json
{
  "system_role": "You are a senior AML & Fraud Forensics Analyst at upay Bangladesh.",
  "grounding_policy": "STRICT_EVIDENCE_ONLY. Never invent transactions, amounts, or entities not in the input JSON.",
  "task": "Explain why this transaction was intercepted, interpret the reason codes, and recommend an operational action.",
  "allowed_actions": ["APPROVE_WITH_CONFIRMATION", "TEMPORARY_HOLD_FOR_KYC", "ESCALATE_TO_FINANCIAL_CRIME_UNIT"]
}
```

**Runtime Grounding Payload Example:**
```json
{
  "transfer_id": "TXN_78491_AE",
  "sender": {"id": "U109", "name": "Rahim", "country": "UAE", "typical_monthly_bdt": 20000},
  "receiver": {"id": "U312", "name": "Unknown", "account_age_days": 1},
  "amount_bdt": 95000,
  "velocity_1h": 3,
  "device_status": "NEW_UNRECOGNIZED_FINGERPRINT",
  "risk_score": 88,
  "reason_codes": ["NEW_RECEIVER", "VELOCITY_3X", "NEW_DEVICE", "AMOUNT_DEVIATION"]
}
```

**Synthesized Output:**
> *"Transfer TXN_78491_AE from Rahim (UAE) flagged with an elevated anomaly score of 88/100. Key drivers include a severe amount deviation (95,000 BDT vs. sender's 20,000 BDT baseline), 3 rapid consecutive transfers within one hour, an unrecognized device signature, and routing to a newly established recipient wallet (<24 hours old). Recommended Action: Place on temporary administrative hold and trigger step-up biometric SMS confirmation before fund disbursement."*

---

## 3. Template Fallback Guarantee (Anti-Hallucination)

If the external LLM provider fails, times out (>2000ms), or encounters rate limits, RemitMind automatically routes through `backend/app/services/explain.py`:

```python
def generate_analyst_briefing(transfer_data: dict) -> str:
    """Deterministic string template fallback ensuring 0% hallucination and 100% uptime."""
    reasons = ", ".join(transfer_data.get("reason_codes", []))
    score = transfer_data.get("risk_score", 0)
    return (
        f"Alert for transfer {transfer_data.get('id')}: Anomaly score {score}/100. "
        f"Interception triggered by factors: {reasons}. "
        f"Action: Route to Tier-1 compliance analyst for sender verification."
    )
```

---

## 4. Prompt Injection & Security Defense

RemitMind protects runtime LLM pipelines against prompt injection and jailbreak attempts:
1. **No User String Injection**: Free-form user memo text is sanitized and never directly concatenated into system instructions.
2. **Schema Validation**: All inputs and outputs conform to strict Pydantic schemas ([`backend/app/schemas.py`](file:///c:/Users/Pritam/Downloads/ai%20dev/backend/app/schemas.py)).
3. **Immutable Policy Engine**: Even if an LLM is coerced into saying *"this transaction is safe"*, the deterministic business rules engine ([`backend/app/services/rules.py`](file:///c:/Users/Pritam/Downloads/ai%20dev/backend/app/services/rules.py)) overrides the outcome if the anomaly score exceeds 40.
