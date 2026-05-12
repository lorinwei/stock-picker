# StockMind V2 规格说明书

> 基于"三省六部"架构的智能选股系统，取长补短：他优我优，他无我有

---

## 一、定位升级

**一句话定位**：小白股民的 AI 跟投助手

**核心价值**：
- 不靠情绪买卖、不追小道消息
- 用客观数据辅助决策
- AI 告诉你买什么 + 一键跟投

**目标用户**：想炒股但不懂技术分析的小白用户

---

## 二、架构设计：三省六部

### 三省（决策主链路）

```
┌─────────────────────────────────────────────┐
│              太子院 CrownPrince（数据层）       │
│  ├─ akshare 实时行情                          │
│  ├─ 内置演示数据（可切换）                     │
│  └─ 数据校验 + 缓存                           │
└──────────────────────┬──────────────────────┘
                       ↓
┌─────────────────────────────────────────────┐
│              中书省 ZhongshuSheng（策略层）     │
│  ├─ 多因子评分模型                            │
│  ├─ 技术信号生成（MACD/KDJ/RSI/布林带）       │
│  └─ 板块轮动分析                              │
└──────────────────────┬──────────────────────┘
                       ↓
┌─────────────────────────────────────────────┐
│              门下省 MenxiaSheng（风控层）       │
│  ├─ 止损线管理（一票否决）                     │
│  ├─ 回撤限制                                 │
│  ├─ 仓位约束                                 │
│  └─ 风险事件记录                              │
└──────────────────────┬──────────────────────┘
                       ↓
┌─────────────────────────────────────────────┐
│              尚书省 ShangshuSheng（执行层）    │
│  ├─ 跟投信号分发                             │
│  ├─ 持仓管理                                 │
│  └─ 收益追踪                                 │
└─────────────────────────────────────────────┘
```

### 六部（职能部门）

| 部 | 职责 | 当前状态 |
|----|------|---------|
| 吏部 LiBu | 策略注册/生命周期管理 | 待实现 |
| 户部 HuBu | 现金/成本/净值核算 | 基础 |
| 礼部 LiBuR | 业绩报表/策略排行 | 待升级 |
| 兵部 BingBu | 撮合执行/交易管理 | 基础 |
| 刑部 XingBu | 违规记录/风险事件 | 待实现 |
| 工部 GongBu | 行情清洗/指标计算 | 基础 |

---

## 三、页面规划

### 页面结构（5个核心页面）

```
┌──────────────────────────────────────────┐
│  StockMind V2 智能选股控制台               │
├──────────────────────────────────────────┤
│  首页 | 选股池 | 持仓 | AI助手 | 行情     │
└──────────────────────────────────────────┘
```

#### 页面1：首页（大盘 + AI推荐信号）

```
┌────────────────────────────────────┐
│  沪深300  3,820.5  ↑0.82%  🚀    │  ← 大盘温度计（颜色随涨跌）
├────────────────────────────────────┤
│  🧠 今日AI推荐  5月11日 星期一      │
│  ┌────────────────────────────────┐ │
│  │ 贵州茅台 600519         ⭐92  │ │
│  │ 买入价 ¥1850  目标 ¥1980      │ │
│  │ 止损 ¥1757  仓位 20%         │ │
│  │ 🧠 AI理由：MACD金叉+北向资金   │ │
│  │ [一键跟投]                   │ │
│  └────────────────────────────────┘ │
│  次选：宁德时代 88⭐ / 招商银行 85⭐ │
├────────────────────────────────────┤
│  ✅ 历史胜率 78%  👥3,241人跟投    │
└────────────────────────────────────┘
```

#### 页面2：选股池（AI信号列表）

```
┌────────────────────────────────────┐
│  📊 AI选股池                       │
│  [综合] [低估] [成长] [北向] [技术] │
├────────────────────────────────────┤
│  ⭐92  贵州茅台 600519  白酒       │
│      买入价 ¥1850  目标 ¥1980       │
│      MACD金叉 | 北向净买入 | ROE高  │
│  ━━━━━━━━━━━━━━━━░░░░░  信号强度  │
├────────────────────────────────────┤
│  ⭐88  宁德时代 300750  新能源     │
│      +1.2%  成交量放大 | 趋势向上   │
├────────────────────────────────────┤
│  [查看更多 →]                      │
└────────────────────────────────────┘
```

#### 页面3：持仓管理

```
┌────────────────────────────────────┐
│  💼 我的持仓                        │
│  总资产 ¥600,000  浮盈 +¥28,000    │
├────────────────────────────────────┤
│  🟢 贵州茅台  100股  成本¥1750     │
│     当前¥1850  盈+¥10,000  +5.71%│
│     建议：持有 | 距止损 ¥1757       │
├────────────────────────────────────┤
│  🟡 宁德时代  200股  成本¥180.5   │
│     当前¥175.2  亏-¥1,060  -2.94% │
│     ⚠️ 接近止损位                   │
├────────────────────────────────────┤
│  [+ 添加持仓] [查看全部交易记录]    │
└────────────────────────────────────┘
```

#### 页面4：AI助手（对话式选股）

```
┌────────────────────────────────────┐
│  💬 AI选股助手                      │
├────────────────────────────────────┤
│  👤 帮我找低估的白酒股              │
│  🤖 贵州茅台 PE偏高，五粮液更低估   │
│      当前PE32.1，接近历史低位...    │
│      [查看分析报告] [一键跟投]      │
├────────────────────────────────────┤
│  [输入你想选股的条件...]            │
│  快捷：[低估] [高ROE] [北向净买入] │
└────────────────────────────────────┘
```

#### 页面5：行情监控

```
┌────────────────────────────────────┐
│  📈 市场行情                        │
│  [指数] [板块] [强势股] [北向]     │
├────────────────────────────────────┤
│  沪深300  3,820.5  ↑0.82%  🚀     │
│  创业板    1,852    ↓0.45%  📉     │
│  上证指数  3,280    ↑0.31%  📈     │
├────────────────────────────────────┤
│  板块涨幅榜                          │
│  1. 新能源  +2.3%  ▲▲▲            │
│  2. 半导体  +1.8%  ▲▲            │
│  3. 白酒    +0.9%  ▲             │
└────────────────────────────────────┘
```

---

## 四、API 接口设计

### 基础信息
- Base URL: `https://stock-picker-ten.vercel.app/api`
- 认证方式: Bearer Token（预留）
- 返回格式: `{ code: 0, data: {...}, message: 'ok' }`

### 接口列表

#### 健康检查
```
GET /api/health
Response: { code: 0, data: { status: 'ok', time: '2026-05-11T...' } }
```

#### 大盘数据
```
GET /api/market/overview
Response: {
  indices: [
    { name: '沪深300', code: 'sh000300', price: 3820.5, change: 0.82, changePct: 0.82 },
    { name: '创业板', code: 'sz399006', price: 1852.3, change: -8.5, changePct: -0.46 },
    { name: '上证指数', code: 'sh000001', price: 3280.1, change: 10.2, changePct: 0.31 }
  ],
  marketStatus: 'BULL',
  sentiment: '乐观'
}
```

#### AI 推荐信号
```
GET /api/signals/today
Response: {
  mainPick: {
    code: '600519', name: '贵州茅台', score: 92,
    buyPrice: 1850, targetPrice: 1980, stopLoss: 1757,
    positionRatio: 20, signal: 'BUY',
    reasons: ['MACD金叉', '北向资金净买入', 'ROE 25%以上'],
    publishTime: '2026-05-11 09:30:00'
  },
  alternatives: [
    { code: '300750', name: '宁德时代', score: 88, change: 1.2, reasons: [...] },
    { code: '600036', name: '招商银行', score: 85, change: 0.8, reasons: [...] }
  ],
  stats: { winRate: 78, followerCount: 3241, pickCount: 156 }
}
```

#### 选股池
```
GET /api/stockpool?category=growth&page=1&pageSize=20
Response: {
  items: [
    {
      code: '600519', name: '贵州茅台', industry: '白酒',
      score: 92, price: 1850, change: 0.82,
      signals: ['BUY'], reasons: ['ROE高于同行', '北向净买入'],
      pe: 45.6, roe: 32.5, marketCap: 23240
    }
  ],
  total: 156, page: 1, pageSize: 20
}
```

#### K线数据
```
GET /api/kline?code=600519&ktype=D&start=2026-01-01&end=2026-05-10
Response: {
  code: '600519', name: '贵州茅台',
  klines: [
    { date: '2026-01-02', open: 1800, high: 1820, low: 1790, close: 1815, volume: 2500000 },
    ...
  ],
  indicators: {
    MA: { MA5: [1810, ...], MA10: [1805, ...], MA20: [1798, ...] },
    MACD: { DIF: [...], DEA: [...], MACD: [...] },
    KDJ: { K: [...], D: [...], J: [...] },
    RSI: [65, 68, 72, ...]
  }
}
```

#### 持仓管理
```
GET /api/portfolio
POST /api/portfolio/add    { code, name, shares, buyPrice, buyDate }
PUT  /api/portfolio/:id     { shares, currentPrice }
DELETE /api/portfolio/:id
```

#### 风控检查
```
POST /api/risk/check
Request: { code: '600519', action: 'BUY', price: 1850, quantity: 100, portfolioValue: 600000 }
Response: {
  approved: true,        // 门下省一票否决结果
  riskLevel: 'safe',    // safe / warning / danger
  warnings: [],          // 风险提示
  maxPosition: 5,        // 最大持仓数
  maxLossPct: 8,        // 最大亏损比例
  currentExposure: 30.8  // 当前仓位占比
}
```

#### 回测
```
POST /api/backtest
Request: { stockCode: '600519', startDate: '2026-01-01', endDate: '2026-05-10', initialCash: 100000, strategyType: 'momentum' }
Response: {
  recordId: 'bt_xxx',
  totalReturn: 35.8,         // 总收益率
  annualizedReturn: 52.3,    // 年化收益率
  maxDrawdown: 8.5,          // 最大回撤
  winRate: 62.5,             // 胜率
  profitFactor: 1.85,        // 盈亏比
  sharpeRatio: 1.95,        // 夏普比率
  totalTrades: 24,
  equityCurve: [            // 权益曲线
    { date: '2026-01-02', value: 100000 },
    { date: '2026-01-03', value: 101500 },
    ...
  ],
  trades: [...]
}
```

#### AI 对话
```
POST /api/ai/chat
Request: { message: '帮我找低估的白酒股', context: [] }
Response: {
  reply: '根据当前估值分析，五粮液（000858）PE32.1，低于茅台的45.6，属于...',
  stocks: [
    { code: '000858', name: '五粮液', pe: 32.1, roe: 25.3, reason: '估值偏低' }
  ],
  actions: [{ label: '查看分析', type: 'analyze', code: '000858' }]
}
```

#### 板块数据
```
GET /api/sector/leaderboard
Response: {
  sectors: [
    { name: '新能源', change: 2.3, stockCount: 45, leaders: [...] },
    { name: '半导体', change: 1.8, stockCount: 38, leaders: [...] }
  ]
}
```

---

## 五、数据结构

### 股票
```typescript
interface Stock {
  code: string;        // 600519
  name: string;        // 贵州茅台
  industry: string;    // 白酒
  price: number;       // 当前价
  change: number;      // 涨跌额
  changePct: number;   // 涨跌幅%
  volume: number;      // 成交量
  marketCap: number;   // 总市值（亿）
  pe?: number;         // 市盈率
  pb?: number;         // 市净率
  roe?: number;        // 净资产收益率
  revenueGrowth?: number;  // 营收增长
  profitGrowth?: number;   // 利润增长
}
```

### 持仓
```typescript
interface Position {
  id: string;
  code: string;
  name: string;
  shares: number;        // 持股数
  cost: number;          // 成本价
  currentPrice: number;   // 当前价
  marketValue: number;   // 市值
  profit: number;        // 盈亏金额
  profitPercent: number; // 盈亏比例
  buyDate: string;       // 买入日期
  riskStatus: 'safe' | 'warning' | 'danger';
  stopLoss?: number;     // 止损价
}
```

### 选股信号
```typescript
interface Signal {
  code: string;
  name: string;
  score: number;         // 1-100综合评分
  type: 'BUY' | 'SELL' | 'WATCH';
  buyPrice?: number;
  targetPrice?: number;
  stopLoss?: number;
  positionRatio?: number;
  reasons: string[];     // 入选理由
  publishTime: string;
}
```

### 回测结果
```typescript
interface BacktestResult {
  recordId: string;
  stockCode: string;
  strategyType: string;
  totalReturn: number;
  annualizedReturn: number;
  maxDrawdown: number;
  winRate: number;
  profitFactor: number;
  sharpeRatio: number;
  totalTrades: number;
  equityCurve: { date: string; value: number }[];
  trades: Trade[];
}
```

---

## 六、实施计划

### Phase 1：架构 + 数据（本周）
- [x] 前端部署到 Vercel ✅
- [x] Node.js API 上线 ✅
- [ ] 重构 api.js，引入三省六部结构
- [ ] 接入 akshare 真实行情
- [ ] 风控层（止损/回撤拦截）

### Phase 2：回测 + 策略（下周）
- [ ] 回测引擎（权益曲线 + 绩效指标）
- [ ] 策略基类 + 4个内置策略
- [ ] 策略参数配置界面

### Phase 3：AI 增强（第三周）
- [ ] MiniMax API 接入
- [ ] AI 选股对话
- [ ] 自动回测验证

### Phase 4：UI 升级（第四周）
- [ ] 深色主题升级（对标金策智算 dashboard）
- [ ] K线图（lightweight-charts）
- [ ] 实时数据看板

---

## 七、竞争优势（他优我优，他无我有）

| 方面 | 金策智算 | StockMind V2 |
|------|---------|-------------|
| 定位 | 专业量化工具 | 小白友好 AI 跟投 |
| 架构 | 三省六部 ✅ | 三省六部 ✅ |
| UI | 专业但复杂 | 简洁易用 ✅ |
| AI选股 | 无 | AI对话 + 一键跟投 ✅ |
| 跟投系统 | 无 | 社交跟投 + 排行榜 ✅ |
| 数据源 | 多数据源 | akshare + 演示切换 ✅ |
| 目标用户 | 量化开发者 | 小白普通股民 ✅ |
