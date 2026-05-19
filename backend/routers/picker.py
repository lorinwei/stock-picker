"""
选股路由 — 缠论选股 + 兼容前端 Store 调用
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from services.picker_service import picker_service

router = APIRouter(tags=["智能选股"])


class CustomFilterRequest(BaseModel):
    pe_min: Optional[float] = 5
    pe_max: Optional[float] = 50
    roe_min: Optional[float] = 5
    pb_max: Optional[float] = 8
    debt_ratio_max: Optional[float] = 60
    market_cap_max: Optional[float] = 500


@router.get("/picker/signals")
async def get_signals():
    """缠论选股信号（TOP 10）"""
    data = await picker_service.generate_signals()
    return {"code": 0, "data": data, "message": "ok"}


@router.get("/picker/stockpool")
async def get_stockpool(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("score"),
):
    """候选股票池（分页）"""
    data = await picker_service.generate_signals()
    signals = data.get("signals", [])
    total = len(signals)
    start = (page - 1) * page_size
    items = signals[start:start + page_size]
    return {
        "code": 0,
        "data": {"items": items, "total": total, "page": page, "page_size": page_size},
        "message": "ok",
    }


@router.post("/picker/custom")
async def custom_filter(req: CustomFilterRequest):
    """自定义筛选"""
    data = await picker_service.generate_signals()
    signals = data.get("signals", [])
    filtered = []
    for s in signals:
        pe = s.get("pe", 0) or 0
        roe = s.get("roe", 0) or 0
        if req.pe_min and pe < req.pe_min:
            continue
        if req.pe_max and pe > req.pe_max:
            continue
        if req.roe_min and roe < req.roe_min:
            continue
        filtered.append(s)
    return {"code": 0, "data": {"items": filtered[:100]}, "message": "ok"}


# ─── 以下路由兼容前端 Store 调用 ───

@router.get("/signals/today")
async def get_today_signals():
    """今日AI选股信号（前端 store 调用）"""
    result = await picker_service.generate_signals()
    signals = result.get("signals", [])

    if not signals:
        return {"code": 0, "data": {"mainPick": None, "alternatives": [], "stats": {}}, "message": "ok"}

    main = signals[0]
    main_pick = {
        "name": main["name"], "code": main["code"],
        "score": main["score"],
        "buyPrice": main["price"], "price": main["price"],
        "targetPrice": round(main["price"] * 1.08, 2),
        "stopLoss": main["stop_loss_price"],
        "positionRatio": main["suggested_position"],
        "reasons": main["entry_reasons"],
        "buyPoint": main.get("buy_point", ""),
        "chanScore": main.get("chan_score", 0),
    }

    alternatives = []
    for s in signals[1:6]:
        alternatives.append({
            "name": s["name"], "code": s["code"],
            "score": s["score"], "price": s["price"],
            "reasons": s["entry_reasons"],
            "changePct": s.get("change_pct", 0),
            "buyPoint": s.get("buy_point", ""),
        })

    return {
        "code": 0,
        "data": {
            "mainPick": main_pick,
            "alternatives": alternatives,
            "stats": {"winRate": 0, "followerCount": 0},
            "market": result.get("market"),
        },
        "message": "ok",
    }


@router.get("/stockpool")
async def get_stockpool_alt(
    category: str = Query("all"),
    page: int = Query(1),
    page_size: int = Query(20),
):
    """选股池（前端 store 调用：/stockpool）"""
    data = await picker_service.generate_signals()
    signals = data.get("signals", [])
    total = len(signals)
    start = (page - 1) * page_size
    items = signals[start:start + page_size]
    return {
        "code": 0,
        "data": {"items": items, "total": total, "page": page, "pageSize": page_size},
        "message": "ok",
    }
