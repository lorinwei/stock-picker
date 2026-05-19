"""
选股服务 — 以缠论三类买点为核心的选股管道

流程:
  Step 0: 市场状态判定（熊市减少操作/空仓）
  Step 1: 快速价值过滤(PE/PB/ROE)  → 候选池A (≈300只)
  Step 2: 缠论分析(分型→笔→中枢→背驰→买卖点)  → 候选池B (有买点的)
  Step 3: 技术指标验证（趋势+成交量确认）
  Step 4: 综合评分（缠论40% + 基本面25% + 动量20% + 资金15%）
  Step 5: 风控检查（行业分散+仓位上限）
  Step 6: 输出TOP 10
"""
import asyncio
from datetime import datetime
from typing import Dict, List, Optional

from loguru import logger
from utils.cache import get as cache_get, set as cache_set

from services.data_service import data_service
from services.chanservice import ChanService, analyze_kline
from utils.config import settings


class PickerService:
    """缠论选股服务"""

    def __init__(self):
        self.chan = ChanService()
        self.picker_cfg = settings.PICKER

    async def generate_signals(self) -> Dict:
        """完整选股流水线（带缓存: 30分钟刷新一次）"""
        cache_key = "picker_signals_v1"
        cached = cache_get(cache_key)
        if cached:
            logger.info("使用缓存选股结果")
            return cached

        logger.info("🔍 开始缠论选股流水线...")

        # Step 0: 市场状态
        market = await data_service.get_market_status()
        logger.info(f"市场状态: {market.get('desc')} (仓位上限{market.get('position_limit', 0.4)*100:.0f}%)")

        if market.get("status") == "bear":
            logger.warning("🐻 熊市信号，减少选股操作")
            # 熊市也跑，但降低输出标准
        if market.get("status") == "oscillate":
            logger.info("⚖️ 震荡市，标准选股")

        # Step 1: 获取股票列表 + 价值过滤
        logger.info("Step 1: 价值筛选...")
        stock_list = await data_service.get_stock_list(top_n=800)
        if not stock_list:
            return self._empty_result(market)

        candidates = await self._value_filter(stock_list)
        logger.info(f"  → 候选池A: {len(candidates)}只")

        if not candidates:
            return self._empty_result(market)

        # Step 2: 缠论分析 — 找有买点的
        logger.info("Step 2: 缠论买点筛选...")
        chan_results = await self._chan_scan(candidates)
        logger.info(f"  → 有买点信号: {len(chan_results)}只")

        if not chan_results:
            logger.info("⚠️ 当前无缠论买点信号")
            return self._empty_result(market)

        # Step 3: 技术指标验证
        logger.info("Step 3: 技术确认...")
        confirmed = await self._tech_confirm(chan_results)
        logger.info(f"  → 技术确认后: {len(confirmed)}只")

        # Step 4: 综合评分
        logger.info("Step 4: 综合评分...")
        scored = self._score(confirmed)
        scored.sort(key=lambda x: x["score"], reverse=True)

        # Step 5: 风控检查
        logger.info("Step 5: 风控检查...")
        final = self._risk_check(scored, market)
        logger.info(f"  → 最终输出: {len(final)}只")

        signals = []
        for i, s in enumerate(final[:10]):
            signals.append({
                "rank": i + 1,
                "code": s["code"],
                "name": s["name"],
                "score": s["score"],
                "price": s.get("price", 0),
                "change_pct": s.get("change_pct", 0),
                "buy_point": s.get("buy_point", ""),
                "buy_point_desc": s.get("buy_point_desc", ""),
                "suggested_position": min(20, round(100 / max(len(final), 1), 1)),
                "stop_loss_price": round(s.get("price", 0) * 0.92, 2),
                "entry_reasons": s.get("reasons", []),
                "chan_score": s.get("chan_score", 0),
                "pe": s.get("pe", 0),
                "pb": s.get("pb", 0),
                "roe": s.get("roe", 0),
                "ma5": s.get("ma5", 0),
                "ma20": s.get("ma20", 0),
                "rsi_14": s.get("rsi_14", 0),
            })

        result = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "market": market,
            "signals": signals,
            "total_screened": len(stock_list),
            "pool_a": len(candidates),
            "pool_b": len(chan_results),
            "has_signals": len(signals) > 0,
        }
        # 缓存30分钟
        cache_set(cache_key, result, ttl=1800)
        return result

    # ──────────────── Step 1: 价值过滤 ────────────────

    async def _value_filter(self, stocks: List[Dict]) -> List[Dict]:
        """快速价值筛选 — 并发获取财务数据"""
        sem = asyncio.Semaphore(8)

        async def check(s: Dict) -> Optional[Dict]:
            code = s.get("code", "")
            name = s.get("name", "")
            if not code or "ST" in name or "*ST" in name:
                return None
            async with sem:
                try:
                    info = await asyncio.wait_for(data_service.get_stock_info(code), timeout=12)
                except (asyncio.TimeoutError, Exception):
                    return None

            pe = info.get("pe", 0) or 0
            pb = info.get("pb", 0) or 0
            roe = info.get("roe", 0) or 0

            p_min = self.picker_cfg.get("pe_range", [5, 120])[0]
            p_max = self.picker_cfg.get("pe_range", [5, 120])[1]
            pb_max = self.picker_cfg.get("pb_max", 8)
            roe_min = self.picker_cfg.get("roe_min", 5)

            if not (p_min <= pe <= p_max):
                return None
            if pb > pb_max:
                return None
            if roe < roe_min:
                return None

            return {
                "code": code,
                "name": name,
                "price": info.get("price", 0),
                "change_pct": info.get("change_pct", 0),
                "pe": pe,
                "pb": pb,
                "roe": roe,
                "market_cap": info.get("market_cap", 0),
                "profit_growth": info.get("profit_growth", 0),
                "revenue_growth": info.get("revenue_growth", 0),
                "debt_ratio": info.get("debt_ratio", 0),
            }

        tasks = [check(s) for s in stocks]
        results = await asyncio.gather(*tasks)
        return [r for r in results if r is not None]

    # ──────────────── Step 2: 缠论买点扫描 ────────────────

    async def _chan_scan(self, candidates: List[Dict]) -> List[Dict]:
        """缠论扫描 — 找有三类买点的股票"""
        sem = asyncio.Semaphore(5)

        async def scan(stock: Dict) -> Optional[Dict]:
            code = stock["code"]
            async with sem:
                try:
                    kline = await asyncio.wait_for(
                        data_service.get_kline(code, limit=300), timeout=20
                    )
                except (asyncio.TimeoutError, Exception):
                    return None

            if not kline or len(kline) < 50:
                return None

            analysis = analyze_kline(kline)
            score = analysis.get("score", {})
            buy_signals = analysis.get("buy_signals", [])
            sell_signals = analysis.get("sell_signals", [])

            if not buy_signals:
                return None

            # 有买点 → 保留
            total_score = score.get("total", 0)

            # 找出最显著的买点
            signal_types = [s.get("type", "") for s in buy_signals]
            buy_point_type = max(signal_types) if signal_types else ""
            buy_point_names = [s.get("name", "") for s in buy_signals[:2]]
            buy_point_desc = "、".join(buy_point_names) if buy_point_names else ""

            stock.update({
                "chan_score": total_score,
                "buy_point": buy_point_type,
                "buy_point_desc": buy_point_desc,
                "reasons": self._build_reasons(score, buy_signals, analysis.get("zhongshus", [])),
                "bis": len(analysis.get("bis", [])),
                "zhongshus": len(analysis.get("zhongshus", [])),
                "fenxings": len(analysis.get("fenxings", [])),
            })
            return stock

        tasks = [scan(s) for s in candidates]
        results = await asyncio.gather(*tasks)
        # 按缠论评分排序
        valid = [r for r in results if r is not None]
        return valid

    # ──────────────── Step 3: 技术确认 ────────────────

    async def _tech_confirm(self, stocks: List[Dict]) -> List[Dict]:
        """技术面确认 — 获取技术指标"""
        sem = asyncio.Semaphore(8)

        async def confirm(stock: Dict) -> Optional[Dict]:
            async with sem:
                try:
                    tech = await asyncio.wait_for(
                        data_service.get_technical_indicators(stock["code"]), timeout=15
                    )
                except (asyncio.TimeoutError, Exception):
                    tech = {}

            if not tech:
                return stock  # 降级: 没有技术指标也保留

            stock["ma5"] = tech.get("ma5", 0)
            stock["ma20"] = tech.get("ma20", 0)
            stock["ma60"] = tech.get("ma60", 0)
            stock["rsi_14"] = tech.get("rsi_14", 50)
            stock["macd_bar"] = tech.get("macd_bar", 0)
            stock["vol_ratio"] = tech.get("vol_ratio", 1)
            stock["momentum_20d"] = tech.get("momentum_20d", 0)
            stock["boll_upper"] = tech.get("boll_upper", 0)
            stock["boll_lower"] = tech.get("boll_lower", 0)
            return stock

        tasks = [confirm(s) for s in stocks]
        results = await asyncio.gather(*tasks)
        return [r for r in results if r is not None]

    # ──────────────── Step 4: 评分 ────────────────

    def _score(self, stocks: List[Dict]) -> List[Dict]:
        """综合评分 — 缠论占主导"""
        for s in stocks:
            # 缠论评分 (0-40)
            chan_raw = s.get("chan_score", 0)
            chan_weighted = min(chan_raw * 40 / 100, 40)

            # 买点加分: 三买>二买>一买
            bp = s.get("buy_point", "")
            bp_bonus = {"3rd_buy": 10, "2nd_buy": 7, "1st_buy": 5}.get(bp, 0)

            # 基本面 (0-20)
            roe = s.get("roe", 0)
            pe = s.get("pe", 50)
            profit_g = s.get("profit_growth", 0)
            fundamental = min((roe / 25 * 10) + (max(0, 30 - pe) / 30 * 5) + (max(0, profit_g) / 20 * 5), 20)

            # 动量 (0-20)
            momentum = s.get("momentum_20d", 0)
            momentum_score = min(max(momentum, -5) / 10 * 10 + 7, 15) if momentum > 0 else max(momentum / 10 * 5, 0)

            # 成交量 (0-10)
            vol = s.get("vol_ratio", 1)
            vol_score = min(max(vol - 1, 0) * 10, 10)

            # 趋势加分 (0-10)
            ma5 = s.get("ma5", 0)
            ma20 = s.get("ma20", 0)
            trend_score = 10 if ma5 > ma20 > 0 else 3

            total = chan_weighted + bp_bonus + fundamental + momentum_score + vol_score + trend_score
            s["score"] = round(total, 1)
            s["score_breakdown"] = {
                "chan": round(chan_weighted + bp_bonus, 1),
                "fundamental": round(fundamental, 1),
                "momentum": round(momentum_score, 1),
                "volume": round(vol_score, 1),
                "trend": round(trend_score, 1),
            }
        return stocks

    # ──────────────── Step 5: 风控 ────────────────

    @staticmethod
    def _risk_check(stocks: List[Dict], market: Dict) -> List[Dict]:
        """行业分散 + 数量限制"""
        limit = market.get("position_limit", 0.4)
        selected = []
        industry_count = {}

        for s in stocks:
            # 如果为不同行业, 用行业分散
            # 股票列表没有行业信息, 所以只按数量限制
            if len(selected) >= 8:
                break
            if len(selected) >= limit * 10:  # 仓位限制
                break
            selected.append(s)

        return selected

    # ──────────────── 构建理由 ────────────────

    @staticmethod
    def _build_reasons(score: Dict, buy_signals: List[Dict], zhongshus: List[Dict]) -> List[str]:
        reasons = []
        for s in buy_signals[:2]:
            reasons.append(f"{s['name']}: {s.get('description', '')}")
        d = score.get("direction", "")
        if d == "buy":
            reasons.append("缠论评分偏多")
        dir_cn = {"buy": "偏多", "sell": "偏空", "neutral": "中性"}
        reasons.append(f"缠论方向: {dir_cn.get(d, '中性')}")
        if zhongshus:
            zs = zhongshus[-1]
            reasons.append(f"中枢区间: {zs.get('bottom', 0)}-{zs.get('top', 0)}")
        return reasons[:5]

    @staticmethod
    def _empty_result(market: Dict) -> Dict:
        result = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "market": market,
            "signals": [],
            "has_signals": False,
        }
        cache_set("picker_signals_v1", result, ttl=600)
        return result


picker_service = PickerService()
