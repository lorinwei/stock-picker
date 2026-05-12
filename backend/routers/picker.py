"""
智能选股路由 - 选股信号、股票池、自定义筛选
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from services.picker_service import PickerService

router = APIRouter()
picker_service = PickerService()


class CustomFilterRequest(BaseModel):
    """自定义筛选请求"""
    pe_min: Optional[float] = 5
    pe_max: Optional[float] = 50
    pb_max: Optional[float] = 5
    roe_min: Optional[float] = 8.0
    profit_growth_min: Optional[float] = 5.0
    revenue_growth_min: Optional[float] = 5.0
    debt_ratio_max: Optional[float] = 60.0
    market_cap_max: Optional[float] = 500.0  # 亿


# ============ 路由 ============

@router.get("/signals")
async def get_signals():
    """
    获取今日选股信号（TOP 10）
    """
    try:
        data = await picker_service.generate_signals()
        return {"code": 0, "data": data, "message": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取选股信号失败: {str(e)}")


@router.get("/stockpool")
async def get_stockpool(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("score", description="排序字段: score/roe/pe/momentum"),
):
    """
    获取当前候选股票池
    """
    try:
        data = await picker_service.get_stockpool(page, page_size, sort_by)
        return {"code": 0, "data": data, "message": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取股票池失败: {str(e)}")


@router.post("/custom")
async def custom_filter(req: CustomFilterRequest):
    """
    自定义筛选条件
    """
    try:
        data = await picker_service.custom_filter(req)
        return {"code": 0, "data": data, "message": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"自定义筛选失败: {str(e)}")


@router.get("/history")
async def get_signal_history(
    days: int = Query(30, ge=1, le=365),
):
    """
    获取历史选股记录
    """
    try:
        data = await picker_service.get_history(days)
        return {"code": 0, "data": data, "message": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取历史记录失败: {str(e)}")


@router.get("/params")
async def get_strategy_params():
    """
    获取当前选股策略参数配置
    """
    params = picker_service.get_params()
    return {"code": 0, "data": params, "message": "ok"}
