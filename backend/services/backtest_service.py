"""
回测服务 — Backtesting.py 封装
"""
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

import pandas as pd
from loguru import logger

from services.data_service import data_service
from utils.config import settings


class BacktestService:
    """回测服务"""

    def __init__(self):
        self.results_dir = settings.BACKTEST_DIR

    async def run(
        self,
        stock_code: str,
        strategy_type: str = "value_trend",
        start_date: str = None,
        end_date: str = None,
        initial_cash: float = 100000.0,
        stop_loss: float = -8.0,
        take_profit: float = 20.0,
    ) -> Dict:
        from datetime import timedelta

        if start_date is None:
            start = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")
        else:
            start = start_date
        if end_date is None:
            end = datetime.now().strftime("%Y-%m-%d")

        kline = await data_service.get_kline(stock_code, "D", 1000)
        if not kline or len(kline) < 60:
            return {"error": f"数据不足 ({len(kline) if kline else 0})"}

        df = pd.DataFrame(kline)
        df["Date"] = pd.to_datetime(df["date"])
        df = df.set_index("Date").sort_index()

        # 计算通用指标
        df["MA5"] = df["close"].rolling(5).mean()
        df["MA20"] = df["close"].rolling(20).mean()
        df["MA60"] = df["close"].rolling(60).mean()
        df["RSI"] = self._rsi(df["close"], 14)
        df["VolMA20"] = df["volume"].rolling(20).mean()

        ema12 = df["close"].ewm(span=12).mean()
        ema26 = df["close"].ewm(span=26).mean()
        df["DIF"] = ema12 - ema26
        df["DEA"] = df["DIF"].ewm(span=9).mean()
        df["MACD"] = (df["DIF"] - df["DEA"]) * 2

        # 策略信号
        if strategy_type == "value_trend":
            def signal(d):
                buy = (d["MA5"] > d["MA20"]) & (d["RSI"] < 75) & (d["RSI"] > 30) & \
                       (d["close"] > d["MA20"]) & (d["volume"] > d["VolMA20"] * 1.2)
                sell = (d["close"] < d["MA20"]) | (d["RSI"] > 85) | (d["MA5"] < d["MA20"])
                return buy, sell
        elif strategy_type == "momentum":
            def signal(d):
                h20 = d["high"].rolling(20).max().shift(1)
                buy = d["close"] > h20
                sell = d["close"] < d["close"].shift(1) * 0.95
                return buy, sell
        elif strategy_type == "breakout":
            def signal(d):
                bb_mid = d["close"].rolling(20).mean()
                bb_std = d["close"].rolling(20).std()
                buy = (d["close"] > bb_mid + 2 * bb_std) & (d["volume"] > d["VolMA20"] * 1.5)
                sell = d["close"] < bb_mid
                return buy, sell
        else:
            return {"error": f"未知策略: {strategy_type}"}

        try:
            from backtesting import Backtest, Strategy

            class S(Strategy):
                def init(self):
                    pass

                def next(self):
                    try:
                        buy, sell = signal(self.data.df)
                        idx = self.data.index[-1]
                        if buy.loc[idx]:
                            self.buy()
                        elif sell.loc[idx]:
                            self.sell()
                    except:
                        pass

            bt = Backtest(df.dropna(), S, cash=initial_cash, commission=0.003)
            result = bt.run()

            equity = pd.Series(bt._equity)
            equity.index = df.dropna().index[:len(equity)]

            equity_curve = [
                {"date": str(k.date()), "value": round(float(v), 2)}
                for k, v in equity.items()
            ]

            trades = []
            for t in result._trades:
                trades.append({
                    "entry_date": str(t.entry_time.date()) if hasattr(t, 'entry_time') else "",
                    "exit_date": str(t.exit_time.date()) if hasattr(t, 'exit_time') else "",
                    "entry_price": round(float(t.entry.price), 2),
                    "exit_price": round(float(t.exit.price), 2),
                    "pnl": round(float(t.pl), 2),
                    "return_pct": round(float(t.pl) / initial_cash * 100, 2),
                })

            rid = str(uuid.uuid4())[:8]
            record = {
                "id": rid, "stock_code": stock_code,
                "strategy_type": strategy_type, "start_date": start, "end_date": end,
                "initial_cash": initial_cash,
                "total_return": round(float(result.get("#策略收益 [%]", 0)), 2),
                "max_drawdown": round(abs(float(result.get("#最大回撤 [%]", 0))), 2),
                "win_rate": round(float(result.get("#胜率 [%]", 0)), 1),
                "num_trades": int(result.get("#交易次数", len(trades))),
                "trades": trades[:50],
                "equity_curve": equity_curve[-200:],
                "created_at": datetime.now().isoformat(),
            }

            self._save(record)
            return record
        except Exception as e:
            logger.error(f"回测失败: {e}")
            return {"error": str(e)}

    async def compare(self, stock_code: str, strategy_ids: List[str],
                      start_date: str, end_date: str, initial_cash: float = 100000.0) -> Dict:
        comparisons = []
        for sid in strategy_ids:
            r = await self.run(stock_code, sid, start_date, end_date, initial_cash)
            if "error" not in r:
                comparisons.append({
                    "id": sid, "total_return": r.get("total_return", 0),
                    "max_drawdown": r.get("max_drawdown", 0),
                    "win_rate": r.get("win_rate", 0), "num_trades": r.get("num_trades", 0),
                    "equity_curve": r.get("equity_curve", []),
                })
        return {"comparisons": comparisons}

    async def optimize(self, stock_code: str, start_date: str, end_date: str) -> Dict:
        best, best_score = None, -999
        for sl in [-5.0, -8.0, -10.0]:
            r = await self.run(stock_code, "value_trend", start_date, end_date, stop_loss=sl)
            if "error" not in r:
                score = r.get("total_return", 0) * 0.6 - r.get("max_drawdown", 0) * 0.4
                if score > best_score:
                    best_score, best = score, r
        return {"best": best, "score": round(best_score, 2)}

    async def get_history(self, limit: int = 20) -> List[Dict]:
        records = []
        for f in sorted(self.results_dir.glob("*.json"), reverse=True)[:limit]:
            with open(f) as fp:
                records.append(json.load(fp))
        return records

    async def get_record(self, record_id: str) -> Dict:
        path = self.results_dir / f"{record_id}.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        raise FileNotFoundError(f"记录 {record_id} 不存在")

    def _save(self, record: Dict):
        path = self.results_dir / f"{record['id']}.json"
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def _rsi(series: pd.Series, period: int = 14) -> pd.Series:
        delta = series.diff()
        gain = delta.clip(lower=0).rolling(period).mean()
        loss = (-delta.clip(upper=0)).rolling(period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))


backtest_service = BacktestService()
