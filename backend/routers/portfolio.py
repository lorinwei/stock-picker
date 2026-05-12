"""
持仓管理路由 - CRUD、风控状态
"""
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from services.portfolio_service import PortfolioService
from services.risk_service import RiskService

router = APIRouter()
portfolio_service = PortfolioService()
risk_service = RiskService()


class AddPositionRequest(BaseModel):
    """添加持仓请求"""
    code: str
    name: str
    buy_date: str
    buy_price: float
    quantity: int
    stop_loss_price: Optional[float] = None


class UpdatePositionRequest(BaseModel):
    """更新持仓请求"""
    current_price: Optional[float] = None
    notes: Optional[str] = None


class SellPositionRequest(BaseModel):
    """卖出持仓请求"""
    sell_date: str
    sell_price: float
    reason: str  # stop_loss / take_profit / trend_break / rebalance / other


# ============ 路由 ============

@router.get("/")
async def get_portfolio():
    """
    获取当前持仓列表
    """
    try:
        positions = await portfolio_service.get_all()
        # 计算各持仓风控状态
        for pos in positions:
            pos["risk_status"] = risk_service.check_position(pos)
        return {"code": 0, "data": positions, "message": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取持仓失败: {str(e)}")


@router.post("/add")
async def add_position(req: AddPositionRequest):
    """
    添加持仓记录
    """
    try:
        position = await portfolio_service.add(req)
        return {"code": 0, "data": position, "message": "持仓添加成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加持仓失败: {str(e)}")


@router.put("/{position_id}")
async def update_position(position_id: str, req: UpdatePositionRequest):
    """
    更新持仓信息（如当前价）
    """
    try:
        position = await portfolio_service.update(position_id, req)
        return {"code": 0, "data": position, "message": "持仓更新成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新持仓失败: {str(e)}")


@router.post("/{position_id}/sell")
async def sell_position(position_id: str, req: SellPositionRequest):
    """
    卖出持仓（平仓）
    """
    try:
        result = await portfolio_service.sell(position_id, req)
        return {"code": 0, "data": result, "message": "平仓成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"平仓失败: {str(e)}")


@router.delete("/{position_id}")
async def delete_position(position_id: str):
    """
    删除持仓记录（仅未持仓时可用）
    """
    try:
        await portfolio_service.delete(position_id)
        return {"code": 0, "data": None, "message": "持仓记录已删除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.get("/risk")
async def get_portfolio_risk():
    """
    获取整体风控状态
    """
    try:
        positions = await portfolio_service.get_all()
        risk_data = {
            "total_value": 0.0,
            "total_cost": 0.0,
            "total_profit": 0.0,
            "profit_rate": 0.0,
            "position_count": len(positions),
            "max_positions": 5,
            "positions": [],
        }

        for pos in positions:
            pos["risk_status"] = risk_service.check_position(pos)
            risk_data["total_value"] += pos.get("current_value", 0)
            risk_data["total_cost"] += pos.get("cost", 0)
            risk_data["positions"].append(pos)

        risk_data["total_profit"] = risk_data["total_value"] - risk_data["total_cost"]
        if risk_data["total_cost"] > 0:
            risk_data["profit_rate"] = risk_data["total_profit"] / risk_data["total_cost"] * 100

        return {"code": 0, "data": risk_data, "message": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取风控状态失败: {str(e)}")


@router.get("/history")
async def get_trade_history(
    limit: int = Query(50, ge=1, le=200),
):
    """
    获取交易历史（包含已平仓）
    """
    try:
        history = await portfolio_service.get_history(limit)
        return {"code": 0, "data": history, "message": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取交易历史失败: {str(e)}")
