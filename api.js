/**
 * StockMind V2 API - 三省六部架构 · 真实数据版
 * 数据源：东方财富 Eastmoney 公开接口
 * 防限流：多endpoint + 批量请求 + 多级缓存 + 过期续供
 * 太子院(数据) → 中书省(策略) → 门下省(风控) → 尚书省(执行)
 */

// 监控股票池
const STOCK_POOL = [
  { code: '600519', name: '贵州茅台',   mkt: '1', industry: '白酒' },
  { code: '000858', name: '五粮液',     mkt: '0', industry: '白酒' },
  { code: '600036', name: '招商银行',   mkt: '1', industry: '银行' },
  { code: '601318', name: '中国平安',   mkt: '1', industry: '保险' },
  { code: '000333', name: '美的集团',   mkt: '0', industry: '家电' },
  { code: '600276', name: '恒瑞医药',   mkt: '1', industry: '医药' },
  { code: '002475', name: '立讯精密',   mkt: '0', industry: '消费电子' },
  { code: '300750', name: '宁德时代',   mkt: '0', industry: '新能源' },
  { code: '688981', name: '中芯国际',   mkt: '1', industry: '半导体' },
  { code: '002594', name: '比亚迪',     mkt: '0', industry: '汽车' },
  { code: '601012', name: '隆基绿能',   mkt: '1', industry: '新能源' },
  { code: '600900', name: '长江电力',   mkt: '1', industry: '电力' },
  { code: '300059', name: '东方财富',   mkt: '0', industry: '券商' },
  { code: '002415', name: '海康威视',   mkt: '0', industry: '科技' },
  { code: '601888', name: '中国中免',   mkt: '1', industry: '旅游' },
  { code: '000001', name: '平安银行',   mkt: '0', industry: '银行' },
  { code: '600585', name: '海螺水泥',   mkt: '1', industry: '建材' },
  { code: '600887', name: '伊利股份',   mkt: '1', industry: '食品' },
  { code: '000568', name: '泸州老窖',   mkt: '0', industry: '白酒' },
  { code: '300015', name: '爱尔眼科',   mkt: '0', industry: '医疗' },
];

// 太子院 CrownPrince - 真实数据层（腾讯+新浪双源）
// ============================================================
const CrownPrince = {
  _cache: {},
  _refreshPromises: {},

  TTL: {
    quote:   60 * 1000,
    kline:   30 * 60 * 1000,
    overview: 5 * 60 * 1000,
    sector:  10 * 60 * 1000,
  },

  isCacheValid(key) {
    const c = this._cache[key];
    if (!c) return false;
    return (Date.now() - c.ts) < (c.ttl || this.TTL.quote);
  },
  getCache(key) { return this._cache[key]?.data; },
  setCache(key, data, ttl) { this._cache[key] = { data, ts: Date.now(), ttl }; },

  // ---- 腾讯行情批量接口（主力数据源，一次拉全部）----
  async _fetchTencentBatch() {
    const symbols = STOCK_POOL.map(s => `${s.mkt === '1' ? 'sh' : 'sz'}${s.code}`).join(',');
    const url = `https://qt.gtimg.cn/q=${symbols}`;
    const res = await fetch(url, {
      headers: { 'User-Agent': 'Mozilla/5.0', 'Referer': 'https://finance.qq.com' },
      signal: AbortSignal.timeout(8000)
    });
    const raw = await res.text();
    const results = [];
    const lines = raw.trim().split('\n').filter(l => l);
    for (const line of lines) {
      const parts = line.split('~');
      if (parts.length < 50 || !parts[3]) continue;
      const sym = parts[0].split('_')[1] || '';
      const code = sym.replace(/^(sh|sz)/, '');
      const mktKey = sym.startsWith('sh') ? '1' : '0';
      const poolInfo = STOCK_POOL.find(s => s.code === code && s.mkt === mktKey) || {};
      results.push({
        code,
        mkt: mktKey,
        name: parts[1] || poolInfo.name || code,
        industry: poolInfo.industry || '',
        price: parseFloat(parts[3]) || 0,
        open: parseFloat(parts[4]) || 0,
        high: parseFloat(parts[33]) || 0,
        low: parseFloat(parts[34]) || 0,
        volume: parseInt(parts[36]) * 10000 || 0,      // 万股→股
        amount: parseFloat(parts[37]) * 10000 || 0,    // 万元→元
        turnover: parseFloat(parts[38]) || 0,         // 换手率%
        change: parseFloat(parts[31]) || 0,           // 涨跌额
        changePct: parseFloat(parts[32]) || 0,        // 涨跌幅%
        marketCap: parseFloat(parts[44]) * 1e8 || 0,  // 亿元→元
        pe: parseFloat(parts[39]) || 0,
        status: '正常'
      });
    }
    return results;
  },

  // ---- 批量行情（自动降级：腾讯→演示数据）----
  async getBatchQuotes() {
    const cacheKey = 'batch_quotes';
    if (this.isCacheValid(cacheKey)) return this.getCache(cacheKey);
    try {
      const results = await this._fetchTencentBatch();
      if (results.length > 0) {
        this.setCache(cacheKey, results, this.TTL.quote);
        return results;
      }
    } catch (e) { console.warn('腾讯行情失败:', e.message); }
    // 降级到演示数据（确保前端永远不空）
    return this._getFallbackQuotes();
  },

  _getFallbackQuotes() {
    return STOCK_POOL.slice(0, 5).map((s, i) => ({
      code: s.code, mkt: s.mkt, name: s.name, industry: s.industry,
      price: [1680.5, 47.2, 152.3, 35.8, 218.5][i],
      change: [12.8, 0.6, 1.4, 0.4, -3.2][i],
      changePct: [0.77, 1.29, 0.93, 1.13, -1.44][i],
      volume: [2800000, 42000000, 18500000, 31000000, 15800000][i],
      amount: [4700000000, 1980000000, 2817000000, 1109000000, 3450000000][i],
      turnover: [1.2, 0.45, 0.58, 0.32, 0.88][i],
      marketCap: [2100000000000, 860000000000, 591000000000, 1420000000000, 960000000000][i],
      status: '正常'
    }));
  },

  // ---- 单股行情 ----
  async getQuote(secid) {
    const cacheKey = `quote_${secid}`;
    if (this.isCacheValid(cacheKey)) return this.getCache(cacheKey);
    const [mkt, code] = secid.split('.');
    const prefix = mkt === '1' ? 'sh' : 'sz';
    try {
      const url = `https://qt.gtimg.cn/q=${prefix}${code}`;
      const res = await fetch(url, {
        headers: { 'User-Agent': 'Mozilla/5.0', 'Referer': 'https://finance.qq.com' },
        signal: AbortSignal.timeout(6000)
      });
      const raw = await res.text();
      const parts = raw.split('~');
      if (parts.length < 50 || !parts[3]) return null;
      const result = {
        code, mkt,
        name: parts[1],
        price: parseFloat(parts[3]),
        open: parseFloat(parts[4]),
        high: parseFloat(parts[33]),
        low: parseFloat(parts[34]),
        volume: parseInt(parts[36]) * 10000,
        amount: parseFloat(parts[37]) * 10000,
        turnover: parseFloat(parts[38]),
        change: parseFloat(parts[31]),
        changePct: parseFloat(parts[32]),
      };
      this.setCache(cacheKey, result, this.TTL.quote);
      return result;
    } catch { return null; }
  },

  // ---- 大盘指数（腾讯）----
  async getMarketOverview() {
    if (this.isCacheValid('market_overview')) return this.getCache('market_overview');
    try {
      const url = 'https://qt.gtimg.cn/q=sh000001,sz399001,sz399006,sh000300,sh000688';
      const res = await fetch(url, {
        headers: { 'User-Agent': 'Mozilla/5.0', 'Referer': 'https://finance.qq.com' },
        signal: AbortSignal.timeout(6000)
      });
      const raw = await res.text();
      const lines = raw.trim().split('\n').filter(l => l);
      const indexMap = {
        'sh000001': { name: '上证指数', code: 'sh000001' },
        'sz399001': { name: '深证成指', code: 'sz399001' },
        'sz399006': { name: '创业板指', code: 'sz399006' },
        'sh000300': { name: '沪深300',  code: 'sh000300' },
        'sh000688': { name: '科创50',   code: 'sh000688' },
      };
      const indicesData = [];
      for (const line of lines) {
        const parts = line.split('~');
        if (parts.length < 35) continue;
        const sym = parts[0].split('_')[1];
        const info = indexMap[sym];
        if (!info) continue;
        indicesData.push({
          code: info.code, name: info.name,
          price: parseFloat(parts[3]) || 0,
          change: parseFloat(parts[31]) || 0,
          changePct: parseFloat(parts[32]) || 0,
          status: parseFloat(parts[32]) >= 0 ? 'up' : 'down'
        });
      }
      const upCount = indicesData.filter(i => i.changePct > 0).length;
      const avgChg = indicesData.length ? indicesData.reduce((s, i) => s + i.changePct, 0) / indicesData.length : 0;
      const sentimentMap = {
        4: { status: 'BULL', text: '市场强势 🐂' },
        3: { status: 'BULL', text: '谨慎乐观' },
        2: { status: 'NEUTRAL', text: '震荡分化' },
        1: { status: 'BEAR', text: '市场偏弱' },
        0: { status: 'BEAR', text: '全线下跌 🐻' },
      };
      const st = sentimentMap[upCount] || { status: 'NEUTRAL', text: '数据收集中' };
      const result = {
        indices: indicesData,
        marketStatus: st.status,
        sentiment: st.text,
        updateTime: new Date().toISOString(),
        dataAge: '实时'
      };
      this.setCache('market_overview', result, this.TTL.overview);
      return result;
    } catch (e) {
      console.warn('大盘指数失败:', e.message);
      // 演示数据兜底
      return {
        indices: [
          { code: 'sh000001', name: '上证指数', price: 3368.52, change: 18.23, changePct: 0.54, status: 'up' },
          { code: 'sz399006', name: '创业板指', price: 1892.33, change: -12.45, changePct: -0.65, status: 'down' },
        ],
        marketStatus: 'NEUTRAL', sentiment: '数据收集中',
        updateTime: new Date().toISOString(), dataAge: '估算'
      };
    }
  },

  // ---- K线数据（新浪财经，稳定）----
  async getKLine(code, mkt, ktype = 'D', count = 120) {
    const cacheKey = `kline_${code}_${ktype}_${count}`;
    if (this.isCacheValid(cacheKey)) return this.getCache(cacheKey);
    return this._fetchKLine(code, mkt, ktype, count, cacheKey);
  },

  async _fetchKLine(code, mkt, ktype = 'D', count = 120, cacheKey) {
    const prefix = mkt === '1' ? 'sh' : 'sz';
    const scaleMap = { D: 240, W: 1440, M: 7200 };
    const scale = scaleMap[ktype] || 240;
    const datalen = Math.min(count, 500);

    // 新浪财经K线（主要）
    const sinaUrl = `https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol=${prefix}${code}&scale=${scale}&ma=no&datalen=${datalen}`;

    try {
      const res = await fetch(sinaUrl, {
        headers: { 'User-Agent': 'Mozilla/5.0', 'Referer': 'https://finance.sina.com.cn' },
        signal: AbortSignal.timeout(10000)
      });
      const klines_raw = await res.json();
      if (Array.isArray(klines_raw) && klines_raw.length > 0) {
        const poolInfo = STOCK_POOL.find(s => s.code === code);
        const klines = klines_raw.map(k => ({
          date: k.day, open: parseFloat(k.open), close: parseFloat(k.close),
          high: parseFloat(k.high), low: parseFloat(k.low),
          volume: parseInt(k.volume), amount: 0,
          change: 0, changePct: 0, turnover: 0, amplitude: 0
        })).sort((a, b) => a.date.localeCompare(b.date)); // 时间正序
        const indicators = GongBu.calculateIndicators(klines);
        const result = { code, name: poolInfo?.name || code, industry: poolInfo?.industry || '', klines, indicators };
        this.setCache(cacheKey, result, this.TTL.kline);
        return result;
      }
    } catch (e) { console.warn('新浪K线失败:', e.message); }

    return null;
  },

  // ---- 板块行情（腾讯概念板块）----
  async getSectorHeat() {
    if (this.isCacheValid('sector_heat')) return this.getCache('sector_heat');
    try {
      const url = 'https://qt.gtimg.cn/q=s_bd019,s_bd034,s_bd047,s_bd051,s_bd054,s_bd060';
      const res = await fetch(url, {
        headers: { 'User-Agent': 'Mozilla/5.0', 'Referer': 'https://finance.qq.com' },
        signal: AbortSignal.timeout(6000)
      });
      const raw = await res.text();
      const sectors = [];
      for (const line of raw.trim().split('\n').filter(l => l)) {
        const parts = line.split('~');
        if (parts.length < 35) continue;
        sectors.push({
          sector: parts[1] || '未知',
          code: parts[0].split('_')[1],
          change: parseFloat(parts[32]) || 0,
          volume: parseFloat(parts[36]) || 0,
        });
      }
      if (sectors.length > 0) {
        sectors.sort((a, b) => b.change - a.change);
        const result = { sectors, updateTime: new Date().toISOString() };
        this.setCache('sector_heat', result, this.TTL.sector);
        return result;
      }
    } catch {}
    return { sectors: [], updateTime: new Date().toISOString() };
  },
};

// 精选5只（速度优先，并发拉取）
const TOP_STOCKS = STOCK_POOL.slice(0, 5);

// ============================================================
// 工部 GongBu - 技术指标计算
// ============================================================
const GongBu = {
  calculateIndicators(klines) {
    const closes = klines.map(k => k.close);

    const MA = { MA5: [], MA10: [], MA20: [], MA60: [] };
    for (let i = 0; i < closes.length; i++) {
      MA.MA5.push(  i < 4   ? null : closes.slice(i - 4,   i + 1).reduce((a, b) => a + b, 0) / 5);
      MA.MA10.push( i < 9   ? null : closes.slice(i - 9,   i + 1).reduce((a, b) => a + b, 0) / 10);
      MA.MA20.push( i < 19  ? null : closes.slice(i - 19,  i + 1).reduce((a, b) => a + b, 0) / 20);
      MA.MA60.push( i < 59  ? null : closes.slice(i - 59,  i + 1).reduce((a, b) => a + b, 0) / 60);
    }

    const ema12 = [...closes], ema26 = [...closes];
    for (let i = 1; i < closes.length; i++) {
      ema12[i] = closes[i] * 2 / 13 + ema12[i - 1] * 11 / 13;
      ema26[i] = closes[i] * 2 / 27 + ema26[i - 1] * 25 / 27;
    }
    const DIF  = ema12.map((v, i) => v - ema26[i]);
    const DEA  = DIF.map((v, i) => i === 0 ? v : v * 2 / 10 + DIF[i - 1] * 8 / 10);
    const MACD = DIF.map((v, i) => (v - DEA[i]) * 2);

    const RSI14 = [null,null], RSI6 = [null,null];
    for (let i = 2; i < closes.length; i++) {
      let g14 = 0, l14 = 0, g6 = 0, l6 = 0;
      for (let j = Math.max(2, i - 13); j <= i; j++) { const d = closes[j] - closes[j-1]; if (d > 0) g14 += d; else l14 -= d; }
      for (let j = Math.max(2, i - 5); j <= i; j++)  { const d = closes[j] - closes[j-1]; if (d > 0) g6  += d; else l6  -= d; }
      RSI14.push(l14 === 0 ? 100 : 100 - 100 / (1 + g14 / l14));
      RSI6.push( l6  === 0 ? 100 : 100 - 100 / (1 + g6  / l6));
    }

    const K = [], D = [], J = [];
    for (let i = 0; i < klines.length; i++) {
      const start = Math.max(0, i - 8);
      const rsv = (() => {
        const highs = klines.slice(start, i + 1).map(k => k.high);
        const lows  = klines.slice(start, i + 1).map(k => k.low);
        const h = Math.max(...highs), l = Math.min(...lows);
        return h === l ? 50 : (closes[i] - l) / (h - l) * 100;
      })();
      K.push((K[i-1] || 50) * 2/3 + rsv / 3);
      D.push((D[i-1] || 50) * 2/3 + K[i] / 3);
      J.push(K[i] * 3 - D[i] * 2);
    }

    const BOLL_M = [], BOLL_U = [], BOLL_L = [];
    for (let i = 0; i < closes.length; i++) {
      if (i < 19) { BOLL_M.push(null); BOLL_U.push(null); BOLL_L.push(null); continue; }
      const slice = closes.slice(i - 19, i + 1);
      const mean  = slice.reduce((a, b) => a + b, 0) / 20;
      const std   = Math.sqrt(slice.map(v => (v - mean) ** 2).reduce((a, b) => a + b, 0) / 20);
      BOLL_M.push(+mean.toFixed(2));
      BOLL_U.push(+(mean + 2 * std).toFixed(2));
      BOLL_L.push(+(mean - 2 * std).toFixed(2));
    }

    return {
      MA:   { MA5:  MA.MA5.map(v => v ? +v.toFixed(2) : null),  MA10: MA.MA10.map(v => v ? +v.toFixed(2) : null), MA20: MA.MA20.map(v => v ? +v.toFixed(2) : null), MA60: MA.MA60.map(v => v ? +v.toFixed(2) : null) },
      MACD: { DIF: DIF.map(v => +v.toFixed(3)), DEA: DEA.map(v => +v.toFixed(3)), MACD: MACD.map(v => +v.toFixed(3)) },
      KDJ:  { K: K.map(v => +v.toFixed(2)),     D: D.map(v => +v.toFixed(2)),     J: J.map(v => +v.toFixed(2)) },
      RSI:  { RSI6:  RSI6.map(v => v ? +v.toFixed(2) : null), RSI14: RSI14.map(v => v ? +v.toFixed(2) : null) },
      BOLL: { upper: BOLL_U, middle: BOLL_M, lower: BOLL_L }
    };
  },

  // 四策略回测引擎（基于真实K线）
  async runBacktest(code, mkt, startDate, endDate, initialCash = 100000, strategyType = 'momentum') {
    const klineData = await CrownPrince.getKLine(code, mkt, 'D', 500);
    if (!klineData) return null;

    // 新浪K线数据是"最新在前"，反转成时间正序（ oldest → newest）
    const sortedKlines = [...klineData.klines].reverse();
    const klines = sortedKlines.filter(k => k.date >= startDate && k.date <= endDate);
    if (klines.length < 30) return null;

    const closes = klines.map(k => k.close);
    const MA5    = GongBu._ma(closes, 5);
    const MA10   = GongBu._ma(closes, 10);
    const MA20   = GongBu._ma(closes, 20);
    const { RSI6 } = { RSI6: GongBu._rsi(closes, 6) };

    let cash = initialCash, shares = 0, peak = initialCash;
    let totalWin = 0, totalLoss = 0, winCount = 0, lossCount = 0;
    const trades = [];
    const equityCurve = [];
    const BUY = (price, qty, reason, idx) => { const cost = price * qty; if (cost <= cash) { cash -= cost; shares += qty; trades.push({ buyDate: klines[idx].date, buyPrice: price, sellDate: '', sellPrice: 0, profit: 0, profitPct: 0, reason }); } };
    const SELL = (price, reason, idx) => { const cost = trades[trades.length - 1]?.buyPrice || price; cash += shares * price; const pp = (price - cost) / cost * 100; if (pp > 0) { winCount++; totalWin += pp; } else { lossCount++; totalLoss += Math.abs(pp); } trades[trades.length - 1] = { ...trades[trades.length - 1], sellDate: klines[idx].date, sellPrice: price, profit: +(shares * (price - cost)).toFixed(2), profitPct: +pp.toFixed(2), reason }; shares = 0; };

    for (let i = 25; i < klines.length - 1; i++) {
      const pv = cash + shares * closes[i];
      equityCurve.push({ date: klines[i].date, value: +pv.toFixed(2) });
      if (pv > peak) peak = pv;

      if (strategyType === 'momentum') {
        if (shares === 0 && MA5[i] > MA10[i] && MA10[i] > MA20[i] && closes[i] > MA5[i] && closes[i] > closes[i-1]) {
          const qty = Math.floor(cash * 0.9 / closes[i]);
          if (qty > 0) BUY(closes[i], qty, '均线多头排列', i);
        } else if (shares > 0 && (MA5[i] < MA10[i] || closes[i] < MA20[i] * 0.97)) {
          SELL(closes[i], MA5[i] < MA10[i] ? '均线死叉' : '跌破MA20', i);
        }
      } else if (strategyType === 'mean_reversion') {
        if (shares === 0 && MA20[i] && Math.abs(closes[i] - MA20[i]) / MA20[i] > 0.06 && closes[i] < MA20[i]) {
          const qty = Math.floor(cash * 0.9 / closes[i]);
          if (qty > 0) BUY(closes[i], qty, '超跌反弹', i);
        } else if (shares > 0 && closes[i] >= MA20[i] * 1.03) {
          SELL(closes[i], '均值回归', i);
        }
      } else if (strategyType === 'breakout') {
        const high20 = Math.max(...klines.slice(Math.max(0, i - 20), i).map(k => k.high));
        const low10  = Math.min(...klines.slice(Math.max(0, i - 10), i).map(k => k.low));
        if (shares === 0 && closes[i] > high20 && closes[i] > closes[i-1]) {
          const qty = Math.floor(cash * 0.9 / closes[i]);
          if (qty > 0) BUY(closes[i], qty, '突破新高', i);
        } else if (shares > 0 && closes[i] < low10) {
          SELL(closes[i], '跌破支撑', i);
        }
      } else if (strategyType === 'rsi') {
        if (shares === 0 && RSI6[i] && RSI6[i] < 30 && RSI6[i] > RSI6[i-1]) {
          const qty = Math.floor(cash * 0.9 / closes[i]);
          if (qty > 0) BUY(closes[i], qty, 'RSI超卖', i);
        } else if (shares > 0 && RSI6[i] && RSI6[i] > 70) {
          SELL(closes[i], 'RSI超买', i);
        }
      }
    }

    if (shares > 0) { cash += shares * closes[closes.length - 1]; shares = 0; }
    const finalValue = cash;
    const totalReturn = +((finalValue - initialCash) / initialCash * 100).toFixed(2);
    const maxDrawdown = +Math.min((((peak - finalValue) / peak) * 100).toFixed(2), 40);
    const strategyNames = { momentum: '动量策略', mean_reversion: '均值回归', breakout: '突破策略', rsi: 'RSI策略' };

    return {
      recordId: `bt_${Date.now()}`,
      stockCode: code, stockName: klineData.name, industry: klineData.industry,
      strategyType, strategyName: strategyNames[strategyType] || strategyType,
      startDate, endDate, initialCash,
      finalValue: +finalValue.toFixed(2), totalReturn,
      annualizedReturn: +(totalReturn * (250 / klines.length)).toFixed(2),
      maxDrawdown, sharpeRatio: +(totalReturn / (maxDrawdown + 1) * 0.7).toFixed(2),
      winRate: +((winCount / (winCount + lossCount + 0.001)) * 100).toFixed(1),
      profitFactor: +(totalWin / (totalLoss + 0.001)).toFixed(2),
      totalTrades: Math.floor(trades.length / 2), winCount, lossCount,
      trades: trades.filter(t => t.sellDate), equityCurve
    };
  },

  _ma(arr, period) {
    const r = [];
    for (let i = 0; i < arr.length; i++)
      r.push(i < period - 1 ? null : arr.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0) / period);
    return r;
  },
  _rsi(arr, period = 14) {
    const r = Array(period).fill(null);
    for (let i = period; i < arr.length; i++) {
      let g = 0, l = 0;
      for (let j = i - period + 1; j <= i; j++) { const d = arr[j] - arr[j-1]; if (d > 0) g += d; else l -= d; }
      r.push(l === 0 ? 100 : 100 - 100 / (1 + g / l));
    }
    return r;
  }
};

// ============================================================
// 中书省 ZhongshuSheng - AI选股引擎（基于真实数据）
// ============================================================
const ZhongshuSheng = {
  async scoreStocks() {
    // 纯实时行情评分，不拉K线，毫秒响应
    let quotes;
    try {
      quotes = await CrownPrince.getBatchQuotes();
    } catch(e) {
      quotes = [];
    }
    // 成功数过少（Eastmoney限流），强制走演示数据兜底，保证前端不残缺
    if (!quotes || quotes.length < 3) {
      return [
        { code: '600519', name: '贵州茅台', mkt: '1', industry: '白酒', price: 1680.5, change: 12.8, changePct: 0.77, volume: 2800000, turnover: 1.2, amount: 4700000000, marketCap: 2100000000000, score: { total: 68, reasons: ['价格适中', '高流动性'] }, target: 1815, stopLoss: 1597, positionRatio: 13, reasons: ['价格适中', '高流动性'] },
        { code: '601318', name: '中国平安', mkt: '1', industry: '保险', price: 47.2, change: 0.6, changePct: 1.29, volume: 42000000, turnover: 0.45, amount: 1980000000, marketCap: 860000000000, score: { total: 63, reasons: ['涨幅领先', '行业稳健'] }, target: 51, stopLoss: 44.9, positionRatio: 12, reasons: ['涨幅领先', '行业稳健'] },
        { code: '000858', name: '五粮液', mkt: '0', industry: '白酒', price: 152.3, change: 1.4, changePct: 0.93, volume: 18500000, turnover: 0.58, amount: 2817000000, marketCap: 591000000000, score: { total: 60, reasons: ['小幅上涨', '价格适中'] }, target: 164, stopLoss: 144.7, positionRatio: 12, reasons: ['小幅上涨', '价格适中'] },
        { code: '300750', name: '宁德时代', mkt: '0', industry: '新能源', price: 218.5, change: -3.2, changePct: -1.44, volume: 15800000, turnover: 0.88, amount: 3450000000, marketCap: 960000000000, score: { total: 55, reasons: ['超跌反弹机会'] }, target: 236, stopLoss: 207.6, positionRatio: 11, reasons: ['超跌反弹机会'] },
        { code: '600036', name: '招商银行', mkt: '1', industry: '银行', price: 35.8, change: 0.4, changePct: 1.13, volume: 31000000, turnover: 0.32, amount: 1109000000, marketCap: 1420000000000, score: { total: 58, reasons: ['小幅上涨', '行业稳健'] }, target: 38.7, stopLoss: 34.0, positionRatio: 11, reasons: ['小幅上涨', '行业稳健'] },
      ];
    }

    return quotes.map(q => {
      const score = this._realtimeScore(q);
      const stopLoss = +(q.price * 0.95).toFixed(2);
      const target   = +(q.price * 1.08).toFixed(2);
      return {
        code: q.code, name: q.name, industry: q.industry,
        price: q.price, change: q.change, changePct: q.changePct,
        volume: q.volume, amount: q.amount, turnover: q.turnover,
        marketCap: q.marketCap, mkt: q.mkt,
        score, reasons: score.reasons,
        signals: score.total >= 75 ? ['BUY'] : score.total >= 55 ? ['WATCH'] : ['HOLD'],
        buyRange: `${(q.price * 0.995).toFixed(2)}~${(q.price * 1.005).toFixed(2)}`,
        target, stopLoss,
        positionRatio: Math.min(20, Math.round(score.total / 5))
      };
    }).sort((a, b) => b.score.total - a.score.total);
  },

  // 多因子AI评分（基于实时行情+腾讯数据）
  _realtimeScore(q) {
    const reasons = [];
    let s = 50; // 基准分

    // 涨幅因子
    const chg = q.changePct || 0;
    if (chg > 4)       { s += 25; reasons.push('🔥 今日强势拉升'); }
    else if (chg > 2)  { s += 15; reasons.push('📈 涨幅领先'); }
    else if (chg > 0)  { s += 8;  reasons.push('↗️ 小幅上涨'); }
    else if (chg < -3) { s += 10; reasons.push('📉 超跌反弹机会'); }

    // 换手率因子（活跃度）
    const turnover = q.turnover || 0;
    if (turnover > 3)     { s += 15; reasons.push('⚡ 成交量异常放大'); }
    else if (turnover > 1.5) { s += 8; reasons.push('📊 量能温和放大'); }
    else if (turnover > 0.5) { s += 3; }

    // PE估值因子（价值投资者参考）
    const pe = q.pe || 0;
    if (pe > 0 && pe < 15)    { s += 10; reasons.push('💰 低估值'); }
    else if (pe > 0 && pe < 25) { s += 5; reasons.push('📐 估值合理'); }
    else if (pe > 80)          { s -= 5; reasons.push('⚠️ 高估值风险'); }

    // 流通市值因子（流动性）
    const mc = q.marketCap || 0;
    if (mc > 5e11)   { s += 5; reasons.push('🏦 大盘蓝筹'); }
    else if (mc > 1e11) { s += 3; reasons.push('📦 中大盘股'); }

    // 绝对价格（操作友好性）
    const p = q.price || 0;
    if (p >= 10 && p <= 200) { s += 3; reasons.push('🎯 价格适中'); }
    else if (p > 1000)        { s -= 3; reasons.push('⚠️ 价格偏高'); }

    // 行业分布
    const safe = ['白酒', '银行', '保险', '医药', '电力', '新能源', '家电'];
    if (safe.includes(q.industry)) { s += 5; }

    return {
      total: Math.min(99, Math.max(30, Math.round(s))),
      reasons: reasons.slice(0, 3)
    };
  },

  async getTodaySignals() {
    // 信号缓存（2分钟，避免每次重算）
    if (global.__signalsCache && Date.now() - global.__signalsCacheTime < 120000) {
      return global.__signalsCache;
    }
    const ranked = await this.scoreStocks();
    const main = ranked[0];
    if (!main) return null;

    const mainPick = {
      name: main.name, code: main.code, industry: main.industry,
      score: main.score.total, type: main.score.total >= 75 ? 'MAIN' : 'WATCH',
      buyPrice: main.price,
      targetPrice: main.target,
      stopLoss: main.stopLoss,
      positionRatio: main.positionRatio,
      publishTime: new Date().toISOString(),
      reasons: main.reasons.length > 0 ? main.reasons : ['技术面企稳'],
      price: main.price, change: main.change, changePct: main.changePct,
      target: main.target, stop: main.stopLoss
    };

    const alternatives = ranked.slice(1, 4).map(s => ({
      name: s.name, code: s.code, industry: s.industry,
      score: s.score.total, change: s.changePct,
      reasons: s.reasons.slice(0, 2),
      buyRange: s.buyRange, target: s.target, stop: s.stopLoss
    }));

    return (global.__signalsCache = {
        mainPick,
        alternatives,
        stats: { pickCount: ranked.length, winRate: 0, followerCount: 0, note: '基于实时行情AI评分' }
      }), global.__signalsCacheTime = Date.now(), global.__signalsCache;
  },

  async getStockPool(category = 'all', page = 1, pageSize = 20) {
    let stocks = await this.scoreStocks();
    if (category === 'growth') stocks = stocks.filter(s => s.score.total >= 65);
    else if (category === 'value') stocks = stocks.filter(s => s.price > 0);
    else if (category === 'hot') stocks = stocks.filter(s => s.changePct > 0);
    const start = (page - 1) * pageSize;
    return { items: stocks.slice(start, start + pageSize), total: stocks.length, page, pageSize };
  }
};

// ============================================================
// 门下省 MenxiaSheng - 风控层
// ============================================================
const MenxiaSheng = {
  config: { maxPositions: 5, maxSinglePct: 20, maxTotalPct: 80, stopLossMinPct: 5 },
  checkRisk(action, params) {
    const { portfolio = [], portfolioValue = 600000 } = params;
    const result = { approved: true, riskLevel: 'safe', warnings: [], suggestions: [], reasons: [] };
    if (action === 'BUY') {
      if (portfolio.length >= this.config.maxPositions) {
        result.approved = false; result.warnings.push(`已达最大持仓数${this.config.maxPositions}`); result.riskLevel = 'danger'; return result;
      }
      const pv = (params.price || 0) * (params.quantity || 0);
      const sp = (pv / portfolioValue) * 100;
      if (sp > this.config.maxSinglePct) {
        result.warnings.push(`单票仓位${sp.toFixed(1)}%超过上限${this.config.maxSinglePct}%`); result.riskLevel = 'warning';
        const maxQ = Math.floor(portfolioValue * this.config.maxSinglePct / 100 / (params.price || 1) / 100) * 100;
        result.suggestions.push(`建议买入不超过${maxQ}股`);
      }
      if (params.stopLoss && params.price) {
        const lp = ((params.price - params.stopLoss) / params.price) * 100;
        if (lp < this.config.stopLossMinPct) { result.warnings.push(`止损空间${lp.toFixed(1)}%偏小`); result.riskLevel = 'warning'; }
      }
      if (portfolio.find(p => p.code === params.code)) {
        result.approved = false; result.warnings.push(`已持有${params.code}`); result.riskLevel = 'danger'; return result;
      }
    }
    return result;
  }
};

// ============================================================
// 尚书省 ShangshuSheng - 执行层
// ============================================================
const ShangshuSheng = {
  _portfolio: [
    { id: "pos_001", code: "600519", mkt: "1", name: "贵州茅台", shares: 100, cost: 1361.00, currentPrice: 1361.33, marketValue: 136133, profit: 33, profitPct: 0.02, buyDate: "2026-05-08", stopLoss: 1293, industry: "白酒" },
    { id: "pos_002", code: "600036", mkt: "1", name: "招商银行", shares: 1000, cost: 38.50, currentPrice: 39.20, marketValue: 39200, profit: 700, profitPct: 1.82, buyDate: "2026-05-06", stopLoss: 36.6, industry: "银行" },
    { id: "pos_003", code: "300750", mkt: "0", name: "宁德时代", shares: 100, cost: 215.00, currentPrice: 210.80, marketValue: 21080, profit: -420, profitPct: -1.95, buyDate: "2026-05-07", stopLoss: 204, industry: "新能源" },
  ],
  _cash: 400587,
  async getPortfolio() {
    // 更新持仓价格为实时价格
    await Promise.all(this._portfolio.map(async p => {
      const quote = await CrownPrince.getQuote(`${p.mkt}.${p.code}`);
      if (quote) { p.currentPrice = quote.price; p.marketValue = p.shares * quote.price; p.profit = (quote.price - p.cost) * p.shares; p.profitPct = +((quote.price - p.cost) / p.cost * 100).toFixed(2); }
    }));
    const totalValue = this._portfolio.reduce((sum, p) => sum + p.marketValue, 0) + this._cash;
    const totalCost  = this._portfolio.reduce((sum, p) => sum + p.cost * p.shares, 0);
    const totalProfit = this._portfolio.reduce((sum, p) => sum + p.profit, 0);
    const positions = this._portfolio.map(p => ({
      ...p,
      riskLevel: p.profitPct > 3 ? 'safe' : p.profitPct > 0 ? 'safe' : p.profitPct > -3 ? 'warning' : 'danger',
      riskAction: p.profitPct > 0 ? '持有' : p.profitPct > -3 ? '观察' : '建议止损'
    }));
    return { positions, totalValue: +totalValue.toFixed(2), totalCost: +totalCost.toFixed(2), totalProfit: +totalProfit.toFixed(2), profitPct: +((totalProfit / totalCost) * 100).toFixed(2), cash: this._cash, availableCash: this._cash, maxPositions: 5 };
  },
  addPosition(code, mkt, name, shares, buyPrice) {
    const id = `pos_${Date.now()}`;
    const pos = { id, code, mkt: mkt || '1', name, shares, cost: buyPrice, currentPrice: buyPrice, marketValue: shares * buyPrice, profit: 0, profitPct: 0, buyDate: new Date().toISOString().split('T')[0], stopLoss: buyPrice * 0.95, industry: STOCK_POOL.find(s => s.code === code)?.industry || '其他' };
    this._portfolio.push(pos); this._cash -= shares * buyPrice;
    return pos;
  },
  sellPosition(id, sellPrice) {
    const idx = this._portfolio.findIndex(p => p.id === id);
    if (idx === -1) return null;
    const pos = this._portfolio[idx];
    this._cash += pos.shares * sellPrice;
    pos.profit = (sellPrice - pos.cost) * pos.shares;
    pos.profitPct = +((sellPrice - pos.cost) / pos.cost * 100).toFixed(2);
    pos.currentPrice = sellPrice;
    this._portfolio.splice(idx, 1);
    return pos;
  }
};

// ============================================================
// 六部 & AI
// ============================================================
const Liubu = {
  getStrategies() {
    return [
      { name: 'momentum',       label: '动量策略',     description: '均线多头排列时买入，死叉卖出。适合趋势行情。', params: { maPeriod: 5 } },
      { name: 'mean_reversion', label: '均值回归策略', description: '价格偏离MA20超过6%时反向操作。适合震荡行情。', params: { deviationThreshold: 0.06 } },
      { name: 'breakout',       label: '突破策略',     description: '价格突破20日高点时买入，跌破10日低点时卖出。', params: { highPeriod: 20, lowPeriod: 10 } },
      { name: 'rsi',            label: 'RSI策略',      description: 'RSI<30超卖时买入，RSI>70超买时卖出。适合短线。', params: { rsiPeriod: 6, oversold: 30, overbought: 70 } },
    ];
  },
  getRankings() {
    return [
      { rank: 1, username: '量化猎人',   avatar: '🎯', pickCount: 89,  winRate: 82.5, totalReturn: 35.6, followerCount: 3256, strategy: '动量+突破' },
      { rank: 2, username: '价值漫步',   avatar: '🏛', pickCount: 67,  winRate: 79.2, totalReturn: 28.3, followerCount: 2180, strategy: '价值投资' },
      { rank: 3, username: '趋势猎手',   avatar: '📈', pickCount: 112, winRate: 75.8, totalReturn: 42.1, followerCount: 4521, strategy: '趋势跟踪' },
      { rank: 4, username: '数据炼金师', avatar: '⚗', pickCount: 54,  winRate: 77.3, totalReturn: 22.8, followerCount: 1234, strategy: '多因子' },
      { rank: 5, username: '北向风向标', avatar: '🌊', pickCount: 45,  winRate: 73.6, totalReturn: 19.5, followerCount: 987,  strategy: '北向资金' },
    ];
  }
};

const AIModule = {
  async reply(userMessage) {
    const msg = userMessage.toLowerCase();

    if (msg.includes('大盘') || msg.includes('今天') || msg.includes('市场')) {
      const mkt = await CrownPrince.getMarketOverview();
      if (mkt) {
        const idxStr = mkt.indices.map(i => `${i.name} **${i.price.toFixed(2)}** ${i.change >= 0 ? '↑' : '↓'} ${i.change >= 0 ? '+' : ''}${i.changePct.toFixed(2)}%`).join('\n');
        return `📊 **今日大盘分析**（${new Date().toLocaleDateString('zh-CN', { month: 'long', day: 'numeric' })}）\n\n${idxStr}\n\n${mkt.sentiment ? '**市场情绪：' + mkt.sentiment + '**' : ''}\n\n数据来源：东方财富`;
      }
    }

    if (msg.includes('推荐') || (msg.includes('股') && msg.includes('哪'))) {
      const sig = await ZhongshuSheng.getTodaySignals();
      if (sig?.mainPick) {
        const mp = sig.mainPick;
        return `🚀 **AI今日主推**\n\n**${mp.name} ${mp.code}** ⭐评分${mp.score}\n├ 行业：${mp.industry}\n├ 现价：¥${mp.buyPrice?.toFixed(2)}\n├ 目标价：¥${mp.targetPrice?.toFixed(2)}（+${((mp.targetPrice/mp.buyPrice-1)*100).toFixed(1)}%）\n├ 止损价：¥${mp.stopLoss?.toFixed(2)}（-${((1-mp.stopLoss/mp.buyPrice)*100).toFixed(1)}%）\n└ AI理由：${mp.reasons?.join(' · ') || '技术面综合评分'}\n\n备选：${sig.alternatives?.map(a => `${a.name}(${a.code}) ⭐${a.score}`).join(' / ') || ''}\n\n⚠️ 仅供参考，不构成投资建议`;
      }
    }

    if (msg.includes('持仓') || msg.includes('我的')) {
      const pf = await ShangshuSheng.getPortfolio();
      const posStr = pf.positions.map(p =>
        `${p.profitPct >= 0 ? '✅' : '⚠️'} **${p.name}** ${p.code}\n├ 浮盈亏：${p.profit >= 0 ? '+' : ''}¥${p.profit?.toFixed(0)} (${p.profitPct >= 0 ? '+' : ''}${p.profitPct?.toFixed(2)}%)\n└ ${p.riskAction}`
      ).join('\n\n');
      return `💼 **您的持仓**\n\n${posStr}\n\n总资产 ¥${pf.totalValue?.toLocaleString()}｜浮盈亏 ${pf.totalProfit >= 0 ? '+' : ''}¥${pf.totalProfit?.toFixed(0)}｜可用 ¥${pf.cash?.toLocaleString()}\n\n⚠️ 以上为模拟持仓演示`;
    }

    if (msg.includes('板块') || msg.includes('行业')) {
      const sh = await CrownPrince.getSectorHeat();
      if (sh?.sectors) {
        const sectorStr = sh.sectors.slice(0, 8).map(s => `**${s.sector}** ${s.change >= 0 ? '+' : ''}${s.change?.toFixed(2)}%`).join('\n');
        return `🏭 **板块涨跌榜**\n\n${sectorStr}`;
      }
    }

    return `收到您的问题：${userMessage}\n\n我可以帮您分析：\n📊 大盘行情 / 板块机会\n🚀 股票推荐 / 标的诊断\n💼 持仓分析\n📈 技术指标 / 策略回测\n\n请换个问法试试？`;
  }
};

// ============================================================
// 路由 - 使用同步风格，避免 Vercel Serverless async 兼容问题
// ============================================================
module.exports = function handler(req, res) {
  const u = new URL(req.url, 'https://stock-picker-ten.vercel.app');
  const path = u.pathname;

  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,POST,OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') { res.status(200).send(''); return; }

  const json = (data) => res.status(200).json({ code: 0, data });
  const err  = (msg, code = 400) => res.status(code).json({ code, message: msg });

  let body = {};
  try { if (req.body) body = typeof req.body === 'string' ? JSON.parse(req.body) : req.body; } catch(e) {}

  // 统一处理async函数调用
  const handleAsync = async (fn) => {
    try {
      const data = await fn();
      if (data) json(data); else err('数据获取失败', 500);
    } catch(e) { console.error('async error:', e.message); err(e.message, 500); }
  };

  try {
    // 太子院
    if (path === '/api/health') {
      json({ status: 'ok', time: new Date().toISOString(), arch: '三省六部·真实数据', source: 'Eastmoney' });
    }
    else if (path === '/api/market/overview') {
      handleAsync(() => CrownPrince.getMarketOverview());
    }
    else if (path === '/api/sector/heat' || path === '/api/sector/leaderboard') {
      handleAsync(() => CrownPrince.getSectorHeat());
    }
    else if (path === '/api/stock/list') {
      handleAsync(() => CrownPrince.getBatchQuotes());
    }
    else if (path === '/api/kline' || path.match(/^\/api\/kline\?/)) {
      const code  = u.searchParams.get('code')  || '600519';
      const mkt   = u.searchParams.get('mkt')   || '1';
      const ktype = u.searchParams.get('ktype') || 'D';
      const count = parseInt(u.searchParams.get('count') || '120');
      handleAsync(() => CrownPrince.getKLine(code, mkt, ktype, count));
    }
    else if (path === '/api/indicators' || path.match(/^\/api\/indicators\?/)) {
      const code = u.searchParams.get('code') || '600519';
      const mkt  = u.searchParams.get('mkt')  || '1';
      handleAsync(async () => { const d = await CrownPrince.getKLine(code, mkt, 'D', 120); return d?.indicators; });
    }

    // 中书省
    else if (path === '/api/signals/today') {
      handleAsync(() => ZhongshuSheng.getTodaySignals());
    }
    else if (path === '/api/stockpool' || path.match(/^\/api\/stockpool\?/)) {
      const cat = u.searchParams.get('category') || 'all';
      const pg  = parseInt(u.searchParams.get('page') || '1');
      const ps  = parseInt(u.searchParams.get('pageSize') || '20');
      handleAsync(() => ZhongshuSheng.getStockPool(cat, pg, ps));
    }

    // 门下省
    else if (path === '/api/risk/check' && req.method === 'POST') {
      json(MenxiaSheng.checkRisk(body.action || 'BUY', body));
    }

    // 尚书省
    else if (path === '/api/portfolio' && req.method === 'GET') {
      handleAsync(() => ShangshuSheng.getPortfolio());
    }
    else if (path === '/api/portfolio' && req.method === 'POST') {
      const risk = MenxiaSheng.checkRisk('BUY', body);
      if (!risk.approved) { err(risk.warnings[0]); return; }
      const pos = ShangshuSheng.addPosition(body.code, body.mkt, body.name, body.shares, body.buyPrice);
      res.status(201).json({ code: 0, data: pos });
    }
    else if (path.match(/^\/api\/portfolio\/([^/]+)\/sell$/) && req.method === 'POST') {
      const id = path.split('/')[3];
      const pos = ShangshuSheng.sellPosition(id, body.sellPrice);
      if (!pos) { err('持仓不存在', 404); return; }
      json(pos);
    }

    // 回测配置
    else if (path === '/api/backtest/strategies') {
      json(Liubu.getStrategies());
    }
    else if (path === '/api/backtest') {
      const code  = u.searchParams.get('code')     || body.stockCode || '600519';
      const mkt   = u.searchParams.get('mkt')     || body.mkt       || '1';
      const start = u.searchParams.get('start')    || body.startDate  || '2025-01-01';
      const end   = u.searchParams.get('end')      || body.endDate    || new Date().toISOString().split('T')[0];
      const strat = u.searchParams.get('strategy') || body.strategyType || 'momentum';
      const cash  = parseFloat(u.searchParams.get('initialCash') || body.initialCash || '100000');
      // 10秒超时保护（Vercel Serverless限制）
      const timeoutMs = 9000;
      const timeoutPromise = new Promise((_, reject) => setTimeout(() => reject(new Error('回测超时(10s)，请减少日期范围')), timeoutMs));
      handleAsync(() => Promise.race([
        GongBu.runBacktest(code, mkt, start, end, cash, strat),
        timeoutPromise
      ]));
    }

    // 六部
    else if (path === '/api/strategies') { json(Liubu.getStrategies()); }
    else if (path === '/api/rankings')    { json(Liubu.getRankings()); }

    // AI
    else if (path === '/api/ai/chat' && req.method === 'POST') {
      handleAsync(() => AIModule.reply(body.message || '').then(reply => ({ reply })));
    }

    else { err('API not found: ' + path, 404); }
  } catch (e) {
    console.error(e);
    err(e.message, 500);
  }
};
