"""
StockMind Backend - FastAPI Entry Point
股票智慧体量化系统后端入口
"""

import os
import sys
import yaml
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

# 导入路由
from routers import stock, picker, backtest, portfolio, ai

# 导入定时任务
from jobs import daily_pick, portfolio_check, daily_summary

# 全局配置
config = None


def load_config():
    """加载配置文件"""
    global config
    config_path = Path(__file__).parent / "config.yaml"
    
    if not config_path.exists():
        # 如果配置文件不存在，使用默认配置
        config = {
            "app": {"name": "StockMind", "version": "2.0.0", "debug": True},
            "database": {"path": "/root/stock-picker/data/stockmind.db"},
            "portfolio": {"initial_cash": 100000.0},
        }
        return config
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    return config


def setup_logging(config):
    """配置日志"""
    log_config = config.get("logging", {})
    level = log_config.get("level", "INFO")
    
    # 移除默认处理器
    logger.remove()
    
    # 添加控制台输出
    logger.add(
        sink=sys.stdout,
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    )
    
    # 添加文件输出
    log_file = log_config.get("file", "/root/stock-picker/data/logs/app.log")
    log_dir = Path(log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logger.add(
        sink=log_file,
        level=level,
        rotation="1 day",
        retention=log_config.get("rotation_days", 30),
        encoding="utf-8",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    )


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例"""
    global config
    config = load_config()
    
    # 配置日志
    setup_logging(config)
    
    # 创建应用
    app = FastAPI(
        title=f"{config['app']['name']} API",
        description="股票智慧体量化系统后端API",
        version=config["app"]["version"],
        debug=config["app"].get("debug", False),
    )
    
    # 配置 CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 生产环境应限制
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 注册路由
    app.include_router(stock.router, prefix="/api/stock", tags=["股票数据"])
    app.include_router(picker.router, prefix="/api/picker", tags=["智能选股"])
    app.include_router(backtest.router, prefix="/api/backtest", tags=["策略回测"])
    app.include_router(portfolio.router, prefix="/api/portfolio", tags=["持仓管理"])
    app.include_router(ai.router, prefix="/api/ai", tags=["AI策略引擎"])
    
    @app.on_event("startup")
    async def startup_event():
        """应用启动时执行"""
        logger.info(f"🚀 {config['app']['name']} v{config['app']['version']} 启动中...")
        
        # 确保数据目录存在
        data_dir = Path("/root/stock-picker/data")
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化数据库
        from utils.database import init_database
        await init_database()
        logger.info("✅ 数据库初始化完成")
        
        # 启动定时任务调度器
        from jobs.scheduler import start_scheduler, shutdown_scheduler
        start_scheduler()
        logger.info("✅ 定时任务调度器已启动")
        
        logger.info(f"✅ {config['app']['name']} 启动完成！")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """应用关闭时执行"""
        logger.info("🔄 正在关闭应用...")
        from jobs.scheduler import shutdown_scheduler
        shutdown_scheduler()
        logger.info("👋 应用已关闭")
    
    @app.get("/")
    async def root():
        """根路径 - 健康检查"""
        return {
            "name": config["app"]["name"],
            "version": config["app"]["version"],
            "status": "running",
            "docs": "/docs"
        }
    
    @app.get("/health")
    async def health_check():
        """健康检查"""
        from utils.database import check_database_health
        db_healthy = await check_database_health()
        
        return {
            "status": "healthy" if db_healthy else "degraded",
            "database": "connected" if db_healthy else "disconnected",
        }
    
    return app


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=config["app"].get("host", "0.0.0.0"),
        port=config["app"].get("port", 8000),
        reload=config["app"].get("debug", True),
        log_level="info"
    )