# 缠论集成StockMind — 实施计划（完整规格）

> 目标：将缠中说禅技术分析体系融入StockMind的选股流水线、回测引擎和AI分析
> 优先级：MVP → 扩展 → 优化

---

## Phase 1: ChanService 核心引擎（4个文件）

### 1.1 新建 `backend/services/chanservice.py`

**类**: `ChanService`

#### 算法清单（从 108课 提取的完整实现）

```python
# ──── 基础层 ────
function handle_baohan(k1, k2, direction)
→ 包含关系处理
→ 向上趋势方向：取高高（high_max, low_max）
→ 向下趋势方向：取低低（low_min, high_min）

function detect_fenxing(klines) → (頂分型列表, 底分型列表)
→ 遍历三根K线判断：
  頂分型：k2.high=max, k2.low=max
  底分型：k2.low=min, k2.high=min
→ 先做包含关系处理

function detect_bi(klines) → (向上笔列表, 向下笔列表)
→ 从分型序列提取笔
→ 规则：頂底交替、至少1根独立K线、至少延伸6根K线单位

# ──── 结构层 ────
function detect_zhongshu(bis, level=0) → 中枢列表 [{high, low, start, end}]
→ 至少3段连续次级别走势重叠
→ 重叠区间 = max(三段低点中的最高), min(三段高点中的最低)

function classify_trend(zhongshus) → 'uptrend'|'downtrend'|'panzheng'
→ 趋势：≥2个同向不重叠中枢
→ 盘整：1个中枢

function zhongshu_zn_curve(zhongshu, ci_level_bis) → Zn曲线
→ 每个次级别震荡的中轴位置
→ 比较Zn与中枢区间ZZ（判断震荡强弱）

# ──── 信号层 ────
function detect_beichi(kline_segment1, kline_segment2, method='macd_area')
→ 两段同向走势的力度比较
→ method='macd_area': MACD柱面积（红柱/绿柱累加）
→ method='macd_line': DIF高度比较
→ method='vol': 成交量递减
→ 输出：{is_beichi: bool, type: 'top'|'bottom', strength: 0~1}

function detect_buy_points(code, klines_1d, klines_30m, klines_5m) → 买卖点信号
→ 第一类买点：下跌趋势背驰段底背驰（区间套逐级确认）
→ 第二类买点：1买后次级别回抽不创新低/盘整背驰
→ 第三类买点：次级别离开→次级别回抽不进中枢
→ 三类卖点同理反向

function interval_tao(kline_large, kline_mid, kline_small) → 区间套序列
→ 大级别背驰段 → 中级别背驰确认 → 小级别精确定位

# ──── 评分层 ────
function score_chan(buy_points, beichi, zhongshu, trend) → float (0~25)
→ 有买点信号 +10 ~ +25
→ 背驰强度 × 权重
→ 趋势质量（中枢清晰度、震荡幅度）
→ 返回缠论维度评分

function entry_reasons(buy_points, beichi) → List[str]
→ 生成中文缠论入选理由
例：
- "日线第三类买点形成，次级别回抽未入中枢"
- "日线底背驰确认，MACD柱面积缩减52%"
- "30分钟级别出现区间套底背驰"
- "中枢下沿盘整背驰，次级别放量启动"
```

#### 数据流设计
```
K线数据 (DataService)
    ↓
handle_baohan() → 包含处理后的K线序列
    ↓
detect_fenxing() → 顶分型/底分型位置
    ↓
detect_bi() → 笔序列（向上笔/向下笔）
    ↓
detect_zhongshu() → 中枢区间 + 级别
    ↓
classify_trend() → 走势类型分类
    ↓
detect_beichi() → 背驰判定 + 力度
    ↓
detect_buy_points() → 三类买卖点信号
    ↓
score_chan() → 缠论量化评分
```

---

### 1.2 修改 `backend/services/picker_service.py`

**改动点**:

1. 导入 ChanService:
```python
from services.chanservice import ChanService
```

2. 在 `__init__` 中增加:
```python
self.chan_service = ChanService()
```

3. 新增 `_chan_filter()` 方法：
```python
async def _chan_filter(self, candidates: List[Dict]) -> List[Dict]:
    """Step 4.5: 缠论验证 — 对每个候选分析缠论结构"""
    for stock in candidates:
        try:
            # 获取K线数据
            klines = await self.data_service.get_kline(stock["code"], "D", limit=200)
            analysis = self.chan_service.analyze(stock["code"], klines)
            stock["chan_analysis"] = analysis
            stock["chan_score"] = self.chan_service.score_chan(
                analysis.get("buy_points", {}),
                analysis.get("beichi", {}),
                analysis.get("zhongshu", []),
            )
        except:
            stock["chan_score"] = 0
            stock["chan_analysis"] = {}
    return candidates
```

4. 修改 `generate_signals()` 在 Step 4 和 Step 5 之间插入 Step 4.5:
```python
# Step 4.5: 缠论验证（新增）
logger.info("Step 4.5: 缠论验证...")
chan = await self._chan_filter(funded)
logger.info(f"  → 缠论池: {len(chan)}只")
```

5. 修改 `_score_and_rank()` 评分维度：
```python
# 原5维 → 新6维（总分100分不变，分配调整）
momentum_score  =  15% (原20%)
trend_score     =  15% (原20%)  
money_score     =  15% (原20%)
fundamental_scr =  15% (原20%)
**chan_score**   =  25% (新增，替换原shape_score 20%)
**shape_score**  =  15% (原20%→15%，改良后的形态评分)
```

6. 修改 entry_reasons 生成逻辑，加入缠论理由：
```python
# 原reasons追加缠论理由
if stock.get("chan_analysis", {}).get("buy_points", {}).get("third_buy"):
    reasons.append("日线第三类买点形成")
if stock.get("chan_analysis", {}).get("beichi", {}).get("is_beichi"):
    reasons.append(f"底背驰确认，力度减弱显著")
```

---

### 1.3 新增 `backend/routers/chan.py`

```python
from fastapi import APIRouter, Query, HTTPException
from services.chanservice import ChanService
from services.data_service import DataService

router = APIRouter()
chan_service = ChanService()
data_service = DataService()

@router.get("/analyze/{code}")
async def chan_analyze(code: str):
    """完整缠论分析"""
    klines = await data_service.get_kline(code, "D", limit=300)
    results = chan_service.analyze(code, klines)
    return {"code": 0, "data": results, "message": "ok"}

@router.get("/fenxing/{code}")
async def chan_fenxing(code: str):
    """顶底分型分析"""
    klines = await data_service.get_kline(code, "D", limit=100)
    fenxings = chan_service.detect_fenxing(klines)
    return {"code": 0, "data": fenxings, "message": "ok"}

@router.get("/zhongshu/{code}")
async def chan_zhongshu(code: str):
    """中枢分析"""
    klines = await data_service.get_kline(code, "D", limit=300)
    bis = chan_service.detect_bi(klines)
    zhongshus = chan_service.detect_zhongshu(bis)
    return {"code": 0, "data": zhongshus, "message": "ok"}

@router.get("/beichi/{code}")
async def chan_beichi(code: str, method: str = "macd_area"):
    """背驰检测"""
    klines = await data_service.get_kline(code, "D", limit=200)
    beichi = chan_service.detect_beichi(klines, method)
    return {"code": 0, "data": beichi, "message": "ok"}

@router.get("/signals/{code}")
async def chan_signals(code: str):
    """三类买卖点信号"""
    klines = await data_service.get_kline(code, "D", limit=300)
    signals = chan_service.detect_buy_points(code, klines, [], [])
    return {"code": 0, "data": signals, "message": "ok"}

@router.get("/score/{code}")
async def chan_score(code: str):
    """缠论评分"""
    klines = await data_service.get_kline(code, "D", limit=300)
    analysis = chan_service.analyze(code, klines)
    score = chan_service.score_chan(
        analysis.get("buy_points", {}),
        analysis.get("beichi", {}),
        analysis.get("zhongshu", []),
        analysis.get("trend", "")
    )
    return {"code": 0, "data": {"score": score, "details": analysis}, "message": "ok"}
```

---

### 1.4 修改 `backend/main.py`

在路由注册部分增加：
```python
from routers import chan  # 新增导入

app.include_router(chan.router, prefix="/api/chan", tags=["缠论分析"])
```

---

## Phase 2: 缠论回测策略

### 2.1 修改 `backend/services/backtest_service.py`

新增策略类型 `chan_theory`：

```python
elif strategy_type == "chan_theory":
    def _signal(data):
        # 1. 识别中枢
        zhongshu_high = data["high"].rolling(20).max()  # 简化中枢
        zhongshu_low = data["low"].rolling(20).min()
        
        # 2. 计算MACD柱面积背驰
        macd_area_prev = data["MACD"].rolling(5).sum().shift(5)
        macd_area_curr = data["MACD"].rolling(5).sum()
        
        # 3. 第一类买点：下跌后MACD柱面积缩减
        price_lower_than_prev = data["close"] < data["close"].shift(10)
        macd_shrinking = (abs(macd_area_curr) < abs(macd_area_prev) * 0.7)
        first_buy = price_lower_than_prev & macd_shrinking & (data["MACD"] > data["MACD"].shift(1))
        
        # 4. 第三类买点：突破中枢后回抽不破
        breakout = data["close"] > zhongshu_high.shift(1)
        pullback_not_break = (data["low"] > zhongshu_high.shift(1)) & (data["close"] > data["MA5"])
        third_buy = breakout.shift(5).rolling(5).max() > 0 & pullback_not_break
        
        buy = first_buy | third_buy
        sell = (data["MACD"] < data["MACD"].shift(1)) & (data["close"] < data["MA10"])
        
        return pd.DataFrame({"Buy": buy, "Sell": sell}, index=data.index)
```

### 2.2 修改 `backend/routers/backtest.py`

策略类型枚举更新：
- `strategy_type` 支持 `"chan_theory"`

---

## Phase 3: AI 集成增强

### 3.1 修改 `backend/services/ai_service.py`

1. 股票问诊增加缠论分析提示词
2. 每日复盘增加缠论市场结构分析
3. 新增 `get_chan_consultation()` 方法

---

## 实施顺序（按文件）

```
Step 1: /backend/services/chanservice.py     【新建】核心引擎
         ├── detect_fenxing() + handle_baohan()
         ├── detect_bi()
         ├── detect_zhongshu()
         ├── classify_trend()
         ├── detect_beichi()
         ├── detect_buy_points()
         ├── score_chan()
         └── analyze() 一站式分析

Step 2: /backend/services/picker_service.py  【修改】6步 → 7步流水线
         ├── 导入ChanService
         ├── __init__ 增加 self.chan_service
         ├── 新增 _chan_filter()
         ├── generate_signals() 插入 Step 4.5
         └── _score_and_rank() 调整评分维度

Step 3: /backend/routers/chan.py             【新建】缠论API路由
         ├── /api/chan/analyze/{code}
         ├── /api/chan/fenxing/{code}
         ├── /api/chan/zhongshu/{code}
         ├── /api/chan/beichi/{code}
         ├── /api/chan/signals/{code}
         └── /api/chan/score/{code}

Step 4: /backend/main.py                     【修改】注册路由

Step 5: /backend/services/backtest_service.py 【修改】新增chan_theory策略

Step 6: /backend/services/ai_service.py      【修改】AI提示词增强
```
