"""
每日复盘任务 - 每日21:00自动执行
"""
from datetime import datetime
from loguru import logger

from services.ai_service import AIService
from services.notifier import notifier


async def run_daily_summary():
    """
    每日收盘后生成AI复盘报告
    """
    logger.info("🔔 开始生成每日复盘...")

    try:
        ai = AIService()
        today = datetime.now().strftime("%Y-%m-%d")
        result = await ai.get_daily_summary(today)

        summary = result.get("summary", "")
        logger.info(f"📝 复盘生成完成，字数: {len(summary)}")

        if summary:
            # 发送到飞书
            await notifier.send_text(f"📋 每日复盘 {today}\n\n{summary[:2000]}")
            logger.info("✅ 复盘已推送至飞书")

        return result

    except Exception as e:
        logger.error(f"每日复盘任务失败: {e}")
        return {"error": str(e)}
