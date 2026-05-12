"""
定时任务调度器 - APScheduler
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

scheduler = AsyncIOScheduler()


def start_scheduler():
    """启动定时任务调度器"""
    from jobs.daily_pick import run_daily_pick
    from jobs.portfolio_check import run_portfolio_check
    from jobs.daily_summary import run_daily_summary

    # 每日16:00 选股
    scheduler.add_job(
        run_daily_pick,
        CronTrigger(hour=16, minute=0),
        id="daily_pick",
        name="每日选股",
        misfire_grace_time=3600,  # 允许1小时内漏执行
    )

    # 每日16:30 持仓检查
    scheduler.add_job(
        run_portfolio_check,
        CronTrigger(hour=16, minute=30),
        id="portfolio_check",
        name="持仓检查",
        misfire_grace_time=3600,
    )

    # 每日21:00 每日复盘
    scheduler.add_job(
        run_daily_summary,
        CronTrigger(hour=21, minute=0),
        id="daily_summary",
        name="每日复盘",
        misfire_grace_time=7200,
    )

    scheduler.start()
    logger.info("✅ 定时任务调度器已启动")


def shutdown_scheduler():
    """关闭定时任务调度器"""
    scheduler.shutdown()
    logger.info("⏹ 定时任务调度器已关闭")
