"""
RemitMind Business Rules Module
Per TRD Rule 2: Fees, limits, thresholds live in rules.py, NEVER in ML or an LLM prompt.
"""

from app.config import settings

# Base exchange rates and corridor fee rules
CORRIDOR_RULES = {
  "AED_BDT": {
    "name": "United Arab Emirates Dirham",
    "base_rate": 32.85,
    "best_rate_delta": 1.00,
    "fee_pct_immediate": 0.020,  # 2.0%
    "fee_pct_scheduled": 0.018,  # 1.8% (0.2% discount)
    "min_amount": 50,
    "max_amount": 50000,
  },
  "SAR_BDT": {
    "name": "Saudi Riyal",
    "base_rate": 32.10,
    "best_rate_delta": 0.85,
    "fee_pct_immediate": 0.022,  # 2.2%
    "fee_pct_scheduled": 0.019,  # 1.9%
    "min_amount": 50,
    "max_amount": 50000,
  },
  "MYR_BDT": {
    "name": "Malaysian Ringgit",
    "base_rate": 27.40,
    "best_rate_delta": 0.75,
    "fee_pct_immediate": 0.019,  # 1.9%
    "fee_pct_scheduled": 0.016,  # 1.6%
    "min_amount": 50,
    "max_amount": 50000,
  },
  "EUR_BDT": {
    "name": "Euro / Italy",
    "base_rate": 133.50,
    "best_rate_delta": 2.90,
    "fee_pct_immediate": 0.015,  # 1.5%
    "fee_pct_scheduled": 0.013,  # 1.3%
    "min_amount": 20,
    "max_amount": 20000,
  },
  "USD_BDT": {
    "name": "US Dollar / Global",
    "base_rate": 121.20,
    "best_rate_delta": 2.60,
    "fee_pct_immediate": 0.018,  # 1.8%
    "fee_pct_scheduled": 0.015,  # 1.5%
    "min_amount": 20,
    "max_amount": 25000,
  },
}

DEFAULT_CORRIDOR = "AED_BDT"

def get_corridor_rule(corridor: str) -> dict:
  return CORRIDOR_RULES.get(corridor.upper(), CORRIDOR_RULES[DEFAULT_CORRIDOR])

def calculate_fees_and_payout(corridor: str, amount_src: float, is_scheduled_best: bool = False):
  rule = get_corridor_rule(corridor)
  rate = (rule["base_rate"] + rule["best_rate_delta"]) if is_scheduled_best else rule["base_rate"]
  fee_pct = rule["fee_pct_scheduled"] if is_scheduled_best else rule["fee_pct_immediate"]

  gross_bdt = amount_src * rate
  fee_bdt = round(gross_bdt * fee_pct, 2)
  net_bdt = round(gross_bdt - fee_bdt, 2)

  return {
    "rate": rate,
    "fee_pct": fee_pct,
    "gross_bdt": gross_bdt,
    "fee_bdt": fee_bdt,
    "net_bdt": net_bdt,
  }

def evaluate_rule_penalties(
    amount_src: float,
    recent_velocity: int,
    is_new_receiver: bool,
    is_new_device: bool,
    hour_of_day: int,
    sender_avg_amount: float
) -> tuple[float, list[str]]:
  """
  Deterministic rule evaluations that add to the base anomaly score.
  Returns (penalty_score_bonus, reason_codes).
  """
  bonus = 0.0
  reasons = []

  # New receiver + new device combined bonus (+15)
  if is_new_receiver and is_new_device:
    bonus += 15.0
    reasons.append("NEW_RECEIVER_NEW_DEVICE")
  elif is_new_receiver:
    bonus += 8.0
    reasons.append("NEW_RECEIVER")
  elif is_new_device:
    bonus += 7.0
    reasons.append("NEW_DEVICE")

  # Rapid velocity
  if recent_velocity >= 3:
    bonus += 22.0
    reasons.append("VELOCITY_3X")
  elif recent_velocity >= 2:
    bonus += 10.0
    reasons.append("VELOCITY_2X")

  # Odd hour transfer (e.g. 01:00 AM - 04:30 AM local sender time)
  if 1 <= hour_of_day <= 4:
    bonus += 12.0
    reasons.append("ODD_HOURS_NIGHT")

  # Amount deviation check vs 30-day mean
  if sender_avg_amount > 0:
    ratio = amount_src / sender_avg_amount
    if ratio >= 4.0:
      bonus += 25.0
      reasons.append("AMOUNT_4X_DEVIATION")
    elif ratio >= 2.5:
      bonus += 12.0
      reasons.append("AMOUNT_2.5X_DEVIATION")

  return bonus, reasons

def determine_status_and_action(score: float) -> tuple[str, str]:
  """
  Rule 5: No transfer is auto-blocked.
  score < 40: completed
  40 <= score < 70: in_review (suggested action: hold)
  score >= 70: in_review (suggested action: hold or escalate)
  """
  if score < settings.RISK_REVIEW_THRESHOLD:
    return "completed", "none"
  elif score < settings.RISK_HIGH_THRESHOLD:
    return "in_review", "hold"
  else:
    return "in_review", "escalate"
