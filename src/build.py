# -*- coding: utf-8 -*-
"""
QDII 早报 —— 页面生成器
读取 data/snapshot.json，渲染出单文件 H5（数据内联，零请求秒开）
附带 PWA 清单：安卓 Chrome「添加到主屏幕」后可全屏独立运行

输出目录优先取环境变量 QDII_OUT，否则用 <项目根>/site
（相对路径，本地与 GitHub Actions 通用）
"""
import base64
import io
import json
import os
import urllib.parse
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)          # src 的上一级
OUT_DIR = os.environ.get("QDII_OUT") or os.path.join(PROJECT_ROOT, "site")


def make_icon_b64(size):
    """生成应用图标（红底 Q 字）并返回 data URI。PWA 安装用。"""
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new("RGB", (size, size), "#c62828")
    d = ImageDraw.Draw(img)
    # 渐变效果：顶部亮一点
    for y in range(size):
        ratio = y / size
        r = int(198 - ratio * 70)
        g = int(40 - ratio * 22)
        b = int(40 - ratio * 22)
        d.line([(0, y), (size, y)], fill=(max(r, 95), max(g, 18), max(b, 18)))
    text = "Q"
    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(size * 0.62)
        )
    except Exception:
        font = ImageFont.load_default()
    box = d.textbbox((0, 0), text, font=font)
    w, h = box[2] - box[0], box[3] - box[1]
    d.text(((size - w) / 2 - box[0], (size - h) / 2 - box[1] - size * 0.02),
           text, font=font, fill="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def make_manifest():
    """内联 PWA 清单（含 data URI 图标），保持单文件交付。"""
    icons = [
        {"src": make_icon_b64(192), "sizes": "192x192", "type": "image/png"},
        {"src": make_icon_b64(512), "sizes": "512x512", "type": "image/png",
         "purpose": "any maskable"},
    ]
    manifest = {
        "name": "QDII 基金净值早报",
        "short_name": "QDII早报",
        "description": "每天早9点发布场外QDII基金最新净值与涨跌",
        "start_url": ".",
        "display": "standalone",
        "background_color": "#f4f5f7",
        "theme_color": "#c62828",
        "icons": icons,
    }
    encoded = urllib.parse.quote(json.dumps(manifest, ensure_ascii=False))
    return "data:application/manifest+json," + encoded

TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<meta name="theme-color" content="#c62828">
<meta name="format-detection" content="telephone=no">
<meta name="mobile-web-app-capable" content="yes">
<link rel="manifest" href="__MANIFEST__">
<link rel="icon" type="image/png" href="__ICON192__">
<title>QDII 早报 · __REPORT_DATE__</title>
<style>
:root{
  --red:#d93025; --green:#0f9d58; --bg:#f4f5f7; --card:#fff;
  --t1:#1a1a1a; --t2:#6b7280; --t3:#9ca3af; --line:#eceef1;
  --shadow:0 1px 2px rgba(16,24,40,.05),0 4px 12px rgba(16,24,40,.05);
}
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
body{
  font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
  background:var(--bg); color:var(--t1); font-size:15px; line-height:1.5;
  padding-bottom:calc(64px + env(safe-area-inset-bottom));
  -webkit-font-smoothing:antialiased; overflow-x:hidden;
}
.wrap{max-width:600px;margin:0 auto}

/* ---------- 顶部 ---------- */
.hero{
  background:linear-gradient(160deg,#c62828 0%,#8e1c1c 55%,#5f1212 100%);
  color:#fff; padding:calc(20px + env(safe-area-inset-top)) 20px 22px;
  border-radius:0 0 22px 22px; position:relative; overflow:hidden;
}
.hero::after{
  content:""; position:absolute; right:-60px; top:-60px; width:180px;height:180px;
  background:radial-gradient(circle,rgba(255,255,255,.13),transparent 70%); border-radius:50%;
}
.hero-top{display:flex;justify-content:space-between;align-items:flex-start;position:relative;z-index:1;gap:10px}
.hero-top .ht-left{min-width:0}
.hero h1{font-size:21px;font-weight:700;letter-spacing:.5px}
.hero .sub{font-size:12.5px;opacity:.82;margin-top:5px}
.badge{
  background:rgba(255,255,255,.18); border:1px solid rgba(255,255,255,.28);
  padding:4px 10px; border-radius:20px; font-size:11.5px; backdrop-filter:blur(6px);
  white-space:nowrap; flex:0 0 auto; margin-top:2px;
}
/* 概览三栏 */
.overview{
  display:flex; margin-top:18px; background:rgba(255,255,255,.12);
  border:1px solid rgba(255,255,255,.16); border-radius:14px; overflow:hidden;
  position:relative; z-index:1; backdrop-filter:blur(8px);
}
.ov-cell{flex:1; padding:12px 6px; text-align:center; position:relative}
.ov-cell + .ov-cell::before{
  content:""; position:absolute; left:0; top:22%; height:56%; width:1px; background:rgba(255,255,255,.2);
}
.ov-num{font-size:20px; font-weight:700; font-variant-numeric:tabular-nums; letter-spacing:-.5px}
.ov-lbl{font-size:11.5px; opacity:.78; margin-top:3px}

/* ---------- 净值日期提示（重要） ---------- */
.notice{
  margin:14px 16px 0; background:#fff8e6; border:1px solid #ffe2a8;
  border-radius:12px; padding:11px 13px; display:flex; gap:9px; align-items:flex-start;
}
.notice .ico{flex:0 0 16px;color:#e8a33d;font-size:14px;line-height:1.35}
.notice .txt{font-size:12.5px;color:#8a6321;line-height:1.55}
.notice b{color:#c47f13}

/* ---------- 指数看板 ---------- */
.sec{padding:0 16px;margin-top:18px}
.sec-hd{display:flex;align-items:baseline;justify-content:space-between;margin-bottom:9px;padding:0 2px}
.sec-hd h2{font-size:15.5px;font-weight:700;letter-spacing:.2px}
.sec-hd .hint{font-size:11.5px;color:var(--t3)}
.idx-card{background:var(--card);border-radius:14px;box-shadow:var(--shadow);overflow:hidden}
.idx-row{
  display:flex;align-items:center;justify-content:space-between;
  padding:12px 15px; position:relative;
}
.idx-row + .idx-row::before{
  content:"";position:absolute;left:15px;right:15px;top:0;height:1px;background:var(--line);
}
.idx-l{display:flex;align-items:center;gap:9px;min-width:0}
.idx-flag{
  font-size:10px;padding:2px 6px;border-radius:5px;font-weight:600;flex:0 0 auto;
  background:#eef1f5;color:#5b6473;
}
.idx-l .nm{font-size:14px;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.idx-r{display:flex;align-items:baseline;gap:12px;flex:0 0 auto}
.idx-price{font-size:14px;font-variant-numeric:tabular-nums;color:var(--t2);font-weight:500}
.idx-chg{
  font-size:14px;font-weight:700;font-variant-numeric:tabular-nums;
  min-width:66px;text-align:right;border-radius:6px;padding:3px 7px;
}
.up{color:#fff;background:var(--red)}
.down{color:#fff;background:var(--green)}
.flat{color:#fff;background:#9aa0a6}

/* ---------- 导航 tabs ---------- */
.tabs{
  display:flex;gap:7px;overflow-x:auto;padding:14px 16px 4px;
  scrollbar-width:none;-ms-overflow-style:none;
}
.tabs::-webkit-scrollbar{display:none}
.tab{
  flex:0 0 auto;padding:7px 14px;border-radius:18px;background:#fff;
  border:1px solid #e4e7eb;font-size:13px;color:var(--t2);font-weight:500;transition:.18s;
}
.tab.on{background:var(--t1);color:#fff;border-color:var(--t1);font-weight:600}

/* ---------- 基金列表 ---------- */
.fund-card{
  background:var(--card);border-radius:14px;box-shadow:var(--shadow);
  overflow:hidden;margin-bottom:11px;
}
.fund-row{
  display:flex;align-items:center;gap:11px;padding:13px 15px;position:relative;
}
.fund-row + .fund-row::before{
  content:"";position:absolute;left:15px;right:15px;top:0;height:1px;background:var(--line);
}
.fund-l{flex:1;min-width:0}
.fund-nm{
  font-size:14px;font-weight:600;line-height:1.35;
  display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;
}
.fund-meta{display:flex;align-items:center;gap:7px;margin-top:5px;flex-wrap:wrap}
.fund-code{
  font-size:11px;color:var(--t3);font-variant-numeric:tabular-nums;
  background:#f3f4f6;padding:1.5px 6px;border-radius:4px;
}
.fund-nav{font-size:12px;color:var(--t2);font-variant-numeric:tabular-nums}
.fund-nav b{color:var(--t1);font-weight:600;font-size:13px}
.fund-r{flex:0 0 auto;text-align:right;min-width:74px}
.fund-chg{
  font-size:16px;font-weight:700;font-variant-numeric:tabular-nums;letter-spacing:-.3px;
}
.c-up{color:var(--red)}
.c-down{color:var(--green)}
.c-flat{color:#9aa0a6}
.fund-date{font-size:11px;color:var(--t3);margin-top:3px;font-variant-numeric:tabular-nums}

/* 空状态 */
.empty{text-align:center;color:var(--t3);font-size:13px;padding:36px 0}

/* ---------- 底部 ---------- */
.foot{
  text-align:center;padding:22px 20px 8px;color:var(--t3);font-size:11px;line-height:1.7;
}
.foot .disc{
  background:#f0f1f3;border-radius:10px;padding:11px 13px;color:#868b94;
  text-align:left;margin-bottom:12px;font-size:11px;line-height:1.65;
}

/* ---------- 固定底栏 ---------- */
.bar{
  position:fixed;left:0;right:0;bottom:0;z-index:20;
  background:rgba(255,255,255,.94);backdrop-filter:blur(14px);
  border-top:1px solid var(--line);
  padding:10px 16px calc(10px + env(safe-area-inset-bottom));
  display:flex;gap:10px;max-width:600px;margin:0 auto;
}
.btn{
  flex:1;text-align:center;padding:11px 0;border-radius:11px;font-size:14px;
  font-weight:600;border:none;transition:.18s;
}
.btn-main{background:var(--red);color:#fff}
.btn-main:active{background:#b71c1c;transform:scale(.98)}
.btn-ghost{background:#f0f1f3;color:var(--t1);flex:0 0 46px}
.btn-ghost:active{background:#e4e6e9}

/* 滚动条美化 */
.hide{display:none}
</style>
</head>
<body>
<div class="wrap">

  <!-- ============ 顶部 ============ -->
  <div class="hero">
    <div class="hero-top">
      <div class="ht-left">
        <h1>QDII 早报</h1>
        <div class="sub">__REPORT_DATE__ 星期__WEEKDAY__ · 每早 9:00 更新</div>
      </div>
      <div class="badge">净值日 __NAV_DATE_SHORT__</div>
    </div>
    <div class="overview">
      <div class="ov-cell">
        <div class="ov-num">__TOTAL__</div>
        <div class="ov-lbl">覆盖基金</div>
      </div>
      <div class="ov-cell">
        <div class="ov-num" style="color:#ffcdd2">__UP__</div>
        <div class="ov-lbl">上涨</div>
      </div>
      <div class="ov-cell">
        <div class="ov-num" style="color:#b9f6ca">__DOWN__</div>
        <div class="ov-lbl">下跌</div>
      </div>
      <div class="ov-cell">
        <div class="ov-num">__AVG__%</div>
        <div class="ov-lbl">平均涨跌</div>
      </div>
    </div>
  </div>

  <!-- ============ 净值口径提示 ============ -->
  <div class="notice">
    <div class="ico">ⓘ</div>
    <div class="txt">
      场外 QDII 净值按 <b>T+2</b> 披露，本期为 <b>__NAV_DATE__</b> 净值（非实时）。
      下方指数为<b>前夜收盘</b>行情，可用于预判下一期净值方向。
    </div>
  </div>

  <!-- ============ 海外指数看板 ============ -->
  <div class="sec">
    <div class="sec-hd">
      <h2>前夜海外市场</h2>
      <span class="hint">__IDX_TIME__</span>
    </div>
    <div class="idx-card" id="idxCard"></div>
  </div>

  <!-- ============ 基金净值 ============ -->
  <div class="sec">
    <div class="sec-hd">
      <h2>基金净值</h2>
      <span class="hint">点击分组筛选</span>
    </div>
  </div>
  <div class="tabs" id="tabs"></div>
  <div class="sec" id="fundList" style="margin-top:9px"></div>

  <!-- ============ 页脚 ============ -->
  <div class="foot">
    <div class="disc">
      <b>风险提示</b>：本页数据来源于天天基金、新浪财经等公开渠道，仅供信息参考，
      不构成任何投资建议。基金过往业绩不代表未来表现，投资需谨慎。
      数据以基金公司官方披露为准。
    </div>
    <div>数据更新于 __GEN_TIME__</div>
    <div>QDII Morning Report · 自动生成</div>
  </div>
</div>

<!-- ============ 底栏 ============ -->
<div class="bar">
  <button class="btn btn-ghost" onclick="location.reload()" title="刷新">↻</button>
  <button class="btn btn-main" onclick="shareIt()">分享今日早报</button>
</div>

<script>
/* ================= 数据（内联，零请求） ================= */
const SNAP = __DATA__;

/* ================= 指数看板 ================= */
(function renderIdx(){
  const box = document.getElementById('idxCard');
  if(!SNAP.indexes || !SNAP.indexes.length){
    box.innerHTML = '<div class="empty">指数数据暂不可用</div>';
    return;
  }
  box.innerHTML = SNAP.indexes.map(i=>{
    const cls = i.chg_pct > 0 ? 'up' : (i.chg_pct < 0 ? 'down' : 'flat');
    return `<div class="idx-row">
      <div class="idx-l">
        <span class="idx-flag">${i.region}</span>
        <span class="nm">${i.name}</span>
      </div>
      <div class="idx-r">
        <span class="idx-price">${fmtNum(i.price)}</span>
        <span class="idx-chg ${cls}">${fmtPct(i.chg_pct)}</span>
      </div>
    </div>`;
  }).join('');
})();

/* ================= 分组 tabs + 基金列表 ================= */
let curGroup = 'ALL';
(function renderTabs(){
  const groups = SNAP.groups || [];
  const tabs = document.getElementById('tabs');
  tabs.innerHTML = `<div class="tab on" data-g="ALL">全部 <span style="opacity:.6">${SNAP.stats.total}</span></div>` +
    groups.map(g=>`<div class="tab" data-g="${g.name}">${g.name} <span style="opacity:.6">${g.funds.length}</span></div>`).join('');
  tabs.querySelectorAll('.tab').forEach(t=>{
    t.onclick = ()=>{
      tabs.querySelectorAll('.tab').forEach(x=>x.classList.remove('on'));
      t.classList.add('on');
      curGroup = t.dataset.g;
      renderFunds();
    };
  });
})();

function renderFunds(){
  const box = document.getElementById('fundList');
  let groups = SNAP.groups || [];
  if(curGroup !== 'ALL') groups = groups.filter(g=>g.name===curGroup);

  let html = '';
  groups.forEach(g=>{
    html += `<div class="fund-card">`;
    g.funds.forEach(f=>{
      const cls = f.chg > 0 ? 'c-up' : (f.chg < 0 ? 'c-down' : 'c-flat');
      html += `<div class="fund-row">
        <div class="fund-l">
          <div class="fund-nm">${esc(f.name)}</div>
          <div class="fund-meta">
            <span class="fund-code">${f.code}</span>
            <span class="fund-nav">净值 <b>${f.nav!=null?f.nav.toFixed(4):'--'}</b></span>
          </div>
        </div>
        <div class="fund-r">
          <div class="fund-chg ${cls}">${fmtPct(f.chg)}</div>
          <div class="fund-date">${f.nav_date||'--'}</div>
        </div>
      </div>`;
    });
    html += `</div>`;
  });
  box.innerHTML = html || '<div class="empty">暂无数据</div>';
}
renderFunds();

/* ================= 工具 ================= */
function fmtNum(v){
  if(v==null) return '--';
  return v.toLocaleString('zh-CN',{minimumFractionDigits:2,maximumFractionDigits:2});
}
function fmtPct(v){
  if(v==null) return '--';
  const s = v>0?'+':'';
  return s + v.toFixed(2) + '%';
}
function esc(s){
  return String(s||'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
}

/* ================= 分享 ================= */
function shareIt(){
  const s = SNAP.stats;
  const lines = [
    `【QDII 早报 · ${SNAP.report_date} 星期${SNAP.weekday}】`,
    `净值日：${SNAP.latest_nav_date}`,
    `共 ${s.total} 只 | 涨 ${s.up} 跌 ${s.down} | 均值 ${s.avg_chg>0?'+':''}${s.avg_chg}%`,
    '',
    '前夜海外：',
    ...SNAP.indexes.slice(0,4).map(i=>`  ${i.name} ${i.chg_pct>0?'+':''}${i.chg_pct.toFixed(2)}%`),
    '',
    '涨幅前列：',
    ...SNAP.all_funds.filter(f=>f.chg>0).slice(0,3).map(f=>`  ${f.name.slice(0,18)} +${f.chg.toFixed(2)}%`),
    '',
    '仅供参考，不构成投资建议'
  ];
  const text = lines.join('\n');
  if(navigator.share){
    navigator.share({title:'QDII 早报', text}).catch(()=>{});
  }else{
    navigator.clipboard.writeText(text).then(()=>{
      toast('早报内容已复制');
    }).catch(()=>{
      prompt('复制以下内容分享：', text);
    });
  }
}
function toast(msg){
  const d=document.createElement('div');
  d.textContent=msg;
  d.style.cssText='position:fixed;left:50%;top:50%;transform:translate(-50%,-50%);background:rgba(0,0,0,.8);color:#fff;padding:11px 20px;border-radius:9px;font-size:14px;z-index:99;';
  document.body.appendChild(d);
  setTimeout(()=>d.remove(),1600);
}
</script>
</body>
</html>
"""


def render(snapshot):
    st = snapshot["stats"]
    idx_times = [i.get("time") for i in snapshot.get("indexes", []) if i.get("time")]
    idx_time = "截至 " + (idx_times[0] if idx_times else "—")

    nav_date = snapshot.get("latest_nav_date") or "—"
    # 徽章用短日期（09-30），避免窄屏溢出
    nav_date_short = nav_date[5:] if len(nav_date) == 10 else nav_date

    html = TEMPLATE
    html = html.replace("__DATA__", json.dumps(snapshot, ensure_ascii=False))
    html = html.replace("__REPORT_DATE__", snapshot["report_date"])
    html = html.replace("__WEEKDAY__", snapshot["weekday"])
    html = html.replace("__NAV_DATE__", nav_date)
    html = html.replace("__NAV_DATE_SHORT__", nav_date_short)
    html = html.replace("__TOTAL__", str(st["total"]))
    html = html.replace("__UP__", str(st["up"]))
    html = html.replace("__DOWN__", str(st["down"]))
    html = html.replace("__AVG__", ("+" if st["avg_chg"] > 0 else "") + str(st["avg_chg"]))
    html = html.replace("__IDX_TIME__", idx_time)
    html = html.replace("__GEN_TIME__", snapshot["generated_at"])
    # PWA：内联清单与图标（安卓 Chrome 添加到主屏幕后独立运行）
    try:
        html = html.replace("__MANIFEST__", make_manifest())
        html = html.replace("__ICON192__", make_icon_b64(192))
    except Exception as e:
        # 图标生成失败不影响主页面
        html = html.replace("__MANIFEST__", "data:application/manifest+json,{}")
        html = html.replace("__ICON192__", "")
        print(f"  [警告] PWA 图标生成失败: {e}")
    return html


def main():
    snap_path = os.path.join(BASE_DIR, "data", "snapshot.json")
    with open(snap_path, encoding="utf-8") as f:
        snapshot = json.load(f)

    os.makedirs(OUT_DIR, exist_ok=True)
    html = render(snapshot)

    out = os.path.join(OUT_DIR, "index.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"页面已生成 -> {out}  ({len(html)} 字符)")

    # 同时归档一份带日期的快照，便于回溯
    arc = os.path.join(DATA_DIR_ARCHIVE, f"{snapshot['report_date']}.html")
    os.makedirs(DATA_DIR_ARCHIVE, exist_ok=True)
    with open(arc, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"归档 -> {arc}")
    return out


DATA_DIR_ARCHIVE = os.path.join(BASE_DIR, "data", "archive")

if __name__ == "__&#8203;main__":
    main()
