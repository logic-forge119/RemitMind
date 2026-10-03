# ML Specification

## Risk model
- Type: Isolation Forest (unsupervised) blended with rule flags.
- Features: amount vs sender 30-day mean (z-score), transfers in last hour, new receiver (0/1), new device (0/1), hour of day, receiver distinct senders in 24 h, corridor.
- Score: anomaly score scaled to 0-100, plus rule bonuses (e.g. +15 for new receiver and new device together).
- Reason codes: from rules and the features with the largest deviation (no SHAP needed).
- Eval: 20% hold-out test set; report recall at top 10% alerts and precision on injected fraud labels.
- Upgrade if time: LightGBM supervised model once analyst labels exist.

## Send-time forecaster
- Type: moving average + linear regression on last 14 days of synthetic rates, per corridor.
- Output: predicted rate for next 5 days, best day, confidence from recent volatility.
- Baseline: send immediately. Report average saving on the held-out period.
- Show confidence and say it is a simulation, never a promise.

## Agent demand forecaster
- Type: gradient boosting or linear regression on day-of-week, days-to-festival, last-7-day mean.
- Eval: MAPE on last 14 days held out.

## LLM explainer
- Input: structured JSON only (scores, reason codes, numbers, language).
- System prompt: explain, do not decide; never invent numbers; say so if a field is missing.
- Outputs: sender plan text, analyst narrative (what happened / why risky / what next), Bangla receiver summary.
- Fallback: string templates filled from the same JSON.
- Security: strip user free text before prompting; no secrets in prompts.
