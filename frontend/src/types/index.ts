// Stock types
export interface Stock {
  code: string
  name: string
  price: number
  change: number
  changePercent: number
  volume: number
  amount: number
  amplitude: number
  turnover: number
  pe: number
  marketCap: number
}

export interface KLineData {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

// Technical indicators
export type IndicatorType = 'MA' | 'MACD' | 'RSI' | 'KDJ' | 'BOLL' | 'NineTurn'

export interface IndicatorResult {
  type: IndicatorType
  data: number[]
  params: Record<string, number>
}

export interface MACDData {
  dif: number[]
  dea: number[]
  histogram: number[]
}

// Signal types
export type SignalType = 'BUY' | 'SELL' | 'WATCH' | 'HOLD'

export interface TradeSignal {
  date: string
  type: SignalType
  price: number
  reason: string
  strength: number // 0-100
}

// Portfolio types
export interface Position {
  code: string
  name: string
  shares: number
  cost: number
  currentPrice: number
  marketValue: number
  profit: number
  profitPercent: number
  positionRatio: number // 占比
}

export interface Portfolio {
  totalValue: number
  totalCost: number
  totalProfit: number
  profitPercent: number
  positions: Position[]
  cash: number
  availableCash: number
}

// Risk control
export interface RiskStatus {
  maxDrawdown: number
  sharpeRatio: number
  volatility: number
  var: number // Value at Risk
  positionLimit: number
  singleStockLimit: number
  warningLevel: 'safe' | 'warning' | 'danger'
}

// Backtest
export interface BacktestConfig {
  stockCode: string
  startDate: string
  endDate: string
  initialCapital: number
  indicators: IndicatorType[]
  strategyParams: Record<string, number>
}

export interface BacktestResult {
  totalReturn: number
  annualizedReturn: number
  maxDrawdown: number
  winRate: number
  profitFactor: number
  trades: TradeSignal[]
  equityCurve: { date: string; value: number }[]
}

// AI Assistant
export interface AIRequest {
  type: 'strategy' | 'diagnosis' | 'review'
  stockCode?: string
  question?: string
  params?: Record<string, any>
}

export interface AIResponse {
  type: 'strategy' | 'diagnosis' | 'review'
  content: string
  suggestions?: string[]
  generatedCode?: string
}

// Stock picker
export interface PickerResult {
  code: string
  name: string
  score: number
  signals: SignalType[]
  reasons: string[]
  change: number
  volume: number
}

// Sector strength
export interface SectorData {
  name: string
  strength: number
  change: number
  stocks: Stock[]
}

// Radar chart
export interface StrategyMetrics {
  momentum: number      // 动量
  volatility: number   // 波动
  liquidity: number    // 流动性
  valuation: number    // 估值
  growth: number       // 成长
  stability: number    // 稳定性
}

// API Response
export interface ApiResponse<T> {
  code: number
  message: string
  data: T
}
