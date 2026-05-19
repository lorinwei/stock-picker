"""
数据库工具 — 使用 aiosqlite，路径从 config 自动获取
"""
import aiosqlite
from loguru import logger
from utils.config import settings


async def init_database():
    """初始化数据库表"""
    db_path = settings.DB_PATH
    logger.info(f"初始化数据库: {db_path}")

    async with aiosqlite.connect(db_path) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA foreign_keys=ON")

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
                current_price REAL DEFAULT 0,
                current_value REAL DEFAULT 0,
                profit REAL DEFAULT 0,
                profit_pct REAL DEFAULT 0,
                highest_price REAL DEFAULT 0,
                status TEXT DEFAULT 'holding',
                notes TEXT,
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime'))
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
                created_at TEXT DEFAULT (datetime('now','localtime'))
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
                buy_point_type TEXT,
                price REAL,
                suggested_position REAL,
                stop_loss_price REAL,
                entry_reasons TEXT,
                picked BOOLEAN DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now','localtime'))
            )
        """)

        await db.commit()
        logger.info("数据库表初始化完成")


async def check_database_health() -> bool:
    """检查数据库健康状态"""
    try:
        async with aiosqlite.connect(settings.DB_PATH) as db:
            await db.execute("SELECT 1")
            return True
    except Exception as e:
        logger.error(f"数据库健康检查失败: {e}")
        return False
