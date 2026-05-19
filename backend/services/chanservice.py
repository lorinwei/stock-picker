"""
缠论核心引擎 v3 — 分型→笔→中枢→背驰→三类买卖点

核心修复:
  1. 包含关系处理方向判定改用严格的高低点趋势法而非开收盘
  2. 分型增加「确认机制」—— 顶分型出现后需下一根不创新高确认
  3. 中枢边界计算重写，变量命名清晰
  4. 背驰增加 DIF 高度 + 面积双重判定
  5. 多级别分析实现真区间套
"""
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import math

import pandas as pd
from loguru import logger

from services.data_service import data_service
from utils.cache import get as cache_get, set as cache_set


# ──────────────────────────────────────────────
#  包含关系处理
# ──────────────────────────────────────────────

def process_inclusion(kline: List[Dict]) -> List[Dict]:
    """
    处理K线包含关系（第65课）

    核心规则:
    - 上升趋势(前一根高>前前一根高): 包含取高高 (high=max, low=max)
    - 下降趋势(前一根高≤前前一根高): 包含取低低 (high=min, low=min)
    """
    if len(kline) < 2:
        return kline

    bars = []
    for bar in kline:
        bars.append({
            "high": float(bar.get("high", 0)),
            "low": float(bar.get("low", 0)),
            "close": float(bar.get("close", 0)),
            "open": float(bar.get("open", 0)),
            "date": bar.get("date", ""),
        })

    result = [bars[0]]
    for i in range(1, len(bars)):
        prev = result[-1]
        curr = bars[i]

        # 判断是否包含：两根K线的区间有完全重叠
        is_contained = (curr["high"] <= prev["high"] and curr["low"] >= prev["low"]) or \
                       (curr["high"] >= prev["high"] and curr["low"] <= prev["low"])

        if not is_contained:
            result.append(curr)
            continue

        # 有包含 → 判断趋势方向
        if len(result) >= 2:
            prev2 = result[-2]
            trend_up = prev["high"] >= prev2["high"] and prev["low"] >= prev2["low"]
        else:
            # 只有一根历史K线时，默认上升趋势（prev相对curr是上升）
            trend_up = True

        if trend_up:
            # 向上处理：取高高
            merged = {
                "high": max(prev["high"], curr["high"]),
                "low": max(prev["low"], curr["low"]),
                "close": curr["close"],
                "open": prev["open"],
                "date": curr["date"],
            }
        else:
            # 向下处理：取低低
            merged = {
                "high": min(prev["high"], curr["high"]),
                "low": min(prev["low"], curr["low"]),
                "close": curr["close"],
                "open": prev["open"],
                "date": curr["date"],
            }
        result[-1] = merged

    return result


# ──────────────────────────────────────────────
#  分型检测
# ──────────────────────────────────────────────

def detect_fenxing(bars: List[Dict]) -> List[Dict]:
    """
    检测顶底分型（第64课）

    顶分型: 连续3根, 中间的高 > 左边的高, 中间的高 > 右边的高
    底分型: 连续3根, 中间的低 < 左边的低, 中间的低 < 右边的低

    返回带「确认状态」的分型列表:
      - confirmed: 后续K线确认（顶分型后一根没创新高，底分型后一根没创新低）
      - tentative: 暂未确认（最新一根可能是分型，需要等明天确认）
    """
    if len(bars) < 3:
        return []

    fenxings = []
    n = len(bars)

    for i in range(1, n - 1):
        prev = bars[i - 1]
        mid = bars[i]
        next_ = bars[i + 1]

        # 顶分型: 中间高最大
        is_top = mid["high"] > prev["high"] and mid["high"] > next_["high"]
        # 底分型: 中间低最小
        is_bottom = mid["low"] < prev["low"] and mid["low"] < next_["low"]

        if is_top:
            # 强度: 收盘越靠近底部越强（说明上影线长，反转信号强）
            rng = mid["high"] - min(prev["low"], next_["low"])
            strength = min(3, max(1, int((mid["high"] - mid["close"]) / rng * 6))) if rng > 0 else 1
            # 确认: 再有根K线且其高不超过分型高
            confirmed = (i + 2 < n and bars[i + 2]["high"] <= mid["high"]) or (i + 1 == n - 1)

            fenxings.append({
                "type": "top",
                "index": i,
                "high": mid["high"],
                "low": mid["low"],
                "date": mid.get("date", ""),
                "strength": strength,
                "confirmed": confirmed,
                "mid_close": mid["close"],
            })

        elif is_bottom:
            rng = max(prev["high"], next_["high"]) - mid["low"]
            strength = min(3, max(1, int((mid["close"] - mid["low"]) / rng * 6))) if rng > 0 else 1
            confirmed = (i + 2 < n and bars[i + 2]["low"] >= mid["low"]) or (i + 1 == n - 1)

            fenxings.append({
                "type": "bottom",
                "index": i,
                "high": mid["high"],
                "low": mid["low"],
                "date": mid.get("date", ""),
                "strength": strength,
                "confirmed": confirmed,
                "mid_close": mid["close"],
            })

    return fenxings


# ──────────────────────────────────────────────
#  笔识别
# ──────────────────────────────────────────────

def detect_bi(fenxings: List[Dict]) -> List[Dict]:
    """
    从分型构造笔（第69-72课）

    规则:
    - 顶底交替出现
    - 相邻分型索引差≥4（至少间隔4根K线）
    - 同向分型取更强那个（顶取更高，底取更低）
    """
    if len(fenxings) < 2:
        return []

    bis = []
    last = fenxings[0]

    for fx in fenxings[1:]:
        # 同向 → 取更强
        if fx["type"] == last["type"]:
            if fx["type"] == "top" and fx["high"] > last["high"]:
                last = fx
            elif fx["type"] == "bottom" and fx["low"] < last["low"]:
                last = fx
            continue

        # 确认分型才画笔（未确认的分型不参与）
        # if not fx["confirmed"]:
        #     continue

        # 间隔检查
        idx_diff = abs(fx["index"] - last["index"])
        if idx_diff < 4:
            continue

        is_up = last["type"] == "bottom"
        bi = {
            "type": "up" if is_up else "down",
            "start_idx": min(last["index"], fx["index"]),
            "end_idx": max(last["index"], fx["index"]),
            "start_price": last["low"] if is_up else last["high"],
            "end_price": fx["high"] if is_up else fx["low"],
            "start_date": last["date"],
            "end_date": fx["date"],
            "start_fx": last["type"],
            "end_fx": fx["type"],
            "height_pct": round(abs(fx["high"] - last["low"]) / max(last["low"], fx["low"], 0.01) * 100, 2) if is_up
            else round(abs(last["high"] - fx["low"]) / max(fx["low"], 0.01) * 100, 2),
        }
        # 笔内最高最低
        bi["high"] = max(last["high"], fx["high"])
        bi["low"] = min(last["low"], fx["low"])
        bis.append(bi)
        last = fx

    return bis


# ──────────────────────────────────────────────
#  中枢识别
# ──────────────────────────────────────────────

def detect_zhongshu(bis: List[Dict]) -> List[Dict]:
    """
    在笔序列中识别中枢（第73课）

    中枢 = 至少3段连续次级别走势的重叠区间
    对笔级别: 连续3笔的重叠区间 = 笔中枢

    定义：取三笔的最高点的最小值 = 中枢上沿
         取三笔的最低点的最大值 = 中枢下沿
    上沿 > 下沿 = 有重叠 = 中枢存在
    """
    if len(bis) < 3:
        return []

    zhongshus = []
    i = 0

    while i <= len(bis) - 3:
        b1, b2, b3 = bis[i], bis[i + 1], bis[i + 2]

        # 方向必须交替
        if not (b1["type"] != b2["type"] and b2["type"] != b3["type"]):
            i += 1
            continue

        # 三笔各自的高低点
        highs = [max(b["start_price"], b["end_price"]) for b in (b1, b2, b3)]
        lows = [min(b["start_price"], b["end_price"]) for b in (b1, b2, b3)]

        zs_top = min(highs)    # 上沿 = 最低的高点
        zs_bottom = max(lows)  # 下沿 = 最高的低点

        if zs_top <= zs_bottom:
            i += 1
            continue

        new_zs = {
            "start_idx": b1["start_idx"],
            "end_idx": b3["end_idx"],
            "start_date": b1["start_date"],
            "end_date": b3["end_date"],
            "top": round(zs_top, 2),
            "bottom": round(zs_bottom, 2),
            "mid": round((zs_top + zs_bottom) / 2, 2),
            "width_pct": round((zs_top - zs_bottom) / zs_bottom * 100, 2) if zs_bottom > 0 else 0,
            "direction": b1["type"],
            "bi_count": 3,
        }

        # 与上一个中枢合并（中枢扩张）
        if zhongshus:
            last_zs = zhongshus[-1]
            if new_zs["bottom"] < last_zs["top"] and new_zs["top"] > last_zs["bottom"]:
                last_zs["end_idx"] = new_zs["end_idx"]
                last_zs["end_date"] = new_zs["end_date"]
                last_zs["top"] = round(max(last_zs["top"], new_zs["top"]), 2)
                last_zs["bottom"] = round(min(last_zs["bottom"], new_zs["bottom"]), 2)
                last_zs["mid"] = round((last_zs["top"] + last_zs["bottom"]) / 2, 2)
                last_zs["width_pct"] = round((last_zs["top"] - last_zs["bottom"]) / last_zs["bottom"] * 100, 2)
                last_zs["bi_count"] += 1
                i += 2
                continue

        zhongshus.append(new_zs)
        i += 2

    return zhongshus


# ──────────────────────────────────────────────
#  背驰检测
# ──────────────────────────────────────────────

def calc_macd_area(kline: List[Dict], start: int, end: int) -> float:
    """计算一段走势的MACD柱面积"""
    if end - start < 2:
        return 0.0
    segment = kline[start:end + 1]
    df = pd.DataFrame(segment)
    close = df["close"].astype(float)

    e12 = close.ewm(span=12, adjust=False).mean()
    e26 = close.ewm(span=26, adjust=False).mean()
    dif = e12 - e26
    dea = dif.ewm(span=9, adjust=False).mean()
    macd = (dif - dea) * 2

    return round(float(macd.abs().sum()), 2)


def calc_dif_height(kline: List[Dict], start: int, end: int) -> Tuple[float, float]:
    """计算DIF（快线）的起止高度，用于判断黄白线高度背驰"""
    segment = kline[start:end + 1]
    if len(segment) < 2:
        return 0, 0
    df = pd.DataFrame(segment)
    close = df["close"].astype(float)
    e12 = close.ewm(span=12, adjust=False).mean()
    e26 = close.ewm(span=26, adjust=False).mean()
    dif = e12 - e26
    return float(dif.iloc[0]), float(dif.iloc[-1])


def detect_beichi(kline: List[Dict], bis: List[Dict]) -> List[Dict]:
    """
    背驰检测（第78-80课）

    二维背驰判定:
    1. MACD柱面积缩小（力度衰减）
    2. DIF黄白线高度不创新高/低（趋势弱化）

    两维同时出现 = 标准背驰
    仅一维出现 = 疑似背驰
    """
    if len(bis) < 2 or len(kline) < 26:
        return []

    beichis = []

    for i, bi in enumerate(bis):
        si, ei = bi["start_idx"], bi["end_idx"]
        if si >= len(kline) or ei >= len(kline):
            continue

        # 找前一个同向笔
        prev = None
        for j in range(i - 1, -1, -1):
            if bis[j]["type"] == bi["type"]:
                prev = bis[j]
                break
        if prev is None:
            continue

        # MACD面积
        curr_area = calc_macd_area(kline, max(0, si), min(ei, len(kline) - 1))
        prev_area = calc_macd_area(kline, max(0, prev["start_idx"]), min(prev["end_idx"], len(kline) - 1))
        if prev_area <= 0:
            continue

        area_ratio = curr_area / prev_area

        # DIF高度
        _, curr_dif_end = calc_dif_height(kline, max(0, si), min(ei, len(kline) - 1))
        _, prev_dif_end = calc_dif_height(kline, max(0, prev["start_idx"]), min(prev["end_idx"], len(kline) - 1))

        # 判断
        area_shrinking = area_ratio < 0.9
        dif_divergence = False
        price_confirms = False

        if bi["type"] == "up":
            # 顶背驰：价格新高但力度减弱
            price_higher = bi["end_price"] > prev["end_price"]
            price_confirms = price_higher
            dif_divergence = curr_dif_end < prev_dif_end  # DIF不创新高
        else:
            # 底背驰：价格新低但力度减弱
            price_lower = bi["end_price"] < prev["end_price"]
            price_confirms = price_lower
            dif_divergence = curr_dif_end > prev_dif_end  # DIF不创新低

        if price_confirms and (area_shrinking or dif_divergence):
            confidence = "strong" if (area_shrinking and dif_divergence) else "normal"
            beichis.append({
                "type": "top_beichi" if bi["type"] == "up" else "bottom_beichi",
                "direction": bi["type"],
                "bi_index": i,
                "start_date": bi["start_date"],
                "end_date": bi["end_date"],
                "start_price": bi["start_price"],
                "end_price": bi["end_price"],
                "curr_area": curr_area,
                "prev_area": prev_area,
                "area_ratio": round(area_ratio, 4),
                "curr_dif": round(curr_dif_end, 4),
                "prev_dif": round(prev_dif_end, 4),
                "dif_divergence": dif_divergence,
                "confidence": confidence,
            })

    return beichis


# ──────────────────────────────────────────────
#  三类买卖点
# ──────────────────────────────────────────────

def detect_3buy_points(bis: List[Dict], zhongshus: List[Dict], beichis: List[Dict]) -> List[Dict]:
    """
    三类买点（第81-87课）

    一买: 趋势底背驰 + 下跌中枢被跌破后出现背驰
    二买: 一买后回调不创新低
    三买: 离开中枢后回抽不进中枢
    """
    signals = []
    if not bis:
        return signals

    # ── 一买: 底背驰 ──
    for b in beichis:
        if b["type"] == "bottom_beichi" and b["confidence"] in ("strong", "normal"):
            bi = bis[b["bi_index"]] if b["bi_index"] < len(bis) else None
            if bi:
                signals.append({
                    "type": "1st_buy", "name": "第一类买点",
                    "description": "底背驰，下跌力度衰竭，趋势反转信号",
                    "date": bi["end_date"], "price": round(bi["end_price"], 2),
                    "bi_index": b["bi_index"],
                    "confidence": b["confidence"],
                })

    # ── 二买: 一买后回调不创新低 ──
    for i, bi in enumerate(bis):
        if bi["type"] != "down":
            continue
        prev_1st = None
        for s in signals:
            if s["type"] == "1st_buy" and s["bi_index"] < i:
                if prev_1st is None or s["bi_index"] > prev_1st["bi_index"]:
                    prev_1st = s
        if prev_1st and bi["end_price"] > prev_1st["price"]:
            signals.append({
                "type": "2nd_buy", "name": "第二类买点",
                "description": f"一买({prev_1st['price']})后回调未创新低，底部确认",
                "date": bi["end_date"], "price": round(bi["end_price"], 2),
                "bi_index": i, "confidence": "high",
            })

    # ── 三买: 离开中枢后回抽不进中枢 ──
    for zs in zhongshus:
        for i, bi in enumerate(bis):
            if bi["type"] != "up":
                continue
            if bi["start_idx"] < zs["end_idx"]:
                continue
            if i + 1 < len(bis) and bis[i + 1]["type"] == "down":
                retrace = bis[i + 1]
                if retrace["end_price"] > zs["top"]:
                    signals.append({
                        "type": "3rd_buy", "name": "第三类买点",
                        "description": f"突破中枢后回踩{zstop}不进入中枢({zs['top']})，强势确认",
                        "date": retrace["end_date"], "price": round(retrace["end_price"], 2),
                        "bi_index": i + 1,
                        "zhongshu_top": zs["top"], "zhongshu_bottom": zs["bottom"],
                        "confidence": "high",
                    })

    return signals


def detect_3sell_points(bis: List[Dict], zhongshus: List[Dict], beichis: List[Dict]) -> List[Dict]:
    """三类卖点（反向对称）"""
    signals = []

    # 一卖: 顶背驰
    for b in beichis:
        if b["type"] == "top_beichi" and b["confidence"] in ("strong", "normal"):
            bi = bis[b["bi_index"]] if b["bi_index"] < len(bis) else None
            if bi:
                signals.append({
                    "type": "1st_sell", "name": "第一类卖点",
                    "description": "顶背驰，上涨力度衰竭",
                    "date": bi["end_date"], "price": round(bi["end_price"], 2),
                    "bi_index": b["bi_index"], "confidence": b["confidence"],
                })

    # 二卖: 一卖后反抽不创新高
    for i, bi in enumerate(bis):
        if bi["type"] != "up":
            continue
        prev_1st = None
        for s in signals:
            if s["type"] == "1st_sell" and s["bi_index"] < i:
                if prev_1st is None or s["bi_index"] > prev_1st["bi_index"]:
                    prev_1st = s
        if prev_1st and bi["end_price"] < prev_1st["price"]:
            signals.append({
                "type": "2nd_sell", "name": "第二类卖点",
                "description": "一卖后反抽未创新高，确认顶部",
                "date": bi["end_date"], "price": round(bi["end_price"], 2),
                "bi_index": i, "confidence": "medium",
            })

    # 三卖: 离开中枢后反抽不进中枢
    for zs in zhongshus:
        for i, bi in enumerate(bis):
            if bi["type"] != "down":
                continue
            if bi["start_idx"] < zs["end_idx"]:
                continue
            if i + 1 < len(bis) and bis[i + 1]["type"] == "up":
                bounce = bis[i + 1]
                if bounce["end_price"] < zs["bottom"]:
                    signals.append({
                        "type": "3rd_sell", "name": "第三类卖点",
                        "description": f"跌破中枢后反抽不进中枢({zs['bottom']})",
                        "date": bounce["end_date"], "price": round(bounce["end_price"], 2),
                        "bi_index": i + 1, "confidence": "high",
                    })

    return signals


# ──────────────────────────────────────────────
#  综合评分 (0-100)
# ──────────────────────────────────────────────

def score_chan_analysis(
    buy_signals: List[Dict], sell_signals: List[Dict],
    zhongshus: List[Dict], bis: List[Dict],
    current_price: float
) -> Dict:
    """
    缠论综合评分 0-100（比原来 0-25 更细致）

    评分维度:
      - 买点信号 (0-35): 分值随买点级别递增（三买>二买>一买）
      - 中枢健康 (0-25): 宽度+位置+突破状态
      - 背驰确认 (0-20): 背驰强度
      - 趋势结构 (0-20): 笔的斜率 和 方向一致性
    """
    buy_score = 0
    sell_penalty = 0

    for s in buy_signals:
        weight = {"1st_buy": 15, "2nd_buy": 25, "3rd_buy": 35}.get(s["type"], 10)
        conf = {"strong": 1.0, "high": 1.0, "normal": 0.7, "medium": 0.7}.get(s.get("confidence", "normal"), 0.5)
        buy_score = max(buy_score, weight * conf)

    for s in sell_signals:
        weight = {"1st_sell": 20, "2nd_sell": 15, "3rd_sell": 10}.get(s["type"], 5)
        sell_penalty = max(sell_penalty, weight)

    # 中枢评分
    zs_score = 0
    if zhongshus:
        zs = zhongshus[-1]
        w = zs.get("width_pct", 100)
        if w < 3:
            zs_score = 20  # 窄中枢→强势
        elif w < 8:
            zs_score = 15
        elif w < 15:
            zs_score = 10
        else:
            zs_score = 5

        # 价格在中枢下沿附近=潜在机会
        if current_price > 0:
            pos = (current_price - zs["bottom"]) / (zs["top"] - zs["bottom"]) if zs["top"] > zs["bottom"] else 0.5
            if pos < 0.3:
                zs_score += 5
            elif pos > 0.7:
                zs_score -= 3

    # 趋势评分
    trend_score = 0
    up_bis = [b for b in bis if b["type"] == "up"]
    down_bis = [b for b in bis if b["type"] == "down"]
    if up_bis and down_bis:
        avg_up = sum(b["height_pct"] for b in up_bis) / len(up_bis)
        avg_down = sum(b["height_pct"] for b in down_bis) / len(down_bis)
        ratio = avg_up / avg_down if avg_down > 0 else 1
        trend_score = min(20, max(0, int(ratio * 10)))  # 0-20

    total = min(100, max(0, buy_score + zs_score + trend_score - sell_penalty))

    direction = "buy" if buy_score > sell_penalty + 5 else "sell" if sell_penalty > buy_score + 5 else "neutral"

    return {
        "total": round(total),
        "breakdown": {
            "buy_signals": round(min(buy_score, 35)),
            "sell_penalty": round(min(sell_penalty, 25)),
            "zhongshu": round(min(zs_score, 25)),
            "trend": round(min(trend_score, 20)),
        },
        "direction": direction,
    }


# ──────────────────────────────────────────────
#  完整分析流程
# ──────────────────────────────────────────────

def analyze_kline(kline: List[Dict]) -> Dict:
    """
    一组K线完整缠论分析:
      包含处理 → 分型 → 笔 → 中枢 → 背驰 → 买卖点 → 评分
    """
    if len(kline) < 20:
        return {"error": f"K线不足 (len={len(kline)}), 至少需20根"}

    try:
        clean = process_inclusion(kline)
        fenxings = detect_fenxing(clean)
        bis = detect_bi(fenxings)
        zhongshus = detect_zhongshu(bis)
        beichis = detect_beichi(kline, bis)
        buy_signals = detect_3buy_points(bis, zhongshus, beichis)
        sell_signals = detect_3sell_points(bis, zhongshus, beichis)
        price = float(kline[-1].get("close", 0))
        score = score_chan_analysis(buy_signals, sell_signals, zhongshus, bis, price)

        return {
            "total_bars": len(kline),
            "clean_bars": len(clean),
            "fenxings": fenxings[-30:],
            "bis": bis[-15:],
            "zhongshus": zhongshus[-5:],
            "beichis": beichis[-5:],
            "buy_signals": buy_signals,
            "sell_signals": sell_signals,
            "score": score,
            "summary": _make_summary(score, bis, buy_signals, sell_signals, price),
        }
    except Exception as e:
        logger.error(f"缠论分析异常: {e}")
        return {"error": str(e)}


def _make_summary(score: Dict, bis: List[Dict], buy_signals: List[Dict],
                  sell_signals: List[Dict], price: float) -> str:
    """生成简洁的中文摘要"""
    total = score.get("total", 0)
    direction = score.get("direction", "neutral")
    d_emoji = {"buy": "📈", "sell": "📉", "neutral": "⚖️"}
    d_cn = {"buy": "偏多", "sell": "偏空", "neutral": "中性"}

    lines = [
        f"{d_emoji.get(direction, '❓')} 缠论评分 {total}/100 | {d_cn.get(direction, '未知')}",
        f"📊 {len(bis)}段笔 | {len(buy_signals)}个买点 | {len(sell_signals)}个卖点"
    ]
    buy_names = [s["name"] for s in buy_signals[:3]]
    sell_names = [s["name"] for s in sell_signals[:3]]
    if buy_names:
        lines.append(f"✅ 买点: {'、'.join(buy_names)}")
    if sell_names:
        lines.append(f"⚠️ 卖点: {'、'.join(sell_names)}")
    lines.append(f"💰 现价: {price:.2f}")
    return "\n".join(lines)


# ──────────────────────────────────────────────
#  多级别分析
# ──────────────────────────────────────────────

async def multi_level_analysis(code: str, levels: List[tuple] = None) -> Dict:
    """多级别联立 + 区间套"""
    if levels is None:
        levels = [("日线", "D", 500), ("30分钟", "30", 800), ("5分钟", "5", 1000)]

    result = {"code": code, "levels": {}}
    level_results = []

    for name, ktype, limit in levels:
        try:
            kline = await data_service.get_kline(code, ktype=ktype, limit=limit)
            if len(kline) < 30:
                result["levels"][name] = {"error": f"数据不足({len(kline)})"}
                continue
            analysis = analyze_kline(kline)
            s = analysis.get("score", {})
            data = {
                "score": s.get("total", 0),
                "direction": s.get("direction", "neutral"),
                "bis": len(analysis.get("bis", [])),
                "zhongshus": len(analysis.get("zhongshus", [])),
                "buy_signals": analysis.get("buy_signals", []),
                "sell_signals": analysis.get("sell_signals", []),
            }
            result["levels"][name] = data
            level_results.append((name, data))
        except Exception as e:
            result["levels"][name] = {"error": str(e)}

    # 区间套判定
    interval_signals = []
    buy_level_names = [n for n, d in level_results if d.get("direction") == "buy"]
    sell_level_names = [n for n, d in level_results if d.get("direction") == "sell"]

    if "日线" in buy_level_names and "30分钟" in buy_level_names:
        interval_signals.append("🔥 日线+30分钟共振买点，区间套成立")
    if "日线" in sell_level_names and "30分钟" in sell_level_names:
        interval_signals.append("⚠️ 日线+30分钟共振卖点，注意风险")
    if "30分钟" in buy_level_names and "5分钟" in buy_level_names:
        interval_signals.append("✅ 30分钟+5分钟共振，短线上攻信号")

    result["interval_signals"] = interval_signals
    buy_cnt = sum(1 for _, d in level_results if d.get("direction") == "buy")
    sell_cnt = sum(1 for _, d in level_results if d.get("direction") == "sell")
    result["overall"] = "buy" if buy_cnt > sell_cnt else "sell" if sell_cnt > buy_cnt else "neutral"

    return result


# ──────────────────────────────────────────────
#  对外服务类
# ──────────────────────────────────────────────

class ChanService:
    """缠论分析服务 — 对外接口"""

    async def analyze(self, code: str) -> Dict:
        """单只股票完整分析"""
        # 尝试缓存
        cache_key = f"chan_{code}"
        cached = cache_get(cache_key)
        if cached:
            return cached

        kline = await data_service.get_kline(code, limit=500)
        if not kline or len(kline) < 30:
            return {"code": code, "error": f"K线数据不足 ({len(kline) if kline else 0})"}

        analysis = analyze_kline(kline)
        multi = await multi_level_analysis(code)

        result = {
            "code": code,
            "price": float(kline[-1].get("close", 0)),
            "date": kline[-1].get("date", ""),
            "analysis": analysis,
            "multi_level": multi,
        }

        cache_set(cache_key, result, ttl=600)
        return result

    def analyze_kline(self, kline: List[Dict]) -> Dict:
        """同步分析接口"""
        return analyze_kline(kline)

    @staticmethod
    def _generate_summary(analysis: Dict, latest_bar: Dict) -> str:
        return analysis.get("summary", "分析完成")


chan_service = ChanService()
