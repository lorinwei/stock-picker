/**
 * StockMind Cloudflare Worker - 炒股量化系统后端
 * 实现选股/回测/持仓/K线/AI全部接口
 * 数据来源：内置演示数据（生产环境请替换为真实数据源）
 */

// ══════════════════════════════════════════════════════════════
// 演示数据 - 股票基础信息
// ══════════════════════════════════════════════════════════════

const STOCKS = [
  { code: "600519", name: "贵州茅台", industry: "白酒", market_cap: 2324000000000, pe: 45.6, pb: 12.3, roe: 32.5, revenue_growth: 16.8, profit_growth: 18.2, debt_ratio: 18.5, goodwill_ratio: 0.2 },
  { code: "000858", name: "五粮液", industry: "白酒", market_cap: 654300000000, pe: 32.1, pb: 8.7, roe: 25.3, revenue_growth: 12.5, profit_growth: 14.8, debt_ratio: 22.1, goodwill_ratio: 0.5 },
  { code: "600036", name: "招商银行", industry: "银行", market_cap: 890000000000, pe: 8.5, pb: 1.2, roe: 16.8, revenue_growth: 7.2, profit_growth: 9.1, debt_ratio: 91.2, goodwill_ratio: 0.1 },
  { code: "601318", name: "中国平安", industry: "保险", market_cap: 780000000000, pe: 11.2, pb: 1.8, roe: 14.5, revenue_growth: 5.8, profit_growth: 6.3, debt_ratio: 88.9, goodwill_ratio: 2.1 },
  { code: "000333", name: "美的集团", industry: "家电", market_cap: 456000000000, pe: 18.5, pb: 3.2, roe: 22.1, revenue_growth: 8.5, profit_growth: 11.2, debt_ratio: 64.5, goodwill_ratio: 8.3 },
  { code: "600276", name: "恒瑞医药", industry: "医药", market_cap: 289000000000, pe: 68.5, pb: 8.9, roe: 18.2, revenue_growth: 6.5, profit_growth: 3.2, debt_ratio: 10.8, goodwill_ratio: 1.2 },
  { code: "002475", name: "立讯精密", industry: "消费电子", market_cap: 234000000000, pe: 28.3, pb: 5.6, roe: 21.5, revenue_growth: 25.8, profit_growth: 22.4, debt_ratio: 55.2, goodwill_ratio: 12.5 },
  { code: "300750", name: "宁德时代", industry: "新能源", market_cap: 876000000000, pe: 35.2, pb: 6.8, roe: 24.8, revenue_growth: 71.5, profit_growth: 65.8, debt_ratio: 58.3, goodwill_ratio: 3.2 },
  { code: "688981", name: "中芯国际", industry: "半导体", market_cap: 178000000000, pe: 52.3, pb: 3.5, roe: 8.5, revenue_growth: 38.5, profit_growth: 25.8, debt_ratio: 35.2, goodwill_ratio: 1.8 },
  { code: "002594", name: "比亚迪", industry: "汽车", market_cap: 678000000000, pe: 42.5, pb: 7.2, roe: 28.5, revenue_growth: 52.8, profit_growth: 458.2, debt_ratio: 72.5, goodwill_ratio: 2.8 },
  { code: "000001", name: "平安银行", industry: "银行", market_cap: 234000000000, pe: 6.8, pb: 0.9, roe: 12.5, revenue_growth: 4.8, profit_growth: 5.2, debt_ratio: 92.5, goodwill_ratio: 0.3 },
  { code: "600900", name: "长江电力", industry: "电力", market_cap: 567000000000, pe: 22.5, pb: 2.8, roe: 16.2, revenue_growth: 6.8, profit_growth: 8.5, debt_ratio: 45.2, goodwill_ratio: 5.8 },
];

// 模拟K线数据生成
function generateKLine(code, days = 120) {
  const basePrice = STOCKS.find(s => s.code === code)?.market_cap / 1e8 || 100;
  const data = [];
  let price = basePrice;
  const now = new Date();

  for (let i = days; i >= 0; i--) {
    const date = new Date(now);
    date.setDate(date.getDate() - i);
    // 跳过周末
    if (date.getDay() === 0 || date.getDay() === 6) continue;

    const change = (Math.random() - 0.48) * price * 0.03;
    const open = price;
    const close = Math.max(1, price + change);
    const high = Math.max(open, close) * (1 + Math.random() * 0.02);
    const low = Math.min(open, close) * (1 - Math.random() * 0.02);
    const volume = Math.floor(1e6 + Math.random() * 5e6);

    data.push({
      date: date.toISOString().split('T')[0],
      open: Math.round(open * 100) / 100,
      high: Math.round(high * 100) / 100,
      low: Math.round(low * 100) / 100,
      close: Math.round(close * 100) / 100,
      volume: volume,
    });
    price = close;
  }
  return data;
}

// 生成技术指标
function generateIndicators(klines) {
  const closes = klines.map(k => k.close);
  const ma5 = [], ma10 = [], ma20 = [];
  for (let i = 0; i < closes.length; i++) {
    ma5.push(i < 4 ? null : Math.round(closes.slice(i - 4, i + 1).reduce((a, b) => a + b, 0) / 5 * 100) / 100);
    ma10.push(i < 9 ? null : Math.round(closes.slice(i - 9, i + 1).reduce((a, b) => a + b, 0) / 10 * 100) / 100);
    ma20.push(i < 19 ? null : Math.round(closes.slice(i - 19, i + 1).reduce((a, b) => a + b, 0) / 20 * 100) / 100);
  }

  // MACD (简化计算)
  const ema12 = [...closes]; const ema26 = [...closes];
  for (let i = 1; i < closes.length; i++) {
    ema12[i] = closes[i] * 2 / 13 + ema12[i - 1] * 11 / 13;
    ema26[i] = closes[i] * 2 / 27 + ema26[i - 1] * 25 / 27;
  }
  const dif = ema12.map((v, i) => Math.round((v - ema26[i]) * 100) / 100);
  const dea = [...dif];
  for (let i = 1; i < dif.length; i++) dea[i] = dif[i] * 2 / 10 + dea[i - 1] * 8 / 10;
  const macd = dif.map((v, i) => Math.round((v - dea[i]) * 2 * 100) / 100);

  // KDJ
  const kdj_k = [], kdj_d = [], kdj_j = [];
  for (let i = 0; i < closes.length; i++) {
    const start = Math.max(0, i - 8);
    const highs = klines.slice(start, i + 1).map(k => k.high);
    const lows = klines.slice(start, i + 1).map(k => k.low);
    const rsv = highs.length ? Math.round((closes[i] - Math.min(...lows)) / (Math.max(...highs) - Math.min(...lows) + 0.001) * 100 * 100) / 100 : 50;
    kdj_k.push(Math.round((kdj_k[i - 1] || 50) * 2 / 3 + rsv / 3 * 100) / 100);
    kdj_d.push(Math.round((kdj_d[i - 1] || 50) * 2 / 3 + kdj_k[i] / 3 * 100) / 100);
    kdj_j.push(Math.round((kdj_k[i] * 3 - kdj_d[i] * 2) * 100) / 100);
  }

  // RSI
  const rsi = [null, null];
  for (let i = 2; i < closes.length; i++) {
    const gains = [], losses = [];
    for (let j = Math.max(2, i - 13); j <= i; j++) {
      const diff = closes[j] - closes[j - 1];
      gains.push(diff > 0 ? diff : 0);
      losses.push(diff < 0 ? -diff : 0);
    }
    const avgGain = gains.reduce((a, b) => a + b, 0) / gains.length;
    const avgLoss = losses.reduce((a, b) => a + b, 0) / losses.length;
    rsi.push(Math.round((100 - 100 / (1 + avgGain / (avgLoss + 0.001))) * 100) / 100);
  }

  return { MA: { MA5: ma5, MA10: ma10, MA20: ma20 }, MACD: { DIF: dif, DEA: dea, MACD: macd }, KDJ: { K: kdj_k, D: kdj_d, J: kdj_j }, RSI: rsi };
}

// 选股信号生成
function generateSignals() {
  const signals = [];
  const types = ['BUY', 'SELL', 'WATCH'];
  const reasons = ['MACD金叉', 'KDJ超卖', '量价齐升', '突破20日均线', 'RSI底背离', '九转序列高9', '布林带下轨', '趋势反转'];
  const stocks = STOCKS.slice(0, 8);

  for (const stock of stocks) {
    const type = types[Math.floor(Math.random() * 2)]; // mostly BUY/WATCH
    signals.push({
      code: stock.code, name: stock.name, type,
      date: new Date().toISOString().split('T')[0],
      price: Math.round(stock.market_cap / 1e8 * 100) / 100,
      reason: reasons[Math.floor(Math.random() * reasons.length)],
      strength: Math.floor(Math.random() * 30 + 60),
    });
  }
  return signals.sort((a, b) => b.strength - a.strength).slice(0, 10);
}

// 生成股票池
function generateStockpool(page = 1, pageSize = 20, sortBy = 'score') {
  const pool = STOCKS.map(s => {
    const score = Math.round((s.roe * 2 + (30 - Math.min(s.pe, 50)) + s.revenue_growth + s.profit_growth / 10) * 100) / 100;
    const price = Math.round(s.market_cap / 1e8 * 100) / 100;
    return {
      code: s.code, name: s.name, industry: s.industry,
      score: Math.min(99, score),
      signals: score > 70 ? ['BUY'] : score > 50 ? ['WATCH'] : ['HOLD'],
      reasons: score > 70 ? ['ROE高于同行', '营收增长强劲'] : ['估值合理'],
      change: Math.round((Math.random() - 0.4) * 10 * 100) / 100,
      volume: Math.floor(1e6 + Math.random() * 5e6),
      price, pe: s.pe, roe: s.roe, market_cap: s.market_cap,
    };
  });
  return { items: pool, total: pool.length, page, pageSize };
}

// 持仓数据
function getPortfolio(kv) {
  return {
    positions: [
      { id: "pos_001", code: "600519", name: "贵州茅台", shares: 100, cost: 1750.00, currentPrice: 1850.00, marketValue: 185000.00, profit: 10000.00, profitPercent: 5.71, positionRatio: 30.8, buyDate: "2024-01-10", risk_status: { level: "safe", warning: null } },
      { id: "pos_002", code: "300750", name: "宁德时代", shares: 200, cost: 180.50, currentPrice: 175.20, marketValue: 35040.00, profit: -1060.00, profitPercent: -2.94, positionRatio: 5.84, buyDate: "2024-01-15", risk_status: { level: "warning", warning: "接近止损位" } },
      { id: "pos_003", code: "002594", name: "比亚迪", shares: 150, cost: 195.00, currentPrice: 210.50, marketValue: 31575.00, profit: 2325.00, profitPercent: 7.95, positionRatio: 5.26, buyDate: "2024-01-08", risk_status: { level: "safe", warning: null } },
    ],
    totalValue: 600000.00, totalCost: 572000.00, totalProfit: 28000.00, profitPercent: 4.90,
    cash: 280385.00, availableCash: 180385.00, maxPositions: 5,
  };
}

// 回测数据生成
function generateBacktestResult(code, strategyType, startDate, endDate, initialCash = 100000) {
  const trades = [];
  const klines = generateKLine(code, 120);
  let cash = initialCash, shares = 0, peak = initialCash;
  let totalWin = 0, totalLoss = 0, winCount = 0, lossCount = 0;

  for (let i = 20; i < klines.length - 1; i++) {
    const k = klines[i];
    // 简化信号：随机买入/卖出
    if (shares === 0 && Math.random() > 0.7) {
      shares = Math.floor(cash / k.close * 0.95);
      cash -= shares * k.close;
      trades.push({ date: k.date, type: 'BUY', price: k.close, shares, reason: '买入信号' });
    } else if (shares > 0 && Math.random() > 0.8) {
      cash += shares * k.close;
      const profit = (k.close - trades[trades.length - 1].price) / trades[trades.length - 1].price * 100;
      if (profit > 0) { winCount++; totalWin += profit; } else { lossCount++; totalLoss += Math.abs(profit); }
      trades.push({ date: k.date, type: 'SELL', price: k.close, shares, reason: '卖出信号', profit });
      shares = 0;
    }
  }
  if (shares > 0) { cash += shares * klines[klines.length - 1].close; shares = 0; }

  const finalValue = cash;
  const totalReturn = Math.round((finalValue - initialCash) / initialCash * 10000) / 100;
  const equityCurve = klines.filter((_, i) => i % 5 === 0).map((k, i) => ({
    date: k.date, value: Math.round((initialCash + (finalValue - initialCash) * i / (klines.length / 5)) * 100) / 100,
  }));

  let maxDrawdown = 0;
  for (const e of equityCurve) {
    if (e.value > peak) peak = e.value;
    const dd = (peak - e.value) / peak * 100;
    if (dd > maxDrawdown) maxDrawdown = dd;
  }

  return {
    recordId: `bt_${Date.now()}`,
    stockCode: code, strategyType, startDate, endDate, initialCash,
    finalValue: Math.round(finalValue * 100) / 100,
    totalReturn, annualizedReturn: Math.round(totalReturn * 1.5 * 100) / 100,
    maxDrawdown: Math.round(maxDrawdown * 100) / 100,
    winRate: Math.round(winCount / (winCount + lossCount + 0.001) * 10000) / 100,
    profitFactor: Math.round((totalWin / (totalLoss + 0.001)) * 100) / 100,
    totalTrades: trades.length, winCount, lossCount,
    trades, equityCurve,
  };
}

// ══════════════════════════════════════════════════════════════
// 工具函数
// ══════════════════════════════════════════════════════════════

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status, headers: {
      'Content-Type': 'application/json; charset=utf-8',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
      'Access-Control-Allow-Headers': '*',
    },
  });
}

function apiOk(data) {
  return json({ code: 0, data, message: 'ok' });
}

function apiErr(msg, status = 500) {
  return json({ code: status, data: null, message: msg }, status);
}

function getBody(request) {
  const ct = request.headers.get('Content-Type') || '';
  if (ct.includes('application/json')) {
    try { return request.json(); } catch { return {}; }
  }
  return {};
}

async function kvGet(kv, key) {
  try { return await kv.get(key); } catch { return null; }
}
async function kvPut(kv, key, value) {
  try { await kv.put(key, value); } catch { /* ignore */ }
}

// ══════════════════════════════════════════════════════════════
// 路由处理
// ══════════════════════════════════════════════════════════════

async function handleStock(request, url) {
  const path = url.pathname;

  // GET /api/stock/list
  if (path === '/api/stock/list') {
    return apiOk(STOCKS);
  }

  // GET /api/stock/{code}
  const stockMatch = path.match(/^\/api\/stock\/([^/]+)$/);
  if (stockMatch && request.method === 'GET' && !path.includes('/kline') && !path.includes('/indicators') && !path.includes('/moneyflow')) {
    const code = stockMatch[1];
    const stock = STOCKS.find(s => s.code === code);
    if (!stock) return apiErr('股票不存在', 404);
    const price = Math.round(stock.market_cap / 1e8 * 100) / 100;
    return apiOk({ ...stock, price, change: Math.round((Math.random() - 0.4) * 5 * 100) / 100, changePercent: Math.round((Math.random() - 0.4) * 5 * 100) / 100, volume: Math.floor(1e6 + Math.random() * 5e6) });
  }

  // GET /api/stock/{code}/kline
  const klineMatch = path.match(/^\/api\/stock\/([^/]+)\/kline$/);
  if (klineMatch) {
    const code = klineMatch[1];
    const ktype = url.searchParams.get('ktype') || 'D';
    const start = url.searchParams.get('start');
    const end = url.searchParams.get('end');
    const limit = parseInt(url.searchParams.get('limit') || '500');
    const data = generateKLine(code, limit);
    return apiOk(data);
  }

  // GET /api/stock/{code}/indicators
  const indMatch = path.match(/^\/api\/stock\/([^/]+)\/indicators$/);
  if (indMatch) {
    const code = indMatch[1];
    const klines = generateKLine(code, 60);
    const data = generateIndicators(klines);
    return apiOk(data);
  }

  // GET /api/stock/{code}/moneyflow
  const mfMatch = path.match(/^\/api\/stock\/([^/]+)\/moneyflow$/);
  if (mfMatch) {
    const data = Array.from({ length: 10 }, (_, i) => {
      const d = new Date(); d.setDate(d.getDate() - 9 + i);
      return { date: d.toISOString().split('T')[0], inflow: Math.round(Math.random() * 1e8), outflow: Math.round(Math.random() * 8e7), net: Math.round((Math.random() - 0.4) * 5e7) };
    });
    return apiOk(data);
  }

  // GET /api/stock/benchmark/market-status
  if (path === '/api/stock/benchmark/market-status') {
    return apiOk({ status: 'BULL', description: '沪深300站稳20周均线，趋势向上', hs300_change: 1.25, ma20_week: 3850, current: 3920 });
  }

  // GET /api/stock/industry/leaderboard
  if (path === '/api/stock/industry/leaderboard') {
    const industries = ['新能源', '半导体', '白酒', '医药', '家电', '汽车', '银行', '电力'];
    return apiOk(industries.map(name => ({ name, change: Math.round((Math.random() - 0.3) * 5 * 100) / 100, stocks: STOCKS.slice(0, 3).map(s => ({ code: s.code, name: s.name })) })));
  }

  return apiErr('接口不存在', 404);
}

async function handlePicker(request, url) {
  const path = url.pathname;

  // GET /api/picker/signals
  if (path === '/api/picker/signals') {
    return apiOk(generateSignals());
  }

  // GET /api/picker/stockpool
  if (path === '/api/picker/stockpool') {
    const page = parseInt(url.searchParams.get('page') || '1');
    const pageSize = parseInt(url.searchParams.get('page_size') || '20');
    const sortBy = url.searchParams.get('sort_by') || 'score';
    return apiOk(generateStockpool(page, pageSize, sortBy));
  }

  // POST /api/picker/custom
  if (path === '/api/picker/custom' && request.method === 'POST') {
    const body = await getBody(request);
    const filtered = STOCKS.filter(s => {
      if (body.pe_min && s.pe < body.pe_min) return false;
      if (body.pe_max && s.pe > body.pe_max) return false;
      if (body.pb_max && s.pb > body.pb_max) return false;
      if (body.roe_min && s.roe < body.roe_min) return false;
      if (body.profit_growth_min && s.profit_growth < body.profit_growth_min) return false;
      if (body.revenue_growth_min && s.revenue_growth < body.revenue_growth_min) return false;
      if (body.debt_ratio_max && s.debt_ratio > body.debt_ratio_max) return false;
      return true;
    }).map(s => ({ code: s.code, name: s.name, industry: s.industry, score: Math.round(s.roe * 2 + 30 - s.pe), signals: ['WATCH'], reasons: ['满足筛选条件'] }));
    return apiOk({ items: filtered, total: filtered.length });
  }

  // GET /api/picker/history
  if (path === '/api/picker/history') {
    const days = parseInt(url.searchParams.get('days') || '30');
    const history = [];
    for (let d = days; d >= 0; d--) {
      const date = new Date(); date.setDate(date.getDate() - d);
      if (date.getDay() === 0 || date.getDay() === 6) continue;
      history.push(...generateSignals().slice(0, 3).map(s => ({ ...s, date: date.toISOString().split('T')[0] })));
    }
    return apiOk(history);
  }

  // GET /api/picker/params
  if (path === '/api/picker/params') {
    return apiOk({ pe_range: [5, 50], pb_max: 5, roe_min: 8, profit_growth_min: 5, revenue_growth_min: 5, debt_ratio_max: 60, market_cap_max: 500 });
  }

  return apiErr('接口不存在', 404);
}

async function handlePortfolio(request, url, kv) {
  const path = url.pathname;
  const method = request.method;

  // GET /api/portfolio/ - 获取持仓列表
  if (path === '/api/portfolio' && method === 'GET') {
    const positions = getPortfolio(kv).positions;
    return apiOk(positions);
  }

  // POST /api/portfolio/add - 添加持仓
  if (path === '/api/portfolio/add' && method === 'POST') {
    const body = await getBody(request);
    const stock = STOCKS.find(s => s.code === body.code);
    const position = {
      id: `pos_${Date.now()}`, code: body.code, name: body.name || stock?.name || body.code,
      shares: body.quantity, cost: body.buy_price, currentPrice: body.buy_price,
      marketValue: body.quantity * body.buy_price, profit: 0, profitPercent: 0,
      positionRatio: 0, buyDate: body.buy_date,
      risk_status: { level: 'safe', warning: null },
    };
    return apiOk(position, 201);
  }

  // PUT /api/portfolio/{id}
  const updateMatch = path.match(/^\/api\/portfolio\/([^/]+)$/);
  if (updateMatch && method === 'PUT') {
    const id = updateMatch[1];
    const body = await getBody(request);
    return apiOk({ id, ...body });
  }

  // POST /api/portfolio/{id}/sell
  const sellMatch = path.match(/^\/api\/portfolio\/([^/]+)\/sell$/);
  if (sellMatch) {
    const body = await getBody(request);
    return apiOk({ sellDate: body.sell_date, sellPrice: body.sell_price, reason: body.reason, profit: Math.round(Math.random() * 5000 - 1000) });
  }

  // DELETE /api/portfolio/{id}
  if (updateMatch && method === 'DELETE') {
    return apiOk(null);
  }

  // GET /api/portfolio/risk
  if (path === '/api/portfolio/risk') {
    const pf = getPortfolio(kv);
    return apiOk({ ...pf, maxDrawdown: 8.5, sharpeRatio: 1.85, volatility: 18.2, var: 15000, warningLevel: 'safe' });
  }

  // GET /api/portfolio/history
  if (path === '/api/portfolio/history') {
    const history = Array.from({ length: 20 }, (_, i) => {
      const d = new Date(); d.setDate(d.getDate() - i);
      if (d.getDay() === 0 || d.getDay() === 6) return null;
      return { id: `th_${i}`, code: STOCKS[i % STOCKS.length].code, name: STOCKS[i % STOCKS.length].name, type: Math.random() > 0.5 ? 'BUY' : 'SELL', date: d.toISOString().split('T')[0], price: Math.round(Math.random() * 500 + 50), shares: Math.floor(Math.random() * 500 + 100), reason: ['止损', '止盈', '趋势破坏', '再平衡'][Math.floor(Math.random() * 4)], profit: Math.round(Math.random() * 3000 - 500) };
    }).filter(Boolean);
    return apiOk(history);
  }

  return apiErr('接口不存在', 404);
}

async function handleBacktest(request, url) {
  const path = url.pathname;

  // POST /api/backtest/run
  if (path === '/api/backtest/run' && request.method === 'POST') {
    const body = await getBody(request);
    const result = generateBacktestResult(body.stock_code, body.strategy_type, body.start_date, body.end_date, body.initial_cash);
    return apiOk(result);
  }

  // POST /api/backtest/compare
  if (path === '/api/backtest/compare' && request.method === 'POST') {
    const body = await getBody(request);
    const strategies = ['价值趋势', '动量策略', '突破策略'];
    const results = body.strategy_ids.map((id, i) => ({ id, name: strategies[i] || `策略${i + 1}`, ...generateBacktestResult(body.stock_code, id, body.start_date, body.end_date, body.initial_cash) }));
    return apiOk(results);
  }

  // POST /api/backtest/optimize
  if (path === '/api/backtest/optimize' && request.method === 'POST') {
    const bestParams = { stop_loss: -8, take_profit: 20, ma_period: 20, rsi_period: 14, rsi_oversold: 30, rsi_overbought: 70 };
    const results = [{ params: bestParams, totalReturn: 35.8, winRate: 62.5, sharpeRatio: 1.95 }];
    return apiOk({ bestParams, results });
  }

  // GET /api/backtest/history
  if (path === '/api/backtest/history') {
    const records = Array.from({ length: 10 }, (_, i) => ({ id: `bt_h_${i}`, stockCode: STOCKS[i % STOCKS.length].code, strategyType: 'value_trend', startDate: '2023-01-01', endDate: '2024-01-01', totalReturn: Math.round(Math.random() * 60 - 10), winRate: Math.round(Math.random() * 40 + 50), createdAt: new Date().toISOString() }));
    return apiOk(records);
  }

  // GET /api/backtest/record/{id}
  const recMatch = path.match(/^\/api\/backtest\/record\/([^/]+)$/);
  if (recMatch) {
    return apiOk(generateBacktestResult('600519', 'value_trend', '2023-01-01', '2024-01-01'));
  }

  return apiErr('接口不存在', 404);
}

async function handleAI(request, url) {
  const path = url.pathname;

  // POST /api/ai/generate-strategy
  if (path === '/api/ai/generate-strategy' && request.method === 'POST') {
    const body = await getBody(request);
    return apiOk({
      description: body.description,
      name: 'AI策略_' + Date.now(),
      code: `def strategy(df):\n    df['MA20'] = df['close'].rolling(20).mean()\n    df['Signal'] = (df['close'] > df['MA20']).astype(int)\n    return df`,
      parameters: { ma_period: 20, stop_loss: -8, take_profit: 20 },
    });
  }

  // POST /api/ai/reverse-strategy
  if (path === '/api/ai/reverse-strategy' && request.method === 'POST') {
    const body = await getBody(request);
    return apiOk({
      description: '该区间呈现典型的"均线多头排列+量价齐升"特征，属于趋势型策略',
      indicators: ['MA5', 'MA20', 'VOL'],
      confidence: 0.85,
      suggestedStrategy: '趋势跟随策略',
    });
  }

  // POST /api/ai/consult
  if (path === '/api/ai/consult' && request.method === 'POST') {
    const body = await getBody(request);
    const diagnoses = body.codes.map(code => {
      const stock = STOCKS.find(s => s.code === code) || STOCKS[0];
      return {
        code, name: stock.name,
        diagnosis: '估值适中，基本面良好，短期存在一定回调风险，建议持有观察',
        score: Math.floor(Math.random() * 30 + 60),
        risks: ['短期波动加大', '行业竞争加剧'],
        suggestions: ['逢低加仓', '设置止损位'],
      };
    });
    return apiOk(diagnoses);
  }

  // GET /api/ai/daily-summary
  if (path === '/api/ai/daily-summary') {
    const date = url.searchParams.get('date') || new Date().toISOString().split('T')[0];
    return apiOk({
      date, summary: '今日市场整体震荡上行，沪深300收涨0.85%。AI策略命中3只涨停股，持仓整体表现优于大盘。明日关注美联储利率决议。',
      marketOverview: '两市成交额8600亿，北向资金净流入52亿。板块方面，新能源、半导体涨幅居前，消费电子回调。',
      aiInsights: ['注意高位股短期回调风险', '关注科技板块轮动机会', '仓位建议控制在7成以内'],
      topPicks: generateSignals().slice(0, 3),
    });
  }

  // POST /api/ai/backtest-strategy
  if (path === '/api/ai/backtest-strategy' && request.method === 'POST') {
    return apiOk(generateBacktestResult('600519', 'ai_strategy', '2023-01-01', '2024-01-01'));
  }

  return apiErr('接口不存在', 404);
}

// ══════════════════════════════════════════════════════════════
// 主入口
// ══════════════════════════════════════════════════════════════

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname.replace(/\/$/, '');
    const kv = env.STOCKMIND_KV;

    try {
      // 根路径 & 健康检查
      if (path === '' || path === '/') {
        return json({ name: 'StockMind API', version: '1.0.0', status: 'running' });
      }
      if (path === '/health' || path === '/api/health') {
        return json({ status: 'healthy', database: 'connected' });
      }

      // OPTIONS 预检
      if (request.method === 'OPTIONS') {
        return new Response('', { status: 204, headers: { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS', 'Access-Control-Allow-Headers': '*' } });
      }

      // 路由分发
      if (path.startsWith('/api/stock')) return handleStock(request, url);
      if (path.startsWith('/api/picker')) return handlePicker(request, url);
      if (path.startsWith('/api/portfolio')) return handlePortfolio(request, url, kv);
      if (path.startsWith('/api/backtest')) return handleBacktest(request, url);
      if (path.startsWith('/api/ai')) return handleAI(request, url);

      return apiErr('API路径不存在', 404);
    } catch (e) {
      return apiErr('服务器内部错误: ' + String(e), 500);
    }
  },
};
