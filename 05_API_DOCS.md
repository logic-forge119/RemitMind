# API Documentation

Base URL: /api/v1. JSON only. Analyst routes need header X-API-Key. Swagger is auto-generated at /docs.

## Endpoints
| Method | Path | Purpose |
|---|---|---|
| GET | /health | Liveness check |
| POST | /plans/recommend | Best send time, fee, goal split |
| POST | /transfers | Create and score a transfer |
| GET | /transfers/{id} | Transfer status and risk summary |
| GET | /analyst/alerts | List alerts (filter by status) |
| GET | /analyst/alerts/{id} | Alert detail with explanation |
| POST | /analyst/alerts/{id}/decision | Approve, hold or escalate |
| GET | /receiver/{id}/summary?lang=bn | Plain-language summary |
| GET | /agents/{id}/forecast | 7-day cash-out forecast |
| GET | /metrics/fairness | Alert rate by corridor and amount band |
| POST | /dev/seed | Regenerate synthetic data (disabled in production) |

## POST /plans/recommend
Request:
```json
{ "sender_id": "u_101", "receiver_id": "u_202", "corridor": "AED_BDT",
  "amount_src": 2000,
  "goals": [{"name":"rent","share_pct":50},{"name":"school","share_pct":30},{"name":"savings","share_pct":20}] }
```
Response 200:
```json
{ "best_day": "2026-10-05",
  "send_now":  {"amount_bdt": 66400, "fee_bdt": 1330},
  "send_best": {"amount_bdt": 67700, "fee_bdt": 1250},
  "expected_saving_bdt": 1380, "confidence": 0.62,
  "split": [{"name":"rent","bdt":33850},{"name":"school","bdt":20310},{"name":"savings","bdt":13540}],
  "explanation": "Rates have trended up for 4 days...",
  "assumptions": ["Synthetic rate series"] }
```

## POST /transfers
Request:
```json
{ "sender_id": "u_101", "receiver_id": "u_202", "corridor": "AED_BDT",
  "amount_src": 2000, "device_id": "dev_77", "channel": "app" }
```
Response 201:
```json
{ "transfer_id": "t_9001", "status": "in_review", "risk_score": 78,
  "reason_codes": ["NEW_RECEIVER","VELOCITY_3X","NEW_DEVICE"],
  "message": "Sent for a quick safety check." }
```

## GET /analyst/alerts/{id}
```json
{ "alert_id": "a_55", "transfer_id": "t_9001", "score": 78,
  "reason_codes": ["NEW_RECEIVER","VELOCITY_3X","NEW_DEVICE"],
  "what_happened": "3 transfers in 40 minutes to a receiver first seen today.",
  "why_risky": "Matches the structuring pattern seen in synthetic mule rings.",
  "suggested_action": "hold",
  "linked_wallets": ["u_310","u_311"],
  "model_version": "risk-v1" }
```

## POST /analyst/alerts/{id}/decision
Request:
```json
{ "decision": "hold", "note": "Linked to known ring", "is_fraud": true }
```
Response 200:
```json
{ "alert_id": "a_55", "status": "closed", "transfer_status": "held" }
```

## GET /receiver/{id}/summary?lang=bn
```json
{ "received_bdt": 67700, "fee_bdt": 1250,
  "summary": "(plain Bangla sentence: amount received and fee)",
  "suggested_split": [{"name":"rent","bdt":33850}] }
```

## GET /agents/{id}/forecast
```json
{ "agent_id": "ag_5",
  "days": [{"date":"2026-10-06","expected_cashout_bdt":420000}],
  "cash_on_hand_bdt": 300000, "top_up_needed_bdt": 120000, "festival_flag": true }
```

## Errors
| Code | Meaning |
|---|---|
| 400 | Validation failed |
| 401 | Missing or wrong API key |
| 404 | Entity not found |
| 422 | Pydantic schema error |
| 503 | LLM unavailable (template fallback used, so rare) |

Error body: { "error": "code", "detail": "human readable" }
