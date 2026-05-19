#!/usr/bin/env python3
"""
选股流水线定时执行器
跑完存 results.json，供 FastAPI 读取
"""
import asyncio
import json
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from services.picker_service import PickerService

RESULTS_FILE = "/root/stock-picker/data/results.json"
LOCK_FILE = "/tmp/stockpicker.lock"


async def run():
    # 防重入
    if os.path.exists(LOCK_FILE):
        with open(LOCK_FILE) as f:
            pid = f.read().strip()
        if os.path.exists(f"/proc/{pid}"):
            print(f"[{datetime.now()}] ⏭ 上次流水线还在跑 (PID {pid})，跳过")
            return
        os.remove(LOCK_FILE)

    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))

    try:
        print(f"[{datetime.now()}] 🚀 启动选股流水线...")
        ps = PickerService()
        result = await ps.generate_signals()

        # 精简输出（去重数据节省空间）
        output = {
            "timestamp": datetime.now().isoformat(),
            "date": result.get("date"),
            "market": result.get("market"),
            "total_screened": result.get("total_screened", 0),
            "signals": result.get("signals", []),
            "pool_sizes": {
                "价值池": result.get("pool_a_size", 0),
                "趋势池": result.get("pool_b_size", 0),
                "资金池": result.get("pool_c_size", 0),
            }
        }
        print(f"[{datetime.now()}] ✅ 完成 | 信号: {len(output['signals'])}只")

        os.makedirs(os.path.dirname(RESULTS_FILE), exist_ok=True)
        with open(RESULTS_FILE, "w") as f:
            json.dump(output, f, ensure_ascii=False, indent=2, default=str)
        print(f"[{datetime.now()}] 💾 已保存 → {RESULTS_FILE}")

    except Exception as e:
        print(f"[{datetime.now()}] ❌ 流水线失败: {type(e).__name__}: {e}")
    finally:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)


if __name__ == "__main__":
    asyncio.run(run())
