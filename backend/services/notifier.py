"""
飞书推送服务
"""
import httpx
from loguru import logger
from typing import Dict, List
from datetime import datetime

from utils.config import settings


class Notifier:
    def __init__(self):
        feishu_cfg = settings.FEISHU
        self.webhook_url = feishu_cfg.get("webhook_url", "")
        self.enabled = feishu_cfg.get("enabled", False)

    async def send_text(self, content: str) -> bool:
        if not self._ready():
            return False
        try:
            async with httpx.AsyncClient(timeout=10) as c:
                resp = await c.post(self.webhook_url, json={"msg_type": "text", "content": {"text": content}})
                resp.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"飞书推送失败: {e}")
            return False

    async def send_signals(self, signals: List[Dict], market: Dict) -> bool:
        if not self._ready():
            return False
        text = f"📊 {datetime.now().strftime('%m/%d')} 选股信号 | {market.get('desc', '')}\n"
        for s in signals[:5]:
            bp = s.get("buy_point_desc", "") or s.get("buy_point", "")
            text += f"\n{s['name']}({s['code']}) 评分{s['score']} | {bp} | 止损{s.get('stop_loss_price', 0)}"
        return await self.send_text(text)

    async def send_portfolio_alert(self, positions: List[Dict]) -> bool:
        if not self._ready():
            return False
        lines = ["📊 持仓预警\n"]
        for p in positions:
            risk = p.get("risk_status", {})
            lines.append(f"{p['name']}({p['code']}) {risk.get('profit_pct', 0):+.1f}% | {risk.get('message', '')}")
        return await self.send_text("\n".join(lines))

    def _ready(self) -> bool:
        if not self.webhook_url or not self.enabled:
            return False
        return True


notifier = Notifier()
