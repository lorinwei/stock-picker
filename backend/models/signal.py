"""
交易信号模型
定义选股信号、交易信号等数据结构
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class SignalType(str):
    """信号类型"""
    BUY = "buy"          # 买入信号
    SELL = "sell"        # 卖出信号
    HOLD = "hold"        # 持有信号
    WATCH = "watch"      # 观望信号
    STOP_LOSS = "stop_loss"  # 止损信号


class SignalLevel(str):
    """信号强度"""
    STRONG = "strong"    # 强信号
    NORMAL = "normal"    # 普通信号
    WEAK = "weak"        # 弱信号


class PickSignal(BaseModel):
    """选股信号"""
    code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    
    # 信号基本信息
    signal_type: str = Field(SignalType.BUY, description="信号类型")
    signal_level: str = Field(SignalLevel.NORMAL, description="信号强度")
    signal_date: str = Field(..., description="信号日期")
    
    # 综合评分
    score: float = Field(..., ge=0, le=100, description="综合评分（0-100）")
    
    # 各维度评分
    momentum_score: float = Field(0, description="动量得分（0-100）")
    trend_score: float = Field(0, description="趋势得分（0-100）")
    fund_score: float = Field(0, description="资金得分（0-100）")
    fundamental_score: float = Field(0, description="基本面得分（0-100）")
    pattern_score: float = Field(0, description="形态得分（0-100）")
    
    # 技术面指标
    current_price: float = Field(..., description="当前价格")
    ma5: float = Field(..., description="5日均线")
    ma20: float = Field(..., description="20日均线")
    ma60: float = Field(..., description="60日均线")
    macd_status: str = Field(..., description="MACD状态")
    rsi: float = Field(..., description="RSI值")
    volume_ratio: float = Field(..., description="量比")
    
    # 趋势条件
    ma_bullish: bool = Field(False, description="均线多头排列")
    breakout: bool = Field(False, description="突破新高")
    volume_confirm: bool = Field(False, description="量能确认")
    macd_golden_cross: bool = Field(False, description="MACD金叉")
    
    # 基本面
    pe: Optional[float] = Field(None, description="市盈率")
    pb: Optional[float] = Field(None, description="市净率")
    roe: Optional[float] = Field(None, description="净资产收益率（%）")
    profit_growth: Optional[float] = Field(None, description="净利润增速（%）")
    
    # 资金面
    north_flow_5d: float = Field(0, description="北向资金5日净流入（万元）")
    main_flow_3d: float = Field(0, description="主力资金3日净流入（万元）")
    
    # 交易建议
    suggested_position: float = Field(0, description="建议仓位（%）")
    suggested_price: float = Field(..., description="建议买入价")
    stop_loss_price: float = Field(..., description="止损价")
    
    # 信号理由
    reasons: List[str] = Field(default_factory=list, description="信号理由列表")
    warnings: List[str] = Field(default_factory=list, description="风险提示列表")
    
    # 行业信息
    industry: Optional[str] = Field(None, description="所属行业")
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": "002594",
                "name": "比亚迪",
                "signal_type": "buy",
                "signal_level": "strong",
                "signal_date": "2025-05-07",
                "score": 92,
                "current_price": 245.30,
                "ma5": 242.50,
                "ma20": 238.00,
                "ma_bullish": True,
                "macd_status": "golden_cross",
                "rsi": 58,
                "volume_ratio": 1.8,
                "north_flow_5d": 23000,
                "main_flow_3d": 15000,
                "suggested_position": 20,
                "suggested_price": 245.30,
                "stop_loss_price": 225.68,
                "reasons": ["均线多头排列", "北向资金持续买入", "放量突破"],
                "warnings": ["RSI接近70，注意短期回调风险"]
            }
        }


class TradeSignal(BaseModel):
    """交易信号（回测中使用）"""
    signal_id: str = Field(..., description="信号ID")
    code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    
    # 信号类型
    signal: str = Field(..., description="交易信号（buy/sell/close）")
    signal_reason: str = Field(..., description="信号原因")
    
    # 价格信息
    price: float = Field(..., description="信号触发价格")
    stop_loss: float = Field(..., description="止损价格")
    take_profit: Optional[float] = Field(None, description="止盈价格")
    
    # 数量和资金
    quantity: int = Field(0, description="交易数量（股）")
    amount: float = Field(0, description="交易金额（元）")
    position_pct: float = Field(0, description="仓位占比（%）")
    
    # 时间
    signal_time: str = Field(..., description="信号时间")
    
    # 执行状态
    executed: bool = Field(False, description="是否已执行")
    executed_time: Optional[str] = Field(None, description="执行时间")
    executed_price: Optional[float] = Field(None, description="执行价格")
    
    # 回测信息
    backtest_id: Optional[str] = Field(None, description="关联的回测ID")


class PickResult(BaseModel):
    """选股结果"""
    date: str = Field(..., description="选股日期")
    total_scanned: int = Field(0, description="扫描股票总数")
    pass_pool_a: int = Field(0, description="通过价值筛选数量")
    pass_pool_b: int = Field(0, description="通过趋势筛选数量")
    pass_pool_c: int = Field(0, description="通过资金筛选数量")
    
    signals: List[PickSignal] = Field(default_factory=list, description="选股信号列表")
    
    # 市场状态
    market_status: str = Field("unknown", description="市场状态（bull/bear/neutral）")
    market_index: str = Field("000300", description="市场基准指数")
    market_index_change: float = Field(0, description="指数涨跌幅（%）")
    
    # 统计信息
    top_industries: List[Dict[str, Any]] = Field(default_factory=list, description="热门行业")
    execution_time: float = Field(0, description="执行耗时（秒）")


class SignalCheckResult(BaseModel):
    """持仓信号检查结果"""
    code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    
    # 检查结果
    needs_action: bool = Field(False, description="需要操作")
    action_type: Optional[str] = Field(None, description="操作类型（hold/sell/stop_loss/take_profit）")
    
    # 当前状态
    current_price: float = Field(..., description="当前价格")
    cost_price: float = Field(..., description="成本价")
    quantity: int = Field(..., description="持仓数量")
    profit_pct: float = Field(..., description="盈亏比例（%）")
    profit_amount: float = Field(..., description="盈亏金额")
    
    # 信号
    signals: List[str] = Field(default_factory=list, description="触发信号列表")
    message: str = Field("", description="检查结果消息")
    
    # 建议
    suggested_action: str = Field("hold", description="建议操作")
    suggested_price: Optional[float] = Field(None, description="建议价格")