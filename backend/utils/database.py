"""
数据库工具 - SQLite初始化和健康检查
"""
import sqlite3
import aiosqlite
from pathlib import Path
from loguru import logger


async def init_database():
    """初始化数据库表"""
    db_path = Path("/root/stock-picker/data/stockmind.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(db_path) as db:
        # 持仓表
        await db.execute("""
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL,
                name TEXT NOT NULL,
                buy_date TEXT NOT NULL,
                buy_price REAL NOT NULL,
                quantity INTEGER NOT NULL,
                cost REAL NOT NULL,
                stop_loss_price REAL,
                current_price REAL,
                current_value REAL,
                profit REAL,
                profit_pct REAL,
                highest_price REAL,
                status TEXT DEFAULT 'holding',
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 交易历史表
        await db.execute("""
            CREATE TABLE IF NOT EXISTS trade_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL,
                name TEXT NOT NULL,
                direction TEXT NOT NULL,
                buy_date TEXT,
                sell_date TEXT,
                buy_price REAL,
                sell_price REAL,
                quantity INTEGER,
                pnl REAL,
                pnl_pct REAL,
                reason TEXT,
                status TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 选股信号历史表
        await db.execute("""
            CREATE TABLE IF NOT EXISTS signal_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                signal_date TEXT NOT NULL,
                rank INTEGER,
                code TEXT NOT NULL,
                name TEXT NOT NULL,
                score REAL,
                price REAL,
                suggested_position REAL,
                stop_loss_price REAL,
                entry_reasons TEXT,
                picked BOOLEAN DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.commit()
        logger.info("✅ 数据库表初始化完成")


async def check_database_health() -> bool:
    """检查数据库健康状态"""
    try:
        db_path = "/root/stock-picker/data/stockmind.db"
        async with aiosqlite.connect(db_path) as db:
            await db.execute("SELECT 1")
            return True
    except Exception as e:
        logger.error(f"数据库健康检查失败: {e}")
        return False
