from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.services.llm import (
    generate_copilot_response,
    explain_risk_with_llm,
    generate_receiver_advice_with_llm,
    forecast_agent_liquidity_advice_with_llm,
    AVAILABLE_MODELS
)

router = APIRouter(prefix="/api/v1/ai", tags=["AI Intelligence & LLMs"])

class ChatRequest(BaseModel):
    message: str
    model: Optional[str] = "gemini-1.5-flash"
    language: Optional[str] = "en"
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    reply: str
    model_used: str
    language: str
    grounded_facts: List[str]

class RiskExplainRequest(BaseModel):
    transfer_id: str
    score: float
    reason_codes: Optional[List[str]] = []
    corridor: Optional[str] = "AED_BDT"
    amount_bdt: Optional[float] = 67780.0
    model: Optional[str] = "gemini-1.5-pro"

class ReceiverAdviceRequest(BaseModel):
    sender_name: Optional[str] = "Rahim Sheikh"
    receiver_name: Optional[str] = "Amina Begum"
    amount_bdt: Optional[float] = 67780.0
    language: Optional[str] = "bn"
    model: Optional[str] = "gemini-1.5-flash"

class AgentLiquidityAdviceRequest(BaseModel):
    agent_id: Optional[str] = "AG-05"
    location: Optional[str] = "Balaganj Bazar, Sylhet"
    current_cash: Optional[float] = 300000.0
    peak_demand: Optional[float] = 420000.0
    model: Optional[str] = "gemini-1.5-flash"

class ModelInfo(BaseModel):
    id: str
    name: str
    provider: str
    description: str

@router.get("/models", response_model=List[ModelInfo])
def get_available_models():
    return AVAILABLE_MODELS

@router.post("/chat", response_model=ChatResponse)
def chat_with_ai(payload: ChatRequest):
    result = generate_copilot_response(
        message=payload.message,
        context=payload.context,
        model=payload.model or "gemini-1.5-flash",
        lang=payload.language or "en"
    )
    return result

@router.post("/explain-risk")
def explain_risk(payload: RiskExplainRequest):
    return explain_risk_with_llm(
        transfer_id=payload.transfer_id,
        score=payload.score,
        reason_codes=payload.reason_codes,
        corridor=payload.corridor or "AED_BDT",
        amount_bdt=payload.amount_bdt or 67780.0,
        model=payload.model or "gemini-1.5-pro"
    )

@router.post("/receiver-advice")
def receiver_advice(payload: ReceiverAdviceRequest):
    return generate_receiver_advice_with_llm(
        sender_name=payload.sender_name or "Rahim Sheikh",
        receiver_name=payload.receiver_name or "Amina Begum",
        amount_bdt=payload.amount_bdt or 67780.0,
        lang=payload.language or "bn",
        model=payload.model or "gemini-1.5-flash"
    )

@router.post("/agent-liquidity")
def agent_liquidity(payload: AgentLiquidityAdviceRequest):
    return forecast_agent_liquidity_advice_with_llm(
        agent_id=payload.agent_id or "AG-05",
        location=payload.location or "Balaganj Bazar, Sylhet",
        current_cash=payload.current_cash or 300000.0,
        peak_demand=payload.peak_demand or 420000.0,
        model=payload.model or "gemini-1.5-flash"
    )
