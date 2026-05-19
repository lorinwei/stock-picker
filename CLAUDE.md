# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

StockMind — A股量化交易系统。后端 FastAPI + 前端 Vue 3，核心是基于缠论（Chan Theory）的多因子选股系统。

## Architecture

```
├── backend/
│   ├── main.py              # FastAPI 应用入口，挂载路由 + 前端静态文件
│   ├── api.py               # 旧版独立 API (port 8800，读 JSON 快照)
│   ├── run.py               # 启动脚本
│   ├── config.yaml.example  # 配置模板（复制为 config.yaml）
│   ├── requirements.txt     # Python 依赖
│   ├── routers/             # FastAPI 路由层
│   ├── services/            # 业务逻辑层
│   ├── jobs/                # 定时任务 (APScheduler)
│   ├── utils/               # 配置/数据库/缓存工具
│   └── models/              # Pydantic 数据模型
├── frontend/
│   ├── src/
│   │   ├── views/           # 6 个页面视图 (Home/Picker/Portfolio/Chat/Market/Backtest)
│   │   ├── stores/          # Pinia 状态 (stock, portfolio, settings)
│   │   ├── api/index.ts     # Axios 客户端
│   │   ├── router/index.ts  # Vue Router 配置
│   │   ├── components/      # 可复用组件 (KLineChart, StockCard 等)
│   │   └── types/index.ts   # TypeScript 类型定义
│   └── package.json
└── data/                    # SQLite 数据库 + 日志 + 回测结果
```

## Key Design Decisions

- **数据层分层**: 腾讯行情API(实时) → 新浪API(K线) → akshare(财务/资金流)，逐级降级
- **缠论引擎**: `services/chanservice.py` — 包含处理→分型→笔→中枢→背驰→三类买卖点，纯算法实现
- **选股流水线**: 市场判定 → 价值过滤 → 缠论扫描 → 技术确认 → 评分 → 风控 → TOP 10
- **评分权重**: 缠论 40% + 基本面 25% + 动量 20% + 资金 15%
- **所有 API 统一响应格式**: `{"code": 0, "data": ..., "message": "ok"}`
- **内存缓存**: cachetools TTLCache，动态 TTL 从 config.yaml 读取
- **数据库**: SQLite (aiosqlite)，`data/stockmind.db`，含 positions/trade_history/signal_history 三表
- **配置**: 单例 `Settings` 对象，YAML + 自动路径解析，所有路径相对项目根

## Commands

### Backend
```bash
cd backend
pip install -r requirements.txt          # 安装依赖
cp config.yaml.example config.yaml       # 首次配置
uvicorn main:app --reload --port 8000    # 开发服务
uvicorn main:app --port 8000             # 生产服务
```

### Frontend
```bash
cd frontend
npm install                              # 安装依赖
npm run dev                              # Vite 开发服务
npm run build                            # 生产构建
npm run preview                          # 预览构建产物
```

### API Docs
启动后端后访问 http://localhost:8000/docs

### Legacy API (读 JSON 快照)
```bash
cd backend && python api.py              # 独立端口 8800
```

## API Endpoints

| 模块 | 端点 | 说明 |
|------|------|------|
| 行情 | `GET /api/stock/{code}` | 实时行情（腾讯API） |
| K线 | `GET /api/stock/{code}/kline` | K线数据（新浪API） |
| 技术指标 | `GET /api/stock/{code}/indicators` | MA/MACD/RSI/KDJ/BOLL |
| 选股 | `GET /api/picker/signals` | 缠论选股 TOP 10 |
| 选股 | `GET /api/signals/today` | 前端 HomeView 调用 |
| 选股池 | `GET /api/stockpool` | 前端 PickerView 调用 |
| 持仓 | `GET /api/portfolio` | 持仓列表 |
| 风控 | `GET /api/portfolio/risk` | 整体风控 |
| 回测 | `POST /api/backtest/run` | 执行回测 |
| 回测 | `GET /api/backtest/history` | 回测历史 |
| 大盘 | `GET /api/market/overview` | 指数+行业排行 |
| AI | `POST /api/ai/generate-strategy` | 策略生成 |
| AI | `POST /api/ai/consult` | 股票问诊 |
| AI | `POST /api/ai/daily-summary` | 每日复盘 |
| 缠论 | `GET /api/chan/{code}` | 单只股票缠论分析 |
| 缠论 | `GET /api/chan/{code}/multilevel` | 多级别分析+区间套 |

## Scheduled Jobs

- 16:00 — `daily_pick.py`: 每日选股 + 飞书推送
- 16:30 — `portfolio_check.py`: 持仓检查 + 风控预警
- 21:00 — `daily_summary.py`: AI 每日复盘推送

## Service Dependencies

- `data_service` → 所有其他服务的底层依赖（行情/K线/财务/资金流）
- `chanservice` → `picker_service` 选股流水线 Step 2
- `picker_service` → `data_service` + `chanservice` + config-based scoring
- `portfolio_service` → SQLite CRUD + 盈亏计算
- `risk_service` → 纯函数式风控计算
- `ai_service` → MiniMax API（策略生成/反推/问诊/复盘）
- `notifier` → 飞书 webhook 推送
- `backtest_service` → backtesting.py 封装

## Data Sources (priority order)

1. **实时行情**: 腾讯 qt.gtimg.cn (最快最稳)
2. **K线**: 新浪财经 API (免费稳定)
3. **财务数据**: akshare (慢但全)
4. **资金流向**: akshare
5. **行业排行**: akshare
6. **AI**: MiniMax API

## Important Notes

- Python 3.11+, Node 18+
- 前端通过 Vite proxy 将 `/api` 请求转发到后端 8000 端口
- 所有现金类数值以 `float` 存储，数量/股数为 `int`
- `picker_service.generate_signals()` 有 30 分钟缓存，`data_service` 各方法有独立 TTL 缓存
- 缠论分析默认 500 根 K 线，日志级别在 config.yaml 控制
