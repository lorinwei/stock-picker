"""
AI 策略引擎路由
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from services.ai_service import ai_service

router = APIRouter(tags=["AI策略引擎"])


class GenReq(BaseModel):
    description: str
    include_stop_loss: bool = True
    include_take_profit: bool = True


class ReverseReq(BaseModel):
    code: str
    start_date: str
    end_date: str


class ConsultReq(BaseModel):
    codes: List[str]
    include_market: bool = True


@router.post("/ai/generate-strategy")
async def generate_strategy(req: GenReq):
    result = await ai_service.generate_strategy(req.description)
    return {"code": 0, "data": result, "message": "ok"}


@router.post("/ai/reverse-strategy")
async def reverse_strategy(req: ReverseReq):
    result = await ai_service.reverse_strategy(req.code, req.start_date, req.end_date)
    return {"code": 0, "data": result, "message": "ok"}


@router.post("/ai/consult")
async def consult_stocks(req: ConsultReq):
    result = await ai_service.consult_stocks(req.codes)
    return {"code": 0, "data": result, "message": "ok"}


@router.get("/ai/daily-summary")
async def get_daily_summary(date: Optional[str] = Query(None)):
    result = await ai_service.get_daily_summary(date)
    return {"code": 0, "data": result, "message": "ok"}
