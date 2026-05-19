# StockMind 架构分析 & 缠论集成方案

> 基于 `/root/stock-picker/backend/` 全量代码逆向分析

---

## 一、现有架构总览

### 技术栈
- **框架**: FastAPI (Python 3.11)
- **数据层**: akshare (股票数据) + SQLite (持久化)
- **外部API**: 腾讯 qt.gtimg.cn (实时行情) + 新浪 (K线) + MiniMax (AI)
- **缓存**: 内存字典 `utils/cache.py`
- **定时任务**: `jobs/scheduler.py`
- **部署**: Vercel

### 路由注册
```
/api/stock/*    → stock.router     (K线/技术指标/资金流向)
/api/picker/*   → picker.router    (智能选股)
/api/backtest/* → backtest.router  (策略回测)
/api/portfolio/* → portfolio.router (持仓管理)
/api/ai/*       → ai.router        (AI策略引擎)
/api/*          → health check
```

### 选股流水线（PickerService - 6步）
```
Step 1: get_stock_list() → 全量数据（top 500只活跃股）
        + get_market_status() → 市场状态
        + get_industry_leaderboard() → 行业排行

Step 2: _value_filter() → 价值筛选（PE 5-50 / PB≤5 / ROE≥8% / 非ST）
        ↓ 价值池 A

Step 3: _trend_filter() → 趋势确认（6条件取4：MA5>MA20 / MA20>MA60 / 动量>0 / 量比≥1.3 / MACD>0 / RSI 30-75）
        ↓ 趋势池 B

Step 4: _money_filter() → 资金验证（北向资金正流入）
        ↓ 资金池 C

Step 5: _score_and_rank() → 综合评分（5维度各20%）
        - 动量得分(20%): 20日动量/10*10, capped at 20
        - 趋势得分(20%): conditions_met/6*20
        - 资金得分(20%): binary (有北向=20, 无=0)
        - 基本面得分(20%): ROE/20*10 + profit_growth/20*10, capped at 20
        - 形态得分(20%): RSI/75*10+10, capped at 20
        
Step 6: _risk_check() → 风控（行业分散≤2/行业，最大5只，仓位上限）
        ↓ 最终 top 10 信号输出
```

### 现有回测策略（BacktestService）
| 策略ID | 买入信号 | 卖出信号 |
|--------|---------|---------|
| `value_trend` | MA5>MA20, RSI∈(30,75), close>MA20, vol>MA20×1.3 | close<MA20, RSI>85, MA5<MA20 |
| `momentum` | break 20-day high | -8%止损 |
| `breakout` | close>BB上轨, vol>MA10×1.5 | close<BB中轨 |

### 现有AI集成（AIService）
- MiniMax API (MiniMax-Text-01)
- 4个功能: 策略生成 / 策略反推 / 股票问诊 / 每日复盘
- 无缠论相关提示词

---

## 二、缠论集成方案（推荐优先级排序）

### Phase 1: 核心引擎（最直接价值）
**新增文件**: `services/chanservice.py`  
**修改文件**: `picker_service.py`, `data_service.py`, `main.py`

#### 2.1 新增 ChanService
```
ChanService
├── detect_fenxing(kline) → 顶分型/底分型
├── detect_bi(fenxings) → 笔序列
├── detect_zhongshu(bis) → 中枢识别
├── detect_beichi(kline) → 背驰检测（MACD柱面积比）
├── detect_3buy_points(zhongshu, beichi) → 三类买点检测
├── detect_3sell_points(zhongshu, beichi) → 三类卖点检测
├── interval_tao(kline, levels) → 区间套（多级别联动）
├── multi_level_analysis(code) → 多级别联立分析
└── score_chan(stock) → 缠论评分（0-20分）
```

关键算法：
- **背驰检测**: 比较两段同向走势的MACD柱面积，面积减小=背驰
- **中枢识别**: 找3段次级别走势重叠区间
- **三类买点**: 
  - 1类：趋势背驰段底背驰
  - 2类：1类后次级别回抽不创新低
  - 3类：离开中枢后回抽不进中枢
- **区间套**: 大级别背驰段内找小级别背驰逐级定位

#### 2.2 改造 PickerService
在 Step 4（资金验证）和 Step 5（评分）之间插入缠论验证步骤：

```
Step 4.5: _chan_filter() → 缠论验证（新增）
    - 对每个候选计算缠论信号
    - 标记：出现第几类买点、背驰状态、中枢位置
    - 缠论评分 (0-20分)
    
Step 5: _score_and_rank() → 综合评分修改为6维度
    - 动量得分(15%)
    - 趋势得分(15%)
    - 资金得分(15%)
    - 基本面得分(15%)
    - **形态得分(15%) → 替换为缠论得分(25%)**
    - **新增: 缠论信号强度(15%)**
```

#### 2.3 新增 API 路由
```
GET /api/chan/analyze/{code}     → 完整缠论分析报告
GET /api/chan/fenxing/{code}     → 分型分析
GET /api/chan/zhongshu/{code}    → 中枢分析  
GET /api/chan/beichi/{code}      → 背驰检测
GET /api/chan/signals/{code}     → 买卖点信号
GET /api/chan/score/{code}       → 缠论评分
```

---

### Phase 2: 缠论回测策略
**修改文件**: `backtest_service.py`, `routers/backtest.py`

新增 `chan_theory` 策略类型：

| 子策略 | 买入 | 卖出 |
|--------|------|------|
| `chan_1st_buy` | 趋势底背驰（第一类买点） | 顶背驰/中枢上沿遇阻 |
| `chan_2nd_buy` | 第二类买点（回抽不新低） | -8%止损/趋势背驰 |
| `chan_3rd_buy` | 第三类买点（回抽不进中枢） | 中枢上沿背驰 |
| `chan_zhongshu_osc` | 中枢下沿盘整背驰 | 中枢上沿盘整背驰 |

参数优化重点：
- 中枢级别选择（日线/30分钟/5分钟）
- 背驰力度阈值（MACD柱面积比%）
- 二三类买点确认窗口期

---

### Phase 3: AI 集成增强
**修改文件**: `ai_service.py`

在以下功能中加入缠论维度：

1. **股票问诊** → 增加缠论技术面分析维度
   - 提示词增加："请从缠论角度分析：当前形成第几类买卖点？中枢位置在哪？是否出现背驰？"

2. **每日复盘** → 增加缠论市场结构分析
   - 提示词增加："用缠论分析当前大盘走势：日线级别中枢位置、是否出现背驰段、市场处于什么阶段？"

3. **策略生成** → 支持缠论策略模板
   - 新增缠论策略模板：三类买卖点、背驰检测、区间套

---

### Phase 4: 前端可视化（可选）
- K线图上标记分型（顶/底）
- 显示中枢区间（染色区域）
- 标记买卖点信号
- 背驰指示

---

## 三、技术可行性评估

### 可实现性等级
| 模块 | 难度 | 数据依赖 | 说明 |
|------|------|---------|------|
| 分型检测 | ⭐ (易) | K线数据 | 纯形态识别，3根K线比较 |
| 笔识别 | ⭐⭐ (中) | 分型序列 | 需要处理包含关系、独立K线 |
| 中枢识别 | ⭐⭐⭐ (中高) | 笔序列 | 需递归构造次级别走势 |
| 背驰检测 | ⭐⭐ (中) | MACD + K线 | MACD柱面积比较即可 |
| 三类买点 | ⭐⭐⭐ (中高) | 中枢+背驰 | 需要先有中枢和走势类型 |
| 区间套 | ⭐⭐⭐⭐ (高) | 多级别K线 | 多分辨率协同分析 |
| 第一类买点回测 | ⭐⭐⭐ (中高) | 历史K线 | 需要精确判定背驰段 |

### 关键发现
1. 现有 akshare 和 Tencent API 提供的K线数据**足够支撑**分型→笔→中枢的递归计算
2. MACD数据已有（`data_service.py` 中计算），可直接用于背驰比较
3. 多级别分析需要获取日线/30分钟/5分钟三个级别的K线
4. 第二类/第三类买点需要**精确的次级别走势分解**，这是实现难点

---

## 四、建议实施顺序

```
Week 1: ChanService核心 (分型+笔+中枢+背驰) + API路由
Week 2: 融入选股流水线 (修改PickerService评分引擎)
Week 3: 缠论回测策略 (chan_theory + 参数优化)
Week 4: AI增强 + 前端K线标记 (可选)
```

**MVP（最小可行产品）**: 
1. ChanService 的 `detect_beichi()` + `detect_3buy_points()`
2. 在 `_score_and_rank()` 中增加缠论评分维度
3. 新增 `/api/chan/signals/{code}` 路由
