# RemitMind &bull; Technical Architecture & Scalability Guide

This document details the architectural layers, data flows, separation of concerns, and the production transition roadmap for RemitMind.

---

## 1. Architectural Philosophy

RemitMind is built following strict architectural principles outlined in Guideline §12:
1. **Separation of Business Rules from Statistical ML**: Hard regulatory rules (sanction lists, daily transaction limits) run independently from unsupervised statistical models (Isolation Forest).
2. **Grounded Explainability**: LLMs are isolated in an explanation-only layer. An LLM never calculates risk scores or authorizes transactions.
3. **Traceability & Auditability**: Every incoming transfer generates a snapshot of feature values, sub-model scores, reason codes, and analyst decisions in relational storage.
4. **Phase 2 Modularity**: Detectors and rules are implemented as pluggable modules behind standardized interfaces to absorb new on-site hackathon requirements rapidly.

---

## 2. End-to-End System Diagram

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 PRESENTATION LAYER                                     │
│  ┌───────────────────────┐  ┌────────────────────────┐  ┌───────────────────────────┐  │
│  │     Sender Portal     │  │ Receiver Plain-Bangla  │  │   Analyst Radar & Queue   │  │
│  │ (Send Plan, Budgeting)│  │ (Voice TTS, Statement) │  │  (SAR Explanations, Feed) │  │
│  └───────────┬───────────┘  └───────────┬────────────┘  └─────────────┬─────────────┘  │
└──────────────┼──────────────────────────┼─────────────────────────────┼────────────────┘
               │                          │                             │
               ▼                          ▼                             ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                APPLICATION & API LAYER                                 │
│                             FastAPI Framework (app/main.py)                            │
│  ┌────────────────────┐ ┌────────────────────┐ ┌───────────────────┐ ┌───────────────┐ │
│  │  plans.py Router   │ │ transfers.py Router│ │ analyst.py Router │ │ agents.py     │ │
│  │ (5-Day Trend/Split)│ │ (Submit & Ingest)  │ │ (Queue & Review)  │ │ (7-Day Demand)│ │
│  └──────────┬─────────┘ └──────────┬─────────┘ └─────────┬─────────┘ └───────┬───────┘ │
└─────────────┼──────────────────────┼─────────────────────┼───────────────────┼─────────┘
              │                      │                     │                   │
              ▼                      ▼                     ▼                   ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              INTELLIGENCE & AI SERVICES                                │
│  ┌─────────────────────────┐  ┌─────────────────────────┐  ┌─────────────────────────┐ │
│  │   rules.py (Engine)     │  │   risk.py (Engine)      │  │  forecast.py (Engine)   │ │
│  │ • Deterministic Rules   │  │ • Isolation Forest      │  │ • 14-Day Rate Trend     │ │
│  │ • Sanction List Watch   │  │ • Anomaly Scoring (0-100│  │ • 7-Day Agent Demand    │ │
│  │ • Velocity Limits       │  │ • Reason Code Generator │  │ • Eid Surge Multiplier  │ │
│  └──────────┬──────────────┘  └──────────┬──────────────┘  └───────────┬─────────────┘ │
│             │                            │                             │               │
│             └────────────────────────────┼─────────────────────────────┘               │
│                                          ▼                                             │
│                       ┌──────────────────────────────────────┐                         │
│                       │         llm.py / explain.py          │                         │
│                       │ • Grounded Gemini 1.5 Flash/Pro API  │                         │
│                       │ • Deterministic Template Fallback    │                         │
│                       │ • Bangla & English SAR Briefings     │                         │
│                       └──────────────────┬───────────────────┘                         │
└──────────────────────────────────────────┼─────────────────────────────────────────────┘
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               PERSISTENCE & DATA LAYER                                 │
│                    SQLAlchemy 2.0 ORM & SQLite / PostgreSQL                            │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐  │
│  │    users     │ │  transfers   │ │ review_alerts│ │review_actions│ │ agent_stats  │  │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘  │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Data Flow: Transfer Ingestion to Human Review

1. **Submission**: Sender submits transfer via `POST /api/v1/transfers`.
2. **Feature Extraction**: Current transfer features are calculated against sender historical baseline (rolling 24h count, rolling 7d sum, average ticket delta, recipient tenure).
3. **Deterministic Rule Check**:
   - Velocity count > 3 in 1 hour &rarr; triggers `VELOCITY_3X` penalty.
   - Recipient created < 48 hours &rarr; triggers `NEW_RECEIVER` penalty.
   - Unknown IP / Device hash &rarr; triggers `NEW_DEVICE` penalty.
4. **Unsupervised ML Anomaly Scoring**:
   - Normalized feature vector is fed to `IsolationForest.decision_function`.
   - Continuous outlier score is mapped to calibrated 0–100 risk scale.
5. **Policy Gateway**:
   - `Score < 40`: Allowed (status `COMPLETED`).
   - `Score ≥ 40`: Intercepted (status `PENDING_REVIEW`, added to `review_alerts`).
6. **Explanation Synthesis**:
   - Structured alert JSON passed to `explain.py`.
   - Generates natural language summary for the analyst console.
7. **Analyst Feedback**:
   - Analyst selects `approve`, `hold`, or `escalate` via `POST /alerts/{id}/decision`.
   - Action stored in `review_actions` table, creating supervised training labels (`is_fraud_label = 0 or 1`).

---

## 4. What Changes When Moving from Synthetic to Enterprise Data

This table satisfies the **Guideline §15 (Scalability & Integration)** requirement detailing production transition:

| Domain | Prototype Implementation | Enterprise upay Production Target | Operational Complexity |
|---|---|---|---|
| **Data Ingestion** | Batch synthetic seed (`generate.py`) into SQLite | Apache Kafka event streaming from upay Core Switch & MFS Ledger | Medium: Requires schema registry, consumer groups, and dead-letter queues. |
| **Feature Store** | On-the-fly SQL aggregate queries | Feast or Redis for sub-millisecond online feature retrieval | Low: Pre-aggregated velocity counters in memory. |
| **Model Serving** | In-process Scikit-Learn within FastAPI worker | Vertex AI / Triton Server behind gRPC endpoints | Medium: Autoscaling GPU/CPU nodes with canary deployment and zero downtime. |
| **Graph Intelligence** | Synthetic cluster IDs & rule tags | Neo4j / AWS Neptune graph DB with Graph Neural Networks (GNNs) | High: Real-time multi-hop traversal to detect complex mule disbursement syndicates. |
| **Database & Storage** | SQLite local file (`remitmind.db`) | PostgreSQL (RDS) for transactional data + BigQuery for analytics | Low: SQLAlchemy models are 100% PostgreSQL-compatible out of the box. |
| **LLM Deployment** | Cloud Gemini API with fallback | On-premises / VPC-hosted open-weights LLM (e.g. Gemma 2 / Llama 3) | Medium: Eliminates cross-border data residency concerns under Bangladesh Bank guidelines. |
| **Security & Auth** | Simulated client roles | UCB Active Directory, OAuth2 / OIDC, mTLS between microservices, PCI-DSS Level 1 | High: Full compliance with Bangladesh Bank ICT Security Guidelines. |
| **Model Monitoring** | Static fairness audit endpoint | Evidently AI / Prometheus drift monitoring (PSI, CSI, feature drift) | Low: Continuous alerting if real-world FX volatility alters model anomaly thresholds. |
