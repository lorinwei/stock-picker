"""
数据服务 - akshare封装、缓存、资金流向
"""
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any

import akshare as ak
import pandas as pd
from loguru import logger

from utils.cache import cache


class DataService:
    """数据服务封装，提供数据获取 + 缓存 + 重试"""

    def __init__(self):
        self._cache = cache

    async def get_stock_list(self) -> List[Dict]:
        """获取A股股票列表"""
        cache_key = "stock_list"
        cached = self._cache.get(cache_key)
        if cached:
            return cached

        try:
            df = ak.stock_info_a_code_name()
            result = df.to_dict("records")
            self._cache.set(cache_key, result, ttl=86400)
            return result
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return []

    async def get_stock_info(self, code: str) -> Dict:
        """获取股票基本信息"""
        cache_key = f"stock_info_{code}"
        cached = self._cache.get(cache_key)
        if cached:
            return cached

        try:
            # 实时行情
            df_today = ak.stock_zh_a_spot_em()
            row = df_today[df_today["代码"] == code]
            if row.empty:
                raise ValueError(f"股票 {code} 不存在")

            info = {
                "code": code,
                "name": row.iloc[0].get("名称", ""),
                "industry": row.iloc[0].get("行业", ""),
                "price": float(row.iloc[0].get("最新价", 0)),
                "change_pct": float(row.iloc[0].get("涨跌幅", 0)),
                "volume": float(row.iloc[0].get("成交量", 0)),
                "amount": float(row.iloc[0].get("成交额", 0)),
            }

            # 尝试获取财务数据
            try:
                financials = await self._get_financials(code)
                info.update(financials)
            except:
                pass

            self._cache.set(cache_key, info, ttl=3600)
            return info

        except Exception as e:
            logger.error(f"获取股票 {code} 信息失败: {e}")
            return {"code": code, "name": "未知", "error": str(e)}

    async def get_kline(
        self,
        code: str,
        ktype: str = "D",
        start: str = None,
        end: str = None,
        limit: int = 500,
    ) -> List[Dict]:
        """获取K线数据"""
        cache_key = f"kline_{code}_{ktype}_{start}_{end}"
        cached = self._cache.get(cache_key)
        if cached:
            return cached

        retry = 3
        for attempt in range(retry):
            try:
                if end is None:
                    end = datetime.now().strftime("%Y%m%d")
                if start is None:
                    start_dt = datetime.now() - timedelta(days=limit * 2)
                    start = start_dt.strftime("%Y%m%d")

                # akshare 日线数据
                df = ak.stock_zh_a_hist(
                    symbol=code,
                    period="daily",
                    start_date=start.replace("-", ""),
                    end_date=end.replace("-", ""),
                    adjust="qfq",
                )

                # 列名标准化
                df = df.rename(columns={
                    "日期": "date",
                    "开盘": "open",
                    "收盘": "close",
                    "最高": "high",
                    "最低": "low",
                    "成交量": "volume",
                    "成交额": "amount",
                    "涨跌幅": "change_pct",
                    "换手率": "turnover",
                })

                df = df.sort_values("date")
                data = df.tail(limit).to_dict("records")

                self._cache.set(cache_key, data, ttl=900)  # 15分钟缓存
                return data

            except Exception as e:
                logger.warning(f"获取K线失败(尝试 {attempt+1}/{retry}): {e}")
                if attempt < retry - 1:
                    await asyncio.sleep(2)
                else:
                    return []

    async def get_technical_indicators(self, code: str, indicators: List[str]) -> Dict:
        """计算技术指标"""
        # 获取K线数据
        kline = await self.get_kline(code, limit=250)
        if not kline:
            return {}

        df = pd.DataFrame(kline)
        result = {"code": code}

        ma_periods = [5, 10, 20, 60]
        for p in ma_periods:
            if len(df) >= p:
                df[f"ma{p}"] = df["close"].rolling(p).mean()
                result[f"ma{p}"] = round(float(df[f"ma{p}"].iloc[-1]), 2)

        # MACD
        if len(df) >= 26:
            ema12 = df["close"].ewm(span=12).mean()
            ema26 = df["close"].ewm(span=26).mean()
            dif = ema12 - ema26
            dea = dif.ewm(span=9).mean()
            macd = (dif - dea) * 2
            result["macd_dif"] = round(float(dif.iloc[-1]), 4)
            result["macd_dea"] = round(float(dea.iloc[-1]), 4)
            result["macd_bar"] = round(float(macd.iloc[-1]), 4)

        # RSI
        if len(df) >= 14:
            delta = df["close"].diff()
            gain = delta.clip(lower=0).rolling(14).mean()
            loss = (-delta.clip(upper=0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            result["rsi_14"] = round(float(rsi.iloc[-1]), 2)

        # KDJ
        if len(df) >= 9:
            low9 = df["low"].rolling(9).min()
            high9 = df["high"].rolling(9).max()
            rsv = (df["close"] - low9) / (high9 - low9) * 100
            result["kdj_k"] = round(float(rsv.ewm(com=2).mean().iloc[-1]), 2)
            result["kdj_d"] = round(float(rsv.ewm(com=2).mean().ewm(com=2).mean().iloc[-1]), 2)
            result["kdj_j"] = round(
                float(3 * float(result["kdj_k"]) - 2 * float(result["kdj_d"])), 2
            )

        # BOLL
        if len(df) >= 20:
            bb = df["close"].rolling(20).mean()
            bb_std = df["close"].rolling(20).std()
            result["boll_upper"] = round(float((bb + 2 * bb_std).iloc[-1]), 2)
            result["boll_mid"] = round(float(bb.iloc[-1]), 2)
            result["boll_lower"] = round(float((bb - 2 * bb_std).iloc[-1]), 2)

        # 动量
        if len(df) >= 20:
            result["momentum_20d"] = round(float((df["close"].iloc[-1] / df["close"].iloc[-20] - 1) * 100), 2)
        if len(df) >= 5:
            result["momentum_5d"] = round(float((df["close"].iloc[-1] / df["close"].iloc[-5] - 1) * 100), 2)

        # 成交量均线
        if len(df) >= 20:
            result["vol_ma20"] = round(float(df["volume"].tail(20).mean()), 0)
            result["vol_ratio"] = round(float(df["volume"].iloc[-1] / df["volume"].tail(20).mean()), 2)

        return result

    async def get_money_flow(self, code: str) -> Dict:
        """获取资金流向"""
        cache_key = f"moneyflow_{code}"
        cached = self._cache.get(cache_key)
        if cached:
            return cached

        try:
            df = ak.stock_individual_fund_flow(stock=code, market="sh" if code.startswith("6") else "sz")
            result = {
                "code": code,
                "north_net": float(df["主力净流入净额"].iloc[-1]) if len(df) > 0 else 0,
                "north_net_pct": float(df["主力净流入净额占比"].iloc[-1]) if len(df) > 0 else 0,
                "date": df["日期"].iloc[-1] if len(df) > 0 else "",
            }
            self._cache.set(cache_key, result, ttl=1800)
            return result
        except Exception as e:
            logger.warning(f"获取资金流向失败 {code}: {e}")
            return {"code": code, "north_net": 0, "north_net_pct": 0}

    async def get_market_status(self) -> Dict:
        """判断牛熊市场状态（沪深300 vs 20周均线）"""
        cache_key = "market_status"
        cached = self._cache.get(cache_key)
        if cached:
            return cached

        try:
            # 获取沪深300数据（周线）
            df = ak.stock_zh_a_hist(
                symbol="000300",
                period="weekly",
                start_date=(datetime.now() - timedelta(days=500)).strftime("%Y%m%d"),
                end_date=datetime.now().strftime("%Y%m%d"),
                adjust="qfq",
            )

            df = df.sort_values("日期")
            current_price = float(df["收盘"].iloc[-1])
            ma20_weeks = float(df["收盘"].tail(20).mean())
            change_20w = (current_price / df["收盘"].tail(20).iloc[0] - 1) * 100

            # 判断状态
            if current_price > ma20_weeks and change_20w > 0:
                status = "bull"  # 牛市
            elif current_price < ma20_weeks and change_20w < -5:
                status = "bear"  # 熊市
            else:
                status = "oscillate"  # 震荡

            result = {
                "status": status,
                "status_text": {"bull": "🐂 牛市", "bear": "🐻 熊市", "oscillate": "⚖️ 震荡"}.get(status, "未知"),
                "hs300_price": current_price,
                "ma20_weeks": round(ma20_weeks, 2),
                "change_20w": round(change_20w, 2),
                "position_limit": {"bull": 0.8, "bear": 0.2, "oscillate": 0.4}.get(status, 0.5),
            }

            self._cache.set(cache_key, result, ttl=86400)
            return result

        except Exception as e:
            logger.error(f"获取市场状态失败: {e}")
            return {"status": "oscillate", "status_text": "⚖️ 震荡（获取失败）", "position_limit": 0.4}

    async def get_industry_leaderboard(self) -> Dict:
        """获取行业涨跌榜"""
        cache_key = "industry_leaderboard"
        cached = self._cache.get(cache_key)
        if cached:
            return cached

        try:
            df = ak.stock_board_industry_name_em()
            df = df.sort_values("涨跌幅", ascending=False)
            result = {
                "leaders": df.head(5)[["板块名称", "涨跌幅", "总市值"]].to_dict("records"),
                "laggers": df.tail(5)[["板块名称", "涨跌幅", "总市值"]].to_dict("records"),
            }
            self._cache.set(cache_key, result, ttl=1800)
            return result
        except Exception as e:
            logger.error(f"获取行业排行失败: {e}")
            return {"leaders": [], "laggers": []}

    async def _get_financials(self, code: str) -> Dict:
        """获取财务数据（内部使用）"""
        try:
            df = ak.stock_financial_analysis_indicator(
                symbol=code, start_year=str(datetime.now().year - 2)
            )
            latest = df.iloc[0]
            return {
                "roe": float(latest.get("净资产收益率(%)", 0) or 0),
                "pe": float(latest.get("市盈率(动)", 0) or 0),
                "pb": float(latest.get("市净率(MRQ)", 0) or 0),
                "debt_ratio": float(latest.get("资产负债率(%)", 0) or 0),
            }
        except:
            return {}
