"""
选股服务 - 6步流水线：价值过滤→趋势确认→资金验证→评分排名→风控→信号输出
融合巴菲特/彼得·林奇/格雷厄姆/利弗莫尔四大投资大师策略
"""
from datetime import datetime
from typing import List, Dict, Optional

import pandas as pd
from loguru import logger

from services.data_service import DataService
from services.risk_service import RiskService


class PickerService:
    """智能选股服务 - 6步流水线"""

    # ============ 策略参数（可配置）============
    PARAMS = {
        # 第一层：价值过滤
        "pe_min": 5,
        "pe_max": 50,
        "pb_max": 5,
        "roe_min": 8.0,  # 下调自10%，提高覆盖率
        "profit_growth_min": 5.0,
        "revenue_growth_min": 5.0,
        "debt_ratio_max": 60.0,
        "goodwill_ratio_max": 30.0,
        "market_cap_max": 500.0,  # 亿，自由流通市值上限
        "listing_days_min": 365,

        # 第二层：趋势过滤
        "ma5_gt_ma20": True,
        "momentum_20d_min": 0,
        "vol_ratio_min": 1.3,
        "macd_positive": True,
        "rsi_min": 30,
        "rsi_max": 75,
        "break_20d_high": True,

        # 第三层：资金过滤
        "north_money_positive": True,

        # 风控
        "max_position": 5,
        "single_position_pct": 20.0,
        "total_position_pct": 80.0,
    }

    def __init__(self):
        self.data_service = DataService()
        self.risk_service = RiskService()

    def get_params(self) -> Dict:
        """获取当前策略参数"""
        return self.PARAMS.copy()

    async def generate_signals(self) -> Dict:
        """
        生成今日选股信号（完整6步流水线）
        """
        logger.info("🔍 开始选股流水线...")

        # Step 1: 获取全量股票数据
        logger.info("Step 1: 获取全量数据...")
        stock_list = await self.data_service.get_stock_list()
        if not stock_list:
            return {"date": datetime.now().strftime("%Y-%m-%d"), "signals": [], "market": {}}

        # 获取市场状态
        market = await self.data_service.get_market_status()
        logger.info(f"市场状态: {market.get('status_text', '未知')}")

        # 获取行业排行
        industry = await self.data_service.get_industry_leaderboard()
        strong_sectors = [x["板块名称"] for x in industry.get("leaders", [])[:3]]

        # Step 2: 价值筛选（批量处理前500只活跃股）
        logger.info("Step 2: 价值筛选...")
        candidates = await self._value_filter(stock_list[:500])
        logger.info(f"  → 价值池: {len(candidates)}只")

        if not candidates:
            return {"date": datetime.now().strftime("%Y-%m-%d"), "signals": [], "market": market}

        # Step 3: 趋势确认
        logger.info("Step 3: 趋势确认...")
        trending = await self._trend_filter(candidates)
        logger.info(f"  → 趋势池: {len(trending)}只")

        if not trending:
            return {"date": datetime.now().strftime("%Y-%m-%d"), "signals": [], "market": market}

        # Step 4: 资金验证
        logger.info("Step 4: 资金验证...")
        funded = await self._money_filter(trending)
        logger.info(f"  → 资金池: {len(funded)}只")

        # Step 5: 评分排名
        logger.info("Step 5: 评分排名...")
        scored = await self._score_and_rank(funded)
        logger.info(f"  → 评分后: {len(scored)}只")

        # Step 6: 风控检查
        logger.info("Step 6: 风控检查...")
        final = await self._risk_check(scored, market)
        logger.info(f"  → 最终候选: {len(final)}只")

        # 生成买入信号
        signals = []
        for i, stock in enumerate(final[:10]):
            signal = {
                "rank": i + 1,
                "code": stock["code"],
                "name": stock["name"],
                "score": stock["score"],
                "price": stock.get("price", 0),
                "change_pct": stock.get("change_pct", 0),
                "suggested_position": min(self.PARAMS["single_position_pct"], 100 / len(final)),
                "stop_loss_price": round(stock.get("price", 0) * 0.92, 2),
                "entry_reasons": stock.get("entry_reasons", []),
                "industry": stock.get("industry", ""),
                # 基本面
                "pe": stock.get("pe", 0),
                "roe": stock.get("roe", 0),
                "profit_growth": stock.get("profit_growth", 0),
                # 技术面
                "ma5": stock.get("ma5", 0),
                "ma20": stock.get("ma20", 0),
                "rsi": stock.get("rsi", 0),
                "macd": stock.get("macd", ""),
                "volume_ratio": stock.get("vol_ratio", 0),
            }
            signals.append(signal)

        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "market": market,
            "strong_sectors": strong_sectors,
            "signals": signals,
            "total_screened": len(stock_list),
            "pool_a_size": len(candidates),
            "pool_b_size": len(trending),
            "pool_c_size": len(funded),
        }

    async def _value_filter(self, stocks: List[Dict]) -> List[Dict]:
        """第一步：价值筛选"""
        p = self.PARAMS
        result = []

        for stock in stocks:
            code = stock.get("代码", "")
            if not code:
                continue
            # 跳过 ST 和 涨跌停
            name = stock.get("名称", "")
            if "ST" in name or "*ST" in name:
                continue

            try:
                info = await self.data_service.get_stock_info(code)
                indicators = await self.data_service.get_technical_indicators(code, [])

                pe = info.get("pe", 0) or 0
                pb = info.get("pb", 0) or 0
                roe = info.get("roe", 0) or 0
                debt = info.get("debt_ratio", 0) or 0

                # 价值条件
                if not (p["pe_min"] <= pe <= p["pe_max"]):
                    continue
                if pb > p["pb_max"]:
                    continue
                if roe < p["roe_min"]:
                    continue

                result.append({
                    "code": code,
                    "name": name,
                    "industry": info.get("industry", ""),
                    "price": info.get("price", 0),
                    "change_pct": info.get("change_pct", 0),
                    "pe": pe,
                    "pb": pb,
                    "roe": roe,
                    "debt_ratio": debt,
                    "profit_growth": info.get("profit_growth", 0),
                    "revenue_growth": info.get("revenue_growth", 0),
                    **{k: v for k, v in indicators.items() if k in ["ma5", "ma10", "ma20", "ma60", "rsi_14", "macd_bar", "momentum_20d", "vol_ratio"]},
                })

            except Exception as e:
                continue

        return result

    async def _trend_filter(self, candidates: List[Dict]) -> List[Dict]:
        """第二步：趋势确认"""
        p = self.PARAMS
        result = []

        for stock in candidates:
            ma5 = stock.get("ma5", 0)
            ma20 = stock.get("ma20", 0)
            ma60 = stock.get("ma60", 0)
            rsi = stock.get("rsi_14", 50)
            momentum = stock.get("momentum_20d", 0)
            macd = stock.get("macd_bar", 0)
            vol_ratio = stock.get("vol_ratio", 1)

            conditions_met = 0

            # 均线多头
            if p["ma5_gt_ma20"] and ma5 > ma20:
                conditions_met += 1
            if ma20 > ma60:
                conditions_met += 1

            # 动量
            if momentum > p["momentum_20d_min"]:
                conditions_met += 1

            # 放量
            if vol_ratio >= p["vol_ratio_min"]:
                conditions_met += 1

            # MACD
            if p["macd_positive"] and macd > 0:
                conditions_met += 1

            # RSI
            if p["rsi_min"] <= rsi <= p["rsi_max"]:
                conditions_met += 1

            # 需要至少4/6条件满足
            if conditions_met >= 4:
                stock["trend_score"] = conditions_met
                result.append(stock)

        return result

    async def _money_filter(self, candidates: List[Dict]) -> List[Dict]:
        """第三步：资金验证"""
        result = []
        for stock in candidates:
            try:
                mf = await self.data_service.get_money_flow(stock["code"])
                north_net = mf.get("north_net", 0)
                north_pct = mf.get("north_net_pct", 0)

                stock["north_net"] = north_net
                stock["north_pct"] = north_pct
                stock["money_score"] = 1 if north_net > 0 else 0
                result.append(stock)
            except:
                stock["money_score"] = 0
                result.append(stock)

        return result

    async def _score_and_rank(self, candidates: List[Dict]) -> List[Dict]:
        """第四步：综合评分排名"""
        for stock in candidates:
            # 动量得分（20%）
            momentum_score = min(stock.get("momentum_20d", 0) / 10 * 10, 20)

            # 趋势得分（20%）
            trend_score = stock.get("trend_score", 0) / 6 * 20

            # 资金得分（20%）
            money_score = stock.get("money_score", 0) * 20

            # 基本面得分（20%）
            roe = stock.get("roe", 0)
            profit_g = stock.get("profit_growth", 0)
            fundamental_score = min((roe / 20 * 10) + (profit_g / 20 * 10), 20)

            # 形态得分（20%）
            shape_score = min(stock.get("rsi_14", 50) / 75 * 10 + 10, 20)

            total = momentum_score + trend_score + money_score + fundamental_score + shape_score
            stock["score"] = round(total, 1)
            stock["score_breakdown"] = {
                "momentum": round(momentum_score, 1),
                "trend": round(trend_score, 1),
                "money": round(money_score, 1),
                "fundamental": round(fundamental_score, 1),
                "shape": round(shape_score, 1),
            }

            # 生成入选理由
            reasons = []
            if stock.get("trend_score", 0) >= 3:
                reasons.append("均线多头排列")
            if stock.get("momentum_20d", 0) > 5:
                reasons.append(f"动量强劲(+{stock['momentum_20d']:.1f}%)")
            if stock.get("north_net", 0) > 0:
                reasons.append(f"北向资金净买入")
            if stock.get("macd_bar", 0) > 0:
                reasons.append("MACD红柱")
            if stock.get("vol_ratio", 0) > 1.5:
                reasons.append(f"放量{int(stock['vol_ratio'])}倍")
            stock["entry_reasons"] = reasons

        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates

    async def _risk_check(self, candidates: List[Dict], market: Dict) -> List[Dict]:
        """第五步：风控检查（行业分散 + 仓位限制）"""
        position_limit = market.get("position_limit", 0.5)
        selected = []
        industry_count = {}

        for stock in candidates:
            industry = stock.get("industry", "未知")
            industry_count[industry] = industry_count.get(industry, 0) + 1

            # 同一行业≤2只
            if industry_count[industry] > 2:
                continue

            # 持仓上限
            total_pct = sum(s.get("suggested_position", 0) for s in selected)
            if total_pct >= position_limit * 100:
                continue
            if len(selected) >= self.PARAMS["max_position"]:
                continue

            selected.append(stock)

        return selected

    async def get_stockpool(
        self, page: int = 1, page_size: int = 20, sort_by: str = "score"
    ) -> Dict:
        """获取候选股票池（分页）"""
        # 生成信号后缓存股票池
        cache_key = "stockpool"
        cached = self.data_service._cache.get(cache_key)
        if not cached:
            result = await self.generate_signals()
            cached = result
            self.data_service._cache.set(cache_key, cached, ttl=1800)

        pool = cached.get("signals", [])

        # 排序
        reverse = True
        if sort_by == "pe":
            pool.sort(key=lambda x: x.get("pe", 999), reverse=False)
            reverse = False
        elif sort_by == "roe":
            pool.sort(key=lambda x: x.get("roe", 0), reverse=True)
        elif sort_by == "momentum":
            pool.sort(key=lambda x: x.get("change_pct", 0), reverse=True)

        total = len(pool)
        start = (page - 1) * page_size
        end = start + page_size
        items = pool[start:end]

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }

    async def custom_filter(self, req) -> List[Dict]:
        """自定义筛选"""
        stocks = await self.data_service.get_stock_list()
        candidates = await self._value_filter(stocks[:500])

        filtered = []
        for s in candidates:
            if req.pe_min and s.get("pe", 0) < req.pe_min:
                continue
            if req.pe_max and s.get("pe", 0) > req.pe_max:
                continue
            if req.roe_min and s.get("roe", 0) < req.roe_min:
                continue
            if req.debt_ratio_max and s.get("debt_ratio", 0) > req.debt_ratio_max:
                continue
            filtered.append(s)

        return filtered[:100]

    async def get_history(self, days: int = 30) -> List[Dict]:
        """获取历史选股记录"""
        return []
