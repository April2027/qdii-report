# -*- coding: utf-8 -*-
"""
QDII 早报 —— 数据抓取器（v2）
抓取：
  ① 每只基金的最新净值 / 当日涨跌 / 近1月 / 近6月 / 近1年（+近3年）
  ② 每只基金近 1 年历史净值（详情页走势图）
  ③ 海外指数前夜行情
产出：data/snapshot.json、data/history.jsonl
"""
import json
import os
import re
import sys
import time
from datetime import datetime, timezone, timedelta

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import ALL_FUNDS, INDEX_BOARD, OTHER_GROUP_ORDER

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

CST = timezone(timedelta(hours=8))

UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
      "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1")

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": UA})

API_BASE = "https://fundmobapi.eastmoney.com/FundMNewApi"
COMMON = {"plat": "Android", "appType": "ttjj", "product": "EFund",
          "Version": "1", "deviceid": "qdii-report"}


# ---------------------------------------------------------------- 通用
def _get_with_retry(url, retries=3, delay=1.5, **kwargs):
    """带重试的 GET。新浪等接口偶发 Forbidden，重试即可恢复。"""
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            r = SESSION.get(url, timeout=20, **kwargs)
            if r.status_code == 200 and "forbidden" not in r.text[:60].lower():
                return r
            last_exc = RuntimeError(f"HTTP {r.status_code}: {r.text[:60]!r}")
        except Exception as e:
            last_exc = e
        if attempt < retries:
            time.sleep(delay * attempt)
    raise last_exc


def _num(v):
    """安全转 float，'--' / '' / None 一律返回 None。"""
    if v in (None, "", "--"):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------- 基金详情
def fetch_detail(code, meta):
    """抓取单只基金详情：净值 + 日涨跌 + 阶段涨幅 + 申购状态 + 公司。"""
    url = f"{API_BASE}/FundMNBasicInformation"
    params = dict(COMMON, FCODE=code, _=int(time.time() * 1000))
    got = {}
    for attempt in range(3):
        try:
            got = (_get_with_retry(url, params=params).json().get("Datas")) or {}
            if got:
                break
        except Exception:
            time.sleep(1.0 * (attempt + 1))
    if not got:
        return None
    return {
        "code": code,
        "name": meta["name"],                                  # 展示用短名（配置为准）
        "full_name": (got.get("SHORTNAME") or "").strip(),      # 官方简称
        "company": got.get("JJGS") or meta.get("company"),
        "nav": _num(got.get("DWJZ")),
        "nav_date": got.get("FSRQ"),
        "chg": _num(got.get("RZDF")),
        "r1m": _num(got.get("SYL_Y")),      # 近 1 月
        "r6m": _num(got.get("SYL_6Y")),     # 近 6 月
        "r1y": _num(got.get("SYL_1N")),     # 近 1 年
        "r3y": _num(got.get("SYL_3N")),     # 近 3 年
        "sgzt": (got.get("SGZT") or "").strip(),
        "ftype": got.get("FTYPE") or "",
        "scale": _num(got.get("ENDNAV")),
        "estab": (got.get("ESTABDATE") or "")[:10],
        "risk": got.get("RISKLEVEL") or "",
    }


def fetch_all_details(funds):
    """逐只抓取详情。天天基金该接口不支持批量，需串行（约 0.2s/只）。"""
    out, missing = {}, []
    for i, f in enumerate(funds, 1):
        code = f["code"]
        d = fetch_detail(code, f)
        if d and d.get("nav") is not None:
            out[code] = d
            print(f"  [{i}/{len(funds)}] {code} {f['name'][:24]:<26} "
                  f"净值 {d['nav']:<8} 日 {d['chg']}% 1月 {d['r1m']}% 1年 {d['r1y']}%  {d['sgzt']}")
        else:
            missing.append(code)
            print(f"  [{i}/{len(funds)}] {code} 抓取失败")
        time.sleep(0.2)
    return out, missing


# ---------------------------------------------------------------- 历史净值
def fetch_history(code, page_size=300):
    """抓取近 1 年历史净值，返回 [[日期, 单位净值], ...]（按时间正序）。"""
    url = f"{API_BASE}/FundMNHisNetList"
    params = dict(COMMON, FCODE=code, pageIndex=1, pageSize=page_size,
                  _=int(time.time() * 1000))
    rows = []
    for attempt in range(3):
        try:
            rows = (_get_with_retry(url, params=params).json().get("Datas")) or []
            if rows:
                break
        except Exception:
            time.sleep(0.8 * (attempt + 1))
    seq = []
    for row in reversed(rows):          # 接口返回倒序 -> 翻正
        try:
            seq.append([row["FSRQ"], round(float(row["DWJZ"]), 4)])
        except (KeyError, TypeError, ValueError):
            continue
    return seq


def fetch_all_history(funds):
    out, missing = {}, []
    for f in funds:
        code = f["code"]
        seq = fetch_history(code)
        if seq:
            out[code] = seq
        else:
            missing.append(code)
        time.sleep(0.15)
    return out, missing


# ---------------------------------------------------------------- 海外指数
SINA_RE = re.compile(r'var hq_str_([^=]+)="([^"]*)"')


def fetch_index_board():
    """抓取海外指数前夜行情。"""
    keys = [i["key"] for i in INDEX_BOARD]
    url = "https://hq.sinajs.cn/list=" + ",".join(keys)
    try:
        r = _get_with_retry(url, retries=4, delay=2,
                            headers={"Referer": "https://finance.sina.com.cn"})
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
        try:
            if meta["key"].startswith("gb_"):
                # 美股格式: 名称,现价,涨跌幅,时间,涨跌额,...
                name, price, chg_pct, ts = p[0], float(p[1]), float(p[2]), p[3]
                chg_amt = float(p[4]) if len(p) > 4 and p[4] else None
            else:
                # 国际指数格式: 名称,现价,涨跌额,涨跌幅
                name, price = p[0], float(p[1])
                chg_amt, chg_pct, ts = float(p[2]), float(p[3]), None
        except (IndexError, ValueError):
            continue
        out.append({
            "key": meta["key"],
            "name": meta["name"], "region": meta["region"],
            "price": price, "chg_pct": chg_pct, "chg_amt": chg_amt,
            "time": ts,
        })
    return out


# ---------------------------------------------------------------- 组装
def _summarize(items):
    """一段基金集合的涨跌统计。"""
    valid = [x for x in items if x.get("chg") is not None]
    up = [x for x in valid if x["chg"] > 0]
    down = [x for x in valid if x["chg"] < 0]
    return {
        "total": len(items),
        "valid": len(valid),
        "up": len(up), "down": len(down),
        "flat": len(valid) - len(up) - len(down),
        "avg_chg": round(sum(x["chg"] for x in valid) / len(valid), 2) if valid else 0,
    }


def build_snapshot():
    now = datetime.now(CST)
    funds_meta = ALL_FUNDS
    codes = [f["code"] for f in funds_meta]
    print(f"[1/4] 抓取 {len(codes)} 只基金详情（净值 / 阶段涨幅）...")
    details, miss_detail = fetch_all_details(funds_meta)
    print(f"      成功 {len(details)} 只")

    print("[2/4] 抓取近 1 年历史净值（详情页走势图）...")
    hist, miss_hist = fetch_all_history(funds_meta)
    print(f"      成功 {len(hist)} 只，共 {sum(len(v) for v in hist.values())} 条")

    print("[3/4] 抓取海外指数行情 ...")
    indexes = fetch_index_board()
    if not indexes:
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

    print("[4/4] 组装数据 ...")
    idx_map = {i["key"]: i for i in indexes}

    # 每只基金合并配置 + 详情
    merged_all = {}
    for meta in funds_meta:
        code = meta["code"]
        d = details.get(code)
        if not d:
            continue
        # 实际申购状态以接口为准（限大额 / 开放申购 都算"可买"）
        sgzt = d.get("sgzt") or ""
        purchasable = ("开放申购" in sgzt) or ("限大额" in sgzt) or ("限购" in sgzt)
        merged_all[code] = {
            "code": code,
            "name": meta["name"],
            "full_name": d.get("full_name") or meta["name"],
            "company": d.get("company") or meta.get("company"),
            "nav": d["nav"],
            "nav_date": d["nav_date"],
            "chg": d["chg"],
            "r1m": d["r1m"], "r6m": d["r6m"], "r1y": d["r1y"], "r3y": d["r3y"],
            "sgzt": sgzt,
            "ftype": d.get("ftype"),
            "scale": d.get("scale"),
            "estab": d.get("estab"),
            "risk": d.get("risk"),
            "status": "on_sale" if purchasable else "paused",
            "family": meta["family"],
            "share": meta["share"],
            "group": meta.get("group"),
            "note": meta.get("note"),
            # 历史净值序列（详情页画图用，压缩成 [ [date, nav], ... ]）
            "hist": hist.get(code) or [],
        }

    # 构建区块
    def build_section(seed_funds):
        """把 A/C 同系列归成一条，主行显示 A，下面挂 C。"""
        families = []
        seen = {}
        for m in seed_funds:
            fam = m["family"]
            if fam not in seen:
                seen[fam] = {"family": fam, "members": []}
                families.append(seen[fam])
            item = merged_all.get(m["code"])
            if item:
                seen[fam]["members"].append(item)
        # 同一 family 内 A 在前 C 在后
        for f in families:
            f["members"].sort(key=lambda x: (x["share"] != "A", x["code"]))
            f["primary"] = f["members"][0] if f["members"] else None
            f["on_sale"] = any(x["status"] == "on_sale" for x in f["members"])
            chgs = [x["chg"] for x in f["members"] if x["chg"] is not None]
            f["chg"] = round(sum(chgs) / len(chgs), 2) if chgs else None
        return families

    sections = []
    for sec in [
        {"key": "NASDAQ100", "name": "纳斯达克100", "short": "纳指100",
         "seed": [f for f in NASDAQ100_CFG], "track": "gb_$ndx"},
        {"key": "SP500", "name": "标普500", "short": "标普500",
         "seed": [f for f in SP500_CFG], "track": "gb_$inx"},
    ]:
        fams = build_section(sec["seed"])
        live = [f for f in fams if f["on_sale"] and f["primary"]]
        hold = [f for f in fams if not f["on_sale"] and f["primary"]]
        # 在售按当日涨跌降序，暂停按近1年降序
        live.sort(key=lambda x: (x["chg"] is None, -(x["chg"] or 0)))
        hold.sort(key=lambda x: (
            x["primary"]["r1y"] is None, -(x["primary"]["r1y"] or 0)))
        members = [x for f in fams for x in f["members"]]
        sections.append({
            "key": sec["key"], "name": sec["name"], "short": sec["short"],
            "track": sec["track"],
            "index": idx_map.get(sec["track"]),
            "live": live, "hold": hold,
            "stats": _summarize(members),
            "count_families": len([f for f in fams if f["primary"]]),
            "count_funds": len(members),
        })

    # 其他板块（按配置分组）
    other_funds = [merged_all[m["code"]] for m in OTHERS_CFG if m["code"] in merged_all]
    other_funds.sort(key=lambda x: (x["chg"] is None, -(x["chg"] or 0)))
    other_groups = []
    for g in OTHER_GROUP_ORDER:
        gs = [x for x in other_funds if x["group"] == g]
        if gs:
            other_groups.append({"name": g, "funds": gs})
    other_section = {
        "key": "OTHERS", "name": "其他热门 QDII", "short": "其他",
        "track": None, "index": None,
        "groups": other_groups,
        "live": [], "hold": [],
        "stats": _summarize(other_funds),
        "count_families": len(other_funds),
        "count_funds": len(other_funds),
    }

    all_items = list(merged_all.values())
    overall = _summarize(all_items)

    nav_dates = sorted({x["nav_date"] for x in all_items if x["nav_date"]}, reverse=True)

    snapshot = {
        "version": 2,
        "generated_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        "report_date": now.strftime("%Y-%m-%d"),
        "weekday": "一二三四五六日"[now.weekday()],
        "nav_dates": nav_dates[:6],
        "latest_nav_date": nav_dates[0] if nav_dates else None,
        "stats": overall,
        "indexes": indexes,
        "sections": sections,
        "other": other_section,
        "funds": merged_all,      # 详情页数据源：code -> 详情（含 hist）
        "missing": {"detail": miss_detail, "history": miss_hist},
    }
    return snapshot


from config import NASDAQ100 as NASDAQ100_CFG, SP500 as SP500_CFG, OTHERS as OTHERS_CFG


def main():
    snap = build_snapshot()
    out = os.path.join(DATA_DIR, "snapshot.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(snap, f, ensure_ascii=False, separators=(",", ":"))

    hist_path = os.path.join(DATA_DIR, "history.jsonl")
    with open(hist_path, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "generated_at": snap["generated_at"],
            "latest_nav_date": snap["latest_nav_date"],
            "stats": snap["stats"],
            "funds": {x["code"]: x["nav"] for x in snap["funds"].values()},
        }, ensure_ascii=False) + "\n")

    s = snap["stats"]
    print(f"\n完成 -> {out}  ({os.path.getsize(out)//1024} KB)")
    print(f"  共 {s['total']} 只 | 涨 {s['up']} 跌 {s['down']} 平 {s['flat']} | 均值 {s['avg_chg']}%")
    print(f"  最新净值日期: {snap['latest_nav_date']}")
    for sec in snap["sections"]:
        st = sec["stats"]
        print(f"  [{sec['name']}] 系列 {sec['count_families']} / 份额 {sec['count_funds']} "
              f"| 在售 {len(sec['live'])} 暂停 {len(sec['hold'])} | 均值 {st['avg_chg']}%")
    if snap["missing"]["detail"]:
        print(f"  未取到详情: {snap['missing']['detail']}")
    return out


if __name__ == "__main__":
    main()
