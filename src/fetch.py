# -*- coding: utf-8 -*-
"""
QDII 早报 —— 数据抓取器
抓取：① 基金最新净值+涨跌  ② 海外指数前夜行情
产出：data/snapshot.json
"""
import json
import os
import re
import sys
import time
from datetime import datetime, timezone, timedelta

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import FUND_POOL, INDEX_BOARD, GROUP_ORDER

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

CST = timezone(timedelta(hours=8))

UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
      "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1")

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": UA})


# ---------------------------------------------------------------- 基金净值
def _get_with_retry(url, retries=3, delay=1.5, **kwargs):
    """带重试的 GET。新浪等接口偶发 Forbidden，重试即可恢复。"""
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            r = SESSION.get(url, timeout=15, **kwargs)
            if r.status_code == 200 and "forbidden" not in r.text[:50].lower():
                return r
            last_exc = RuntimeError(f"HTTP {r.status_code}: {r.text[:60]!r}")
        except Exception as e:
            last_exc = e
        if attempt < retries:
            time.sleep(delay * attempt)
    raise last_exc


def fetch_funds(codes):
    """批量抓取基金最新净值。天天基金单次上限约 20 只，分批。"""
    url = "https://fundmobapi.eastmoney.com/FundMNewApi/FundMNFInfo"
    result = {}
    for i in range(0, len(codes), 20):
        batch = codes[i:i + 20]
        params = {
            "pageIndex": 1, "pageSize": len(batch),
            "plat": "Android", "appType": "ttjj", "product": "EFund",
            "Version": "1", "deviceid": "qdii-report",
            "Fcodes": ",".join(batch),
            "_": int(time.time() * 1000),
        }
        try:
            payload = _get_with_retry(url, params=params).json()
        except Exception as e:
            print(f"  [警告] 批次 {batch} 抓取失败: {e}")
            continue
        for item in payload.get("Datas") or []:
            code = item.get("FCODE")
            try:
                nav = float(item.get("NAV"))
            except (TypeError, ValueError):
                nav = None
            try:
                chg = float(item.get("NAVCHGRT"))
            except (TypeError, ValueError):
                chg = None
            result[code] = {
                "code": code,
                "name": (item.get("SHORTNAME") or "").strip(),
                "nav": nav,
                "acc_nav": item.get("ACCNAV"),
                "chg": chg,
                "nav_date": item.get("PDATE"),
            }
        time.sleep(0.25)
    return result


def fetch_history(code, pages=1):
    """抓取历史净值（用于迷你走势图）。"""
    url = "https://fundmobapi.eastmoney.com/FundMNewApi/FundMNHisNetList"
    params = {
        "FCODE": code, "pageIndex": 1, "pageSize": 20,
        "plat": "Android", "appType": "ttjj", "product": "EFund",
        "Version": "1", "deviceid": "qdii-report",
        "_": int(time.time() * 1000),
    }
    try:
        r = SESSION.get(url, params=params, timeout=15)
        rows = r.json().get("Datas") or []
    except Exception:
        return []
    out = []
    for row in reversed(rows):          # 接口返回倒序，翻正
        try:
            out.append({"date": row["FSRQ"], "nav": float(row["DWJZ"])})
        except (KeyError, TypeError, ValueError):
            continue
    return out


# ---------------------------------------------------------------- 海外指数
SINA_RE = re.compile(r'var hq_str_([^=]+)="([^"]*)"')


def fetch_index_board():
    """抓取海外指数前夜行情（内置重试）。"""
    keys = [i["key"] for i in INDEX_BOARD]
    url = "https://hq.sinajs.cn/list=" + ",".join(keys)
    try:
        r = _get_with_retry(
            url, retries=4, delay=2,
            headers={"Referer": "https://finance.sina.com.cn"},
        )
        r.encoding = "gbk"
        text = r.text
    except Exception as e:
        print(f"  [警告] 指数抓取失败(已重试): {e}")
        return []

    raw = dict(SINA_RE.findall(text))
    out = []
    for meta in INDEX_BOARD:
        line = raw.get(meta["key"], "")
        if not line:
            continue
        p = line.split(",")
        # 国际指数格式: 名称,现价,涨跌额,涨跌幅
        # 美股格式:     名称,现价,涨跌幅,时间,涨跌额,...
        try:
            if meta["key"].startswith("gb_"):
                name, price, chg_pct, ts = p[0], float(p[1]), float(p[2]), p[3]
                chg_amt = float(p[4]) if len(p) > 4 and p[4] else None
            else:
                name, price = p[0], float(p[1])
                chg_amt, chg_pct, ts = float(p[2]), float(p[3]), None
        except (IndexError, ValueError):
            continue
        out.append({
            "name": meta["name"], "region": meta["region"],
            "price": price, "chg_pct": chg_pct, "chg_amt": chg_amt,
            "time": ts,
        })
    return out


# ---------------------------------------------------------------- 汇总
def build_snapshot():
    now = datetime.now(CST)
    codes = [f["code"] for f in FUND_POOL]

    print(f"[1/3] 抓取 {len(codes)} 只基金净值 ...")
    funds_raw = fetch_funds(codes)
    print(f"      成功 {len(funds_raw)} 只")

    print("[2/3] 抓取海外指数行情 ...")
    indexes = fetch_index_board()
    if not indexes:
        # 兜底：沿用上一次快照里的指数（标注为上期数据）
        prev = os.path.join(DATA_DIR, "snapshot.json")
        if os.path.exists(prev):
            try:
                with open(prev, encoding="utf-8") as f:
                    old = json.load(f)
                indexes = old.get("indexes") or []
                if indexes:
                    print(f"      今日抓取失败，沿用上期 {len(indexes)} 个指数")
            except Exception:
                pass
    print(f"      成功 {len(indexes)} 个指数")

    print("[3/3] 组装数据 ...")
    meta_map = {f["code"]: f for f in FUND_POOL}
    groups = {g: [] for g in GROUP_ORDER}
    missing = []

    for code in codes:
        item = funds_raw.get(code)
        if not item:
            missing.append(code)
            continue
        meta = meta_map[code]
        merged = {
            "code": code,
            "name": meta["name"],
            "short_name": item["name"] or meta["name"],
            "nav": item["nav"],
            "chg": item["chg"],
            "nav_date": item["nav_date"],
        }
        groups.setdefault(meta["group"], []).append(merged)

    # 组内按当日涨跌排序（涨在前）
    for g in groups:
        groups[g].sort(key=lambda x: (x["chg"] is None, -(x["chg"] or 0)))

    all_funds = [f for g in GROUP_ORDER for f in groups.get(g, [])]
    valid = [f for f in all_funds if f["chg"] is not None]
    up = [f for f in valid if f["chg"] > 0]
    down = [f for f in valid if f["chg"] < 0]

    # 净值日期分布（用于提示"这是哪天的净值"）
    nav_dates = sorted({f["nav_date"] for f in all_funds if f["nav_date"]}, reverse=True)

    snapshot = {
        "generated_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        "report_date": now.strftime("%Y-%m-%d"),
        "weekday": "一二三四五六日"[now.weekday()],
        "nav_dates": nav_dates[:5],
        "latest_nav_date": nav_dates[0] if nav_dates else None,
        "stats": {
            "total": len(all_funds),
            "up": len(up), "down": len(down),
            "flat": len(valid) - len(up) - len(down),
            "avg_chg": round(sum(f["chg"] for f in valid) / len(valid), 2) if valid else 0,
        },
        "indexes": indexes,
        "groups": [{"name": g, "funds": groups.get(g, [])}
                   for g in GROUP_ORDER if groups.get(g)],
        "all_funds": all_funds,
        "missing": missing,
    }
    return snapshot


def main():
    snap = build_snapshot()
    out = os.path.join(DATA_DIR, "snapshot.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(snap, f, ensure_ascii=False, indent=2)

    # 追加到历史归档，便于以后做趋势
    hist_path = os.path.join(DATA_DIR, "history.jsonl")
    with open(hist_path, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "generated_at": snap["generated_at"],
            "latest_nav_date": snap["latest_nav_date"],
            "stats": snap["stats"],
            "funds": {x["code"]: x["nav"] for x in snap["all_funds"]},
        }, ensure_ascii=False) + "\n")

    s = snap["stats"]
    print(f"\n完成 -> {out}")
    print(f"  共 {s['total']} 只 | 涨 {s['up']} 跌 {s['down']} 平 {s['flat']} "
          f"| 均值 {s['avg_chg']}%")
    print(f"  最新净值日期: {snap['latest_nav_date']}")
    if snap["missing"]:
        print(f"  未取到: {snap['missing']}")
    return out


if __name__ == "__main__":
    main()
