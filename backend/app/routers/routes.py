# app/routers/routes.py
from fastapi import APIRouter
from pydantic import BaseModel
from app.services.route_service import optimize_daily_routes


router = APIRouter()


class OptimizeRequest(BaseModel):
    date: str         # Format: YYYY-MM-DD
    business_id: str


@router.post('/optimize')
async def optimize_routes(req: OptimizeRequest):
    """Run full-day VRP optimization. Time limit: 30 seconds."""
    result = await optimize_daily_routes(req.date, req.business_id)
    return {'date': req.date, 'assignments': result}


@router.post('/reoptimize')
async def reoptimize_routes(req: OptimizeRequest):
    """Re-run optimizer after cancellation or emergency insertion.
    In production: filter out 'completed' jobs so they stay frozen."""
    result = await optimize_daily_routes(req.date, req.business_id)
    return {'date': req.date, 'reoptimized': True, 'assignments': result}

