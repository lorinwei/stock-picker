"""
akshare 数据获取层 - 第一阶段升级
提供：资金流、财务指标、龙虎榜、热度榜
"""
import json, sys, time, traceback
from datetime import datetime, timedelta

def fmt(val):
    """安全转float"""
    if val is None: return 0.0
    try: return float(val)
    except: return 0.0

def safe_get(df, row_idx, col):
    """从DataFrame安全取值"""
    try:
        if df is None: return 0.0
        if row_idx >= len(df): return 0.0
        import pandas as pd
        if isinstance(df, pd.DataFrame):
            val = df.iloc[row_idx].get(col, 0)
            return fmt(val)
        return 0.0
    except: return 0.0

def get_all_codes():
    """获取全市场股票列表"""
    try:
        import akshare as ak
        df = ak.stock_info_a_code_name()
        return df.to_json(orient='records', force_ascii=False)
    except Exception as e:
        return json.dumps({'error': str(e)})

def get_financial_indicators(code, years=2):
    """获取财务指标（ROE/净利润增速/资产负债率等）"""
    try:
        import akshare as ak
        end_year = datetime.now().year
        start_year = end_year - years
        df = ak.stock_financial_analysis_indicator(symbol=code, start_year=str(start_year))
        if df is None or len(df) == 0:
            return json.dumps({'error': 'no data'})
        
        latest = df.iloc[-1]
        
        # 提取关键字段
        result = {
            'code': code,
            'date': str(latest.get('日期', '')),
            '净资产收益率': fmt(latest.get('净资产收益率(%)', 0)),
            '加权净资产收益率': fmt(latest.get('加权净资产收益率(%)', 0)),
            '摊薄每股收益': fmt(latest.get('摊薄每股收益(元)', 0)),
            '净利润增长率': fmt(latest.get('净利润增长率(%)', 0)),
            '主营业务收入增长率': fmt(latest.get('主营业务收入增长率(%)', 0)),
            '总资产增长率': fmt(latest.get('总资产增长率(%)', 0)),
            '资产负债率': fmt(latest.get('资产负债率(%)', 0)),
            '流动比率': fmt(latest.get('流动比率', 0)),
            '速动比率': fmt(latest.get('速动比率', 0)),
            '存货周转率': fmt(latest.get('存货周转率(次)', 0)),
            '总资产周转率': fmt(latest.get('总资产周转率(次)', 0)),
            '销售毛利率': fmt(latest.get('销售毛利率(%)', 0)),
            '成本费用利润率': fmt(latest.get('成本费用利润率(%)', 0)),
            '净资本收益率': fmt(latest.get('净资产报酬率(%)', 0)),
            '营业利润率': fmt(latest.get('营业利润率(%)', 0)),
            'status': 'ok'
        }
        
        # 计算趋势（与上期对比）
        if len(df) >= 2:
            prev = df.iloc[-2]
            result['净利润增速趋势'] = 'up' if fmt(latest.get('净利润增长率(%)', 0)) > fmt(prev.get('净利润增长率(%)', 0)) else 'down'
            result['ROE趋势'] = 'up' if fmt(latest.get('净资产收益率(%)', 0)) > fmt(prev.get('净资产收益率(%)', 0)) else 'down'
        
        return json.dumps(result)
    except Exception as e:
        return json.dumps({'code': code, 'error': str(e), 'status': 'error'})

def get_capital_flow(code):
    """获取资金流数据（主力/中单/小单净流入）"""
    try:
        import akshare as ak
        df = ak.stock_individual_fund_flow(symbol=code)
        if df is None or len(df) == 0:
            return json.dumps({'error': 'no data'})
        
        latest = df.iloc[0]  # 最新在第一行
        
        result = {
            'code': code,
            'date': str(latest.get('日期', '')),
            '收盘价': fmt(latest.get('收盘价', 0)),
            '涨跌幅': fmt(latest.get('涨跌幅', 0)),
            '主力净流入_净额': fmt(latest.get('主力净流入-净额', 0)),
            '主力净流入_净占比': fmt(latest.get('主力净流入-净占比', 0)),
            '超大单净流入_净额': fmt(latest.get('超大单净流入-净额', 0)),
            '超大单净流入_净占比': fmt(latest.get('超大单净流入-净占比', 0)),
            '大单净流入_净额': fmt(latest.get('大单净流入-净额', 0)),
            '大单净流入_净占比': fmt(latest.get('大单净流入-净占比', 0)),
            '中单净流入_净额': fmt(latest.get('中单净流入-净额', 0)),
            '中单净流入_净占比': fmt(latest.get('中单净流入-净占比', 0)),
            '小单净流入_净额': fmt(latest.get('小单净流入-净额', 0)),
            '小单净流入_净占比': fmt(latest.get('小单净流入-净占比', 0)),
            'status': 'ok'
        }
        
        # 计算5日平均（反映趋势）
        if len(df) >= 5:
            avg_main = df.iloc[:5]['主力净流入-净额'].apply(fmt).mean()
            avg_ratio = df.iloc[:5]['主力净流入-净占比'].apply(fmt).mean()
            result['主力5日均额'] = round(avg_main, 2)
            result['主力5日均占比'] = round(avg_ratio, 2)
            result['主力趋势'] = '流入' if avg_main > 0 else '流出'
        else:
            result['主力5日均额'] = 0
            result['主力5日均占比'] = 0
            result['主力趋势'] = 'unknown'
            
        return json.dumps(result)
    except Exception as e:
        return json.dumps({'code': code, 'error': str(e), 'status': 'error'})

def get_lhb_list(date=None, limit=20):
    """获取龙虎榜列表"""
    try:
        import akshare as ak
        if date is None:
            df = ak.stock_lhb_detail_em()
        else:
            df = ak.stock_lhb_detail_em(start_date=date, end_date=date)
        if df is None or len(df) == 0:
            return json.dumps({'error': 'no data'})
        
        records = []
        for _, row in df.head(limit).iterrows():
            records.append({
                '代码': str(row.get('代码', '')),
                '名称': str(row.get('名称', '')),
                '上榜日': str(row.get('上榜日', '')),
                '收盘价': fmt(row.get('收盘价', 0)),
                '涨跌幅': fmt(row.get('涨跌幅', 0)),
                '龙虎榜净买额': fmt(row.get('龙虎榜净买额', 0)),
                '净买额占比': fmt(row.get('净买额占总成交比', 0)),
                '换手率': fmt(row.get('换手率', 0)),
                '上榜原因': str(row.get('上榜原因', '')),
                '上榜后1日': fmt(row.get('上榜后1日', 0)),
                '上榜后5日': fmt(row.get('上榜后5日', 0)),
                '成功率': fmt(row.get('解读', ''))  # 特殊处理
            })
        return json.dumps({'items': records, 'total': len(records), 'status': 'ok'})
    except Exception as e:
        return json.dumps({'error': str(e), 'status': 'error'})

def get_hot_rank():
    """获取个股人气排名"""
    try:
        import akshare as ak
        df = ak.stock_hot_rank_em()
        if df is None or len(df) == 0:
            return json.dumps({'error': 'no data'})
        
        records = []
        for _, row in df.head(30).iterrows():
            records.append({
                '代码': str(row.get('代码', row.get('code', ''))),
                '名称': str(row.get('名称', row.get('name', ''))),
                '排名': int(row.get('排名', row.get('rank', 0))),
                '热度值': fmt(row.get('热度值', 0)),
                '涨跌': fmt(row.get('涨跌幅', 0)),
                '换手率': fmt(row.get('换手率', 0)),
            })
        return json.dumps({'items': records, 'total': len(records), 'status': 'ok'})
    except Exception as e:
        return json.dumps({'error': str(e), 'status': 'error'})

def batch_financial(codes):
    """批量获取财务指标（用于选股池）"""
    results = []
    for code in codes[:20]:  # 限制最多20只，防超时
        time.sleep(0.3)  # 防限流
        data = json.loads(get_financial_indicators(code))
        results.append(data)
    return json.dumps(results)

def batch_capital_flow(codes):
    """批量获取资金流"""
    results = []
    for code in codes[:20]:
        time.sleep(0.2)
        data = json.loads(get_capital_flow(code))
        results.append(data)
    return json.dumps(results)

# CLI 接口
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'no action specified'}))
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == 'financial':
        code = sys.argv[2] if len(sys.argv) > 2 else '600519'
        print(get_financial_indicators(code))
    elif action == 'flow':
        code = sys.argv[2] if len(sys.argv) > 2 else '600519'
        print(get_capital_flow(code))
    elif action == 'lhb':
        date = sys.argv[2] if len(sys.argv) > 2 else None
        print(get_lhb_list(date))
    elif action == 'hot':
        print(get_hot_rank())
    elif action == 'batch_financial':
        codes = sys.argv[2].split(',') if len(sys.argv) > 2 else ['600519', '000858']
        print(batch_financial(codes))
    elif action == 'batch_flow':
        codes = sys.argv[2].split(',') if len(sys.argv) > 2 else ['600519', '000858']
        print(batch_capital_flow(codes))
    elif action == 'codes':
        print(get_all_codes())
    else:
        print(json.dumps({'error': f'unknown action: {action}'}))
