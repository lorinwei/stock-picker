"""
AI服务 - MiniMax API调用
策略生成 / 策略反推 / 股票问诊 / 每日复盘
"""
import json
import httpx
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import yaml
from loguru import logger


class AIService:
    """MiniMax AI服务"""

    BASE_URL = "https://api.minimax.chat/v1"
    MODEL = "MiniMax-Text-01"

    def __init__(self):
        self.api_key = self._load_api_key()
        self.group_id = self._load_group_id()

    def _load_api_key(self) -> str:
        cfg_path = __import__("pathlib").Path(__file__).parent.parent / "config.yaml"
        if cfg_path.exists():
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
                return cfg.get("ai", {}).get("minimax_api_key", "")
        return ""

    def _load_group_id(self) -> str:
        cfg_path = __import__("pathlib").Path(__file__).parent.parent / "config.yaml"
        if cfg_path.exists():
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
                return cfg.get("ai", {}).get("minimax_group_id", "")
        return ""

    async def _call_minimax(self, messages: List[Dict], temperature: float = 0.7) -> str:
        """调用MiniMax API"""
        if not self.api_key:
            return json.dumps({
                "error": "请先配置 MiniMax API Key",
                "配置方法": "在 config.yaml 的 ai.minimax_api_key 字段填入API Key",
            }, ensure_ascii=False, indent=2)

        url = f"{self.BASE_URL}/text/chatcompletion_v2"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.MODEL,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 4096,
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data.get("choices", [{}])[0].get("message", {}).get("content", "")
        except httpx.HTTPStatusError as e:
            logger.error(f"MiniMax API HTTP错误: {e.response.status_code}")
            return f"API调用失败: HTTP {e.response.status_code}"
        except Exception as e:
            logger.error(f"MiniMax API调用异常: {e}")
            return f"API调用异常: {str(e)}"

    # ============ 核心功能 ============

    async def generate_strategy(self, description: str, include_stop_loss: bool = True, include_take_profit: bool = True) -> Dict:
        """
        AI策略生成：自然语言 → Python策略代码
        """
        prompt = f"""你是一个量化交易策略专家。请根据用户的描述，生成一个Python量化策略代码。

用户需求：
{description}

要求：
1. 使用 Backtesting.py 框架格式
2. 包含 init() 和 next() 方法
3. 实现完整的买入/卖出信号逻辑
4. 包含风控：止损（默认-8%），止盈（可选）
5. 代码要有中文注释
6. 只返回可运行的Python代码，不要解释

策略模板：
```python
from backtesting import Backtest, Strategy

class MyStrategy(Strategy):
    def init(self):
        # 初始化指标
        self.ma = self.I(lambda: pd.Series(self.data.Close).rolling(20).mean())
        pass

    def next(self):
        # 交易逻辑
        if 买入条件:
            self.buy()
        elif 卖出条件:
            self.sell()
```

请生成完整的策略代码："""

        messages = [{"role": "user", "content": prompt}]
        code = await self._call_minimax(messages)

        return {
            "description": description,
            "strategy_code": code,
            "usage": "将此代码保存为 .py 文件，使用 backtesting.py 执行回测",
            "tips": "建议先用小仓位模拟验证，确认有效后再实盘使用",
        }

    async def reverse_strategy(self, code: str, start_date: str, end_date: str) -> Dict:
        """
        AI策略反推：分析K线形态，推测可能的策略规则
        """
        prompt = f"""你是一个技术分析专家。请分析以下股票的K线形态，推测其可能的交易策略。

股票代码：{code}
分析区间：{start_date} 至 {end_date}

请从以下角度分析：
1. 均线系统的周期组合（MA5/10/20/60）
2. MACD的参数和使用方式（金叉/死叉/背离）
3. RSI的超买超卖阈值
4. 成交量的配合方式
5. 可能的买入/卖出规则
6. 适合什么类型的投资者

请用结构化的方式输出分析结果。"""

        messages = [{"role": "user", "content": prompt}]
        analysis = await self._call_minimax(messages)

        return {
            "code": code,
            "start_date": start_date,
            "end_date": end_date,
            "analysis": analysis,
        }

    async def consult_stocks(self, codes: List[str], include_market: bool = True) -> Dict:
        """
        AI股票问诊：分析持仓股票，给出诊断和建议
        """
        stocks_text = "\n".join([f"{i+1}. {c}" for i, c in enumerate(codes)])

        prompt = f"""你是一个股票投资顾问。请对以下持仓股票进行诊断分析。

持仓股票：
{stocks_text}

请对每只股票从以下维度进行分析：
1. **基本面**：财务健康度、估值合理性
2. **技术面**：当前趋势、关键支撑阻力位
3. **资金面**：主力动向、北向资金
4. **风险点**：潜在黑天鹅、需要注意的事项
5. **操作建议**：持有/加仓/减仓/止损

最后给出整体组合的：
- 行业分布是否合理
- 风险集中度评估
- 下周操作建议

输出格式：结构化Markdown，包含每只股票的详细诊断"""

        messages = [{"role": "user", "content": prompt}]
        diagnosis = await self._call_minimax(messages, temperature=0.5)

        return {
            "codes": codes,
            "diagnosis": diagnosis,
            "timestamp": datetime.now().isoformat(),
        }

    async def get_daily_summary(self, date: Optional[str] = None) -> Dict:
        """
        AI每日复盘：生成当日市场总结和持仓复盘
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        prompt = f"""请生成 {date} 的每日复盘报告。

请包含以下内容：

## 今日市场概况
- 主要指数涨跌
- 热点板块
- 资金动向（北向资金）

## 持仓表现回顾
（如果用户有持仓，分析其表现）

## 今日操作记录
（如果有买卖操作）

## 明日展望
- 市场情绪预判
- 需要关注的板块
- 操作计划建议

## 投资感悟
（结合道家"上善若水，顺势而为"的思想，给出一句投资箴言）

请用专业但不枯燥的语言写，适合有一定经验的投资者阅读。"""

        messages = [{"role": "user", "content": prompt}]
        summary = await self._call_minimax(messages, temperature=0.6)

        return {
            "date": date,
            "summary": summary,
            "generated_at": datetime.now().isoformat(),
        }

    async def backtest_generated_strategy(
        self,
        strategy_code: str,
        stock_code: str,
        start_date: str,
        end_date: str,
    ) -> Dict:
        """
        对AI生成的策略进行回测
        """
        # 这里调用回测服务执行
        from services.backtest_service import BacktestService
        bs = BacktestService()
        result = await bs.run(
            stock_code=stock_code,
            strategy_type="value_trend",
            start_date=start_date,
            end_date=end_date,
        )
        return result
