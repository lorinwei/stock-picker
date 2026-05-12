"""
持仓管理服务 - CRUD、盈亏计算、交易历史
"""
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

import yaml


class PortfolioService:
    """持仓管理服务（SQLite存储）"""

    def __init__(self):
        config = self._load_config()
        self.db_path = config.get("database", {}).get("path", "/root/stock-picker/data/stockmind.db")
        self.initial_cash = config.get("portfolio", {}).get("initial_cash", 100000.0)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _load_config(self) -> Dict:
        cfg_path = Path(__file__).parent.parent / "config.yaml"
        if cfg_path.exists():
            with open(cfg_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """初始化数据库表"""
        conn = self._get_conn()
        conn.execute("""
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
        conn.execute("""
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
        conn.commit()
        conn.close()

    async def get_all(self) -> List[Dict]:
        """获取所有持仓"""
        conn = self._get_conn()
        conn.row_factory = sqlite3.Row
        cur = conn.execute(
            "SELECT * FROM positions WHERE status='holding' ORDER BY created_at DESC"
        )
        rows = cur.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    async def add(self, req) -> Dict:
        """添加持仓"""
        cost = req.buy_price * req.quantity
        stop_loss = req.stop_loss_price or round(req.buy_price * 0.92, 2)

        conn = self._get_conn()
        cur = conn.execute(
            """INSERT INTO positions
               (code, name, buy_date, buy_price, quantity, cost, stop_loss_price, current_price, current_value, profit, profit_pct, highest_price, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                req.code, req.name, req.buy_date, req.buy_price, req.quantity,
                cost, stop_loss, req.buy_price, cost, 0.0, 0.0, req.buy_price, "holding",
            ),
        )
        conn.commit()
        position_id = cur.lastrowid
        conn.close()

        return {
            "id": position_id,
            "code": req.code,
            "name": req.name,
            "buy_date": req.buy_date,
            "buy_price": req.buy_price,
            "quantity": req.quantity,
            "cost": cost,
            "stop_loss_price": stop_loss,
        }

    async def update(self, position_id: str, req) -> Dict:
        """更新持仓（如更新当前价）"""
        updates = []
        params = []
        if req.current_price is not None:
            updates.append("current_price = ?")
            params.append(req.current_price)
        if req.notes is not None:
            updates.append("notes = ?")
            params.append(req.notes)

        if req.current_price is not None:
            conn = self._get_conn()
            cur = conn.execute(
                f"SELECT * FROM positions WHERE id=?", (position_id,)
            )
            row = cur.fetchone()
            if row:
                current_value = req.current_price * row[4]  # quantity
                profit = current_value - row[6]  # cost
                profit_pct = profit / row[6] * 100
                highest = max(row[11] or 0, req.current_price)  # highest_price

                updates.extend([
                    "current_value = ?",
                    "profit = ?",
                    "profit_pct = ?",
                    "highest_price = ?",
                    "updated_at = CURRENT_TIMESTAMP",
                ])
                params.extend([current_value, profit, profit_pct, highest])

        params.append(position_id)
        conn = self._get_conn()
        conn.execute(f"UPDATE positions SET {', '.join(updates)} WHERE id=?", params)
        conn.commit()
        conn.close()

        return {"id": position_id, "updated": True}

    async def sell(self, position_id: str, req) -> Dict:
        """平仓"""
        conn = self._get_conn()
        cur = conn.execute("SELECT * FROM positions WHERE id=? AND status='holding'", (position_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return {"error": "持仓不存在或已平仓"}

        code, name = row[1], row[2]
        buy_price = row[3]
        quantity = row[4]
        cost = row[6]
        sell_price = req.sell_price
        pnl = (sell_price - buy_price) * quantity
        pnl_pct = pnl / cost * 100

        # 更新持仓为已平仓
        conn.execute(
            "UPDATE positions SET status='closed', current_price=?, current_value=?, profit=?, profit_pct=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (sell_price, sell_price * quantity, pnl, pnl_pct, position_id),
        )

        # 写入交易历史
        conn.execute(
            """INSERT INTO trade_history
               (code, name, direction, buy_date, sell_date, buy_price, sell_price, quantity, pnl, pnl_pct, reason, status)
               VALUES (?, ?, 'sell', ?, ?, ?, ?, ?, ?, ?, ?, 'closed')""",
            (code, name, row[3], req.sell_date, buy_price, sell_price, quantity, pnl, pnl_pct, req.reason),
        )
        conn.commit()
        conn.close()

        return {
            "code": code,
            "name": name,
            "buy_price": buy_price,
            "sell_price": sell_price,
            "quantity": quantity,
            "pnl": round(pnl, 2),
            "pnl_pct": round(pnl_pct, 2),
            "reason": req.reason,
        }

    async def delete(self, position_id: str):
        """删除持仓记录"""
        conn = self._get_conn()
        conn.execute("DELETE FROM positions WHERE id=? AND status='closed'", (position_id,))
        conn.commit()
        conn.close()

    async def get_history(self, limit: int = 50) -> List[Dict]:
        """获取交易历史"""
        conn = self._get_conn()
        conn.row_factory = sqlite3.Row
        cur = conn.execute(
            "SELECT * FROM trade_history ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        rows = cur.fetchall()
        conn.close()
        return [dict(r) for r in rows]
