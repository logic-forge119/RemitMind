from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Agent
from app.schemas import AgentForecastResponse, AgentStructuringResponse
from app.services.forecast import forecast_agent_demand
from app.services.structuring import calculate_agent_structuring_metrics
from app.auth import require_role

router = APIRouter(prefix="/api/v1/agents", tags=["Agent Liquidity & Structuring Intelligence"])

@router.get("/structuring-risk", response_model=AgentStructuringResponse)
@router.get("/structuring", response_model=AgentStructuringResponse)
def get_agent_structuring_risk(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("analyst", "admin", "agent"))
):
    """
    Returns agent network structuring intelligence:
    - Volume Z-Score relative to district peers
    - Near-Threshold (BDT 45k-49.9k) CTR smurfing share
    - Night transaction share (00:00 - 06:00 BST)
    - Cash-out to float replenishment turnover ratio
    """
    return calculate_agent_structuring_metrics(db)

@router.get("/{id}/forecast", response_model=AgentForecastResponse)
def get_agent_forecast(id: str, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.id == id).first()
    cash_on_hand = agent.cash_on_hand if agent else 300000.0

    forecast = forecast_agent_demand(agent_id=id, cash_on_hand=cash_on_hand)
    return forecast
