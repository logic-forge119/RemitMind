# PRD: RemitMind

## 1. Problem statement
For migrant workers and their families in Bangladesh, poorly timed and unprotected remittances cause lost money, fraud exposure, and agent cash shortages. We will build an AI-powered remittance layer for upay that uses synthetic transfer data to recommend sending plans, flag risky transfers for human review, explain money in simple Bangla, and forecast agent liquidity. Success is measured by fees saved, fraud caught, and cash-outs served.

## 2. Personas
| Persona | Who | Pain | What we give |
|---|---|---|---|
| Sender (Rahim) | Worker in Dubai | Unsure when/how much to send; fears fraud | Best-time and split plan, safe-transfer check |
| Receiver (Amina) | Mother in village | Does not understand amounts, fees, next steps | Plain Bangla summary, simple goal plan |
| Agent (Karim) | Local upay agent | Runs out of cash before Eid | Cash-out demand forecast, top-up alert |
| Analyst (Nusrat) | upay risk team | Too many alerts, no context | Ranked queue with reasons and suggested action |

## 3. Goals / Non-goals
Goals: one end-to-end story; three ML components plus grounded LLM explainer; every AI output explainable and human-reviewable.
Non-goals: real money movement, real bank/SWIFT integration, real customer data, autonomous blocking/approving, credit decisions.

## 4. Features (MoSCoW)
| ID | Feature | Priority |
|---|---|---|
| F1 | Create transfer | Must |
| F2 | Send-plan recommendation (best time, amount, fee comparison) | Must |
| F3 | Goal split (rent, school, savings) | Should |
| F4 | Risk scoring 0-100 with reason codes | Must |
| F5 | Analyst review queue: approve / hold / escalate | Must |
| F6 | Receiver summary in Bangla and English | Must |
| F7 | Agent 7-day cash-out forecast | Should |
| F8 | LLM explanations grounded in model outputs | Must |
| F9 | Feedback loop: analyst decisions saved as labels | Should |
| F10 | Fairness check by corridor and amount band | Should |
| F11 | Voice in/out in Bangla | Could |

## 5. User stories and acceptance criteria
- US1 Sender sees best day, expected saving, and split. Accept: under 2 s; shows fee, rate, saving in BDT.
- US2 Transfer is risk-scored on submit. Accept: low risk completes (simulated); medium/high go to review.
- US3 Analyst opens queue. Accept: score, top 3 reason codes, explanation, suggested action, approve/hold/escalate.
- US4 Receiver sees what arrived in simple language. Accept: amount, fee, plain Bangla sentence, split suggestion.
- US5 Agent sees expected demand. Accept: 7-day forecast and top-up flag.

## 6. Success metrics (synthetic data)
| Metric | Target |
|---|---|
| Fees saved vs send-immediately baseline | avg 8% or more |
| Fraud recall at top 10% of alerts | 70% or more |
| Agent demand forecast MAPE | under 20% |
| End-to-end demo | works live without errors |

## 7. Risks
| Risk | Mitigation |
|---|---|
| Scope too big for 12 h | Cut order in the 12-hour plan |
| LLM down/slow | Template fallback explanations |
| Final-day changes | Modular services, rules separate from ML |
| Looks like a toy | Show metrics, fairness check, path to real data |
