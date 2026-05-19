"""
StockMind v3 — FastAPI 入口（自托管前端）
"""
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from loguru import logger

from utils.config import settings

from routers import stock, picker, backtest, portfolio, ai, chan


def setup_logging():
    logger.remove()
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format="<green>{time:HH:mm:ss}</green> | <level>{level:<7}</level> | <cyan>{name}</cyan> <level>{message}</level>",
    )
    logger.add(
        settings.LOG_FILE,
        level=settings.LOG_LEVEL,
        rotation="1 day",
        retention=30,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level:<7} | {name}:{line} | {message}",
    )


def create_app() -> FastAPI:
    setup_logging()
    logger.info(f"  {settings.APP_NAME} v{settings.APP_VERSION} starting ...")
    logger.info(f"  数据目录: {settings.DATA_DIR}")
    logger.info(f"  数据库: {settings.DB_PATH}")

    app = FastAPI(
        title=f"{settings.APP_NAME}",
        docs_url=None,
        redoc_url=None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── API 路由 ──
    app.include_router(stock.router, prefix="/api")
    app.include_router(picker.router, prefix="/api")
    app.include_router(backtest.router, prefix="/api")
    app.include_router(portfolio.router, prefix="/api")
    app.include_router(ai.router, prefix="/api")
    app.include_router(chan.router, prefix="/api")

    # ── 前端静态文件 ──
    frontend_dist = settings.PROJECT_ROOT / "frontend" / "dist"
    if frontend_dist.exists():
        app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")
        logger.info(f"  前端静态资源: {frontend_dist}")

        # 健康检查
        @app.get("/api/health")
        async def api_health():
            return {"status": "ok", "service": "stockmind"}

        # SPA catch-all: 仅匹配非 /api 路径
        from fastapi.responses import JSONResponse

        @app.get("/{full_path:path}", include_in_schema=False)
        async def serve_frontend(full_path: str):
            # /api/* 路径没有匹配路由时返回 JSON 404
            if full_path.startswith("api/"):
                return JSONResponse({"error": "API endpoint not found"}, status_code=404)
            index_path = frontend_dist / "index.html"
            if index_path.exists():
                return FileResponse(str(index_path))
            return JSONResponse({"error": "frontend not built"}, status_code=500)
    else:
        logger.warning("  ⚠️ 前端未构建，请运行 cd frontend && npm run build")
        # 没有前端时返回简单提示
        @app.get("/")
        async def root():
            return {"name": settings.APP_NAME, "version": settings.APP_VERSION, "status": "running", "note": "请运行 cd frontend && npm run build 构建前端"}

    # ── 启动事件 ──
    @app.on_event("startup")
    async def startup():
        from utils.database import init_database
        await init_database()
        from jobs.scheduler import start_scheduler
        start_scheduler()
        logger.info(f"✅ {settings.APP_NAME} 启动完成  http://localhost:{settings.PORT}")

    @app.on_event("shutdown")
    async def shutdown():
        from jobs.scheduler import shutdown_scheduler
        shutdown_scheduler()
        logger.info("应用已关闭")

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
