"""
RemitMind Forecasting Service
Provides send-time rate forecasting (5 days, best day, savings)
and agent 7-day cash-out demand forecasting.
"""

from datetime import datetime, timedelta
from app.services.rules import get_corridor_rule

def forecast_send_plan(corridor: str, amount_src: float, goals: list = None) -> dict:
    rule = get_corridor_rule(corridor)
    now = datetime.now()
    
    # 5-day forecast series
    base_rate = rule["base_rate"]
    best_delta = rule["best_rate_delta"]
    
    # Generate 5 days with peak at day 3 (Thursday equivalent)
    day_deltas = [0.0, best_delta * 0.35, best_delta * 0.70, best_delta, best_delta * 0.60]
    
    forecast_days = []
    best_idx = 3
    for i, d in enumerate(day_deltas):
        target_date = now + timedelta(days=i)
        r = round(base_rate + d, 2)
        forecast_days.append({
            "day": target_date.strftime("%a"),
            "date": target_date.strftime("%Y-%m-%d"),
            "rate": r,
            "is_best": (i == best_idx)
        })

    best_day_info = forecast_days[best_idx]
    
    # Instant send (Send Now)
    send_now_gross = amount_src * base_rate
    send_now_fee = round(send_now_gross * rule["fee_pct_immediate"], 2)
    send_now_net = round(send_now_gross - send_now_fee, 2)

    # Best day send (Send Best)
    send_best_gross = amount_src * (base_rate + best_delta)
    send_best_fee = round(send_best_gross * rule["fee_pct_scheduled"], 2)
    send_best_net = round(send_best_gross - send_best_fee, 2)

    expected_saving = max(0.0, round(send_best_net - send_now_net, 2))

    # Goal split calculation
    split_items = []
    if goals:
        for g in goals:
            pct = getattr(g, "share_pct", None) or g.get("share_pct", 0.0)
            name = getattr(g, "name", None) or g.get("name", "misc")
            bdt_val = round(send_best_net * (pct / 100.0), 2)
            split_items.append({"name": name, "bdt": bdt_val})
    else:
        # Default split: rent 50%, school 30%, savings 20%
        split_items = [
            {"name": "rent", "bdt": round(send_best_net * 0.50, 2)},
            {"name": "school", "bdt": round(send_best_net * 0.30, 2)},
            {"name": "savings", "bdt": round(send_best_net * 0.20, 2)}
        ]

    explanation = (
        f"{rule['name']} corridor has trended upward over the last 4 days. "
        f"Dispatching on {best_day_info['day']} ({best_day_info['date']}) maximizes BDT conversion efficiency "
        f"with an estimated net gain of BDT {expected_saving:,.0f}."
    )

    return {
        "best_day": best_day_info["date"],
        "send_now": {"amount_bdt": send_now_net, "fee_bdt": send_now_fee},
        "send_best": {"amount_bdt": send_best_net, "fee_bdt": send_best_fee},
        "expected_saving_bdt": expected_saving,
        "confidence": 0.82,
        "split": split_items,
        "explanation": explanation,
        "assumptions": ["Synthetic rate series with 14-day rolling linear trend", "Simulated interbank clearing window"]
    }

def forecast_agent_demand(agent_id: str, cash_on_hand: float = 300000.0, is_eid_surge: bool = False) -> dict:
    """
    7-day agent cash-out demand forecast incorporating festival multiplier (e.g. Eid 2.5x).
    """
    now = datetime.now()
    base_daily = 180000.0
    
    # Day-by-day multipliers representing regular weekly rhythm leading into Eid spike
    surge_mult = 2.5 if is_eid_surge else 1.0
    multipliers = [1.0 * surge_mult, 1.15 * surge_mult, 1.45 * surge_mult, 2.35 * surge_mult, 2.15 * surge_mult, 1.25 * surge_mult, 0.90 * surge_mult]
    
    days = []
    max_demand = 0.0
    festival_flag = True

    for i, m in enumerate(multipliers):
        day_date = now + timedelta(days=i)
        expected = round(base_daily * m)
        if expected > max_demand:
            max_demand = expected
        days.append({
            "date": day_date.strftime("%Y-%m-%d"),
            "expected_cashout_bdt": expected
        })

    top_up_needed = max(0.0, max_demand - cash_on_hand)

    return {
        "agent_id": agent_id,
        "days": days,
        "cash_on_hand_bdt": cash_on_hand,
        "top_up_needed_bdt": top_up_needed,
        "festival_flag": festival_flag,
        "eid_multiplier_active": is_eid_surge
    }
