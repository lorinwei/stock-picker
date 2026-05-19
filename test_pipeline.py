#!/usr/bin/env python3
"""测试选股流水线"""
import asyncio
import sys
sys.path.insert(0, '/root/stock-picker/backend')
from services.picker_service import PickerService


async def test():
    ps = PickerService()
    print('🚀 启动选股流水线测试...')
    result = await ps.generate_signals()

    signals = result.get('signals', [])
    print(f'\n🎯 最终信号: {len(signals)}只')
    for s in signals[:5]:
        score = s.get('score', 0)
        price = s.get('price', 0)
        cpct = s.get('change_pct', 0)
        chan_sig = s.get('chan_signal', '?')
        chan_sc = s.get('chan_score', 0)
        reasons = s.get('entry_reasons', [])[:2]
        print(f'  #{s["rank"]} {s["name"]}({s["code"]}): {score}分 | ¥{price} | {cpct}%')
        print(f'     理由: {reasons}')
        print(f'     缠论: {chan_sig} 评分{chan_sc}')
    print(f'\n📊 市场状态: {result.get("market", {}).get("status_text", "?")}')
    print(f'⏱ 完成')


asyncio.run(test())
