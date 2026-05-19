"""
回测路由
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List

from services.backtest_service import backtest_service

router = APIRouter(tags=["策略回测"])


class BacktestReq(BaseModel):
    stock_code: str
    strategy_type: str = "value_trend"
    start_date: str = ""
    end_date: str = ""
    initial_cash: float = 100000.0
    stop_loss: float = -8.0
    take_profit: float = 20.0


class CompareReq(BaseModel):
    stock_code: str
    strategy_ids: List[str]
    start_date: str
    end_date: str
    initial_cash: float = 100000.0


@router.post("/backtest/run")
async def run_backtest(req: BacktestReq):
    """执行回测"""
    result = await backtest_service.run(
        stock_code=req.stock_code,
        strategy_type=req.strategy_type,
        start_date=req.start_date or None,
        end_date=req.end_date or None,
        initial_cash=req.initial_cash,
        stop_loss=req.stop_loss,
        take_profit=req.take_profit,
    )
    return {"code": 0, "data": result, "message": "ok"}


@router.post("/backtest/compare")
async def compare_strategies(req: CompareReq):
    """多策略对比"""
    result = await backtest_service.compare(
        stock_code=req.stock_code,
        strategy_ids=req.strategy_ids,
        start_date=req.start_date,
        end_date=req.end_date,
        initial_cash=req.initial_cash,
    )
    return {"code": 0, "data": result, "message": "ok"}


@router.post("/backtest/optimize")
async def optimize_params(
    stock_code: str,
    start_date: str,
    end_date: str,
):
    """参数优化"""
    result = await backtest_service.optimize(stock_code, start_date, end_date)
    return {"code": 0, "data": result, "message": "ok"}


@router.get("/backtest/history")
async def get_history(limit: int = Query(20, le=100)):
    """回测历史"""
    records = await backtest_service.get_history(limit)
    return {"code": 0, "data": records, "message": "ok"}


@router.get("/backtest/record/{record_id}")
async def get_record(record_id: str):
    """回测详情"""
    record = await backtest_service.get_record(record_id)
    return {"code": 0, "data": record, "message": "ok"}
