"""
股票数据路由
"""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Depends
from services.data_service import data_service

router = APIRouter(tags=["股票数据"])


@router.get("/stock/list")
async def get_stock_list():
    """获取股票列表"""
    data = await data_service.get_stock_list()
    return {"code": 0, "data": data, "message": "ok"}


@router.get("/stock/{code}")
async def get_stock_info(code: str):
    """获取股票实时行情"""
    info = await data_service.get_stock_info(code)
    return {"code": 0, "data": info, "message": "ok"}


@router.get("/stock/{code}/kline")
async def get_kline(
    code: str,
    ktype: str = Query("D"),
    limit: int = Query(500),
):
    """获取K线数据"""
    data = await data_service.get_kline(code, ktype=ktype, limit=limit)
    return {"code": 0, "data": data, "message": "ok"}


@router.get("/stock/{code}/indicators")
async def get_indicators(code: str):
    """获取技术指标"""
    data = await data_service.get_technical_indicators(code)
    return {"code": 0, "data": data, "message": "ok"}


@router.get("/stock/{code}/moneyflow")
async def get_money_flow(code: str):
    """获取资金流向"""
    data = await data_service.get_money_flow(code)
    return {"code": 0, "data": data, "message": "ok"}


# ─── 以下路由兼容前端 Store 调用 ───

@router.get("/market/overview")
async def get_market_overview():
    """大盘全景（前端 store 调用）"""
    status = await data_service.get_market_status()
    industry = await data_service.get_industry_leaderboard()

    hs300_info = await data_service.get_stock_info("sh000300")
    sz_info = await data_service.get_stock_info("sz399001")
    cy_info = await data_service.get_stock_info("sz399006")

    indices = [
        {"code": "sh000300", "name": "沪深300", "current": status.get("hs300"),
         "change": hs300_info.get("change_pct", 0), "changePct": hs300_info.get("change_pct", 0)},
        {"code": "sz399001", "name": "深证成指", "current": sz_info.get("price"),
         "change": sz_info.get("change_pct", 0), "changePct": sz_info.get("change_pct", 0)},
        {"code": "sz399006", "name": "创业板指", "current": cy_info.get("price"),
         "change": cy_info.get("change_pct", 0), "changePct": cy_info.get("change_pct", 0)},
    ]
    return {
        "code": 0,
        "data": {
            "indices": indices,
            "marketStatus": status.get("desc", "震荡"),
            "positionLimit": status.get("position_limit", 0.4),
            "industries": industry,
        },
        "message": "ok",
    }


@router.get("/stock/benchmark/market-status")
async def get_market_status():
    """市场状态"""
    data = await data_service.get_market_status()
    return {"code": 0, "data": data, "message": "ok"}


@router.get("/stock/industry/leaderboard")
async def get_industry_leaderboard():
    """行业排行"""
    data = await data_service.get_industry_leaderboard()
    return {"code": 0, "data": data, "message": "ok"}


# ─── 兼容前端 Store 的 /kline 端点 ───
@router.get("/kline")
async def get_kline_alt(
    code: str = Query(...),
    ktype: str = Query("D"),
    start: str = Query(None),
    end: str = Query(None),
):
    """获取K线+指标（前端 store 调用: /kline）"""
    kline = await data_service.get_kline(code, ktype=ktype, limit=500)

    # 过滤日期
    if start:
        kline = [k for k in kline if k.get("date", "") >= start]
    if end:
        kline = [k for k in kline if k.get("date", "") <= end]

    indicators = await data_service.get_technical_indicators(code) if kline else {}
    market = await data_service.get_market_status()

    return {
        "code": 0,
        "data": {
            "klines": kline,
            "indicators": indicators,
            "marketStatus": market.get("desc", "震荡"),
        },
        "message": "ok",
    }
