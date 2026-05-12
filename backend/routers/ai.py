"""
AI策略引擎路由 - 策略生成、策略反推、股票问诊、每日复盘
"""
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from services.ai_service import AIService

router = APIRouter()
ai_service = AIService()


class StrategyGenerateRequest(BaseModel):
    """策略生成请求"""
    description: str  # 自然语言描述
    include_stop_loss: bool = True
    include_take_profit: bool = True


class StrategyReverseRequest(BaseModel):
    """策略反推请求"""
    code: str
    start_date: str
    end_date: str


class StockConsultRequest(BaseModel):
    """股票问诊请求"""
    codes: List[str]
    include_market: bool = True


# ============ 路由 ============

@router.post("/generate-strategy")
async def generate_strategy(req: StrategyGenerateRequest):
    """
    AI策略生成：自然语言 → Python策略代码
    """
    try:
        result = await ai_service.generate_strategy(
            description=req.description,
            include_stop_loss=req.include_stop_loss,
            include_take_profit=req.include_take_profit,
        )
        return {"code": 0, "data": result, "message": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"策略生成失败: {str(e)}")


@router.post("/reverse-strategy")
async def reverse_strategy(req: StrategyReverseRequest):
    """
    AI策略反推：指定K线区间 → 策略描述
    """
    try:
        result = await ai_service.reverse_strategy(
            code=req.code,
            start_date=req.start_date,
            end_date=req.end_date,
        )
        return {"code": 0, "data": result, "message": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"策略反推失败: {str(e)}")


@router.post("/consult")
async def consult_stocks(req: StockConsultRequest):
    """
    AI股票问诊：持仓 → 诊断报告
    """
    try:
        result = await ai_service.consult_stocks(
            codes=req.codes,
            include_market=req.include_market,
        )
        return {"code": 0, "data": result, "message": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"股票问诊失败: {str(e)}")


@router.get("/daily-summary")
async def get_daily_summary(date: Optional[str] = Query(None, description="日期 YYYY-MM-DD，默认今日")):
    """
    AI每日复盘报告
    """
    try:
        result = await ai_service.get_daily_summary(date)
        return {"code": 0, "data": result, "message": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取复盘失败: {str(e)}")


@router.post("/backtest-strategy")
async def backtest_generated_strategy(
    strategy_code: str,
    stock_code: str,
    start_date: str,
    end_date: str,
):
    """
    对AI生成的策略进行回测
    """
    try:
        result = await ai_service.backtest_generated_strategy(
            strategy_code=strategy_code,
            stock_code=stock_code,
            start_date=start_date,
            end_date=end_date,
        )
        return {"code": 0, "data": result, "message": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"策略回测失败: {str(e)}")
