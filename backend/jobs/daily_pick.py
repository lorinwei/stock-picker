"""
每日选股任务 — 16:00 自动执行
"""
from loguru import logger
from services.picker_service import picker_service
from services.notifier import notifier


async def run_daily_pick():
    logger.info("每日选股任务开始...")
    try:
        result = await picker_service.generate_signals()
        signals = result.get("signals", [])
        market = result.get("market", {})
        logger.info(f"选股完成: {len(signals)}个信号")

        if signals:
            await notifier.send_signals(signals, market)
            logger.info("信号已推送至飞书")

        return result
    except Exception as e:
        logger.error(f"选股任务失败: {e}")
        return {"error": str(e)}
