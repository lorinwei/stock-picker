"""
持仓检查任务 - 每日16:30自动执行
"""
from loguru import logger

from services.portfolio_service import PortfolioService
from services.risk_service import RiskService
from services.data_service import DataService
from services.notifier import notifier


async def run_portfolio_check():
    """
    每日收盘后检查持仓状态，发送预警
    """
    logger.info("🔔 开始执行持仓检查任务...")

    try:
        portfolio = PortfolioService()
        risk = RiskService()
        data = DataService()

        positions = await portfolio.get_all()

        if not positions:
            logger.info("📭 当前无持仓")
            return {"positions": [], "message": "无持仓"}

        # 更新各持仓的当前价格
        for pos in positions:
            try:
                info = await data.get_stock_info(pos["code"])
                current_price = info.get("price", pos.get("buy_price", 0))
                current_value = current_price * pos["quantity"]
                profit = current_value - pos["cost"]
                profit_pct = profit / pos["cost"] * 100 if pos["cost"] > 0 else 0
                highest = max(pos.get("highest_price", 0), current_price)

                # 更新到数据库
                import sqlite3
                conn = sqlite3.connect(portfolio.db_path)
                conn.execute(
                    """UPDATE positions SET
                       current_price=?, current_value=?, profit=?, profit_pct=?,
                       highest_price=?, updated_at=CURRENT_TIMESTAMP
                       WHERE id=?""",
                    (current_price, current_value, profit, profit_pct, highest, pos["id"]),
                )
                conn.commit()
                conn.close()

                pos["current_price"] = current_price
                pos["current_value"] = current_value
                pos["profit"] = profit
                pos["profit_pct"] = profit_pct
                pos["highest_price"] = highest

            except Exception as e:
                logger.warning(f"更新持仓 {pos['code']} 价格失败: {e}")

        # 风控检查
        alerts = []
        for pos in positions:
            status = risk.check_position(pos)
            pos["risk_status"] = status

            if status["status"] in ["stop_loss", "warning", "take_profit", "time_stop"]:
                alerts.append(pos)

        logger.info(f"📊 持仓检查完成: {len(positions)} 只，{len(alerts)} 个预警")

        # 推送预警
        if alerts:
            await notifier.send_portfolio_alert(alerts)
            logger.info(f"✅ 持仓预警已推送至飞书")

        return {"positions": positions, "alerts": alerts}

    except Exception as e:
        logger.error(f"持仓检查任务失败: {e}")
        return {"error": str(e)}
