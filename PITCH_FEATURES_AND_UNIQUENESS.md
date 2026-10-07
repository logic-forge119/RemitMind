# RemitMind: Features, Problem-Solution Fit & Uniqueness

## One-line pitch

**RemitMind is an explainable AI safety and intelligence layer for upay that helps migrant workers send money at a better time, protects transfers from coordinated fraud, makes remittance information understandable in Bangla, and helps rural agents prepare cash before demand spikes.**

## The problem we solve

Remittances are a lifeline for Bangladeshi families, but the journey from sender to receiver has four connected weaknesses:

1. **Senders lose money through poor timing and unstructured transfers.** Exchange-rate movement, fees, and family expenses make it difficult to know when to send and how to divide the money.
2. **Risk teams face too many alerts and too little context.** Rules alone produce false positives, create analyst fatigue, and can delay legitimate transfers while still missing coordinated fraud.
3. **Receivers struggle to understand what they received.** Complex SMS messages and unclear deductions are especially difficult for people with limited digital or financial literacy.
4. **Rural agents can run out of cash during predictable surges.** Eid and other high-demand periods can leave recipients travelling farther or waiting longer to collect money.

## How RemitMind solves it

RemitMind connects the full remittance lifecycle in one platform:

- It recommends a better dispatch window and a practical family budget.
- It scores suspicious transfers using machine learning plus business rules, then gives analysts evidence and control.
- It explains the final amount in simple Bangla and can read the summary aloud.
- It forecasts agent cash-out demand and flags shortages before they happen.
- It keeps humans responsible for consequential decisions and makes every AI output reviewable.

---

## Priority 1: AI send-plan recommendation

### Problem

A migrant worker may send money immediately without knowing whether a short wait could reduce exchange-rate and fee losses. The receiver may also need the money divided across essentials rather than delivered as one unstructured amount.

### Solution

The **AI Send-Plan Forecaster** analyzes recent corridor-rate movement and recommends an optimal dispatch window. It shows the expected fee, rate, saving, and a suggested split across goals such as rent, education, and emergency savings.

### Why it matters to judges

- Creates an immediate, easy-to-understand user benefit.
- Turns AI into an actionable recommendation rather than a hidden score.
- Supports the core success metric: average savings versus sending immediately.
- Gives the demo a clear before-and-after moment.

### Key capabilities

- 14-day corridor trend analysis.
- Recommended 5-day dispatch window.
- Fee and exchange-rate comparison.
- Goal-based multi-bucket budgeting.
- Simulated international payment checkout.

### Prototype evidence

The synthetic benchmark targets an average saving of **8% or more**; project simulations report approximately **8.4%** compared with sending immediately.

---

## Priority 2: Explainable hybrid fraud defense with human review

### Problem

Traditional rule-only systems can overwhelm risk teams with false positives, while fully automated blocking can unfairly delay or deny legitimate remittances. Coordinated mule activity and account takeovers also require more than one simple rule.

### Solution

RemitMind combines an **Isolation Forest anomaly model** with deterministic business rules. Every flagged transfer receives a 0-100 risk score, clear reason codes, and a suggested action. Medium- and high-risk transfers go to an analyst queue for `approve`, `hold`, or `escalate` decisions.

### Why it is unique

- **No autonomous blocking:** the system supports analysts instead of replacing them.
- **Evidence before explanation:** the grounded explainer receives verified model outputs and reason codes, not uncontrolled user text.
- **Hybrid detection:** statistical anomalies catch unusual behavior while rules enforce known operational and regulatory constraints.
- **Learning from decisions:** analyst outcomes are stored as labels for future model improvement.

### Key capabilities

- Isolation Forest anomaly scoring.
- Rules such as `VELOCITY_3X`, `NEW_DEVICE`, `NEW_RECEIVER`, and `AMOUNT_DEVIATION`.
- Prioritized analyst review queue.
- Grounded AI briefing with deterministic fallback.
- Feedback loop through analyst decisions.

### Prototype evidence

The project benchmark reports **72% recall in the top 10% of alerts**, with the hybrid approach outperforming rules-only and unsupervised-only baselines.

---

## Priority 3: One platform for four people in the remittance ecosystem

### Problem

Most remittance products optimize one step, such as sending or receiving. They do not connect the sender's decision, the risk team's review, the receiver's understanding, and the agent's cash availability.

### Solution

RemitMind provides role-specific workflows for:

| Persona | Need | RemitMind response |
|---|---|---|
| Sender | Send at the right time and plan the money | Send-plan recommendation and goal split |
| Risk analyst | Investigate suspicious activity efficiently | Ranked queue, reasons, evidence, and actions |
| Receiver | Understand what arrived | Plain Bangla statement and voice playback |
| upay agent | Have enough cash for payouts | Seven-day demand forecast and top-up alert |

### Why it is unique

This is not four disconnected features. Each workflow addresses a different failure point in the same remittance journey, creating a stronger operational story for upay.

---

## Priority 4: Plain Bangla and voice-first receiver experience

### Problem

A technically correct transaction receipt can still fail the person receiving the money if it is filled with financial jargon or unclear deductions.

### Solution

The receiver portal translates the transfer into simple Bangla, clearly showing the amount received, fees, and the next step. Web Speech API support can read the summary aloud in Bangla for users who have difficulty reading.

### Why it matters

- Makes financial information more inclusive.
- Builds trust by making deductions visible.
- Demonstrates that the product is designed for real people, not only analysts.
- Connects AI and localization to a concrete user outcome.

---

## Priority 5: Seven-day agent liquidity forecasting

### Problem

Cash shortages at local agents are predictable around festivals and other demand spikes, but reacting after the shortage occurs is too late.

### Solution

The agent dashboard forecasts seven days of cash-out demand using transaction patterns and calendar context. It flags a likely shortfall early enough for a top-up or cash-in-transit request.

### Why it is unique

RemitMind treats physical cash availability as part of the digital remittance experience. A transfer is not truly successful if the recipient cannot collect it locally.

### Key capabilities

- Seven-day demand forecast.
- Festival-aware surge modeling, including Eid periods.
- Top-up warning before a predicted shortage.
- Agent-level operational visibility.

### Prototype evidence

The target is **under 20% forecast MAPE**; project simulations report reducing agent dry-out events during pre-festival spikes.

---

## Priority 6: Responsible AI built into the product

### Problem

Financial AI can create harm when its decisions are opaque, trained on sensitive data without safeguards, or allowed to act without oversight.

### Solution

RemitMind makes governance part of the product design:

- **100% synthetic data** for the prototype; no customer PII or real banking records.
- **Human-in-the-loop review** for medium- and high-risk transfers.
- **Reason codes and evidence** for every risk decision.
- **Fairness monitoring** across corridors and transfer amount bands.
- **Prompt-injection defenses and input validation.**
- **Deterministic fallback explanations** if the external LLM is unavailable or slow.
- Clear separation between prediction, assumption, and AI-written explanation.

### Why judges should care

The project does not treat responsibility as a post-launch document. Safety, explainability, fairness, and fallback behavior are visible in the user workflow.

---

## What makes RemitMind different

### 1. It optimizes value, safety, access, and availability together

Most solutions focus on only one question: **Can the transfer be sent?** RemitMind asks four better questions:

- Can the sender lose less money?
- Is the transfer safe, and can a human explain why?
- Can the receiver understand the outcome?
- Will the local agent have enough cash to complete the journey?

### 2. It uses AI where it improves a decision

The project applies different techniques to different problems:

- Rate forecasting for timing.
- Goal allocation for household planning.
- Hybrid anomaly detection for risk.
- Grounded language generation for explanations.
- Time-series forecasting for agent liquidity.

### 3. It is explainable by design

The system exposes scores, reason codes, forecast values, assumptions, and human actions. It does not ask users or analysts to trust an unexplained model output.

### 4. It is designed for Bangladesh, not a generic global demo

The product includes Bangla summaries, rural agent operations, Bangladesh-relevant remittance corridors, festival-aware demand, and the practical realities of cash-out access.

### 5. It has a credible path beyond the prototype

The current system uses reproducible synthetic data and simulated payment flows. A production path is already defined: anonymized upay aggregates, licensed FX data, shadow-mode model validation, stronger identity and access management, and real-time graph analytics for mule networks.

---

## Judge-facing impact summary

| Area | Current prototype value | Success measure |
|---|---|---|
| Sender savings | Better timing and structured family budgeting | Average fee/rate saving of 8%+ |
| Fraud defense | Hybrid detection with analyst control | 70%+ recall in top 10% of alerts |
| Receiver trust | Simple Bangla and voice explanation | Clear amount, fee, and next step |
| Agent resilience | Early warning for cash shortages | Demand forecast MAPE under 20% |
| Responsible AI | Synthetic data, fairness checks, no auto-blocking | Auditable human decisions |

## Closing pitch

**RemitMind protects the entire journey of money sent home: it helps the sender keep more, helps upay detect risk responsibly, helps the receiver understand what arrived, and helps the local agent stay ready to pay out.**
