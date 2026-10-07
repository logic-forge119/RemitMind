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

class RiskFactor(BaseModel):
    name: str
    contribution_pct: float
    impact: Optional[str] = "elevates_risk"

class TransferResponse(BaseModel):
    transfer_id: str
    status: str
    risk_score: float
    reason_codes: List[str]
    message: str
    amount_bdt: Optional[float] = None
    fee_bdt: Optional[float] = None
    factors: Optional[List[RiskFactor]] = []
    prediction_set: Optional[List[str]] = []
    is_doubt: Optional[bool] = False
    q_hat: Optional[float] = None
    suggested_action: Optional[str] = "none"

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
    factors: Optional[List[RiskFactor]] = []
    prediction_set: Optional[List[str]] = []
    is_doubt: Optional[bool] = False
    q_hat: Optional[float] = None

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

class PolicyWeights(BaseModel):
    supervised_ml: float = 0.35
    behavioral_anomaly: float = 0.20
    velocity: float = 0.15
    device: float = 0.15
    graph_centrality: float = 0.10
    scamshield_coercion: float = 0.05

class PolicyThresholds(BaseModel):
    review_threshold: float = 45.0
    hold_threshold: float = 75.0
    conformal_alpha: Optional[float] = 0.05
    cooling_off_seconds: Optional[int] = 30

class PolicyUpdateRequest(BaseModel):
    preset: Optional[str] = None
    weights: Optional[Dict[str, float]] = None
    thresholds: Optional[Dict[str, float]] = None

class PolicyResponse(BaseModel):
    version: str
    active_preset: str
    updated_at: str
    updated_by: str
    weights: Dict[str, float]
    thresholds: Dict[str, float]
    presets: Dict[str, Any]

class AgentStructuringMetric(BaseModel):
    agent_id: str
    district: str
    total_transfers_30d: int
    total_volume_bdt: float
    volume_zscore: float
    near_threshold_count: int
    near_threshold_share_pct: float
    night_count: int
    night_share_pct: float
    cashout_bdt: float
    cashin_bdt: float
    cashout_ratio: float
    risk_level: str
    structuring_flags: List[str]

class AgentStructuringResponse(BaseModel):
    agents: List[AgentStructuringMetric]
    flagged_agent_count: int
    high_risk_count: int
    audited_at: str

class AnalystKPIResponse(BaseModel):
    open_today: int
    closed_today: int
    avg_review_time_seconds: float
    false_positive_trend: Dict[str, float]
    top_5_risky_corridors: List[Dict[str, Any]]
    fraud_caught_vs_missed: Dict[str, int]
    generated_at: str

