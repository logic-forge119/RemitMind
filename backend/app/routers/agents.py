from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Agent
from app.schemas import AgentForecastResponse
from app.services.forecast import forecast_agent_demand

router = APIRouter(prefix="/api/v1/agents", tags=["Agent Liquidity"])

@router.get("/{id}/forecast", response_model=AgentForecastResponse)
def get_agent_forecast(id: str, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.id == id).first()
    cash_on_hand = agent.cash_on_hand if agent else 300000.0

    forecast = forecast_agent_demand(agent_id=id, cash_on_hand=cash_on_hand)
    return forecast
