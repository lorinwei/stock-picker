"""
风控服务 - 止损计算、仓位管理、持仓状态判断
融合利弗莫尔8%止损法则 + 彼得·林奇仓位管理
"""
from typing import Dict, Optional
from datetime import datetime


class RiskService:
    """风控计算服务"""

    # 固定参数
    STOP_LOSS_PCT = -8.0      # 单笔最大亏损
    TAKE_PROFIT_PCT = 20.0    # 止盈线
    MAX_POSITIONS = 5          # 最大持仓数
    SINGLE_POSITION_PCT = 20.0 # 单只仓位上限
    TOTAL_POSITION_PCT = 80.0  # 总仓位上限
    HOLDING_DAYS_LIMIT = 30    # 最大持仓天数
    TRAILING_PCT = 5.0        # 动态止盈回撤幅度

    def check_position(self, position: Dict) -> Dict:
        """
        检查单只持仓的风控状态
        返回状态: normal(正常) / warning(警戒) / stop_loss(止损) / take_profit(止盈)
        """
        buy_price = position.get("buy_price", 0)
        current_price = position.get("current_price", buy_price)
        buy_date = position.get("buy_date", "")
        highest_price = position.get("highest_price", current_price)

        if not buy_price or not current_price:
            return {"status": "unknown", "status_color": "gray", "message": "数据不足"}

        # 计算盈亏
        profit_pct = (current_price / buy_price - 1) * 100
        holding_days = self._calc_holding_days(buy_date)

        # 状态判断（优先级）
        if profit_pct <= self.STOP_LOSS_PCT:
            status = "stop_loss"
            color = "red"
            message = f"触发止损！亏损 {profit_pct:.1f}%"
        elif profit_pct >= self.TAKE_PROFIT_PCT:
            # 动态止盈：涨20%后，回撤超过5%则止盈
            if highest_price and (current_price / highest_price - 1) * 100 <= -self.TRAILING_PCT:
                status = "take_profit"
                color = "green"
                message = f"动态止盈！盈利 {profit_pct:.1f}%，从高点回撤超过5%"
            else:
                status = "profit"
                color = "green"
                message = f"浮盈中 {profit_pct:.1f}%，继续持有"
        elif profit_pct <= -5.0:
            status = "warning"
            color = "yellow"
            message = f"接近止损线！亏损 {profit_pct:.1f}%"
        elif holding_days >= self.HOLDING_DAYS_LIMIT and profit_pct > 5.0:
            status = "time_stop"
            color = "blue"
            message = f"持仓超30天且盈利，建议止盈"
        elif holding_days >= self.HOLDING_DAYS_LIMIT and profit_pct <= 0:
            status = "time_stop_loss"
            color = "orange"
            message = f"持仓超30天仍亏损，建议止损"
        else:
            status = "normal"
            color = "green"
            message = f"正常持有 盈亏 {profit_pct:+.1f}%"

        # 止损价
        stop_loss_price = round(buy_price * (1 + self.STOP_LOSS_PCT / 100), 2)

        # 止盈价（动态）
        take_profit_price = round(buy_price * (1 + self.TAKE_PROFIT_PCT / 100), 2)

        return {
            "status": status,
            "status_color": color,
            "status_text": {
                "normal": "🟢 正常",
                "warning": "🟡 警戒",
                "stop_loss": "🔴 止损",
                "take_profit": "🟢 止盈",
                "profit": "🟢 盈利",
                "time_stop": "🔵 时间止盈",
                "time_stop_loss": "🟠 时间止损",
                "unknown": "⚪ 未知",
            }.get(status, "⚪ 未知"),
            "message": message,
            "profit_pct": round(profit_pct, 2),
            "profit_amount": round((current_price - buy_price) * position.get("quantity", 0), 2),
            "stop_loss_price": stop_loss_price,
            "take_profit_price": take_profit_price,
            "holding_days": holding_days,
            "distance_to_stop": round(current_price - stop_loss_price, 2),
            "distance_to_stop_pct": round((current_price / stop_loss_price - 1) * 100, 2),
        }

    def calc_position_size(
        self,
        total_cash: float,
        stock_price: float,
        atr_pct: float = 5.0,
    ) -> Dict:
        """
        计算仓位（彼得·林奇GARP策略：波动率加权）
        atr_pct: ATR/价格 的百分比
        """
        # 单只仓位 = 总资金 × (20% / ATR百分比)
        raw_position = total_cash * (self.SINGLE_POSITION_PCT / 100) / (atr_pct / 100) if atr_pct > 0 else total_cash * 0.2

        # 限制上下限
        max_position = total_cash * self.SINGLE_POSITION_PCT / 100
        min_position = total_cash * 0.05
        position_value = max(min(raw_position, max_position), min_position)

        # 计算股数（100股为1手）
        shares = int(position_value / stock_price / 100) * 100
        actual_position = shares * stock_price
        position_pct = actual_position / total_cash * 100

        return {
            "shares": shares,
            "position_value": round(actual_position, 2),
            "position_pct": round(position_pct, 2),
            "stop_loss_price": round(stock_price * (1 + self.STOP_LOSS_PCT / 100), 2),
        }

    def check_portfolio_risk(self, positions: list, total_cash: float) -> Dict:
        """检查整体组合风险"""
        total_value = sum(p.get("current_value", 0) for p in positions)
        total_cost = sum(p.get("cost", 0) for p in positions)
        position_count = len(positions)

        # 行业分散
        industries = {}
        for p in positions:
            ind = p.get("industry", "未知")
            industries[ind] = industries.get(ind, 0) + 1

        over_industry = {k: v for k, v in industries.items() if v > 2}

        # 总仓位
        total_value_with_cash = total_value + total_cash
        position_ratio = total_value / total_value_with_cash * 100 if total_value_with_cash > 0 else 0

        # 最大亏损持仓
        worst = min(positions, key=lambda p: p.get("profit_pct", 0), default=None)

        warnings = []
        if position_count >= self.MAX_POSITIONS:
            warnings.append(f"持仓数已达上限({self.MAX_POSITIONS}只)")
        if position_ratio >= self.TOTAL_POSITION_PCT:
            warnings.append(f"总仓位过重({position_ratio:.0f}%)")
        if over_industry:
            warnings.append(f"行业过度集中: {over_industry}")
        if worst and worst.get("profit_pct", 0) <= -5.0:
            warnings.append(f"持仓{worst.get('name', '')}亏损严重({worst.get('profit_pct', 0):.1f}%)")

        return {
            "total_value": round(total_value, 2),
            "total_cost": round(total_cost, 2),
            "total_profit": round(total_value - total_cost, 2),
            "profit_rate": round((total_value - total_cost) / total_cost * 100, 2) if total_cost > 0 else 0,
            "available_cash": round(total_cash, 2),
            "position_ratio": round(position_ratio, 2),
            "position_count": position_count,
            "max_positions": self.MAX_POSITIONS,
            "worst_position": worst,
            "industry_concentration": industries,
            "over_industry": over_industry,
            "warnings": warnings,
            "risk_level": "high" if len(warnings) >= 2 else "medium" if warnings else "low",
        }

    def _calc_holding_days(self, buy_date: str) -> int:
        """计算持仓天数"""
        if not buy_date:
            return 0
        try:
            buy = datetime.strptime(buy_date, "%Y-%m-%d")
            return (datetime.now() - buy).days
        except:
            return 0
