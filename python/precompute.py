"""
一次性预计算脚本 - 生成 data/*.json 供 api.js 使用
运行方式: python3 python/precompute.py
预计耗时: 2-3分钟（串行，防限流）
"""
import json, time, os, sys
from datetime import datetime

# 股票池
STOCK_POOL = [
    {'code': '600519', 'name': '贵州茅台',   'mkt': '1', 'industry': '白酒'},
    {'code': '000858', 'name': '五粮液',     'mkt': '0', 'industry': '白酒'},
    {'code': '600036', 'name': '招商银行',   'mkt': '1', 'industry': '银行'},
    {'code': '601318', 'name': '中国平安',   'mkt': '1', 'industry': '保险'},
    {'code': '000333', 'name': '美的集团',   'mkt': '0', 'industry': '家电'},
    {'code': '600276', 'name': '恒瑞医药',   'mkt': '1', 'industry': '医药'},
    {'code': '002475', 'name': '立讯精密',   'mkt': '0', 'industry': '消费电子'},
    {'code': '300750', 'name': '宁德时代',   'mkt': '0', 'industry': '新能源'},
    {'code': '688981', 'name': '中芯国际',   'mkt': '1', 'industry': '半导体'},
    {'code': '002594', 'name': '比亚迪',     'mkt': '0', 'industry': '汽车'},
    {'code': '601012', 'name': '隆基绿能',   'mkt': '1', 'industry': '新能源'},
    {'code': '600900', 'name': '长江电力',   'mkt': '1', 'industry': '电力'},
    {'code': '300059', 'name': '东方财富',   'mkt': '0', 'industry': '券商'},
    {'code': '002415', 'name': '海康威视',   'mkt': '0', 'industry': '科技'},
    {'code': '601888', 'name': '中国中免',   'mkt': '1', 'industry': '旅游'},
    {'code': '000001', 'name': '平安银行',   'mkt': '0', 'industry': '银行'},
    {'code': '600585', 'name': '海螺水泥',   'mkt': '1', 'industry': '建材'},
    {'code': '600887', 'name': '伊利股份',   'mkt': '1', 'industry': '食品'},
    {'code': '000568', 'name': '泸州老窖',   'mkt': '0', 'industry': '白酒'},
    {'code': '300015', 'name': '爱尔眼科',   'mkt': '0', 'industry': '医疗'},
]

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
os.makedirs(DATA_DIR, exist_ok=True)

def fmt(v):
    try: return float(v) if v is not None else 0.0
    except: return 0.0

print(f"开始预计算 {len(STOCK_POOL)} 只股票...")
print(f"输出目录: {DATA_DIR}")
print("="*50)

# ===== 1. 财务指标 =====
print("\n[1/3] 获取财务指标...")
financial_map = {}
for i, s in enumerate(STOCK_POOL):
    code = s['code']
    time.sleep(0.5)
    try:
        import akshare as ak
        df = ak.stock_financial_analysis_indicator(symbol=code, start_year='2023')
        if df is not None and len(df) > 0:
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) >= 2 else latest
            
            # ROE 综合（加权 > 摊薄）
            roe = fmt(latest.get('加权净资产收益率(%)', 0)) or fmt(latest.get('净资产收益率(%)', 0))
            prev_roe = fmt(prev.get('加权净资产收益率(%)', 0)) or fmt(prev.get('净资产收益率(%)', 0))
            
            # 净利润增速
            ni_growth = fmt(latest.get('净利润增长率(%)', 0))
            prev_ni_growth = fmt(prev.get('净利润增长率(%)', 0))
            
            # 资产负债率
            debt_ratio = fmt(latest.get('资产负债率(%)', 0))
            
            # 毛利率
            gross_margin = fmt(latest.get('销售毛利率(%)', 0))
            
            # 营收增速
            revenue_growth = fmt(latest.get('主营业务收入增长率(%)', 0))
            
            # 每股收益
            eps = fmt(latest.get('摊薄每股收益(元)', 0))
            
            # 成本费用利润率
            cost_margin = fmt(latest.get('成本费用利润率(%)', 0))
            
            financial_map[code] = {
                'date': str(latest.get('日期', '')),
                'roe': round(roe, 2),
                'roe_growth': round(roe - prev_roe, 2),
                'ni_growth': round(ni_growth, 2),
                'ni_growth_trend': 'up' if ni_growth > prev_ni_growth else 'down',
                'revenue_growth': round(revenue_growth, 2),
                'debt_ratio': round(debt_ratio, 2),
                'gross_margin': round(gross_margin, 2),
                'eps': round(eps, 2),
                'cost_margin': round(cost_margin, 2),
                'status': 'ok'
            }
            print(f"  {i+1:02d}. {code} {s['name']}: ROE={roe:.1f}%, 净利润增速={ni_growth:.1f}%, 资产负债率={debt_ratio:.1f}%")
        else:
            financial_map[code] = {'code': code, 'status': 'no_data'}
            print(f"  {i+1:02d}. {code} {s['name']}: 无数据")
    except Exception as e:
        financial_map[code] = {'code': code, 'error': str(e)[:50], 'status': 'error'}
        print(f"  {i+1:02d}. {code} {s['name']}: 错误 {str(e)[:40]}")

with open(f'{DATA_DIR}/financial.json', 'w', encoding='utf-8') as f:
    json.dump(financial_map, f, ensure_ascii=False, indent=2)
print(f"✅ 财务指标已保存: {len(financial_map)} 条")

# ===== 2. 资金流 =====
print("\n[2/3] 获取资金流...")
flow_map = {}
for i, s in enumerate(STOCK_POOL):
    code = s['code']
    time.sleep(0.3)
    try:
        import akshare as ak
        df = ak.stock_individual_fund_flow(code)
        if df is not None and len(df) > 0:
            latest = df.iloc[0]
            
            main_net = fmt(latest.get('主力净流入-净额', 0))
            main_ratio = fmt(latest.get('主力净流入-净占比', 0))
            super_net = fmt(latest.get('超大单净流入-净额', 0))
            big_net = fmt(latest.get('大单净流入-净额', 0))
            mid_net = fmt(latest.get('中单净流入-净额', 0))
            small_net = fmt(latest.get('小单净流入-净额', 0))
            
            # 5日平均
            if len(df) >= 5:
                avg_main_net = df.iloc[:5]['主力净流入-净额'].apply(fmt).mean()
                avg_main_ratio = df.iloc[:5]['主力净流入-净占比'].apply(fmt).mean()
                avg5_main_net = round(avg_main_net, 0)
                avg5_main_ratio = round(avg_main_ratio, 2)
            else:
                avg5_main_net = 0
                avg5_main_ratio = 0
            
            # 趋势判断
            if avg5_main_net > 1e7: trend = 'strong_inflow'
            elif avg5_main_net > 0: trend = 'mild_inflow'
            elif avg5_main_net < -1e7: trend = 'strong_outflow'
            else: trend = 'mild_outflow'
            
            flow_map[code] = {
                'date': str(latest.get('日期', '')),
                'main_net': round(main_net, 0),
                'main_ratio': round(main_ratio, 2),
                'super_net': round(super_net, 0),
                'big_net': round(big_net, 0),
                'mid_net': round(mid_net, 0),
                'small_net': round(small_net, 0),
                'main_5d_avg_net': avg5_main_net,
                'main_5d_avg_ratio': avg5_main_ratio,
                'trend': trend,
                'status': 'ok'
            }
            print(f"  {i+1:02d}. {code} {s['name']}: 主力净流入 {main_net/1e6:.1f}万, 5日均 {avg5_main_net/1e6:.1f}万, 趋势={trend}")
        else:
            flow_map[code] = {'code': code, 'status': 'no_data'}
            print(f"  {i+1:02d}. {code} {s['name']}: 无数据")
    except Exception as e:
        flow_map[code] = {'code': code, 'error': str(e)[:50], 'status': 'error'}
        print(f"  {i+1:02d}. {code} {s['name']}: 错误 {str(e)[:40]}")

with open(f'{DATA_DIR}/capital_flow.json', 'w', encoding='utf-8') as f:
    json.dump(flow_map, f, ensure_ascii=False, indent=2)
print(f"✅ 资金流已保存: {len(flow_map)} 条")

# ===== 3. 龙虎榜 =====
print("\n[3/3] 获取龙虎榜...")
time.sleep(1)
try:
    import akshare as ak
    df = ak.stock_lhb_detail_em()
    if df is not None and len(df) > 0:
        records = []
        for _, row in df.head(50).iterrows():
            records.append({
                '代码': str(row.get('代码', '')),
                '名称': str(row.get('名称', '')),
                '上榜日': str(row.get('上榜日', '')),
                '收盘价': round(fmt(row.get('收盘价', 0)), 2),
                '涨跌幅': round(fmt(row.get('涨跌幅', 0)), 2),
                '净买额': round(fmt(row.get('龙虎榜净买额', 0)) / 1e8, 2),  # 转为亿
                '净买额占比': round(fmt(row.get('净买额占总成交比', 0)), 2),
                '换手率': round(fmt(row.get('换手率', 0)), 2),
                '上榜原因': str(row.get('上榜原因', ''))[:30],
                '上榜后1日': round(fmt(str(row.get('上榜后1日', 0))), 2),
                '上榜后5日': round(fmt(str(row.get('上榜后5日', 0))), 2),
            })
        
        with open(f'{DATA_DIR}/lhb.json', 'w', encoding='utf-8') as f:
            json.dump({'items': records, 'total': len(records), 'date': datetime.now().strftime('%Y-%m-%d'), 'status': 'ok'}, f, ensure_ascii=False, indent=2)
        print(f"✅ 龙虎榜已保存: {len(records)} 条")
    else:
        print("⚠️ 龙虎榜无数据")
except Exception as e:
    print(f"❌ 龙虎榜错误: {str(e)[:60]}")

# ===== 汇总 =====
print("\n" + "="*50)
print(f"预计算完成！生成文件:")
for fname in ['financial.json', 'capital_flow.json', 'lhb.json']:
    fpath = f'{DATA_DIR}/{fname}'
    if os.path.exists(fpath):
        size = os.path.getsize(fpath)
        print(f"  ✅ {fname} ({size/1024:.1f} KB)")
    else:
        print(f"  ❌ {fname} (未生成)")

with open(f'{DATA_DIR}/meta.json', 'w', encoding='utf-8') as f:
    json.dump({
        'updated': datetime.now().isoformat(),
        'stock_count': len(STOCK_POOL),
        'version': 'v1.0-akshare-phase1'
    }, f)
print("\n🎉 预计算完成！运行 `node api.js` 即可使用升级版选股系统")
