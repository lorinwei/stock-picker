"""
数据服务 — 统一数据获取层

数据源架构（优先顺序）：
  实时行情:  腾讯行情API (qt.gtimg.cn)   ← 最快最稳
  K线:      新浪财经API                   ← 免费且稳定
  财务数据:  akshare                      ← 慢但全
  资金流向:  akshare                      ← 慢但全

所有获取自动缓存 + 超时重试 + 降级
"""
import asyncio
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

import akshare as ak
import httpx
import pandas as pd
from loguru import logger

from utils.cache import get as cache_get, set as cache_set


class DataService:
    """统一数据服务 — 自动缓存 + 超时重试"""

    # K线 scale 映射
    SINA_SCALE = {"5": 5, "15": 15, "30": 30, "60": 60, "D": 240, "W": 1000, "M": 4000}

    def __init__(self):
        self._http = httpx.AsyncClient(timeout=15, limits=httpx.Limits(max_keepalive_connections=20))

    # ──────────────── 实时行情（腾讯API）───────────────

    async def get_stock_info(self, code: str) -> Dict:
        """获取单只股票实时行情 + 基础财务"""
        cleaned = code.replace("sh", "").replace("sz", "").replace("SH", "").replace("SZ", "")
        # 补前缀
        if not code.startswith(("sh", "sz", "SH", "SZ")):
            prefix = "sh" if cleaned.startswith(("5", "6", "9")) else "sz"
            code = prefix + cleaned

        cache_key = f"info_{code}"
        cached = cache_get(cache_key)
        if cached:
            return cached

        try:
            url = f"https://qt.gtimg.cn/q={code}"
            resp = await self._http.get(url, timeout=10)
            text = resp.text.strip()
            if not text or "=" not in text:
                raise ValueError(f"腾讯返回空: {text[:100]}")

            parts = text.split("~")
            if len(parts) < 40:
                raise ValueError(f"腾讯格式异常")

            name = self._clean(parts[1])
            price = self._safe_float(parts[3])
            prev_close = self._safe_float(parts[4]) or price
            change_pct = round((price - prev_close) / prev_close * 100, 2) if prev_close else 0
            pe = self._safe_float(parts[39])
            mkt_cap = self._safe_float(parts[44])  # 流通市值(亿)
            total_mkt = self._safe_float(parts[45])
            turnover = self._safe_float(parts[38])
            high = self._safe_float(parts[33]) or price
            low = self._safe_float(parts[34]) or price
            open_p = self._safe_float(parts[5]) or price
            vol = self._safe_float(parts[6])  # 手
            amount = self._safe_float(parts[37])

            info = {
                "code": code, "name": name, "price": price,
                "open": open_p, "high": high, "low": low,
                "prev_close": prev_close, "change_pct": change_pct,
                "volume": int(vol * 100), "amount": amount,
                "turnover": turnover, "pe": pe,
                "market_cap": mkt_cap, "total_market_cap": total_mkt,
            }

            # 尝试补充财务数据（静默失败）
            fin = await self._get_financials(cleaned)
            if fin:
                info.update(fin)
                info["pb"] = fin.get("pb", 0)
                info["roe"] = fin.get("roe", 0)
                info["debt_ratio"] = fin.get("debt_ratio", 0)

            cache_set(cache_key, info, ttl=3600)
            return info

        except Exception as e:
            logger.warning(f"行情获取失败 {code}: {e}")
            return {"code": code, "name": "", "price": 0, "error": str(e)}

    # ──────────────── 股票列表 ───────────────

    async def get_stock_list(self, top_n: int = 800) -> List[Dict]:
        """获取活跃股票列表（按成交额排序）"""
        cached = cache_get("stock_list_active")
        if cached:
            return cached

        try:
            url = ("https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/"
                   f"Market_Center.getHQNodeData?page=1&num={top_n}&sort=amount&asc=0&node=hs_a")
            resp = await self._http.get(url, timeout=20)
            raw = resp.json()
            if not raw or not isinstance(raw, list):
                raise ValueError(f"格式错误")

            result = []
            for item in raw:
                sym = item.get("symbol", "")
                code = ("sh" if sym.startswith(("5", "6", "9")) else "sz") + sym
                result.append({
                    "code": code,
                    "name": self._clean(item.get("name", "")),
                    "price": self._safe_float(item.get("trade", 0)),
                    "change_pct": self._safe_float(item.get("changepercent", 0)),
                    "amount": self._safe_float(item.get("amount", 0)),
                    "market_cap": self._safe_float(item.get("mktcap", 0)) / 1e8,
                    "turnover": self._safe_float(item.get("turnoverratio", 0)),
                })

            cache_set("stock_list_active", result, ttl=86400)
            return result
        except Exception as e:
            logger.error(f"股票列表获取失败: {e}")
            return []

    # ──────────────── K线数据（新浪API）───────────────

    async def get_kline(self, code: str, ktype: str = "D", limit: int = 500) -> List[Dict]:
        """获取K线数据"""
        cache_key = f"kl_{code}_{ktype}_{limit}"
        cached = cache_get(cache_key)
        if cached:
            return cached

        # ── Sina 使用 sh600519 / sz000001 / sh000300 格式 ──
        # 如果 code 已有前缀，保留原始前缀
        if code.startswith(("sh", "sz", "SH", "SZ")):
            symbol = code.lower()
        else:
            raw = code.replace("sh", "").replace("sz", "").strip()
            if raw.startswith(("5", "6", "9")):
                symbol = "sh" + raw
            elif raw.startswith(("0", "3")):
                # 000xxx / 001xxx / 002xxx / 003xxx 是深市
                # 但 000300(沪深300) 是沪市指数, 399xxx 是深市指数
                if raw in ("000300", "000001", "000016", "000688", "000905"):
                    symbol = "sh" + raw
                else:
                    symbol = "sz" + raw
            else:
                symbol = "sh" + raw

        scale = self.SINA_SCALE.get(ktype, 240)
        datalen = limit if ktype == "D" else min(limit * 3, 1500)

        for attempt in range(3):
            try:
                url = (f"https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/"
                       f"CN_MarketData.getKLineData?symbol={symbol_final}&scale={scale}&datalen={datalen}")
                resp = await self._http.get(url, timeout=15)
                data = resp.json()
                if not data or not isinstance(data, list):
                    raise ValueError(f"新浪返回空")

                records = []
                for item in data:
                    day = item.get("day", "")[:10]
                    close_v = self._safe_float(item.get("close", 0))
                    records.append({
                        "date": day,
                        "open": self._safe_float(item.get("open", 0)),
                        "close": close_v,
                        "high": self._safe_float(item.get("high", 0)),
                        "low": self._safe_float(item.get("low", 0)),
                        "volume": int(self._safe_float(item.get("volume", 0))),
                    })
                records = records[-limit:]
                cache_set(cache_key, records, ttl=300)
                return records

            except Exception as e:
                logger.warning(f"K线失败({attempt+1}/3) {code}: {e}")
                if attempt < 2:
                    await asyncio.sleep(1.5)

        return []

    # ──────────────── 技术指标计算 ───────────────

    async def get_technical_indicators(self, code: str) -> Dict:
        """批量计算技术指标（基于K线数据）"""
        kline = await self.get_kline(code, limit=250)
        if not kline or len(kline) < 30:
            return {}

        df = pd.DataFrame(kline)
        result = {"code": code}

        # MA
        for p in [5, 10, 20, 60]:
            if len(df) >= p:
                df[f"ma{p}"] = df["close"].rolling(p).mean()
                result[f"ma{p}"] = round(float(df[f"ma{p}"].iloc[-1]), 2)

        # MACD
        if len(df) >= 26:
            e12 = df["close"].ewm(span=12).mean()
            e26 = df["close"].ewm(span=26).mean()
            dif = e12 - e26
            dea = dif.ewm(span=9).mean()
            macd = (dif - dea) * 2
            result["macd_dif"] = round(float(dif.iloc[-1]), 4)
            result["macd_dea"] = round(float(dea.iloc[-1]), 4)
            result["macd_bar"] = round(float(macd.iloc[-1]), 4)

        # RSI(14)
        if len(df) >= 15:
            delta = df["close"].diff()
            gain = delta.clip(lower=0).rolling(14).mean()
            loss = (-delta.clip(upper=0)).rolling(14).mean()
            rs = gain / loss
            result["rsi_14"] = round(float((100 - 100 / (1 + rs)).iloc[-1]), 2)

        # KDJ
        if len(df) >= 9:
            l9 = df["low"].rolling(9).min()
            h9 = df["high"].rolling(9).max()
            rsv = (df["close"] - l9) / (h9 - l9).replace(0, 0.001) * 100
            k = rsv.ewm(com=2).mean()
            d = k.ewm(com=2).mean()
            result["kdj_k"] = round(float(k.iloc[-1]), 2)
            result["kdj_d"] = round(float(d.iloc[-1]), 2)
            result["kdj_j"] = round(float(3 * k.iloc[-1] - 2 * d.iloc[-1]), 2)

        # BOLL
        if len(df) >= 20:
            mid = df["close"].rolling(20).mean()
            std = df["close"].rolling(20).std()
            result["boll_mid"] = round(float(mid.iloc[-1]), 2)
            result["boll_upper"] = round(float((mid + 2 * std).iloc[-1]), 2)
            result["boll_lower"] = round(float((mid - 2 * std).iloc[-1]), 2)

        # 动量
        if len(df) >= 20:
            result["momentum_20d"] = round(float((df["close"].iloc[-1] / df["close"].iloc[-20] - 1) * 100), 2)
        if len(df) >= 5:
            result["momentum_5d"] = round(float((df["close"].iloc[-1] / df["close"].iloc[-5] - 1) * 100), 2)

        # 成交量比
        if len(df) >= 20:
            vol_ma20 = df["volume"].tail(20).mean()
            result["vol_ratio"] = round(float(df["volume"].iloc[-1] / vol_ma20), 2) if vol_ma20 else 1

        return result

    # ──────────────── 资金流向（akshare）───────────────

    async def get_money_flow(self, code: str) -> Dict:
        """获取主力资金流向"""
        cache_key = f"mf_{code}"
        cached = cache_get(cache_key)
        if cached:
            return cached

        raw = code.replace("sh", "").replace("sz", "").replace("SH", "").replace("SZ", "")
        market = "sh" if raw.startswith(("5", "6", "9")) else "sz"

        try:
            loop = asyncio.get_event_loop()
            df = await asyncio.wait_for(
                loop.run_in_executor(None, lambda: ak.stock_individual_fund_flow(stock=raw, market=market)),
                timeout=20
            )
            if df is None or df.empty:
                raise ValueError("空数据")

            cols = df.columns.tolist()
            # akshare 字段名可能变化，自适应
            net_col = [c for c in cols if "净额" in c or "净流入" in c]
            pct_col = [c for c in cols if "占比" in c or "净流入" in c]

            net_amount = float(df.iloc[-1][net_col[0]]) if net_col else 0
            net_3d = sum(float(df.iloc[i][net_col[0]]) for i in range(-3, 0)) if net_col and len(df) >= 3 else 0

            result = {
                "code": code,
                "main_net": net_amount,
                "main_net_pct": float(df.iloc[-1][pct_col[0]]) if pct_col else 0,
                "net_3d": net_3d,
                "date": str(df.iloc[-1]["日期"]) if "日期" in cols else "",
            }
            cache_set(cache_key, result, ttl=1800)
            return result
        except Exception as e:
            logger.debug(f"资金流不可用 {code}: {e}")
            return {"code": code, "main_net": 0, "net_3d": 0}

    # ──────────────── 市场状态 ───────────────

    async def get_market_status(self) -> Dict:
        """判断牛熊市场状态 — 优先用沪深300K线，失败则用实时价+简单判断"""
        cached = cache_get("market_status")
        if cached:
            return cached

        # 法1: 从K线计算（需要新浪API支持）
        daily = await self.get_kline("sh000300", ktype="D", limit=150)
        if daily and len(daily) >= 100:
            df = pd.DataFrame(daily)
            cur = float(df["close"].iloc[-1])
            ma100 = float(df["close"].tail(100).mean())
            chg20w = (cur / df["close"].iloc[-100] - 1) * 100
            if cur > ma100 and chg20w > 0:
                status = "bull"; pos_limit = 0.8; desc = "牛市"
            elif cur < ma100 and chg20w < -5:
                status = "bear"; pos_limit = 0.2; desc = "熊市"
            else:
                status = "oscillate"; pos_limit = 0.4; desc = "震荡"
            result = {"status": status, "desc": desc, "hs300": round(cur, 2),
                      "ma100": round(ma100, 2), "change_20w": round(chg20w, 2),
                      "position_limit": pos_limit}
            cache_set("market_status", result, ttl=86400)
            return result

        # 法2: 直接拿腾讯实时价做简单判断
        try:
            info = await self.get_stock_info("sh000300")
            price = info.get("price", 0)
            chg = info.get("change_pct", 0)
            if price > 3800:
                status, desc = "bull", "牛市"
                pos_limit = 0.8
            elif price > 3500:
                status, desc = "oscillate", "震荡"
                pos_limit = 0.5
            elif chg < -5:
                status, desc = "bear", "弱势"
                pos_limit = 0.2
            else:
                status, desc = "oscillate", "震荡"
                pos_limit = 0.4
            result = {"status": status, "desc": desc, "hs300": price,
                      "position_limit": pos_limit, "note": "简估"}
            cache_set("market_status", result, ttl=3600)
            return result
        except Exception:
            return {"status": "oscillate", "desc": "震荡", "position_limit": 0.4}

    # ──────────────── 行业排行 ───────────────

    async def get_industry_leaderboard(self) -> Dict:
        """获取行业涨跌幅排行"""
        cached = cache_get("industry_board")
        if cached:
            return cached
        try:
            # akshare 可能在有代理时失败，用短超时
            loop = asyncio.get_event_loop()
            df = await asyncio.wait_for(
                loop.run_in_executor(None, lambda: ak.stock_board_industry_name_em()),
                timeout=15
            )
            if df is not None and not df.empty:
                df = df.sort_values("涨跌幅", ascending=False)
                leaders = df.head(5)[["板块名称", "涨跌幅"]].to_dict("records")
                laggers = df.tail(5)[["板块名称", "涨跌幅"]].to_dict("records")
                result = {"leaders": leaders, "laggers": laggers}
                cache_set("industry_board", result, ttl=3600)
                return result
        except Exception as e:
            logger.warning(f"行业排行不可用: {e}")
        return {"leaders": [], "laggers": []}

    # ──────────────── 财务数据（akshare）───────────────

    async def _get_financials(self, raw_code: str) -> Dict:
        """获取财务指标"""
        try:
            loop = asyncio.get_event_loop()
            df = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: ak.stock_financial_analysis_indicator(
                        symbol=raw_code, start_year=str(datetime.now().year - 1)
                    )
                ),
                timeout=20
            )
            if df is None or df.empty:
                return {}
            latest = df.iloc[0]
            return {
                "roe": self._safe_float(latest.get("净资产收益率(%)", 0)),
                "pb": self._safe_float(latest.get("市净率(MRQ)", 0)),
                "debt_ratio": self._safe_float(latest.get("资产负债率(%)", 0)),
                "profit_growth": self._safe_float(latest.get("营业利润增长率(%)", 0)),
                "revenue_growth": self._safe_float(latest.get("营业收入增长率(%)", 0)),
            }
        except Exception as e:
            logger.debug(f"财务数据不可用 {raw_code}: {e}")
            return {}

    # ──────────────── 工具方法 ───────────────

    @staticmethod
    def _safe_float(v) -> float:
        try:
            return float(v)
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def _clean(s: str) -> str:
        """清理字符串中的引号和特殊字符"""
        if not s:
            return ""
        return s.replace('"', "").replace("'", "").strip()


# 全局单例
data_service = DataService()
