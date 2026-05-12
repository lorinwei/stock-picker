"""
每日选股任务 - 每日16:00自动执行
"""
from datetime import datetime
from loguru import logger

from services.picker_service import PickerService
from services.notifier import notifier


async def run_daily_pick():
    """
    每日收盘后自动执行选股
    """
    logger.info("🔔 开始执行每日选股任务...")

    try:
        picker = PickerService()
        result = await picker.generate_signals()

        date = result.get("date", datetime.now().strftime("%Y-%m-%d"))
        signals = result.get("signals", [])
        market = result.get("market", {})

        logger.info(f"📊 选股完成: {len(signals)} 个信号")

        if signals:
            # 推送飞书
            await notifier.send_signals(signals, market)
            logger.info(f"✅ 选股信号已推送至飞书")
        else:
            logger.warning("⚠️ 今日无选股信号")

        return result

    except Exception as e:
        logger.error(f"每日选股任务失败: {e}")
        return {"error": str(e)}
