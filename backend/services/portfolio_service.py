"""
持仓管理服务 — SQLite存储 + 盈亏计算
"""
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from utils.config import settings


class PortfolioService:
    """持仓管理"""

    def __init__(self):
        self.db_path = settings.DB_PATH
        self.initial_cash = settings.PORTFOLIO_CFG.get("initial_cash", 100000.0)
        self._init_db()

    def _conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        conn = self._conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL, name TEXT NOT NULL,
                buy_date TEXT NOT NULL, buy_price REAL NOT NULL,
                quantity INTEGER NOT NULL, cost REAL NOT NULL,
                stop_loss_price REAL, current_price REAL DEFAULT 0,
                current_value REAL DEFAULT 0, profit REAL DEFAULT 0,
                profit_pct REAL DEFAULT 0, highest_price REAL DEFAULT 0,
                industry TEXT DEFAULT '', status TEXT DEFAULT 'holding',
                notes TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS trade_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL, name TEXT NOT NULL,
                direction TEXT NOT NULL,
                buy_date TEXT, sell_date TEXT,
                buy_price REAL, sell_price REAL, quantity INTEGER,
                pnl REAL, pnl_pct REAL, reason TEXT,
                created_at TEXT DEFAULT (datetime('now','localtime'))
            )
        """)
        conn.commit()
        conn.close()

    async def get_all(self) -> List[Dict]:
        """获取持仓列表"""
        conn = self._conn()
        conn.row_factory = sqlite3.Row
        cur = conn.execute("SELECT * FROM positions WHERE status='holding' ORDER BY created_at DESC")
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    async def add(self, code: str, name: str, buy_date: str, buy_price: float, quantity: int) -> Dict:
        """添加持仓"""
        cost = buy_price * quantity
        stop_loss = round(buy_price * 0.92, 2)
        conn = self._conn()
        cur = conn.execute(
            """INSERT INTO positions
               (code, name, buy_date, buy_price, quantity, cost, stop_loss_price,
                current_price, current_value, profit, profit_pct, highest_price)
               VALUES (?,?,?,?,?,?,?,?,?,0,0,?)""",
            (code, name, buy_date, buy_price, quantity, cost, stop_loss,
             buy_price, cost, buy_price),
        )
        conn.commit()
        pid = cur.lastrowid
        conn.close()
        return {"id": pid, "code": code, "name": name, "buy_price": buy_price,
                "quantity": quantity, "cost": cost, "stop_loss_price": stop_loss}

    async def update(self, position_id: int, current_price: float = None) -> Dict:
        """更新持仓现价和盈亏"""
        if current_price is None:
            return {"updated": False}
        conn = self._conn()
        cur = conn.execute("SELECT * FROM positions WHERE id=?", (position_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return {"error": "not found"}

        quantity = row[4]
        cost = row[6]
        cur_val = round(current_price * quantity, 2)
        profit = round(cur_val - cost, 2)
        pct = round(profit / cost * 100, 2) if cost else 0
        highest = max(row[11] or 0, current_price)

        conn.execute(
            """UPDATE positions SET current_price=?, current_value=?, profit=?,
               profit_pct=?, highest_price=?, updated_at=datetime('now','localtime')
               WHERE id=?""",
            (current_price, cur_val, profit, pct, highest, position_id),
        )
        conn.commit()
        conn.close()
        return {"id": position_id, "current_price": current_price, "profit": profit, "profit_pct": pct}

    async def sell(self, position_id: int, sell_price: float, reason: str = "manual") -> Dict:
        """平仓"""
        conn = self._conn()
        cur = conn.execute("SELECT * FROM positions WHERE id=? AND status='holding'", (position_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return {"error": "持仓不存在或已平仓"}

        code, name = row[1], row[2]
        buy_price, quantity, cost = row[3], row[4], row[6]
        buy_date = row[5]
        pnl = round((sell_price - buy_price) * quantity, 2)
        pnl_pct = round(pnl / cost * 100, 2) if cost else 0

        conn.execute("UPDATE positions SET status='closed', current_price=?, current_value=?, profit=?, profit_pct=?, updated_at=datetime('now','localtime') WHERE id=?",
                     (sell_price, sell_price * quantity, pnl, pnl_pct, position_id))
        conn.execute(
            "INSERT INTO trade_history (code,name,direction,buy_date,sell_date,buy_price,sell_price,quantity,pnl,pnl_pct,reason) VALUES (?,?,'sell',?,?,?,?,?,?,?,?)",
            (code, name, buy_date, datetime.now().strftime("%Y-%m-%d"), buy_price, sell_price, quantity, pnl, pnl_pct, reason),
        )
        conn.commit()
        conn.close()
        return {"code": code, "name": name, "pnl": pnl, "pnl_pct": pnl_pct, "reason": reason}

    async def delete(self, position_id: int):
        """删除已平仓记录"""
        conn = self._conn()
        conn.execute("DELETE FROM positions WHERE id=? AND status='closed'", (position_id,))
        conn.commit()
        conn.close()

    async def get_history(self, limit: int = 50) -> List[Dict]:
        """交易历史"""
        conn = self._conn()
        conn.row_factory = sqlite3.Row
        cur = conn.execute("SELECT * FROM trade_history ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows


portfolio_service = PortfolioService()
