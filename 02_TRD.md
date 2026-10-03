# TRD: RemitMind

## 1. Stack (beginner-friendly, minimal)
| Layer | Choice | Why |
|---|---|---|
| Language | Python 3.11 | ML-friendly, familiar |
| API | FastAPI | Auto Swagger docs |
| DB | SQLite via SQLAlchemy (Postgres-compatible schema) | Zero setup |
| ML | scikit-learn, pandas, numpy | Simple, reliable |
| LLM | Any free-tier API behind one wrapper | Swappable |
| Frontend | React + Vite + Tailwind (or plain HTML + fetch) | Fast |
| Deploy | Render/Railway (API), Vercel (frontend) | Free tiers, live URL |

## 2. Architecture
```
Synthetic generator -> SQLite
        |
  Feature layer (pandas)
        |
 +--------------+---------------+---------------+
 | Send-time    | Risk model    | Demand        |
 | forecaster   | (IsoForest +  | forecaster    |
 | (rates)      |  rules)       | (agent cash)  |
 +--------------+---------------+---------------+
        |
 Business rules (fees, limits, thresholds)  <- separate from ML
        |
 FastAPI service layer
        |
 LLM explainer (structured JSON only)
        |
 React: Sender | Receiver+Agent | Analyst
```

## 3. Folder structure
```
remitmind/
  backend/
    app/
      main.py  config.py  db.py  models.py  schemas.py
      routers/   plans.py transfers.py analyst.py receiver.py agents.py
      services/  risk.py forecast.py rules.py explain.py
      ml/        train_risk.py train_demand.py artifacts/
    data/generate.py
    tests/
    requirements.txt
    .env.example
  frontend/
  docs/
  README.md
```

## 4. Design rules
1. Data preparation separate from model inference.
2. Fees, limits, thresholds live in rules.py, never in ML or an LLM prompt.
3. LLM receives only structured JSON and cannot change any decision.
4. Every model output returns reason codes.
5. No transfer is auto-blocked: medium/high risk go to human review.
6. Keep a clean test split never used for training.

## 5. Non-functional requirements
| Area | Requirement |
|---|---|
| Performance | Score and plan endpoints under 2 s |
| Reliability | LLM failure falls back to templates |
| Security | Env secrets only, Pydantic validation, rate limit on /explain, API key on analyst routes, sanitize user text before LLM (prompt-injection guard) |
| Privacy | Synthetic data only |
| Observability | Request log with transfer_id, model version, latency |

## 6. Environment variables
| Name | Purpose |
|---|---|
| DATABASE_URL | e.g. sqlite:///./remitmind.db |
| LLM_API_KEY | Explainer LLM key (placeholder in .env.example) |
| LLM_MODEL | Model name |
| ANALYST_API_KEY | Auth for analyst endpoints |
| RISK_REVIEW_THRESHOLD | Default 40 |
| RISK_HIGH_THRESHOLD | Default 70 |
| ALLOWED_ORIGINS | Frontend URL for CORS |
