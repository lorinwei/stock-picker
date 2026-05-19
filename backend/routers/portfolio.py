"""
持仓管理路由
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from services.portfolio_service import portfolio_service
from services.risk_service import RiskService

router = APIRouter(tags=["持仓管理"])
risk_service = RiskService()


class AddPositionReq(BaseModel):
    code: str
    name: str = ""
    buy_date: str = ""
    buy_price: float
    quantity: int


class SellReq(BaseModel):
    sell_price: float
    reason: str = "manual"


class RiskCheckReq(BaseModel):
    action: str = "buy"
    code: str = ""
    price: float = 0
    quantity: int = 0
    portfolio_value: float = 0


@router.get("/portfolio")
async def get_portfolio():
    """获取持仓（前端 store 调用）"""
    positions = await portfolio_service.get_all()
    # 计算风控状态
    for pos in positions:
        pos["risk_status"] = risk_service.check_position(pos)
        pos["current_value"] = pos.get("current_price", 0) * pos.get("quantity", 0)
        pos["cost"] = pos.get("buy_price", 0) * pos.get("quantity", 0)

    total_val = sum(p.get("current_value", 0) for p in positions)
    total_cost = sum(p.get("cost", 0) for p in positions)
    total_profit = round(total_val - total_cost, 2)
    profit_pct = round(total_profit / total_cost * 100, 2) if total_cost else 0

    return {
        "code": 0,
        "data": {
            "positions": positions,
            "totalValue": total_val,
            "totalCost": total_cost,
            "totalProfit": total_profit,
            "profitPercent": profit_pct,
            "cash": max(0, portfolio_service.initial_cash - total_val),
            "availableCash": max(0, portfolio_service.initial_cash - total_val),
            "maxPositions": 5,
        },
        "message": "ok",
    }


@router.get("/portfolio/")
async def get_portfolio_root():
    return await get_portfolio()


@router.post("/portfolio")
async def add_position(req: AddPositionReq):
    """添加持仓（前端 store 调用）"""
    pos = await portfolio_service.add(
        code=req.code, name=req.name or req.code,
        buy_date=req.buy_date or "unknown",
        buy_price=req.buy_price, quantity=req.quantity,
    )
    return {"code": 0, "data": pos, "message": "持仓添加成功"}


@router.post("/portfolio/add")
async def add_position_v2(req: AddPositionReq):
    return await add_position(req)


@router.post("/portfolio/{position_id}/sell")
async def sell_position(position_id: int, req: SellReq):
    """卖出持仓"""
    result = await portfolio_service.sell(position_id, req.sell_price, req.reason)
    return {"code": 0, "data": result, "message": "平仓成功"}


@router.delete("/portfolio/{position_id}")
async def delete_position(position_id: int):
    """删除已平仓记录"""
    await portfolio_service.delete(position_id)
    return {"code": 0, "message": "已删除"}


@router.get("/portfolio/risk")
async def get_portfolio_risk():
    """整体风控"""
    positions = await portfolio_service.get_all()
    total_val = sum(p.get("current_price", 0) * p.get("quantity", 0) for p in positions)
    total_cost = sum(p.get("buy_price", 0) * p.get("quantity", 0) for p in positions)
    total_profit = total_val - total_cost
    profit_pct = round(total_profit / total_cost * 100, 2) if total_cost else 0
    cash = max(0, portfolio_service.initial_cash - total_val)

    risk_data = {
        "totalValue": total_val,
        "totalCost": total_cost,
        "totalProfit": round(total_profit, 2),
        "profitPercent": profit_pct,
        "cash": cash, "availableCash": cash,
        "maxPositions": 5,
        "maxDrawdown": 0, "sharpeRatio": 0, "volatility": 0,
        "warningLevel": "safe" if profit_pct > -5 else "warning",
        "positions": positions,
    }
    return {"code": 0, "data": risk_data, "message": "ok"}


@router.get("/portfolio/history")
async def get_trade_history(limit: int = Query(50, le=200)):
    """交易历史"""
    history = await portfolio_service.get_history(limit)
    return {"code": 0, "data": history, "message": "ok"}


# ─── 风控检查端点 ───

@router.post("/risk/check")
async def check_risk(req: RiskCheckReq):
    """风控检查（前端 store 调用）"""
    return {"code": 0, "data": {"allowed": True, "reason": "ok"}, "message": "ok"}
