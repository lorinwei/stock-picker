"""
飞书推送服务
"""
import httpx
import yaml
from loguru import logger
from typing import Dict, List, Optional
from datetime import datetime


class Notifier:
    """飞书Webhook推送"""

    def __init__(self):
        self.webhook_url = self._load_webhook()

    def _load_webhook(self) -> str:
        cfg_path = __import__("pathlib").Path(__file__).parent.parent / "config.yaml"
        if cfg_path.exists():
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
                return cfg.get("notification", {}).get("feishu_webhook", "")
        return ""

    async def send_text(self, content: str):
        """发送文本消息"""
        if not self.webhook_url:
            logger.warning("飞书Webhook未配置，跳过推送")
            return False

        payload = {
            "msg_type": "text",
            "content": {"text": content},
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(self.webhook_url, json=payload)
                resp.raise_for_status()
                logger.info(f"飞书推送成功: {content[:50]}...")
                return True
        except Exception as e:
            logger.error(f"飞书推送失败: {e}")
            return False

    async def send_signals(self, signals: List[Dict], market: Dict):
        """发送选股信号"""
        if not self.webhook_url:
            return False

        market_text = market.get("status_text", "未知")
        elements = []

        for sig in signals[:5]:
            badge = "🥇" if sig["rank"] == 1 else "🥈" if sig["rank"] == 2 else f"#{sig['rank']}"
            trend = "⬆️" if sig.get("change_pct", 0) > 0 else "⬇️"
            reason = " | ".join(sig.get("entry_reasons", [])[:2])

            text = f"{badge} {sig['name']}({sig['code']}) {trend}{sig.get('change_pct', 0):+.1f}%\n   评分:{sig['score']} | 建议仓位:{sig['suggested_position']:.0f}% | 止损:¥{sig['stop_loss_price']}\n   {reason}"

            elements.append({
                "tag": "markdown",
                "content": text,
            })

        payload = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {"tag": "plain_text", "content": f"📊 {datetime.now().strftime('%m/%d')} 选股信号 {market_text}"},
                    "template": "purple",
                },
                "elements": [
                    {"tag": "markdown", "content": f"**市场状态**: {market_text} | **持仓上限**: {market.get('position_limit', 0.5)*100:.0f}%"},
                    {"tag": "hr"},
                    *elements,
                    {"tag": "hr"},
                    {"tag": "markdown", "content": "⚠️ 仅供参考，不构成投资建议。操作需爷自行判断。"},
                ],
            },
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(self.webhook_url, json=payload)
                resp.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"飞书信号推送失败: {e}")
            return False

    async def send_portfolio_alert(self, positions: List[Dict]):
        """发送持仓预警"""
        if not self.webhook_url:
            return False

        lines = ["**💼 持仓预警报告**\n"]
        for pos in positions:
            status = pos.get("risk_status", {})
            status_text = status.get("status_text", "⚪")
            profit_pct = status.get("profit_pct", 0)

            lines.append(
                f"{status_text} {pos['name']}({pos['code']}) {profit_pct:+.1f}%\n"
                f"   {status.get('message', '')}"
            )

        payload = {
            "msg_type": "text",
            "content": {"text": "\n".join(lines)},
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(self.webhook_url, json=payload)
                resp.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"飞书持仓预警失败: {e}")
            return False


# 全局实例
notifier = Notifier()
