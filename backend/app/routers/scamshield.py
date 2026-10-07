"""
AegisShield Pre-Flight Interception Router
Provides real-time pre-transaction screening and social-engineering defense.
Enforces mandatory cooling-off countdown periods and bilingual (EN + BN) safety advisories.
"""

from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User, Transfer

router = APIRouter(prefix="/api/v1/scamshield", tags=["AegisShield"])

class ScamShieldCheckRequest(BaseModel):
    sender_id: str
    receiver_id: str
    amount: float
    corridor: Optional[str] = "AED_BDT"
    memo: Optional[str] = ""
    device_id: Optional[str] = "app_default_device"
    timestamp: Optional[str] = None

class ScamShieldCheckResponse(BaseModel):
    intercept: bool
    risk_level: str  # "low" | "medium" | "high" | "critical"
    warning_message_en: str
    warning_message_bn: str
    cooling_off_seconds: int
    scam_type: str  # "lottery_fraud" | "family_emergency" | "fake_regulator" | "accidental_refund_trap" | "night_novel_beneficiary" | "none"
    reasons: List[str]
    risk_score: float

LOTTERY_KEYWORDS = [
    "lottery", "prize", "winner", "reward", "jackpot", "gift card",
    "processing fee", "won", "congratulations", "lucky draw",
    "লটারি", "পুরস্কার", "উপহার", "জিতেছেন", "প্রসেসিং ফি"
]

EMERGENCY_KEYWORDS = [
    "emergency", "hospital", "urgent bail", "accident", "arrested",
    "police station", "icu", "kidnapped", "surgery",
    "হাঁসপাতাল", "হাসপাতাল", "দুর্ঘটনা", "জরুরি", "থানা", "গ্রেফতার", "অপারেশন"
]

REGULATOR_KEYWORDS = [
    "bangladesh bank", "bfiu", "tax penalty", "unfreeze", "police fine",
    "court fine", "customs clearance", "cid investigation",
    "কমিশন", "ট্যাক্স", "জরিমানা", "অ্যাকাউন্ট ফ্রিজ", "বাংলাদেশ ব্যাংক", "কাস্টমস"
]

REFUND_KEYWORDS = [
    "refund", "reversal", "mistake sent", "wrong number", "return money",
    "ভুল করে", "ফেরত", "ভুল টাকা", "রিফান্ড"
]

from app.services.normalizer import contains_scam_keyword

@router.post("/check", response_model=ScamShieldCheckResponse)
@router.post("/verify", response_model=ScamShieldCheckResponse)
def check_transaction_safety(req: ScamShieldCheckRequest, db: Session = Depends(get_db)):
    """
    Pre-flight safety analysis of a proposed remittance.
    Scans semantic intent, transaction novelty, off-hours timing, and velocity deviation.
    Neutralizes zero-width characters, homoglyphs, NFKC decomposition, and leet evasion.
    """
    intercept = False
    risk_level = "low"
    scam_type = "none"
    cooling_off = 0
    reasons = []
    risk_score = 15.0

    memo_text = req.memo or ""

    # 1. Semantic Threat Categorization with Anti-Evasion Normalization
    if contains_scam_keyword(memo_text, LOTTERY_KEYWORDS):
        scam_type = "lottery_fraud"
        intercept = True
        risk_level = "critical"
        cooling_off = 30
        risk_score = max(risk_score, 88.0)
        reasons.append("SUSPECTED_ADVANCE_FEE_LOTTERY_SCAM")
        msg_en = (
            "CRITICAL ALERT: Legitimate lotteries and promotional rewards NEVER ask for upfront transfer fees. "
            "This recipient request matches verified advance-fee scam signatures."
        )
        msg_bn = (
            "জরুরি সতর্কতা: কোনো বৈধ লটারি বা পুরস্কারের জন্য কখনো অগ্রিম প্রসেসিং ফি বা টাকা পাঠাতে হয় না। "
            "এটি প্রতারক চক্রের একটি ফাঁদ। টাকা পাঠাবেন না।"
        )
    elif contains_scam_keyword(memo_text, REGULATOR_KEYWORDS):
        scam_type = "fake_regulator"
        intercept = True
        risk_level = "critical"
        cooling_off = 30
        risk_score = max(risk_score, 92.0)
        reasons.append("SUSPECTED_GOVERNMENT_OR_REGULATOR_IMPERSONATION")
        msg_en = (
            "CRITICAL ALERT: Law enforcement, Bangladesh Bank, and BFIU NEVER instruct individuals to transfer funds "
            "to mobile wallets or personal accounts to avoid arrest or account freezing."
        )
        msg_bn = (
            "সর্বোচ্চ সতর্কতা: পুলিশ, বিএফআইইউ বা বাংলাদেশ ব্যাংক কখনোই জরিমানা বা অ্যাকাউন্ট চালুর নামে কোনো ব্যক্তিগত ওয়ালেটে টাকা পাঠাতে বলে না। "
            "এটি সরকারি সংস্থার পরিচয় ব্যবহারকারী প্রতারণা।"
        )
    elif contains_scam_keyword(memo_text, EMERGENCY_KEYWORDS):
        scam_type = "family_emergency"
        intercept = True
        risk_level = "high"
        cooling_off = 30
        risk_score = max(risk_score, 74.0)
        reasons.append("SUSPECTED_EMERGENCY_IMPERSONATION")
        msg_en = (
            "HIGH RISK: Fraud syndicates frequently exploit emotional distress by impersonating hospital staff or police. "
            "You MUST call your family member directly on their known personal phone before transferring any money."
        )
        msg_bn = (
            "উচ্চ ঝুঁকি: প্রতারকরা প্রায়শই স্বজন দুর্ঘটনা বা হাসপাতালে থাকার ভুয়া নাটক তৈরি করে আতঙ্ক সৃষ্টি করে। "
            "টাকা পাঠানোর আগে অবিলম্বে আপনার স্বজনের পরিচিত নিজস্ব নম্বরে কল করে সত্যতা যাচাই করুন।"
        )
    elif contains_scam_keyword(memo_text, REFUND_KEYWORDS):
        scam_type = "accidental_refund_trap"
        intercept = True
        risk_level = "high"
        cooling_off = 15
        risk_score = max(risk_score, 68.0)
        reasons.append("SUSPECTED_ACCIDENTAL_TRANSFER_REFUND_TRAP")
        msg_en = (
            "HIGH RISK: Fraudsters often claim they 'mistakenly sent money' and demand an immediate reversal to a different number. "
            "Verify your actual statement balance directly with customer care first."
        )
        msg_bn = (
            "উচ্চ ঝুঁকি: কেউ 'ভুল করে টাকা পাঠানো হয়েছে' বলে ভিন্ন নম্বরে টাকা ফেরত চাইলে সতর্ক থাকুন। "
            "প্রথমে নিজের ওয়ালেট ব্যালেন্স ও অফিশিয়াল মেসেজ যাচাই করুন।"
        )
    else:
        msg_en = ""
        msg_bn = ""

    # 2. Novel Beneficiary & Off-Hours Check
    now = datetime.now(timezone.utc)
    if req.timestamp:
        try:
            ts = datetime.fromisoformat(req.timestamp.replace("Z", "+00:00"))
            current_hour = ts.hour
        except Exception:
            current_hour = 14
    else:
        # Bangladesh Standard Time (UTC+6)
        current_hour = (now.hour + 6) % 24
    
    is_off_hours = (current_hour >= 23 or current_hour <= 5)

    receiver = db.query(User).filter(User.id == req.receiver_id).first()
    sender_history = db.query(Transfer).filter(Transfer.sender_id == req.sender_id).all()

    # Check if sender has ever transferred to this receiver
    has_prior_transfer = any(t.receiver_id == req.receiver_id for t in sender_history)
    
    if not has_prior_transfer:
        reasons.append("NOVEL_BENEFICIARY_FIRST_TRANSACTION")
        risk_score += 20.0
        # High-risk nocturnal novel transfer or massive sum
        if (is_off_hours and req.amount >= 5000) or req.amount >= 25000:
            intercept = True
            if risk_level != "critical":
                risk_level = "critical" if req.amount >= 50000 else "high"
            cooling_off = max(cooling_off, 30)
            if scam_type == "none":
                scam_type = "night_novel_beneficiary"
            if not msg_en:
                msg_en = (
                    "SECURITY INTERCEPT: First-time remittance to a new recipient initiated during high-risk off-hours. "
                    "A mandatory 30-second cooling-off verification window has been engaged."
                )
                msg_bn = (
                    "নিরাপত্তা যাচাই: নতুন প্রাপকের কাছে গভীর রাতে বড় অঙ্কের লেনদেন শুরু করা হয়েছে। "
                    "যেকোনো ভুল বা প্রতারণা এড়াতে বাধ্যতামূলক ৩০ সেকেন্ডের সচেতনতা বিরতি প্রযোজ্য।"
                )

    # 3. Velocity / Baseline Amount Deviation Check
    if sender_history:
        completed = [t.amount_src for t in sender_history if t.status == "completed"]
        if completed:
            avg_amount = sum(completed) / len(completed)
            if req.amount >= 3.0 * avg_amount and req.amount > 1000:
                reasons.append("AMOUNT_EXCEEDS_3X_BASELINE")
                risk_score += 25.0
                if risk_level != "critical":
                    risk_level = "high"
                intercept = True
                cooling_off = max(cooling_off, 20)
                if not msg_en:
                    msg_en = (
                        f"HIGH VALUE ADVISORY: This transaction amount ({req.amount:,.2f}) is more than 3x higher "
                        "than your regular remittance pattern. Please confirm the recipient identity."
                    )
                    msg_bn = (
                        f"সতর্কতা: এই লেনদেনের পরিমাণ ({req.amount:,.2f}) আপনার নিয়মিত গড় লেনদেনের চেয়ে ৩ গুণেরও বেশি। "
                        "অনুগ্রহ করে প্রাপকের পরিচয় নিশ্চিত করুন।"
                    )

    # 4. Final Intercept Threshold Evaluation
    if risk_score >= 60.0:
        intercept = True
        if risk_level == "low":
            risk_level = "medium"

    if not intercept:
        risk_level = "low"
        cooling_off = 0
        msg_en = "No elevated fraud signatures detected. Transaction cleared for pre-flight dispatch."
        msg_bn = "কোনো ঝুঁকিপূর্ণ লক্ষণ শনাক্ত হয়নি। লেনদেনটি সুরক্ষিত।"

    return ScamShieldCheckResponse(
        intercept=intercept,
        risk_level=risk_level,
        warning_message_en=msg_en,
        warning_message_bn=msg_bn,
        cooling_off_seconds=cooling_off,
        scam_type=scam_type,
        reasons=reasons,
        risk_score=round(min(risk_score, 99.0), 1)
    )
