from fastapi import APIRouter
from app.schemas import PlanRecommendRequest, PlanRecommendResponse
from app.services.forecast import forecast_send_plan

router = APIRouter(prefix="/api/v1/plans", tags=["Send Plans"])

@router.post("/recommend", response_model=PlanRecommendResponse)
def get_send_plan_recommendation(payload: PlanRecommendRequest):
    plan = forecast_send_plan(
        corridor=payload.corridor,
        amount_src=payload.amount_src,
        goals=payload.goals
    )
    return plan
