"""
股票数据路由 - K线、技术指标、资金流向
"""
import asyncio
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from services.data_service import DataService
from utils.cache import cache

router = APIRouter()
data_service = DataService()


# ============ 请求/响应模型 ============

class KLineRequest(BaseModel):
    code: str
    ktype: str = "D"  # D=日线, W=周线, M=月线
    start: Optional[str] = None
    end: Optional[str] = None


class StockInfoResponse(BaseModel):
    code: str
    name: str
    industry: str
    market_cap: float
    pe: float
    pb: float
    roe: float
    revenue_growth: float
    profit_growth: float
    debt_ratio: float
    goodwill_ratio: float


# ============ 路由 ============

@router.get("/list")
async def get_stock_list():
    """获取A股股票列表"""
    cache_key = "stock_list_all"
    cached = cache.get(cache_key)
    if cached:
        return {"code": 0, "data": cached, "message": "ok"}

    data = await data_service.get_stock_list()
    cache.set(cache_key, data, ttl=86400)  # 缓存1天
    return {"code": 0, "data": data, "message": "ok"}


@router.get("/{code}")
async def get_stock_info(code: str):
    """获取股票基本信息"""
    try:
        info = await data_service.get_stock_info(code)
        return {"code": 0, "data": info, "message": "ok"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"获取股票信息失败: {str(e)}")


@router.get("/{code}/kline")
async def get_kline(
    code: str,
    ktype: str = Query("D", description="D=日线 W=周线 M=月线"),
    start: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    limit: int = Query(500, description="返回条数上限"),
):
    """获取K线数据"""
    try:
        if end is None:
            end = datetime.now().strftime("%Y-%m-%d")
        if start is None:
            start = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

        data = await data_service.get_kline(code, ktype, start, end, limit)
        return {"code": 0, "data": data, "message": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取K线失败: {str(e)}")


@router.get("/{code}/indicators")
async def get_indicators(
    code: str,
    indicators: str = Query("MA,MACD,RSI,KDJ,BOLL,ATR", description="指标列表，逗号分隔"),
):
    """获取技术指标"""
    try:
        ind_list = [x.strip() for x in indicators.split(",")]
        data = await data_service.get_technical_indicators(code, ind_list)
        return {"code": 0, "data": data, "message": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取指标失败: {str(e)}")


@router.get("/{code}/moneyflow")
async def get_money_flow(code: str):
    """获取资金流向"""
    try:
        data = await data_service.get_money_flow(code)
        return {"code": 0, "data": data, "message": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取资金流向失败: {str(e)}")


@router.get("/benchmark/market-status")
async def get_market_status():
    """获取市场牛熊状态（沪深300 vs 20周均线）"""
    try:
        data = await data_service.get_market_status()
        return {"code": 0, "data": data, "message": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取市场状态失败: {str(e)}")


@router.get("/industry/leaderboard")
async def get_industry_leaderboard():
    """获取行业涨跌排行"""
    try:
        data = await data_service.get_industry_leaderboard()
        return {"code": 0, "data": data, "message": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取行业排行失败: {str(e)}")
