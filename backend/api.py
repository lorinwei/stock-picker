#!/usr/bin/env python3
"""
Stock Picker API — 读流水线结果 JSON，零计算即时返回
"""
import json
import os
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

RESULTS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "results.json")

app = FastAPI(
    title="StockMind Picker API",
    description="A股选股信号 — 每30分钟由流水线刷新一次",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _load_results():
    """读取流水线最近一次运行结果"""
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE) as f:
            return json.load(f)
    return None


@app.get("/")
async def root():
    return {
        "service": "StockMind Picker API",
        "docs": "/docs",
        "status": "running",
        "version": "2.0.0",
    }


@app.get("/health")
async def health():
    last = _load_results()
    return {
        "status": "ok",
        "last_update": last.get("timestamp") if last else None,
        "has_signals": len(last.get("signals", [])) > 0 if last else False,
        "time": datetime.now().isoformat(),
    }


@app.get("/api/signals")
async def get_signals():
    """获取最新选股信号"""
    data = _load_results()
    if not data:
        return {"status": "pending", "message": "流水线尚未运行，请稍后再试", "signals": []}
    return data


@app.get("/api/signals/top")
async def get_top(limit: int = 5):
    """获取排名前 N 的信号"""
    data = _load_results()
    if not data:
        return {"status": "pending", "message": "流水线尚未运行", "signals": []}
    top_signals = data.get("signals", [])[:limit]
    return {
        "timestamp": data.get("timestamp"),
        "market": data.get("market"),
        "total_screened": data.get("total_screened", 0),
        "count": len(top_signals),
        "signals": top_signals,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8800, reload=False)
