#!/usr/bin/env python3
"""调试选股流水线 — 看每只候选被筛的原因"""
import asyncio
import sys
sys.path.insert(0, '/root/stock-picker/backend')
from services.data_service import DataService


async def test():
    ds = DataService()

    # 1. 先看股票列表前5只
    stocks = await ds.get_stock_list()
    print(f"=== 股票列表: {len(stocks)}只 ===")
    for s in stocks[:3]:
        print(f"  {s}")

    print()
    print("=== 测试腾讯行情API ===")
    info = await ds.get_stock_info("sh600519")
    print(f"  茅台: pe={info.get('pe')}, price={info.get('price')}, name={info.get('name')}")

    info2 = await ds.get_stock_info("sz000977")
    print(f"  浪潮: pe={info2.get('pe')}, price={info2.get('price')}, name={info2.get('name')}")

    print()
    print("=== 测试akshare财务数据 ===")
    try:
        import akshare as ak
        df = ak.stock_zh_analyst_forward("sh600519")
        print(f"  金融数据可用: {df.columns.tolist()[:10]}")
    except Exception as e:
        print(f"  akshare金融不可用: {e}")

    print()
    print("=== 价值筛选测试 ===")
    # 直接模拟筛选流程
    from services.picker_service import PickerService
    ps = PickerService()
    p = ps.PARAMS

    count_pass = 0
    count_fail = {"st": 0, "pe_low": 0, "pe_high": 0, "pb": 0, "roe": 0, "debt": 0, "other": 0}
    test_count = 0

    for stock in stocks[:50]:
        code = stock.get("code", "")
        name = stock.get("name", "")
        if not code:
            continue

        # 跳过ST
        if "ST" in name or "*ST" in name:
            count_fail["st"] += 1
            continue

        try:
            test_count += 1
            info = await ds.get_stock_info(code)
            pe = info.get("pe", 0) or 0
            pb = info.get("pb", 0) or 0
            roe = info.get("roe", 0) or 0
            debt = info.get("debt_ratio", 0) or 0

            print(f"  {code} {name}: pe={pe}, pb={pb}, roe={roe}%")

            if not (p["pe_min"] <= pe <= p["pe_max"]):
                if pe < p["pe_min"]: count_fail["pe_low"] += 1
                else: count_fail["pe_high"] += 1
                print(f"    ❌ PE筛掉: {pe} not in [{p['pe_min']}, {p['pe_max']}]")
                continue
            if pb > p["pb_max"]:
                count_fail["pb"] += 1
                continue
            if roe < p["roe_min"]:
                count_fail["roe"] += 1
                print(f"    ❌ ROE筛掉: {roe} < {p['roe_min']}")
                continue
            count_pass += 1
            print(f"    ✅ 通过")

        except Exception as e:
            count_fail["other"] += 1
            print(f"    ❌ 异常: {e}")
            continue

    print(f"\n=== 结果: 通过{count_pass}/{test_count}只 ===")
    for k, v in count_fail.items():
        if v > 0: print(f"  {k}: {v}")


asyncio.run(test())
