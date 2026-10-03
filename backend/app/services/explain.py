"""
RemitMind Grounded Explainer Service
Receives strictly structured JSON input and outputs natural language narratives.
Features zero-downtime template fallback strings.
"""

def generate_analyst_explanation(data: dict) -> dict:
    """
    Produces:
    - what_happened
    - why_risky
    - suggested_action
    """
    reasons = data.get("reason_codes", [])
    amount_src = data.get("amount_src", 0.0)
    score = data.get("score", 0.0)
    velocity = data.get("velocity", 1)

    what_happened_parts = []
    if "VELOCITY_3X" in reasons or velocity >= 3:
        what_happened_parts.append(f"{velocity} rapid transfers initiated within 45 minutes")
    else:
        what_happened_parts.append("Single transfer submitted")

    if "NEW_RECEIVER" in reasons or "NEW_RECEIVER_NEW_DEVICE" in reasons:
        what_happened_parts.append("to a newly registered beneficiary account first seen today")
    
    if "NEW_DEVICE" in reasons or "NEW_RECEIVER_NEW_DEVICE" in reasons:
        what_happened_parts.append("from an unverified mobile device hardware fingerprint")

    what_happened = ", ".join(what_happened_parts) + "."

    why_risky_parts = []
    if score >= 70:
        why_risky_parts.append("Transaction characteristics closely mirror structured syndicates and synthetic mule account testing.")
    elif score >= 40:
        why_risky_parts.append("Deviation detected from sender's baseline 30-day volume frequency.")
    else:
        why_risky_parts.append("Matches historical family remittance profile.")

    why_risky = " ".join(why_risky_parts)

    suggested_action = data.get("suggested_action", "hold" if score >= 40 else "none")

    return {
        "what_happened": what_happened,
        "why_risky": why_risky,
        "suggested_action": suggested_action
    }

def generate_receiver_summary(received_bdt: float, fee_bdt: float, sender_name: str = "রহিম ভাই", lang: str = "bn") -> str:
    """
    Generates plain-language summary for village receiver without banking jargon.
    """
    if lang == "bn":
        return f"আপনার কাছে {sender_name}-এর পাঠানো মোট {int(received_bdt):,} টাকা নিরাপদে পৌঁছেছে। কোনো গোপন বা বাড়তি চার্জ কাটা হয়নি।"
    else:
        return f"A total of BDT {int(received_bdt):,} has safely arrived from {sender_name}. No hidden fees were deducted."
