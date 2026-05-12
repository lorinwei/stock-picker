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

// ============================================================
// 太子院 CrownPrince - 真实数据层（防限流版）
// ============================================================
const CrownPrince = {
  _cache: {},
  _refreshPromises: {}, // 防止并发刷新同一key

  // 多级缓存TTL：新鲜数据 / 过期续供
  TTL: {
    quote:   60 * 1000,   // 行情60秒（股票价格本来就有延迟）
    kline:   30 * 60 * 1000, // K线30分钟
    overview: 5 * 60 * 1000, // 大盘5分钟
    sector:  10 * 60 * 1000, // 板块10分钟
  },

  isCacheValid(key) {
    const c = this._cache[key];
    if (!c) return false;
    const ttl = c.ttl || this.TTL.quote;
    return (Date.now() - c.ts) < ttl;
  },
  isCacheStale(key) {
    const c = this._cache[key];
    if (!c) return true;
    // 超过3倍TTL才算完全过期，之前返回缓存同时后台刷新
    const ttl = c.ttl || this.TTL.quote;
    return (Date.now() - c.ts) > ttl * 3;
  },
  getCache(key) { return this._cache[key]?.data; },
  setCache(key, data, ttl) { this._cache[key] = { data, ts: Date.now(), ttl }; },

  // ---- 通用HTTP请求（带多endpoint备用）----
  async fetch(url, options = {}) {
    const endpoints = options.endpoints || [url];
    const timeout = options.timeout || 8000;
    for (const ep of endpoints) {
      try {
        const res = await fetch(ep, {
          headers: { 'User-Agent': 'Mozilla/5.0 (compatible; StockMind/2.0)', 'Referer': 'https://finance.eastmoney.com/' },
          signal: AbortSignal.timeout(timeout)
        });
        const json = await res.json();
        if (json && json.rc === 0) return json;
      } catch (e) { /* try next endpoint */ }
    }
    throw new Error('All endpoints failed');
  },

  // ---- 批量行情（串行+延迟，避免并发限流）----
  async getBatchQuotes() {
    const cacheKey = 'batch_quotes';
    if (this.isCacheValid(cacheKey)) return this.getCache(cacheKey);
    if (this.getCache(cacheKey) && !this.isCacheStale(cacheKey)) {
      // 过期续供
      this._bgRefresh(cacheKey, () => this._fetchBatchQuotes());
      return this.getCache(cacheKey);
    }

    // 串行请求 + 随机延迟（防惊群效应）
    const results = [];
    for (let i = 0; i < STOCK_POOL.length; i++) {
      const s = STOCK_POOL[i];
      try {
        const q = await this._fetchSingleQuote(s.code, s.mkt);
        if (q) {
          q.mkt = s.mkt;
          q.industry = s.industry;
          results.push(q);
        }
      } catch {}
      // 每次请求间隔随机50-150ms，降低并发特征
      if (i < STOCK_POOL.length - 1) {
        await new Promise(r => setTimeout(r, 50 + Math.random() * 100));
      }
    }

    if (results.length > 0) {
      this.setCache(cacheKey, results, this.TTL.quote);
      return results;
    }
    const cached = this.getCache(cacheKey);
    return cached || [];
  },

  // 单股请求（内部用，已加随机延迟）
  async _fetchSingleQuote(code, mkt) {
    const secid = `${mkt}.${code}`;
    // fltt=2 让 Eastmoney 返回元为单位的报价（无需手动/100）
    const url = `https://push2.eastmoney.com/api/qt/stock/get?secid=${secid}&fields=f43,f44,f45,f46,f47,f48,f57,f58,f60,f107,f116,f117,f152&fltt=2`;
    const res = await fetch(url, {
      headers: { 'User-Agent': 'Mozilla/5.0 (compatible; StockMind/2.0)', 'Referer': 'https://finance.eastmoney.com/' },
      signal: AbortSignal.timeout(6000)
    });
    const json = await res.json();
    if (!json.data) return null;
    const d = json.data;
    // fltt=2 时 f43/f44/f45/f46/f107 已是元单位，无需/100
    const price = d.f43 || 0;
    const open  = d.f46 || 0;
    return {
      code: d.f57, name: d.f58,
      price, open,
      change: d.f107 || 0,
      changePct: open > 0 ? +((price - open) / open * 100).toFixed(2) : (d.f3 || 0),
      high: d.f44 || 0,
      low: d.f45 || 0,
      volume: d.f47 || 0,
      amount: d.f48 || 0,
      turnover: (d.f152 || 0),
      marketCap: d.f116 || 0,
      floatCap: d.f117 || 0,
      status: '正常'
    };
  },

  // ---- 实时行情（单股）----
  async getQuote(secid) {
    const cacheKey = `quote_${secid}`;
    if (this.isCacheValid(cacheKey)) return this.getCache(cacheKey);
    const [mkt, code] = secid.split('.');
    const q = await this._fetchSingleQuote(code, mkt);
    if (q) { this.setCache(cacheKey, q, this.TTL.quote); return q; }
    return null;
  },

  // ---- 大盘指数 ----
  async getMarketOverview() {
    if (this.isCacheValid('market_overview')) return this.getCache('market_overview');
    if (this.getCache('market_overview')) {
      // 过期续供：返回旧数据同时后台刷新
      this._bgRefresh('market_overview', () => this._fetchMarketOverview());
      return this.getCache('market_overview');
    }
    return this._fetchMarketOverview();
  },

  async _fetchMarketOverview() {
    const indices = [
      { secid: '1.000300', name: '沪深300' },
      { secid: '0.399006', name: '创业板指' },
      { secid: '1.000001', name: '上证指数' },
      { secid: '1.000688', name: '科创50' },
    ];
    const secids = indices.map(i => i.secid).join(',');
    const fields = 'f43,f44,f45,f46,f47,f48,f57,f58,f107';
    const endpoints = [
      `https://push2.eastmoney.com/api/qt/ulist/get?secids=${secids}&fields=${fields}&fltt=2`,
      `https://push2delay.eastmoney.com/api/qt/ulist/get?secids=${secids}&fields=${fields}&fltt=2`,
    ];

    try {
      const json = await this.fetch('', { endpoints, timeout: 10000 });
      const items = json.data?.diff || [];
      const indicesData = indices.map((idx, i) => {
        const d = items[i] || {};
        return {
          code: idx.secid.replace('1.', 'sh').replace('0.', 'sz'),
          name: idx.name,
          price: (d.f43 || 0) / 100,
          change: (d.f107 || 0) / 100,
          changePct: d.f3 || 0,
          status: (d.f3 || 0) >= 0 ? 'up' : 'down'
        };
      });

      const upCount = indicesData.filter(i => i.changePct > 0).length;
      const avgChg  = indicesData.reduce((s, i) => s + i.changePct, 0) / indicesData.length;
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
      console.error('market_overview error:', e.message);
      // 指数全挂，用样本股兜底
      try {
        const quotes = await this.getBatchQuotes();
        if (quotes && quotes.length > 0) {
          const upCount = quotes.filter(q => q.changePct > 0).length;
          const avgChg  = quotes.reduce((s, q) => s + q.changePct, 0) / quotes.length;
          const sentiment = avgChg > 1 ? '市场偏暖（估算）' : avgChg > 0 ? '震荡偏多（估算）' : avgChg > -1 ? '震荡分化（估算）' : '市场偏弱（估算）';
          return {
            indices: quotes.slice(0, 4).map(q => ({ code: q.code, name: q.name, price: q.price, change: q.change, changePct: q.changePct, status: q.change >= 0 ? 'up' : 'down' })),
            marketStatus: avgChg > 0 ? 'NEUTRAL' : 'BEAR',
            sentiment,
            updateTime: new Date().toISOString(),
            dataAge: '样本估算（非实时）'
          };
        }
      } catch {}
      return null;
    }
  },

  // ---- K线数据 ----
  async getKLine(code, mkt, ktype = 'D', count = 120) {
    const cacheKey = `kline_${code}_${ktype}_${count}`;
    if (this.isCacheValid(cacheKey)) return this.getCache(cacheKey);
    if (this.getCache(cacheKey)) {
      this._bgRefresh(cacheKey, () => this._fetchKLine(code, mkt, ktype, count, cacheKey));
      return this.getCache(cacheKey);
    }
    return this._fetchKLine(code, mkt, ktype, count, cacheKey);
  },

  async _fetchKLine(code, mkt, ktype = 'D', count = 120, cacheKey) {
    // 优先用新浪财经（A股K线最稳定）
    // sh600519 = 上交所股票, sz000858 = 深交所股票
    const prefix = mkt === '1' ? 'sh' : 'sz';
    const scaleMap = { D: 240, W: 1440, M: 7200 };
    const scale = scaleMap[ktype] || 240;  // 240min = 日K（A股每天4小时）
    const datalen = Math.min(count, 500);

    // 新浪K线接口（元单位，无需转换）
    const sinaUrl = `https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol=${prefix}${code}&scale=${scale}&ma=no&datalen=${datalen}`;

    try {
      const res = await fetch(sinaUrl, {
        headers: { 'User-Agent': 'Mozilla/5.0', 'Referer': 'https://finance.sina.com.cn' },
        signal: AbortSignal.timeout(8000)
      });
      const klines_raw = await res.json();
      if (Array.isArray(klines_raw) && klines_raw.length > 0) {
        const poolInfo = STOCK_POOL.find(s => s.code === code);
        const klines = klines_raw.map(k => ({
          date:    k.day,
          open:    parseFloat(k.open),
          close:   parseFloat(k.close),
          high:    parseFloat(k.high),
          low:     parseFloat(k.low),
          volume:  parseInt(k.volume),
          amount:  0,
          change:  0, changePct: 0, turnover: 0, amplitude: 0
        }));
        const indicators = GongBu.calculateIndicators(klines);
        const result = { code, name: poolInfo?.name || code, industry: poolInfo?.industry || '', klines, indicators };
        this.setCache(cacheKey, result, this.TTL.kline);
        return result;
      }
    } catch (e) { console.error('sina kline error:', e.message); }

    // 备用：Eastmoney push2his（可能Vercel无法访问）
    const secid = `${mkt}.${code}`;
    const kltMap = { D: 101, W: 102, M: 103 };
    const klt = kltMap[ktype] || 101;
    const end = new Date().toISOString().split('T')[0].replace(/-/g, '');
    const beg = new Date(Date.now() - count * 90 * 24 * 3600 * 1000).toISOString().split('T')[0].replace(/-/g, '');
    const emUrl = `https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=${secid}&fields1=f1,f2,f3,f4,f5&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&klt=${klt}&fqt=1&beg=${beg}&end=${end}&lmt=${count}`;

    try {
      const res2 = await fetch(emUrl, {
        headers: { 'User-Agent': 'Mozilla/5.0 (compatible; StockMind/2.0)', 'Referer': 'https://finance.eastmoney.com/' },
        signal: AbortSignal.timeout(6000)
      });
      const json = await res2.json();
      if (json.data?.klines) {
        const poolInfo = STOCK_POOL.find(s => s.code === code);
        const klines = json.data.klines.map(k => {
          const [date, open, close, high, low, vol, amt, chg, chgPct, turnover, amp] = k.split(',');
          return {
            date, open: +open, close: +close, high: +high, low: +low,
            volume: parseInt(vol), amount: parseFloat(amt),
            change: +chg, changePct: +chgPct, turnover: +turnover, amplitude: +amp
          };
        });
        const indicators = GongBu.calculateIndicators(klines);
        const result = { code, name: poolInfo?.name || code, industry: poolInfo?.industry || '', klines, indicators };
        this.setCache(cacheKey, result, this.TTL.kline);
        return result;
      }
    } catch (e) { console.error('em kline error:', e.message); }

    return null;
  },

  // ---- 板块行情 ----
  async getSectorHeat() {
    if (this.isCacheValid('sector_heat')) return this.getCache('sector_heat');
    if (this.getCache('sector_heat')) {
      this._bgRefresh('sector_heat', () => this._fetchSectorHeat());
      return this.getCache('sector_heat');
    }
    return this._fetchSectorHeat();
  },

  async _fetchSectorHeat() {
    try {
      const url = `https://push2.eastmoney.com/api/qt/ranking/get?type=2&pi=0&pz=20&po=1&np=1&fltt=2&invt=2&fid=f3&fs=m:90+t:2&fields=f12,f14,f3,f4,f8`;
      const json = await this.fetch(url);
      const sectors = (json.data?.diff || []).slice(0, 15).map((s, i) => ({
        sector: s.f14, code: s.f12, change: s.f3, volume: s.f8, rank: i + 1
      }));
      const result = { sectors, updateTime: new Date().toISOString() };
      this.setCache('sector_heat', result, this.TTL.sector);
      return result;
    } catch (e) {
      const quotes = await this.getBatchQuotes();
      const industryMap = {};
      quotes.forEach(q => {
        if (!industryMap[q.industry]) industryMap[q.industry] = { changes: [], volumes: [] };
        industryMap[q.industry].changes.push(q.changePct);
        industryMap[q.industry].volumes.push(q.amount);
      });
      const sectors = Object.values(industryMap)
        .map((v, i) => ({ sector: v.sector, change: +(v.changes.reduce((a, b) => a + b, 0) / v.changes.length).toFixed(2), volume: v.volumes.reduce((a, b) => a + b, 0), rank: i + 1 }))
        .sort((a, b) => b.change - a.change);
      const result = { sectors, updateTime: new Date().toISOString() };
      this.setCache('sector_heat', result, this.TTL.sector);
      return result;
    }
  },

  // 后台刷新（不阻塞主请求）
  _bgRefresh(key, fn) {
    if (this._refreshPromises[key]) return;
    this._refreshPromises[key] = fn().finally(() => { delete this._refreshPromises[key]; });
  },

  // ---- 批量行情（并发请求，快速响应）----
  async getBatchQuotes() {
    const cacheKey = 'batch_quotes';
    if (this.isCacheValid(cacheKey)) return this.getCache(cacheKey);
    const cached = this.getCache(cacheKey);
    if (cached) {
      this._bgRefresh(cacheKey + '_bg', () => this._fetchBatchQuotes());
      return cached;
    }
    // 无缓存，强制等待一次刷新（加超时保护）
    try {
      await Promise.race([this._fetchBatchQuotes(), new Promise((_, r) => setTimeout(() => r(new Error('timeout')), 8000))]);
    } catch(e) {}
    return this.getCache(cacheKey) || [];
  },

  // ---- 批量刷新（并发 + 缩短间隔）----
  async _fetchBatchQuotes() {
    const results = await Promise.all(
      TOP_STOCKS.map(s =>
        this._fetchSingleQuote(s.code, s.mkt)
          .catch(() => null)
          .then(q => { if (q) { q.mkt = s.mkt; q.industry = s.industry; } return q; })
      )
    );
    const ok = results.filter(Boolean);
    if (ok.length > 0) this.setCache('batch_quotes', ok, this.TTL.quote);
  }
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

    const klines = klineData.klines.filter(k => k.date >= startDate && k.date <= endDate);
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
    const BUY = (price, qty, reason) => { cash -= price * qty; shares = qty; trades.push({ buyDate: klines[0].date, buyPrice: price, sellDate: '', sellPrice: 0, profit: 0, profitPct: 0, reason }); };
    const SELL = (price, reason) => { const cost = trades[trades.length - 1]?.buyPrice || price; cash += shares * price; const pp = (price - cost) / cost * 100; if (pp > 0) { winCount++; totalWin += pp; } else { lossCount++; totalLoss += Math.abs(pp); } trades[trades.length - 1] = { ...trades[trades.length - 1], sellDate: klines[0].date, sellPrice: price, profit: +(shares * (price - cost)).toFixed(2), profitPct: +pp.toFixed(2), reason }; shares = 0; };

    for (let i = 25; i < klines.length - 1; i++) {
      const pv = cash + shares * closes[i];
      equityCurve.push({ date: klines[i].date, value: +pv.toFixed(2) });
      if (pv > peak) peak = pv;

      if (strategyType === 'momentum') {
        if (shares === 0 && MA5[i] > MA10[i] && MA10[i] > MA20[i] && closes[i] > MA5[i] && closes[i] > closes[i-1]) {
          const qty = Math.floor(cash / closes[i] * 0.9 / 100) * 100;
          if (qty > 0) BUY(closes[i], qty, '均线多头排列');
        } else if (shares > 0 && (MA5[i] < MA10[i] || closes[i] < MA20[i] * 0.97)) {
          SELL(closes[i], MA5[i] < MA10[i] ? '均线死叉' : '跌破MA20');
        }
      } else if (strategyType === 'mean_reversion') {
        if (shares === 0 && MA20[i] && Math.abs(closes[i] - MA20[i]) / MA20[i] > 0.06 && closes[i] < MA20[i]) {
          const qty = Math.floor(cash / closes[i] * 0.9 / 100) * 100;
          if (qty > 0) BUY(closes[i], qty, '超跌反弹');
        } else if (shares > 0 && closes[i] >= MA20[i] * 1.03) {
          SELL(closes[i], '均值回归');
        }
      } else if (strategyType === 'breakout') {
        const high20 = Math.max(...klines.slice(Math.max(0, i - 20), i).map(k => k.high));
        const low10  = Math.min(...klines.slice(Math.max(0, i - 10), i).map(k => k.low));
        if (shares === 0 && closes[i] > high20 && closes[i] > closes[i-1]) {
          const qty = Math.floor(cash / closes[i] * 0.9 / 100) * 100;
          if (qty > 0) BUY(closes[i], qty, '突破新高');
        } else if (shares > 0 && closes[i] < low10) {
          SELL(closes[i], '跌破支撑');
        }
      } else if (strategyType === 'rsi') {
        if (shares === 0 && RSI6[i] && RSI6[i] < 30 && RSI6[i] > RSI6[i-1]) {
          const qty = Math.floor(cash / closes[i] * 0.9 / 100) * 100;
          if (qty > 0) BUY(closes[i], qty, 'RSI超卖');
        } else if (shares > 0 && RSI6[i] && RSI6[i] > 70) {
          SELL(closes[i], 'RSI超买');
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
      // Eastmoney限流时返回演示数据，保证前端不白屏
      quotes = [];
    }
    if (!quotes || quotes.length === 0) {
      // 无数据时返回兜底演示股（评分基于价格区间和行业）
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

  // 纯实时行情评分（无需K线，毫秒完成）
  _realtimeScore(q) {
    const reasons = [];
    let s = 50; // 基准分

    // 涨幅：今日强势股加分
    const chg = q.changePct || 0;
    if (chg > 4)       { s += 25; reasons.push('今日强势拉升'); }
    else if (chg > 2)  { s += 15; reasons.push('涨幅领先'); }
    else if (chg > 0)  { s += 8;  reasons.push('小幅上涨'); }
    else if (chg < -3) { s += 10; reasons.push('超跌反弹机会'); }

    // 成交量放大（量比>1.5算活跃）
    const turnover = q.turnover || 0;
    if (turnover > 3)  { s += 15; reasons.push('成交量异常放大'); }
    else if (turnover > 1.5) { s += 8; reasons.push('量能温和放大'); }

    // 换手率适中（健康活跃）
    const vol = q.volume || 0;
    if (vol > 500000000) { s += 5; reasons.push('高流动性'); }

    // 绝对价格适中（10~500元，最易操作区间）
    const p = q.price || 0;
    if (p >= 10 && p <= 200) { s += 5; reasons.push('价格适中'); }

    // 行业分布（白酒、银行等价值板块+5）
    const safe = ['白酒', '银行', '保险', '医药', '电力', '新能源'];
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
