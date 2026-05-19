"""
缠论分析路由
"""
from fastapi import APIRouter, HTTPException, Query
from services.chanservice import ChanService

router = APIRouter(tags=["缠论分析"])


@router.get("/chan/{code}")
async def get_chan_analysis(code: str):
    """缠论综合分析"""
    try:
        result = await ChanService().analyze(code)
        return {"code": 0, "data": result, "message": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chan/{code}/buy-signals")
async def get_buy_signals(code: str):
    """缠论三类买点"""
    result = await ChanService().analyze(code)
    signals = result.get("analysis", {}).get("buy_signals", [])
    return {"code": 0, "data": signals, "message": "ok"}


@router.get("/chan/{code}/sell-signals")
async def get_sell_signals(code: str):
    """缠论三类卖点"""
    result = await ChanService().analyze(code)
    signals = result.get("analysis", {}).get("sell_signals", [])
    return {"code": 0, "data": signals, "message": "ok"}
