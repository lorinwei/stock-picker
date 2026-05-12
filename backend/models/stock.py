"""
股票数据模型
定义股票相关的数据结构和枚举类型
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field


class MarketType(str, Enum):
    """市场类型枚举"""
    SH = "sh"      # 上海主板
    SZ = "sz"      # 深圳主板
    BJ = "bj"      # 北京板
    CY = "cy"      # 创业板


class StockBase(BaseModel):
    """股票基础信息模型"""
    code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    market: str = Field(..., description="市场代码（sh/sz/bj）")


class StockInfo(StockBase):
    """股票详细信息"""
    industry: Optional[str] = Field(None, description="所属行业")
    list_date: Optional[str] = Field(None, description="上市日期")
    total_shares: Optional[float] = Field(None, description="总股本（万股）")
    float_shares: Optional[float] = Field(None, description="流通股本（万股）")
    
    # 基本面
    pe: Optional[float] = Field(None, description="市盈率TTM")
    pb: Optional[float] = Field(None, description="市净率")
    market_cap: Optional[float] = Field(None, description="总市值（亿）")
    float_market_cap: Optional[float] = Field(None, description="流通市值（亿）")
    
    # 财务指标
    roe: Optional[float] = Field(None, description="净资产收益率TTM（%）")
    gross_margin: Optional[float] = Field(None, description="毛利率（%）")
    net_margin: Optional[float] = Field(None, description="净利率（%）")
    debt_ratio: Optional[float] = Field(None, description="资产负债率（%）")
    revenue: Optional[float] = Field(None, description="营业收入（亿）")
    profit: Optional[float] = Field(None, description="净利润（亿）")
    
    # 增长指标
    revenue_growth: Optional[float] = Field(None, description="营收增速（%）")
    profit_growth: Optional[float] = Field(None, description="净利润增速（%）")
    
    # 风险指标
    goodwill_ratio: Optional[float] = Field(None, description="商誉/净资产（%）")


class StockPrice(BaseModel):
    """股票价格数据（单条K线）"""
    date: str = Field(..., description="日期")
    open: float = Field(..., description="开盘价")
    high: float = Field(..., description="最高价")
    low: float = Field(..., description="最低价")
    close: float = Field(..., description="收盘价")
    volume: float = Field(..., description="成交量")
    amount: Optional[float] = Field(None, description="成交额")
    
    # 技术指标
    ma5: Optional[float] = Field(None, description="5日均线")
    ma10: Optional[float] = Field(None, description="10日均线")
    ma20: Optional[float] = Field(None, description="20日均线")
    ma60: Optional[float] = Field(None, description="60日均线")
    
    # MACD
    dif: Optional[float] = Field(None, description="DIF")
    dea: Optional[float] = Field(None, description="DEA")
    macd: Optional[float] = Field(None, description="MACD柱")
    
    # KDJ
    k: Optional[float] = Field(None, description="K值")
    d: Optional[float] = Field(None, description="D值")
    j: Optional[float] = Field(None, description="J值")
    
    # RSI
    rsi6: Optional[float] = Field(None, description="RSI6")
    rsi12: Optional[float] = Field(None, description="RSI12")
    rsi24: Optional[float] = Field(None, description="RSI24")
    
    # 布林带
    boll_upper: Optional[float] = Field(None, description="布林上轨")
    boll_mid: Optional[float] = Field(None, description="布林中轨")
    boll_lower: Optional[float] = Field(None, description="布林下轨")


class StockKlineData(BaseModel):
    """股票K线数据（多条）"""
    code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    klines: List[StockPrice] = Field(default_factory=list, description="K线列表")
    update_time: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"), description="更新时间")


class StockRealtime(BaseModel):
    """股票实时行情"""
    code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    price: float = Field(..., description="当前价")
    change_pct: float = Field(..., description="涨跌幅（%）")
    change: float = Field(..., description="涨跌额")
    volume: float = Field(..., description="成交量")
    amount: float = Field(..., description="成交额")
    high: float = Field(..., description="最高价")
    low: float = Field(..., description="最低价")
    open: float = Field(..., description="开盘价")
    pre_close: float = Field(..., description="昨收价")
    time: Optional[str] = Field(None, description="更新时间")


class MoneyFlowData(BaseModel):
    """资金流向数据"""
    code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    date: str = Field(..., description="日期")
    
    # 主力资金
    main_net_inflow: float = Field(..., description="主力净流入（万元）")
    main_inflow: float = Field(..., description="主力流入（万元）")
    main_outflow: float = Field(..., description="主力流出（万元）")
    
    # 超大单
    huge_net_inflow: float = Field(0, description="超大单净流入")
    huge_inflow: float = Field(0, description="超大单流入")
    huge_outflow: float = Field(0, description="超大单流出")
    
    # 大单
    big_net_inflow: float = Field(0, description="大单净流入")
    big_inflow: float = Field(0, description="大单流入")
    big_outflow: float = Field(0, description="大单流出")
    
    # 中单
    mid_net_inflow: float = Field(0, description="中单净流入")
    mid_inflow: float = Field(0, description="中单流入")
    mid_outflow: float = Field(0, description="中单流出")
    
    # 小单
    small_net_inflow: float = Field(0, description="小单净流入")
    small_inflow: float = Field(0, description="小单流入")
    small_outflow: float = Field(0, description="小单流出")


class NorthFlowData(BaseModel):
    """北向资金数据（陆股通）"""
    code: Optional[str] = Field(None, description="股票代码")
    name: Optional[str] = Field(None, description="股票名称")
    date: str = Field(..., description="日期")
    
    # 持仓和持股变化
    holdings: Optional[float] = Field(None, description="陆股通持股量（万股）")
    holdings_pct: Optional[float] = Field(None, description="陆股通持股占比（%）")
    change_holdings: Optional[float] = Field(None, description="持股变化量（万股）")
    
    # 资金流向
    net_inflow: Optional[float] = Field(None, description="北向资金净流入（万元）")
    buy_amount: Optional[float] = Field(None, description="买入金额（万元）")
    sell_amount: Optional[float] = Field(None, description="卖出金额（万元）")