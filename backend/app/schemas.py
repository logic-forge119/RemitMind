from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class PlanGoal(BaseModel):
    name: str
    share_pct: float

class PlanRecommendRequest(BaseModel):
    sender_id: str
    receiver_id: str
    corridor: str  # AED_BDT, SAR_BDT, MYR_BDT, EUR_BDT, USD_BDT
    amount_src: float
    goals: List[PlanGoal] = []

class SendDetail(BaseModel):
    amount_bdt: float
    fee_bdt: float

class SplitItem(BaseModel):
    name: str
    bdt: float

class PlanRecommendResponse(BaseModel):
    best_day: str
    send_now: SendDetail
    send_best: SendDetail
    expected_saving_bdt: float
    confidence: float
    split: List[SplitItem]
    explanation: str
    assumptions: List[str] = []

class TransferCreateRequest(BaseModel):
    sender_id: str
    receiver_id: str
    corridor: str
    amount_src: float
    device_id: Optional[str] = "app_default_device"
    channel: Optional[str] = "app"
    agent_id: Optional[str] = None
    goals: Optional[List[PlanGoal]] = None
    simulate_anomaly: Optional[bool] = False

class TransferResponse(BaseModel):
    transfer_id: str
    status: str
    risk_score: float
    reason_codes: List[str]
    message: str
    amount_bdt: Optional[float] = None
    fee_bdt: Optional[float] = None

class RiskAlertDetailResponse(BaseModel):
    alert_id: str
    transfer_id: str
    score: float
    reason_codes: List[str]
    what_happened: str
    why_risky: str
    suggested_action: str
    linked_wallets: List[str] = []
    model_version: str

class AnalystDecisionRequest(BaseModel):
    decision: str  # 'approve', 'hold', 'escalate'
    note: Optional[str] = None
    is_fraud: Optional[bool] = None

class AnalystDecisionResponse(BaseModel):
    alert_id: str
    status: str
    transfer_status: str

class ReceiverSummaryResponse(BaseModel):
    received_bdt: float
    fee_bdt: float
    summary: str
    suggested_split: List[SplitItem]

class AgentForecastDay(BaseModel):
    date: str
    expected_cashout_bdt: float

class AgentForecastResponse(BaseModel):
    agent_id: str
    days: List[AgentForecastDay]
    cash_on_hand_bdt: float
    top_up_needed_bdt: float
    festival_flag: bool

class FairnessMetricItem(BaseModel):
    corridor: str
    amount_band: str
    total_transfers: int
    flagged_count: int
    alert_rate_pct: float

class FairnessMetricsResponse(BaseModel):
    metrics: List[FairnessMetricItem]
    overall_alert_rate_pct: float
    audited_at: str
    notes: str
