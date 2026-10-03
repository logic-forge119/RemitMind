# Responsible AI Checklist

| Principle | What we do |
|---|---|
| Privacy | Synthetic data only, stated in README |
| Explainability | Reason codes on every alert and plan |
| Fairness | /metrics/fairness shows alert rate by corridor and amount band; note any gap |
| Security | API key on analyst routes, input validation, prompt-injection guard, env secrets |
| Human oversight | Medium/high risk go to analyst queue, no auto-block |
| Transparency | UI labels: Prediction vs Assumption vs AI-written explanation |
| No harmful automation | System never approves or denies consequential decisions on its own |

## Path to real data
1. Replace the synthetic generator with a read-only feed of anonymized upay transfer aggregates.
2. Retrain risk model on analyst-confirmed labels; validate in a shadow period (alerts shown, no action).
3. Swap the mock rate series for a licensed FX feed.
4. Add governance: model cards, drift monitoring, audit log of every analyst decision.
5. Pilot one corridor with a small agent group; measure fees saved and fraud caught.
