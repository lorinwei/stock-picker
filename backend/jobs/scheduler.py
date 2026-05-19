"""
定时任务调度
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

scheduler = AsyncIOScheduler()


def start_scheduler():
    from jobs.daily_pick import run_daily_pick
    from jobs.portfolio_check import run_portfolio_check
    from jobs.daily_summary import run_daily_summary

    scheduler.add_job(run_daily_pick, CronTrigger(hour=16, minute=0),
                      id="daily_pick", misfire_grace_time=3600)
    scheduler.add_job(run_portfolio_check, CronTrigger(hour=16, minute=30),
                      id="portfolio_check", misfire_grace_time=3600)
    scheduler.add_job(run_daily_summary, CronTrigger(hour=21, minute=0),
                      id="daily_summary", misfire_grace_time=7200)

    scheduler.start()
    logger.info("定时任务已启动")


def shutdown_scheduler():
    scheduler.shutdown()
    logger.info("定时任务已关闭")
