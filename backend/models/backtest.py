"""
回测模型
定义回测配置、回测结果等数据结构
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class BacktestConfig(BaseModel):
    """回测配置"""
    # 基础配置
    name: str = Field(..., description="策略名称")
    description: Optional[str] = Field(None, description="策略描述")
    
    # 股票选择
    codes: List[str] = Field(..., description="股票代码列表")
    
    # 回测时间
    start_date: str = Field(..., description="开始日期")
    end_date: str = Field(..., description="结束日期")
    
    # 资金配置
    initial_cash: float = Field(100000.0, description="初始资金")
    position_pct: float = Field(20.0, description="单只仓位比例（%）")
    
    # 策略参数
    ma_short: int = Field(5, description="短期均线周期")
    ma_long: int = Field(20, description="长期均线周期")
    rsi_buy: float = Field(40.0, description="RSI买入阈值")
    rsi_sell: float = Field(70.0, description="RSI卖出阈值")
    stop_loss_pct: float = Field(8.0, description="止损比例（%）")
    take_profit_pct: float = Field(20.0, description="止盈比例（%）")
    max_holding_days: int = Field(30, description="最大持仓天数")
    
    # 费用设置
    commission: float = Field(0.0003, description="手续费（%）")
    stamp_duty: float = Field(0.0005, description="印花税（%）")
    slippage: float = Field(0.005, description="滑点（%）")
    
    # 基准
    benchmark: str = Field("000300", description="基准代码")


class BacktestResult(BaseModel):
    """回测结果"""
    # 基本信息
    backtest_id: str = Field(..., description="回测ID")
    name: str = Field(..., description="策略名称")
    created_at: str = Field(..., description="创建时间")
    
    # 收益指标
    total_return: float = Field(0, description="总收益率（%）")
    annual_return: float = Field(0, description="年化收益率（%）")
    benchmark_return: float = Field(0, description="基准收益率（%）")
    excess_return: float = Field(0, description="超额收益率（%）")
    
    # 风险指标
    max_drawdown: float = Field(0, description="最大回撤（%）")
    max_drawdown_date: Optional[str] = Field(None, description="最大回撤日期")
    max_drawdown_duration: int = Field(0, description="最大回撤持续天数")
    
    # 风险调整收益
    sharpe_ratio: float = Field(0, description="夏普比率")
    calmar_ratio: float = Field(0, description="卡玛比率")
    
    # 交易统计
    total_trades: int = Field(0, description="总交易次数")
    win_trades: int = Field(0, description="盈利交易数")
    lose_trades: int = Field(0, description="亏损交易数")
    win_rate: float = Field(0, description="胜率（%）")
    profit_loss_ratio: float = Field(0, description="盈亏比")
    avg_profit: float = Field(0, description="平均盈利（%）")
    avg_loss: float = Field(0, description="平均亏损（%）")
    
    # 持仓统计
    avg_holding_days: float = Field(0, description="平均持仓天数")
    total_commission: float = Field(0, description="总手续费")
    
    # 资金曲线
    equity_curve: List[Dict[str, Any]] = Field(default_factory=list, description="资金曲线数据")
    benchmark_curve: List[Dict[str, Any]] = Field(default_factory=list, description="基准曲线数据")
    
    # 交易记录
    trades: List[Dict[str, Any]] = Field(default_factory=list, description="交易记录列表")
    
    # 统计信息
    start_date: str = Field(..., description="回测开始日期")
    end_date: str = Field(..., description="回测结束日期")
    trading_days: int = Field(0, description="交易天数")


class BacktestTrade(BaseModel):
    """回测交易记录"""
    trade_id: int = Field(..., description="交易序号")
    date: str = Field(..., description="交易日期")
    code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    
    # 交易信息
    action: str = Field(..., description="交易动作（buy/sell）")
    price: float = Field(..., description="成交价格")
    quantity: int = Field(..., description="成交数量")
    amount: float = Field(..., description="成交金额")
    commission: float = Field(0, description="手续费")
    balance: float = Field(..., description="账户余额")
    
    # 持仓信息
    position_size: int = Field(0, description="持仓数量")
    avg_cost: float = Field(0, description="持仓成本")
    
    # 信号原因
    signal: str = Field("", description="交易信号")


class EquityPoint(BaseModel):
    """资金曲线数据点"""
    date: str = Field(..., description="日期")
    equity: float = Field(..., description="账户权益")
    cash: float = Field(..., description="现金")
    position_value: float = Field(0, description="持仓价值")
    drawdown: float = Field(0, description="回撤比例（%）")
    benchmark: float = Field(0, description="基准点位")


class BacktestSummary(BaseModel):
    """回测摘要（用于列表展示）"""
    backtest_id: str = Field(..., description="回测ID")
    name: str = Field(..., description="策略名称")
    created_at: str = Field(..., description="创建时间")
    
    # 核心指标
    total_return: float = Field(0, description="总收益率（%）")
    annual_return: float = Field(0, description="年化收益率（%）")
    max_drawdown: float = Field(0, description="最大回撤（%）")
    sharpe_ratio: float = Field(0, description="夏普比率")
    win_rate: float = Field(0, description="胜率（%）")
    total_trades: int = Field(0, description="总交易次数")
    
    # 状态
    status: str = Field("completed", description="状态（running/completed/failed）")
    
    # 股票数量
    stock_count: int = Field(0, description="股票数量")
    
    # 时间范围
    start_date: str = Field("", description="开始日期")
    end_date: str = Field("", description="结束日期")