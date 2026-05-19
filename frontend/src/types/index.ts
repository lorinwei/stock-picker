export interface ApiResponse<T = any> {
  code: number
  data: T
  message: string
}

export interface Stock {
  code: string
  name: string
  price: number
  change_pct: number
  pe?: number
  pb?: number
  roe?: number
}

export interface ChanSignal {
  rank: number
  code: string
  name: string
  score: number
  price: number
  buy_point: string
  stop_loss_price: number
  entry_reasons: string[]
  pe?: number
  roe?: number
}

export interface Position {
  id: number
  code: string
  name: string
  buy_price: number
  quantity: number
  current_price: number
  profit_pct: number
  stop_loss_price: number
  risk_status?: { status: string; status_text: string; profit_pct: number }
}

export interface KLine {
  date: string
  open: number
  close: number
  high: number
  low: number
  volume: number
}
