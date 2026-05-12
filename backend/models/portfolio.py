"""
持仓管理模型
定义持仓、交易记录等数据结构
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class PositionStatus(str, Enum):
    """持仓状态"""
    NORMAL = "normal"           # 正常
    WARNING = "warning"          # 警戒（亏损5%-8%）
    STOP_LOSS = "stop_loss"     # 止损（亏损>=8%）
    TAKE_PROFIT = "take_profit" # 止盈
    CLOSED = "closed"           # 已平仓


class TradeType(str, Enum):
    """交易类型"""
    BUY = "buy"         # 买入
    SELL = "sell"       # 卖出
    DIVIDEND = "dividend"  # 分红
    SPLIT = "split"        # 拆股


class Position(BaseModel):
    """持仓"""
    id: Optional[int] = Field(None, description="持仓ID")
    code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    
    # 持仓信息
    quantity: int = Field(..., description="持仓数量（股）")
    available_quantity: int = Field(0, description="可用数量")
    frozen_quantity: int = Field(0, description="冻结数量（挂单中）")
    
    # 成本和价格
    cost_price: float = Field(..., description="成本价（含手续费）")
    current_price: float = Field(0, description="当前价格")
    
    # 盈亏计算
    profit: float = Field(0, description="浮盈亏金额")
    profit_pct: float = Field(0, description="浮盈亏比例（%）")
    
    # 持仓成本
    total_cost: float = Field(..., description="总成本")
    market_value: float = Field(0, description="市值")
    
    # 止损和止盈
    stop_loss_price: float = Field(..., description="止损价")
    stop_loss_pct: float = Field(8.0, description="止损比例（%）")
    take_profit_price: float = Field(0, description="动态止盈价")
    trailing_stop_pct: float = Field(5.0, description="移动止损回撤比例（%）")
    
    # 时间信息
    buy_date: str = Field(..., description="买入日期")
    buy_time: Optional[str] = Field(None, description="买入时间")
    holding_days: int = Field(0, description="持仓天数")
    last_update: str = Field(..., description="最后更新时间")
    
    # 状态
    status: str = Field(PositionStatus.NORMAL, description="持仓状态")
    status_color: str = Field("green", description="状态颜色")
    
    # 备注
    note: Optional[str] = Field(None, description="备注")
    
    # 关联
    backtest_id: Optional[str] = Field(None, description="关联回测ID（模拟盘）")


class TradeRecord(BaseModel):
    """交易记录"""
    id: Optional[int] = Field(None, description="记录ID")
    code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    
    # 交易信息
    trade_type: str = Field(..., description="交易类型（buy/sell/dividend/split）")
    quantity: int = Field(..., description="成交数量")
    price: float = Field(..., description="成交价格")
    amount: float = Field(..., description="成交金额")
    commission: float = Field(0, description="手续费")
    stamp_duty: float = Field(0, description="印花税")
    total_amount: float = Field(..., description="总金额（含费用）")
    
    # 时间
    trade_date: str = Field(..., description="交易日期")
    trade_time: Optional[str] = Field(None, description="交易时间")
    
    # 关联持仓
    position_id: Optional[int] = Field(None, description="关联持仓ID")
    position_id_before: Optional[int] = Field(None, description="变动前持仓ID")
    
    # 回测
    backtest_id: Optional[str] = Field(None, description="关联回测ID")
    
    # 备注
    note: Optional[str] = Field(None, description="备注")


class PortfolioSummary(BaseModel):
    """账户总览"""
    # 基本信息
    date: str = Field(..., description="日期")
    total_assets: float = Field(..., description="总资产")
    available_cash: float = Field(..., description="可用资金")
    market_value: float = Field(0, description="持仓市值")
    
    # 盈亏
    total_profit: float = Field(0, description="总盈亏")
    total_profit_pct: float = Field(0, description="总盈亏比例（%）")
    today_profit: float = Field(0, description="今日盈亏")
    today_profit_pct: float = Field(0, description="今日盈亏比例（%）")
    
    # 持仓统计
    position_count: int = Field(0, description="持仓数量")
    max_positions: int = Field(5, description="最大持仓数")
    total_position_pct: float = Field(0, description="总仓位比例（%）")
    max_position_pct: float = Field(80.0, description="最大仓位限制（%）")
    
    # 风控状态
    warning_count: int = Field(0, description="警戒数量")
    stop_loss_count: int = Field(0, description="止损数量")
    risk_status: str = Field("normal", description="风险状态")
    
    # 持仓列表
    positions: List[Position] = Field(default_factory=list, description="持仓列表")
    
    # 历史统计
    total_trades: int = Field(0, description="总交易次数")
    win_rate: float = Field(0, description="胜率（%）")
    avg_holding_days: float = Field(0, description="平均持仓天数")


class CashFlow(BaseModel):
    """资金流水"""
    id: Optional[int] = Field(None, description="ID")
    date: str = Field(..., description="日期")
    time: str = Field(..., description="时间")
    
    # 金额
    amount: float = Field(..., description="金额")
    balance: float = Field(..., description="余额")
    
    # 类型
    type: str = Field(..., description="类型（deposit/withdraw/trade/profit）")
    note: Optional[str] = Field(None, description="备注")
    
    # 关联
    trade_id: Optional[int] = Field(None, description="关联交易ID")


class PerformanceMetrics(BaseModel):
    """绩效指标"""
    # 收益指标
    total_return: float = Field(0, description="总收益率（%）")
    annual_return: float = Field(0, description="年化收益率（%）")
    benchmark_return: float = Field(0, description="基准收益率（%）")
    excess_return: float = Field(0, description="超额收益率（%）")
    
    # 风险指标
    max_drawdown: float = Field(0, description="最大回撤（%）")
    max_drawdown_days: int = Field(0, description="最大回撤持续天数")
    volatility: float = Field(0, description="波动率（%）")
    
    # 风险调整收益
    sharpe_ratio: float = Field(0, description="夏普比率")
    calmar_ratio: float = Field(0, description="卡玛比率")
    sortino_ratio: float = Field(0, description="索提诺比率")
    
    # 交易统计
    total_trades: int = Field(0, description="总交易次数")
    winning_trades: int = Field(0, description="盈利次数")
    losing_trades: int = Field(0, description="亏损次数")
    win_rate: float = Field(0, description="胜率（%）")
    avg_profit: float = Field(0, description="平均盈利")
    avg_loss: float = Field(0, description="平均亏损")
    profit_loss_ratio: float = Field(0, description="盈亏比")
    
    # 持仓统计
    avg_holding_days: float = Field(0, description="平均持仓天数")
    max_holding_days: int = Field(0, description="最长持仓天数")