# StockMind 量化系统后端

> 股票智慧体 - 让散户也能用机构级策略

## 快速启动

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置（复制并编辑）
cp config.yaml.example config.yaml
# 编辑 config.yaml，填入你的 API Key

# 启动服务
uvicorn main:app --reload --port 8000
```

## API 文档

启动后访问：http://localhost:8000/docs

## 主要接口

| 模块 | 路由 | 说明 |
|------|------|------|
| 股票数据 | GET /api/stock/{code}/kline | K线数据 |
| 技术指标 | GET /api/stock/{code}/indicators | MA/MACD/RSI/KDJ/BOLL |
| 选股信号 | GET /api/picker/signals | 今日TOP10信号 |
| 持仓管理 | GET/POST /api/portfolio | 持仓CRUD |
| 策略回测 | POST /api/backtest/run | 执行回测 |
| AI引擎 | POST /api/ai/generate-strategy | 策略生成 |

## 定时任务

- 16:00 每日选股 + 飞书推送
- 16:30 持仓检查 + 风控预警
- 21:00 AI每日复盘

## 技术栈

FastAPI · akshare · Backtesting.py · SQLite · APScheduler · MiniMax API
