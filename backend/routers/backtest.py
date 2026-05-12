"""
策略回测路由 - 单策略回测、多策略对比、参数优化
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from services.backtest_service import BacktestService

router = APIRouter()
backtest_service = BacktestService()


class BacktestRequest(BaseModel):
    """回测请求"""
    stock_code: str
    strategy_type: str = "value_trend"  # value_trend / momentum / breakout
    start_date: str
    end_date: str
    initial_cash: float = 100000.0
    stop_loss: float = -8.0  # 止损线 %
    take_profit: float = 20.0  # 止盈线 %


class CompareRequest(BaseModel):
    """对比回测请求"""
    stock_code: str
    strategy_ids: List[str]
    start_date: str
    end_date: str
    initial_cash: float = 100000.0


# ============ 路由 ============

@router.post("/run")
async def run_backtest(req: BacktestRequest):
    """
    执行单策略回测
    """
    try:
        result = await backtest_service.run(
            stock_code=req.stock_code,
            strategy_type=req.strategy_type,
            start_date=req.start_date,
            end_date=req.end_date,
            initial_cash=req.initial_cash,
            stop_loss=req.stop_loss,
            take_profit=req.take_profit,
        )
        return {"code": 0, "data": result, "message": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"回测执行失败: {str(e)}")


@router.post("/compare")
async def compare_strategies(req: CompareRequest):
    """
    多策略对比回测
    """
    try:
        result = await backtest_service.compare(
            stock_code=req.stock_code,
            strategy_ids=req.strategy_ids,
            start_date=req.start_date,
            end_date=req.end_date,
            initial_cash=req.initial_cash,
        )
        return {"code": 0, "data": result, "message": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"策略对比失败: {str(e)}")


@router.post("/optimize")
async def optimize_params(
    stock_code: str,
    start_date: str,
    end_date: str,
):
    """
    参数优化（网格搜索）
    """
    try:
        result = await backtest_service.optimize(
            stock_code=stock_code,
            start_date=start_date,
            end_date=end_date,
        )
        return {"code": 0, "data": result, "message": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"参数优化失败: {str(e)}")


@router.get("/history")
async def get_backtest_history(
    limit: int = Query(20, ge=1, le=100),
):
    """
    获取历史回测记录
    """
    try:
        records = await backtest_service.get_history(limit)
        return {"code": 0, "data": records, "message": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取历史记录失败: {str(e)}")


@router.get("/record/{record_id}")
async def get_backtest_record(record_id: str):
    """
    获取指定回测记录的详情
    """
    try:
        record = await backtest_service.get_record(record_id)
        return {"code": 0, "data": record, "message": "ok"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"记录不存在: {str(e)}")
