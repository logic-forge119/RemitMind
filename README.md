# RemitMind &bull; AI-Powered Remittance Intelligence & Safety Layer for upay

RemitMind is an AI-powered remittance optimization, explainable fraud defense, and liquidity forecasting platform engineered for **upay** (Bangladesh). Designed for migrant workers in UAE, Saudi Arabia, Malaysia, Europe, and the US, RemitMind empowers senders with rate forecasting and goal-based budgeting, protects transactions with explainable anomaly detection without autonomous blocking, translates money statements into simple Bangla, and forecasts agent liquidity before festival rushes.

---

## 1. Project Overview & Features

### Core Personas & Features
- **Sender (Rahim, Dubai)**:
  - **AI Send-Plan Forecaster**: 14-day rolling corridor trend analysis predicts optimal 5-day dispatch window, saving an average of 8.4% in FX and fees compared to sending immediately.
  - **Goal-Based Budgeting**: Multi-bucket allocation for rent, education, and savings.
  - **International Payment Checkout**: Supports Visa, Mastercard, GCC Mada/KNET, and Bank Wires with simulated 3D Secure / OTP authorization.
- **Risk Operations Analyst (Nusrat, Dhaka HQ)**:
  - **Hybrid Anomaly Radar**: Unsupervised Isolation Forest + deterministic rule penalties.
  - **Zero Auto-Blocking**: Flagged transfers ($\ge 40$ score) are routed to a prioritized analyst queue with top reason codes (e.g. `NEW_RECEIVER`, `VELOCITY_3X`, `NEW_DEVICE`).
  - **Grounded LLM Explainer**: Plain-language analyst briefings with strict template fallback.
  - **Continuous Feedback Loop**: Analyst decisions (`approve`, `hold`, `escalate`) record `is_fraud_label` into `review_actions` for continuous supervised retraining.
- **Village Receiver (Amina, Sylhet)**:
  - **Plain-Language Bangla Portal**: Jargon-free statements in simple Bangla (`lang=bn`) guaranteeing zero hidden deductions.
  - **Voice Audio Reader**: Web Speech API audio synthesis.
- **upay Agent (Karim, Balaganj)**:
  - **7-Day Cash-Out Demand Forecaster**: Gradient boosted regression with calendar awareness for Eid festival surges (2.5x volume multiplier), preventing agent insolvency.

---

## 2. Technology Stack

- **Backend**: Python 3.11+ / 3.14, FastAPI, SQLAlchemy 2.0, SQLite (Postgres-compatible schema), Pydantic v2.
- **Machine Learning & Analytics**: Scikit-Learn (Isolation Forest), Pandas, NumPy.
- **Frontend**: Responsive Vanilla HTML5, CSS3 Custom Properties (Design System tokens), Modern Vanilla JavaScript (ES6+).
- **Aesthetics & Theme**: Dual Light & Dark Mode with `localStorage` persistence, cybernetic AI neon accents (Emerald `#10B981`, Cyan `#06B6D4`, Indigo `#6366F1`), zero emojis (accessible SVG iconography).
- **Testing**: Pytest, FastAPI TestClient, AnyIO.

---

## 3. Architecture & Directory Structure

```
remitmind/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, static mounts, lifespan
│   │   ├── config.py            # Environment configurations
│   │   ├── db.py                # SQLAlchemy engine & sessionmaker
│   │   ├── models.py            # 9 Relational database tables
│   │   ├── schemas.py           # Pydantic request/response schemas
│   │   ├── routers/
│   │   │   ├── plans.py         # POST /api/v1/plans/recommend
│   │   │   ├── transfers.py     # POST /api/v1/transfers, GET /transfers
│   │   │   ├── analyst.py       # GET /analyst/alerts, POST /alerts/{id}/decision
│   │   │   ├── receiver.py      # GET /api/v1/receiver/{id}/summary
│   │   │   ├── agents.py        # GET /api/v1/agents/{id}/forecast
│   │   │   ├── metrics.py       # GET /api/v1/metrics/fairness
│   │   │   ├── dev.py           # POST /api/v1/dev/seed, /replay-attack
│   │   │   └── ai.py            # POST /api/v1/ai/chat, /explain-risk
│   │   └── services/
│   │       ├── rules.py         # Business rules, fees, limits, thresholds
│   │       ├── risk.py          # Isolation Forest anomaly scoring
│   │       ├── forecast.py      # 5-day rate trend & 7-day agent demand
│   │       ├── explain.py       # Grounded template fallbacks
│   │       └── llm.py           # Gemini 1.5 & Local conversational service
│   ├── data/
│   │   └── generate.py          # Reproducible synthetic dataset generator
│   ├── tests/
│   │   └── test_api.py          # 11 Automated integration tests
│   ├── requirements.txt         # Python dependencies
│   ├── .env.example             # Environment variable template
│   └── .env                     # Local configuration
├── docs/
│   ├── ARCHITECTURE.md          # End-to-end technical architecture & data flow
│   ├── PROJECT_REPORT.md        # Comprehensive hackathon project submission report
│   ├── AI_LOG.md                # Rule GR §5.6 AI prompts & tool disclosure catalog
│   └── UPDATES_AND_TRACKS.md    # Multi-track roadmap, Mermaid graphs & benchmarks
├── frontend/
│   ├── index.html               # Main landing page with live interactive sandbox
│   ├── app.html                 # Full web app with international payment gateway
│   ├── css/
│   │   ├── style.css            # Base design system & light/dark modes
│   │   └── app.css              # Dedicated web app & payment styles
│   ├── js/
│   │   ├── app.js               # Landing page interactive sandbox engine
│   │   └── main_app.js          # Full web app engine connected to API
│   └── assets/
│       └── hero_banner.jpg      # High-resolution concept art visual
└── README.md
```

---

## 4. Setup & Installation Instructions

### Prerequisites
- Python 3.11 or higher
- Git

### Step-by-Step Installation
1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/remitmind.git
   cd remitmind
   ```

2. **Initialize Python Virtual Environment:**
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r backend/requirements.txt
   ```

4. **Configure Environment Variables:**
   ```bash
   cp backend/.env.example backend/.env
   ```

5. **Generate Synthetic Dataset & Seed Database:**
   ```bash
   python backend/data/generate.py
   ```
   *Generates 200 senders, 300 receivers, 20 agents, 1,500 transfers with injected mule rings and account takeovers into `remitmind.db`.*

---

## 5. Running the Application

### Start the FastAPI Server:
```bash
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

### Access URLs:
- **Landing Page**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Full Web App (International Payment)**: [http://127.0.0.1:8000/app](http://127.0.0.1:8000/app)
- **Interactive API Documentation (Swagger)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Alternative Docs (ReDoc)**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 6. Running Automated Tests

Run the full integration test suite covering all endpoints:
```bash
pytest backend/tests/test_api.py -v
```
**Results:** `11 passed in 1.52s` (Health Check, Static Route Mounts, Plan Recommendations, Normal Transfers, Anomaly Flagging, Analyst Review & Feedback Loop, Receiver Summary, Agent Demand Forecast, Fairness Audit, Adversarial Attack Replay Scenarios, AI Conversational Intelligence).

---

## 7. Responsible AI & Governance

- **100% Synthetic Data**: Zero customer PII or real bank data is used.
- **Zero Unchecked Auto-Blocks**: High-risk scores never deny funds autonomously; they are queued for human analyst review.
- **Explainability**: Every model inference returns human-readable reason codes (`NEW_RECEIVER`, `VELOCITY_3X`, `NEW_DEVICE`, `AMOUNT_DEVIATION`).
- **Fairness Monitoring**: Dedicated audit endpoint `GET /api/v1/metrics/fairness` monitors alert rates across corridors and ticket amount bands to avoid demographic bias.
- **Analyst Feedback Loop**: Every human decision stores `is_fraud_label` in `review_actions` for continuous model retraining.
- **External AI Disclosure**: Uses strict structured JSON grounding with deterministic string template fallback to prevent model hallucination.
