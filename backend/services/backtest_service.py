"""
回测服务 - Backtesting.py封装、多策略对比、参数优化
融合四大投资大师的经典策略
"""
import uuid
from datetime import datetime
from typing import List, Dict, Optional
import json

import pandas as pd
from loguru import logger

from services.data_service import DataService


class BacktestService:
    """回测服务"""

    def __init__(self):
        self.data_service = DataService()
        self._results_dir = "/root/stock-picker/backtest_results"
        import os
        os.makedirs(self._results_dir, exist_ok=True)

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
        """
        执行回测（使用Backtesting.py）
        """
        if start_date is None:
            start = (datetime.now() - pd.Timedelta(days=730)).strftime("%Y-%m-%d")
        else:
            start = start_date

        if end_date is None:
            end = datetime.now().strftime("%Y-%m-%d")

        # 获取K线数据
        kline = await self.data_service.get_kline(stock_code, "D", start, end, 1000)
        if not kline or len(kline) < 60:
            return {"error": "数据不足，无法回测"}

        df = pd.DataFrame(kline)
        df["Date"] = pd.to_datetime(df["date"])
        df = df.set_index("Date").sort_index()

        # 计算指标
        df["MA5"] = df["close"].rolling(5).mean()
        df["MA20"] = df["close"].rolling(20).mean()
        df["MA60"] = df["close"].rolling(60).mean()
        df["RSI"] = self._calc_rsi(df["close"], 14)
        df["Momentum"] = df["close"].pct_change(20)

        # MACD
        ema12 = df["close"].ewm(span=12).mean()
        ema26 = df["close"].ewm(span=26).mean()
        df["DIF"] = ema12 - ema26
        df["DEA"] = df["DIF"].ewm(span=9).mean()
        df["MACD"] = (df["DIF"] - df["DEA"]) * 2

        # ============ 策略1：价值趋势策略（融合四大大师）============
        if strategy_type == "value_trend":

            def _signal(data):
                buy = (
                    (data["MA5"] > data["MA20"]) &  # 彼得·林奇：趋势向上
                    (data["RSI"] < 75) & (data["RSI"] > 30) &  # RSI适中
                    (data["close"] > data["MA20"]) &  # 站上20日均线
                    (data["volume"] > data["volume"].rolling(20).mean() * 1.3)  # 放量
                )
                sell = (
                    (data["close"] < data["MA20"]) |  # 趋势破坏
                    (data["RSI"] > 85) |  # RSI极度超买
                    (data["MA5"] < data["MA20"])  # 均线死叉
                )
                return pd.DataFrame({"Buy": buy, "Sell": sell}, index=data.index)

        elif strategy_type == "momentum":
            # 利弗莫尔：突破买入，8%止损
            def _signal(data):
                data["High20"] = data["high"].rolling(20).max().shift(1)
                buy = data["close"] > data["High20"]
                sell = data["close"] < data["close"].shift(1) * (1 + stop_loss / 100)
                return pd.DataFrame({"Buy": buy, "Sell": sell}, index=data.index)

        elif strategy_type == "breakout":
            # 布林带突破策略
            def _signal(data):
                bb_mid = df["close"].rolling(20).mean()
                bb_std = df["close"].rolling(20).std()
                bb_upper = bb_mid + 2 * bb_std
                bb_lower = bb_mid - 2 * bb_std
                buy = (df["close"] > bb_upper) & (df["volume"] > df["volume"].rolling(10).mean() * 1.5)
                sell = df["close"] < bb_mid
                return pd.DataFrame({"Buy": buy, "Sell": sell}, index=data.index)

        else:
            _signal = None

        if _signal is None:
            return {"error": f"未知策略类型: {strategy_type}"}

        # ============ 执行回测 ============
        try:
            from backtesting import Backtest, Strategy

            class S(Strategy):
                def init(self):
                    pass

                def next(self):
                    try:
                        sig = _signal(self.data.df)
                        if sig.loc[self.data.index[-1], "Buy"]:
                            self.buy()
                        elif sig.loc[self.data.index[-1], "Sell"]:
                            self.sell()
                    except:
                        pass

            bt = Backtest(df.dropna(), S, cash=initial_cash, commission=0.003, margin=1.0)
            result = bt.run()

            # 提取结果
            equity = pd.Series(bt._equity)
            equity.index = df.dropna().index[:len(equity)]

            # 收益曲线
            equity_curve = [
                {"date": str(k.date()), "value": round(v, 2)}
                for k, v in equity.items()
            ]

            # 买卖点
            trades = []
            for i, t in enumerate(result._trades):
                trades.append({
                    "entry_date": str(t.entry_date.date()) if t.entry_date else "",
                    "entry_price": round(t.entry.price, 2),
                    "exit_date": str(t.exit_date.date()) if t.exit_date else "",
                    "exit_price": round(t.exit.price, 2),
                    "pnl": round(t.pl / initial_cash * 100, 2),
                    "pnl_abs": round(t.pl, 2),
                    "return_pct": round(t.return_pct * 100, 2) if hasattr(t, 'return_pct') else 0,
                })

            # 统计指标
            total_return = float(result["#策略收益 [%]"]) if "#策略收益 [%]" in result else 0.0
            max_drawdown = float(result.get("#最大回撤 [%]", 0)) if "#最大回撤 [%]" in result else 0.0
            win_rate = float(result["#胜率 [%]"]) if "#胜率 [%]" in result else 0.0
            num_trades = int(result.get("#交易次数", len(trades)))

            record_id = str(uuid.uuid4())[:8]
            record = {
                "id": record_id,
                "stock_code": stock_code,
                "strategy_type": strategy_type,
                "start_date": start,
                "end_date": end,
                "initial_cash": initial_cash,
                "total_return": round(total_return, 2),
                "annual_return": round(total_return / 2, 2),  # 近似年化
                "max_drawdown": round(abs(max_drawdown), 2),
                "win_rate": round(win_rate, 1),
                "num_trades": num_trades,
                "trades": trades[:50],
                "equity_curve": equity_curve[-200:],  # 限制200个点
                "created_at": datetime.now().isoformat(),
            }

            # 保存记录
            self._save_record(record)

            return record

        except Exception as e:
            logger.error(f"回测执行失败: {e}")
            return {"error": str(e)}

    async def compare(
        self,
        stock_code: str,
        strategy_ids: List[str],
        start_date: str,
        end_date: str,
        initial_cash: float = 100000.0,
    ) -> Dict:
        """多策略对比"""
        results = []
        for sid in strategy_ids:
            r = await self.run(
                stock_code=stock_code,
                strategy_type=sid,
                start_date=start_date,
                end_date=end_date,
                initial_cash=initial_cash,
            )
            if "error" not in r:
                results.append({
                    "strategy_id": sid,
                    "total_return": r.get("total_return", 0),
                    "max_drawdown": r.get("max_drawdown", 0),
                    "win_rate": r.get("win_rate", 0),
                    "num_trades": r.get("num_trades", 0),
                    "equity_curve": r.get("equity_curve", []),
                })

        return {"comparisons": results}

    async def optimize(
        self,
        stock_code: str,
        start_date: str,
        end_date: str,
    ) -> Dict:
        """参数优化（网格搜索）"""
        # 简化版：测试不同止损参数
        best_result = None
        best_score = -999

        for stop_loss in [-5.0, -8.0, -10.0, -15.0]:
            result = await self.run(
                stock_code=stock_code,
                strategy_type="value_trend",
                start_date=start_date,
                end_date=end_date,
                stop_loss=stop_loss,
            )
            if "error" not in result:
                score = result.get("total_return", 0) * 0.6 - result.get("max_drawdown", 0) * 0.4
                if score > best_score:
                    best_score = score
                    best_result = result

        return {"best": best_result, "best_score": round(best_score, 2)}

    async def get_history(self, limit: int = 20) -> List[Dict]:
        """获取历史回测记录"""
        records = []
        import os
        for fname in sorted(os.listdir(self._results_dir), reverse=True)[:limit]:
            if fname.endswith(".json"):
                with open(os.path.join(self._results_dir, fname)) as f:
                    records.append(json.load(f))
        return records

    async def get_record(self, record_id: str) -> Dict:
        """获取指定回测记录"""
        path = os.path.join(self._results_dir, f"{record_id}.json")
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
        raise FileNotFoundError(f"记录 {record_id} 不存在")

    def _save_record(self, record: Dict):
        import os
        path = os.path.join(self._results_dir, f"{record['id']}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)

    def _calc_rsi(self, series: pd.Series, period: int = 14) -> pd.Series:
        delta = series.diff()
        gain = delta.clip(lower=0).rolling(period).mean()
        loss = (-delta.clip(upper=0)).rolling(period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
