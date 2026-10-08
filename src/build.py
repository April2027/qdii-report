# -*- coding: utf-8 -*-
"""
QDII 早报 —— 页面生成器（v2）

产出：
  index.html            首页（数据内联，零请求秒开）
  f/{code}.html         每只基金的独立详情页（近1月/半年/1年 + 净值走势图）

设计要点：
  · 首页只内联「列表所需」的轻量字段，详情页数据各存一份，避免首页体积膨胀
  · 首页点基金 -> f/{code}.html，详情页里 A/C 可一键互跳
  · 详情页走势图用纯 SVG 手绘，无第三方依赖
  · PWA 清单内联（data URI），安卓 Chrome 可「添加到主屏幕」
"""
import base64
import io
import json
import os
import urllib.parse
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
OUT_DIR = os.environ.get("QDII_OUT") or os.path.join(PROJECT_ROOT, "site")


# ============================================================ 图标 / PWA
def make_icon_b64(size):
    """生成应用图标（红底 Q 字）并返回 data URI。"""
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new("RGB", (size, size), "#c62828")
    d = ImageDraw.Draw(img)
    for y in range(size):
        ratio = y / size
        r = int(198 - ratio * 70)
        g = int(40 - ratio * 22)
        b = int(40 - ratio * 22)
        d.line([(0, y), (size, y)], fill=(max(r, 95), max(g, 18), max(b, 18)))
    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(size * 0.62))
    except Exception:
        font = ImageFont.load_default()
    box = d.textbbox((0, 0), "Q", font=font)
    w, h = box[2] - box[0], box[3] - box[1]
    d.text(((size - w) / 2 - box[0], (size - h) / 2 - box[1] - size * 0.02),
           "Q", font=font, fill="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def make_manifest():
    """内联 PWA 清单。"""
    manifest = {
        "name": "QDII 基金净值早报",
        "short_name": "QDII早报",
        "description": "每天早9点发布场外QDII基金最新净值与涨跌",
        "start_url": ".",
        "display": "standalone",
        "background_color": "#f4f5f7",
        "theme_color": "#c62828",
        "icons": [
            {"src": make_icon_b64(192), "sizes": "192x192", "type": "image/png"},
            {"src": make_icon_b64(512), "sizes": "512x512", "type": "image/png",
             "purpose": "any maskable"},
        ],
    }
    return "data:application/manifest+json," + urllib.parse.quote(
        json.dumps(manifest, ensure_ascii=False))


# ============================================================ 公共 CSS
COMMON_CSS = r"""
:root{
  --red:#d93025; --green:#0f9d58; --bg:#f4f5f7; --card:#fff;
  --t1:#1a1a1a; --t2:#6b7280; --t3:#9ca3af; --line:#eceef1;
  --shadow:0 1px 2px rgba(16,24,40,.05),0 4px 12px rgba(16,24,40,.05);
}
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
body{
  font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
  background:var(--bg); color:var(--t1); font-size:15px; line-height:1.5;
  -webkit-font-smoothing:antialiased; overflow-x:hidden;
}
.wrap{max-width:600px;margin:0 auto}
.up{color:#fff;background:var(--red)}
.down{color:#fff;background:var(--green)}
.flat{color:#fff;background:#9aa0a6}
.c-up{color:var(--red)}
.c-down{color:var(--green)}
.c-flat{color:#9aa0a6}
.hide{display:none}
.empty{text-align:center;color:var(--t3);font-size:13px;padding:36px 0}
"""


# ============================================================ 首页模板
INDEX_TEMPLATE = r"""<!DOCTYPE html>
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
__COMMON_CSS__
body{padding-bottom:calc(64px + env(safe-area-inset-bottom))}

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

/* ---------- 净值口径提示 ---------- */
.notice{
  margin:14px 16px 0; background:#fff8e6; border:1px solid #ffe2a8;
  border-radius:12px; padding:11px 13px; display:flex; gap:9px; align-items:flex-start;
}
.notice .ico{flex:0 0 16px;color:#e8a33d;font-size:14px;line-height:1.35}
.notice .txt{font-size:12.5px;color:#8a6321;line-height:1.55}
.notice b{color:#c47f13}

/* ---------- 通用区块 ---------- */
.sec{padding:0 16px;margin-top:18px}
.sec-hd{display:flex;align-items:baseline;justify-content:space-between;margin-bottom:9px;padding:0 2px;gap:8px}
.sec-hd h2{font-size:15.5px;font-weight:700;letter-spacing:.2px}
.sec-hd .hint{font-size:11.5px;color:var(--t3);white-space:nowrap}

/* ---------- 指数看板 ---------- */
.idx-card{background:var(--card);border-radius:14px;box-shadow:var(--shadow);overflow:hidden}
.idx-row{display:flex;align-items:center;justify-content:space-between;padding:12px 15px;position:relative}
.idx-row + .idx-row::before{
  content:"";position:absolute;left:15px;right:15px;top:0;height:1px;background:var(--line);
}
.idx-l{display:flex;align-items:center;gap:9px;min-width:0}
.idx-flag{font-size:10px;padding:2px 6px;border-radius:5px;font-weight:600;flex:0 0 auto;background:#eef1f5;color:#5b6473}
.idx-l .nm{font-size:14px;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.idx-r{display:flex;align-items:baseline;gap:12px;flex:0 0 auto}
.idx-price{font-size:14px;font-variant-numeric:tabular-nums;color:var(--t2);font-weight:500}
.idx-chg{font-size:14px;font-weight:700;font-variant-numeric:tabular-nums;min-width:66px;text-align:right;border-radius:6px;padding:3px 7px}

/* ---------- 顶层 tabs ---------- */
.tabs{display:flex;gap:7px;overflow-x:auto;padding:14px 16px 4px;scrollbar-width:none;-ms-overflow-style:none}
.tabs::-webkit-scrollbar{display:none}
.tab{flex:0 0 auto;padding:7px 14px;border-radius:18px;background:#fff;border:1px solid #e4e7eb;font-size:13px;color:var(--t2);font-weight:500;transition:.18s;cursor:pointer}
.tab.on{background:var(--t1);color:#fff;border-color:var(--t1);font-weight:600}

/* ---------- 板块头 ---------- */
.sec-title{
  display:flex;align-items:center;gap:9px;padding:6px 2px 10px;margin-top:6px;
}
.sec-title .bar{width:3px;height:15px;border-radius:2px;background:var(--red);flex:0 0 auto}
.sec-title h3{font-size:15px;font-weight:700}
.sec-title .idx-pill{
  font-size:11.5px;padding:2.5px 8px;border-radius:11px;font-weight:700;
  font-variant-numeric:tabular-nums;margin-left:2px;
}
.sec-title .cnt{font-size:11.5px;color:var(--t3);margin-left:auto;white-space:nowrap}

/* ---------- 基金卡 ---------- */
.fund-card{background:var(--card);border-radius:14px;box-shadow:var(--shadow);overflow:hidden;margin-bottom:11px}
.fam{position:relative}
.fam + .fam::before{content:"";position:absolute;left:15px;right:15px;top:0;height:1px;background:var(--line)}
.fund-row{display:flex;align-items:center;gap:11px;padding:13px 15px;cursor:pointer;transition:background .15s}
.fund-row:active{background:#fafbfc}
.fund-l{flex:1;min-width:0}
.fund-nm{font-size:14px;font-weight:600;line-height:1.35;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.fund-meta{display:flex;align-items:center;gap:7px;margin-top:5px;flex-wrap:wrap}
.fund-code{font-size:11px;color:var(--t3);font-variant-numeric:tabular-nums;background:#f3f4f6;padding:1.5px 6px;border-radius:4px}
.fund-nav{font-size:12px;color:var(--t2);font-variant-numeric:tabular-nums}
.fund-nav b{color:var(--t1);font-weight:600;font-size:13px}
.tag{font-size:10px;padding:1.5px 6px;border-radius:4px;font-weight:600}
.tag-a{background:#e8f0fe;color:#1a73e8}
.tag-c{background:#fce8e6;color:#c5221f}
.tag-limit{background:#fff3e0;color:#e07b00}
.tag-etf{background:#f1f3f4;color:#5f6368}
.fund-r{flex:0 0 auto;text-align:right;min-width:74px}
.fund-chg{font-size:16px;font-weight:700;font-variant-numeric:tabular-nums;letter-spacing:-.3px}
.fund-date{font-size:11px;color:var(--t3);margin-top:3px;font-variant-numeric:tabular-nums}
.arrow{flex:0 0 auto;color:#c9ced6;font-size:15px;margin-left:-3px}

/* C 份额次级行（同系列内嵌） */
.sub-row{display:flex;align-items:center;gap:9px;padding:9px 15px 10px 15px;background:#fafbfc;cursor:pointer;
  border-top:1px dashed #eceef1}
.sub-row:active{background:#f3f4f6}
.sub-share{font-size:10.5px;font-weight:700;color:#c5221f;background:#fce8e6;padding:2px 7px;border-radius:5px;flex:0 0 auto}
.sub-nm{font-size:12.5px;color:#5b6473;flex:1;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.sub-code{font-size:10.5px;color:var(--t3);font-variant-numeric:tabular-nums}
.sub-chg{font-size:13.5px;font-weight:700;font-variant-numeric:tabular-nums;flex:0 0 auto;min-width:62px;text-align:right}

/* ---------- 折叠（暂停申购） ---------- */
.fold{margin-top:4px;margin-bottom:12px}
.fold-hd{
  display:flex;align-items:center;gap:8px;padding:11px 15px;background:#fff;border-radius:12px;
  box-shadow:var(--shadow);cursor:pointer;font-size:13px;color:var(--t2);font-weight:500;
}
.fold-hd:active{background:#fafbfc}
.fold-hd .fbar{width:3px;height:13px;border-radius:2px;background:#c9ced6;flex:0 0 auto}
.fold-hd .fcnt{margin-left:auto;font-size:11.5px;color:var(--t3)}
.fold-hd .chev{color:#c9ced6;font-size:12px;transition:transform .2s}
.fold.open .fold-hd .chev{transform:rotate(90deg)}
.fold-body{margin-top:9px}
.fold:not(.open) .fold-body{display:none}
.fold-note{font-size:11px;color:var(--t3);padding:0 3px 8px;line-height:1.5}

/* ---------- 其他板块分组标题 ---------- */
.grp-title{font-size:12.5px;color:var(--t2);font-weight:600;padding:8px 3px 7px;letter-spacing:.2px}
.grp-title span{color:var(--t3);font-weight:400;margin-left:5px}

/* ---------- 页脚 + 底栏 ---------- */
.foot{text-align:center;padding:22px 20px 8px;color:var(--t3);font-size:11px;line-height:1.7}
.foot .disc{background:#f0f1f3;border-radius:10px;padding:11px 13px;color:#868b94;text-align:left;margin-bottom:12px;font-size:11px;line-height:1.65}
.bar{
  position:fixed;left:0;right:0;bottom:0;z-index:20;
  background:rgba(255,255,255,.94);backdrop-filter:blur(14px);
  border-top:1px solid var(--line);
  padding:10px 16px calc(10px + env(safe-area-inset-bottom));
  display:flex;gap:10px;max-width:600px;margin:0 auto;
}
.btn{flex:1;text-align:center;padding:11px 0;border-radius:11px;font-size:14px;font-weight:600;border:none;transition:.18s;cursor:pointer}
.btn-main{background:var(--red);color:#fff}
.btn-main:active{background:#b71c1c;transform:scale(.98)}
.btn-ghost{background:#f0f1f3;color:var(--t1);flex:0 0 46px}
.btn-ghost:active{background:#e4e6e9}
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
      <div class="ov-cell"><div class="ov-num">__TOTAL__</div><div class="ov-lbl">覆盖基金</div></div>
      <div class="ov-cell"><div class="ov-num" style="color:#ffcdd2">__UP__</div><div class="ov-lbl">上涨</div></div>
      <div class="ov-cell"><div class="ov-num" style="color:#b9f6ca">__DOWN__</div><div class="ov-lbl">下跌</div></div>
      <div class="ov-cell"><div class="ov-num">__AVG__%</div><div class="ov-lbl">平均涨跌</div></div>
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
    <div class="sec-hd"><h2>前夜海外市场</h2><span class="hint">__IDX_TIME__</span></div>
    <div class="idx-card" id="idxCard"></div>
  </div>

  <!-- ============ 顶层筛选 ============ -->
  <div class="sec" style="margin-top:18px">
    <div class="sec-hd"><h2>基金净值</h2><span class="hint">点基金看详情 ›</span></div>
  </div>
  <div class="tabs" id="tabs"></div>
  <div class="sec" id="content" style="margin-top:9px"></div>

  <!-- ============ 页脚 ============ -->
  <div class="foot">
    <div class="disc">
      <b>风险提示</b>：本页数据来源于天天基金、新浪财经等公开渠道，仅供信息参考，
      不构成任何投资建议。基金过往业绩不代表未来表现，投资需谨慎。数据以基金公司官方披露为准。
    </div>
    <div>数据更新于 __GEN_TIME__</div>
    <div>QDII Morning Report · 自动生成</div>
  </div>
</div>

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
  const arr = SNAP.indexes || [];
  if(!arr.length){ box.innerHTML = '<div class="empty">指数数据暂不可用</div>'; return; }
  box.innerHTML = arr.map(i=>{
    const cls = i.chg_pct > 0 ? 'up' : (i.chg_pct < 0 ? 'down' : 'flat');
    return `<div class="idx-row">
      <div class="idx-l"><span class="idx-flag">${i.region}</span><span class="nm">${esc(i.name)}</span></div>
      <div class="idx-r">
        <span class="idx-price">${fmtNum(i.price)}</span>
        <span class="idx-chg ${cls}">${fmtPct(i.chg_pct)}</span>
      </div>
    </div>`;
  }).join('');
})();

/* ================= 顶层 tabs ================= */
let cur = 'ALL';
const SECS = [].concat(SNAP.sections||[], [SNAP.other]).filter(Boolean);
(function renderTabs(){
  const total = SNAP.stats.total;
  const tabs = document.getElementById('tabs');
  const items = [{k:'ALL', n:'全部', c:total}];
  (SNAP.sections||[]).forEach(s=>items.push({k:s.key, n:s.name, c:s.count_funds}));
  if(SNAP.other && SNAP.other.count_funds) items.push({k:'OTHERS', n:'其他热门', c:SNAP.other.count_funds});
  tabs.innerHTML = items.map((it,i)=>
    `<div class="tab${i===0?' on':''}" data-k="${it.k}">${esc(it.n)} <span style="opacity:.6">${it.c}</span></div>`
  ).join('');
  tabs.querySelectorAll('.tab').forEach(t=>{
    t.onclick = ()=>{
      tabs.querySelectorAll('.tab').forEach(x=>x.classList.remove('on'));
      t.classList.add('on'); cur = t.dataset.k; renderContent();
    };
  });
})();

/* ================= 渲染内容 ================= */
function renderContent(){
  const box = document.getElementById('content');
  let html = '';
  const secs = (SNAP.sections||[]).concat([SNAP.other]).filter(Boolean)
    .filter(s => cur==='ALL' || s.key===cur);

  if(cur === 'ALL'){
    html += '<div class="grp-title" style="padding-top:2px">点击任意基金查看 近1月 / 近半年 / 近1年 涨跌 ›</div>';
  }

  secs.forEach(s=>{
    if(s.key === 'OTHERS'){ html += renderOthers(s); return; }
    html += renderSection(s);
  });
  box.innerHTML = html || '<div class="empty">暂无数据</div>';

  box.querySelectorAll('[data-fold]').forEach(hd=>{
    hd.onclick = ()=>{
      const f = hd.closest('.fold');
      f.classList.toggle('open');
      f.querySelector('.fcnt').textContent = f.classList.contains('open')
        ? '收起 ▾' : ('展开 ' + f.dataset.n + ' 只 ›');
    };
  });
  box.querySelectorAll('[data-href]').forEach(el=>{
    el.onclick = ()=> location.href = el.dataset.href;
  });
}

function idxPill(idx){
  if(!idx) return '';
  const cls = idx.chg_pct > 0 ? 'up' : (idx.chg_pct < 0 ? 'down' : 'flat');
  return `<span class="idx-pill ${cls}">${esc(idx.name)} ${fmtPct(idx.chg_pct)}</span>`;
}

function renderSection(s){
  const held = (s.hold||[]).length;
  return `
  <div class="sec-title">
    <span class="bar"></span><h3>${esc(s.name)}</h3>
    ${idxPill(s.index)}
    <span class="cnt">${s.count_families} 只 · ${s.count_funds} 份额</span>
  </div>
  ${s.live && s.live.length ? `<div class="fund-card">${s.live.map(renderFam).join('')}</div>`
    : '<div class="empty" style="padding:14px 0;font-size:12.5px">该板块暂无在售基金</div>'}
  ${held ? `
    <div class="fold" data-n="${held}">
      <div class="fold-hd" data-fold>
        <span class="fbar"></span>
        <span>暂停申购 ${held} 只（仍可赎回）</span>
        <span class="fcnt">展开 ${held} 只 ›</span>
        <span class="chev">›</span>
      </div>
      <div class="fold-body">
        <div class="fold-note">以下基金当前暂停申购，通常因外汇额度受限；已持有的份额仍可正常赎回，后续可能恢复申购。</div>
        <div class="fund-card">${s.hold.map(renderFam).join('')}</div>
      </div>
    </div>` : ''}
  `;
}

function renderOthers(s){
  if(!s.groups || !s.groups.length) return '';
  let h = `<div class="sec-title"><span class="bar"></span><h3>其他热门 QDII</h3>
    <span class="cnt">${s.count_funds} 只</span></div>`;
  s.groups.forEach(g=>{
    h += `<div class="grp-title">${esc(g.name)}<span>${g.funds.length}</span></div>`;
    h += `<div class="fund-card">${g.funds.map(f=>renderRow(f,false)).join('')}</div>`;
  });
  return h;
}

/* 一个「系列」= A 主行 + C 次级行 */
function renderFam(f){
  if(!f.primary) return '';
  const ms = f.members || [];
  const a = ms.find(x=>x.share==='A') || ms[0];
  const rest = ms.filter(x=>x !== a);
  let h = renderRow(a, true);
  rest.forEach(c=>{ h += renderSub(c); });
  return `<div class="fam">${h}</div>`;
}

function renderRow(f, inFam){
  const cls = f.chg > 0 ? 'c-up' : (f.chg < 0 ? 'c-down' : 'c-flat');
  const limit = (f.sgzt && f.sgzt !== '开放申购') ? `<span class="tag tag-limit">${esc(f.sgzt)}</span>` : '';
  const note  = f.note ? `<span class="tag tag-etf">${esc(f.note)}</span>` : '';
  return `<div class="fund-row" data-href="f/${f.code}.html">
    <div class="fund-l">
      <div class="fund-nm">${esc(f.name)}</div>
      <div class="fund-meta">
        <span class="tag tag-a">${esc(f.share)}</span>
        <span class="fund-code">${f.code}</span>
        <span class="fund-nav">净值 <b>${f.nav!=null?f.nav.toFixed(4):'--'}</b></span>
        ${limit}${note}
      </div>
    </div>
    <div class="fund-r">
      <div class="fund-chg ${cls}">${fmtPct(f.chg)}</div>
      <div class="fund-date">${f.nav_date||'--'}</div>
    </div>
    <div class="arrow">›</div>
  </div>`;
}

function renderSub(f){
  const cls = f.chg > 0 ? 'c-up' : (f.chg < 0 ? 'c-down' : 'c-flat');
  return `<div class="sub-row" data-href="f/${f.code}.html">
    <span class="sub-share">${esc(f.share)}</span>
    <span class="sub-nm">${esc(f.name)}</span>
    <span class="sub-code">${f.code}</span>
    <span class="sub-chg ${cls}">${fmtPct(f.chg)}</span>
    <span class="arrow" style="font-size:13px">›</span>
  </div>`;
}
renderContent();

/* ================= 工具 ================= */
function fmtNum(v){
  if(v==null) return '--';
  return v.toLocaleString('zh-CN',{minimumFractionDigits:2,maximumFractionDigits:2});
}
function fmtPct(v){
  if(v==null) return '--';
  return (v>0?'+':'') + v.toFixed(2) + '%';
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
    '纳指100 涨幅前列：',
    ...((SNAP.sections[0] && SNAP.sections[0].live) || []).slice(0,3)
        .map(f=>`  ${f.family.slice(0,16)} ${fmtPct(f.chg)}`),
    '',
    '仅供参考，不构成投资建议'
  ];
  const text = lines.join('\n');
  if(navigator.share){ navigator.share({title:'QDII 早报', text}).catch(()=>{}); }
  else if(navigator.clipboard){
    navigator.clipboard.writeText(text).then(()=>toast('早报内容已复制')).catch(()=>prompt('复制以下内容分享：', text));
  } else { prompt('复制以下内容分享：', text); }
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


# ============================================================ 详情页模板
DETAIL_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<meta name="theme-color" content="#c62828">
<meta name="format-detection" content="telephone=no">
<meta name="mobile-web-app-capable" content="yes">
<title>__NAME__ · QDII 早报</title>
<style>
__COMMON_CSS__
body{padding-bottom:calc(24px + env(safe-area-inset-bottom))}

/* ---------- 顶部 ---------- */
.top{
  background:linear-gradient(160deg,#c62828 0%,#8e1c1c 60%,#5f1212 100%);
  color:#fff; padding:calc(14px + env(safe-area-inset-top)) 16px 20px;
  border-radius:0 0 22px 22px; position:relative; overflow:hidden;
}
.top::after{content:"";position:absolute;right:-50px;top:-60px;width:170px;height:170px;
  background:radial-gradient(circle,rgba(255,255,255,.12),transparent 70%);border-radius:50%}
.tnav{display:flex;align-items:center;gap:8px;position:relative;z-index:1;margin-bottom:14px}
.tnav a{color:#fff;text-decoration:none;font-size:13.5px;opacity:.9;display:flex;align-items:center;gap:3px}
.tnav .sp{margin-left:auto}
.tnav .sp a{background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.26);
  padding:4px 11px;border-radius:16px;font-size:12px}
.tname{font-size:18.5px;font-weight:700;line-height:1.35;position:relative;z-index:1}
.tmeta{display:flex;align-items:center;gap:7px;flex-wrap:wrap;margin-top:9px;position:relative;z-index:1}
.tmeta .pill{font-size:11px;padding:2.5px 8px;border-radius:11px;background:rgba(255,255,255,.17);
  border:1px solid rgba(255,255,255,.22)}
.tmeta .pill.warn{background:rgba(255,214,102,.24);border-color:rgba(255,214,102,.45);color:#ffe9a8}

.navbig{display:flex;align-items:flex-end;gap:12px;margin-top:16px;position:relative;z-index:1}
.navbig .v{font-size:33px;font-weight:700;font-variant-numeric:tabular-nums;letter-spacing:-1px;line-height:1}
.navbig .c{font-size:15px;font-weight:700;padding:4px 10px;border-radius:8px;font-variant-numeric:tabular-nums}
.navbig-c{font-size:11.5px;opacity:.8;margin-top:8px;position:relative;z-index:1}

/* ---------- 阶段涨幅 ---------- */
.sec{padding:0 16px;margin-top:16px}
.sec-hd{display:flex;align-items:baseline;justify-content:space-between;margin-bottom:9px;padding:0 2px}
.sec-hd h2{font-size:15px;font-weight:700}
.sec-hd .hint{font-size:11.5px;color:var(--t3)}
.perf{display:grid;grid-template-columns:repeat(3,1fr);gap:9px}
.perf-cell{background:#fff;border-radius:13px;box-shadow:var(--shadow);padding:13px 8px;text-align:center}
.perf-lbl{font-size:11.5px;color:var(--t2)}
.perf-val{font-size:17.5px;font-weight:700;font-variant-numeric:tabular-nums;margin-top:6px;letter-spacing:-.4px}
.perf-sub{font-size:10.5px;color:var(--t3);margin-top:4px}

/* ---------- 走势图 ---------- */
.chart-card{background:#fff;border-radius:14px;box-shadow:var(--shadow);padding:14px 12px 8px}
.chart-tabs{display:flex;gap:6px;padding:0 2px 11px}
.ctab{flex:1;text-align:center;padding:6px 0;border-radius:8px;font-size:12.5px;color:var(--t2);
  background:#f3f4f6;font-weight:600;cursor:pointer;transition:.15s}
.ctab.on{background:var(--t1);color:#fff}
svg{display:block;width:100%;height:auto}
.chart-foot{display:flex;justify-content:space-between;font-size:11px;color:var(--t3);padding:7px 3px 4px;
  font-variant-numeric:tabular-nums}

/* ---------- 关键指标 ---------- */
.kv{background:#fff;border-radius:14px;box-shadow:var(--shadow);overflow:hidden}
.kv-row{display:flex;justify-content:space-between;align-items:center;padding:12px 15px;position:relative;font-size:13.5px}
.kv-row + .kv-row::before{content:"";position:absolute;left:15px;right:15px;top:0;height:1px;background:var(--line)}
.kv-k{color:var(--t2)}
.kv-v{font-weight:600;font-variant-numeric:tabular-nums;text-align:right}

/* ---------- 同系列 A/C 互跳 ---------- */
.sibs{display:flex;gap:9px}
.sib{flex:1;background:#fff;border-radius:13px;box-shadow:var(--shadow);padding:12px 13px;text-decoration:none;color:inherit;display:block}
.sib.on{border:1.5px solid var(--red);box-shadow:0 0 0 2px rgba(217,48,37,.08),var(--shadow)}
.sib .sh{font-size:11px;font-weight:700;color:#c5221f;background:#fce8e6;padding:1.5px 7px;border-radius:5px;display:inline-block}
.sib .sn{font-size:12px;color:var(--t2);margin-top:7px;line-height:1.4;height:34px;overflow:hidden;
  display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical}
.sib .sv{font-size:15px;font-weight:700;font-variant-numeric:tabular-nums;margin-top:7px}
.sib .sc{font-size:11px;color:var(--t3);margin-top:3px;font-variant-numeric:tabular-nums}

.foot{text-align:center;padding:20px 20px 6px;color:var(--t3);font-size:11px;line-height:1.7}
.foot .disc{background:#f0f1f3;border-radius:10px;padding:11px 13px;color:#868b94;text-align:left;margin-bottom:12px;font-size:10.5px;line-height:1.65}
</style>
</head>
<body>
<div class="wrap">
  <div class="top">
    <div class="tnav">
      <a href="../index.html">‹ 返回早报</a>
      <span class="sp"><a href="__SIB_URL__">切换到 __SIB_SHARE__ 份额 ›</a></span>
    </div>
    <div class="tname">__NAME__</div>
    <div class="tmeta">
      <span class="pill">__CODE__</span>
      <span class="pill">__COMPANY__</span>
      <span class="pill">__SHARE__ 份额</span>
      __STATUS_PILL__
    </div>
    <div class="navbig">
      <span class="v">__NAV__</span>
      <span class="c __CHG_CLS__" style="background:__CHG_BG__;color:#fff">__CHG__</span>
    </div>
    <div class="navbig-c">净值日期 __NAV_DATE__ · 场外 QDII 按 T+2 披露</div>
  </div>

  <!-- ============ 阶段涨幅 ============ -->
  <div class="sec">
    <div class="sec-hd"><h2>阶段涨跌幅</h2><span class="hint">截至 __NAV_DATE__</span></div>
    <div class="perf" id="perf"></div>
  </div>

  <!-- ============ 净值走势 ============ -->
  <div class="sec">
    <div class="sec-hd"><h2>净值走势</h2><span class="hint" id="chartHint"></span></div>
    <div class="chart-card">
      <div class="chart-tabs" id="ctabs">
        <div class="ctab" data-r="1m">近1月</div>
        <div class="ctab" data-r="6m">近半年</div>
        <div class="ctab on" data-r="1y">近1年</div>
        <div class="ctab" data-r="all">成立来</div>
      </div>
      <svg id="chart" viewBox="0 0 320 150" preserveAspectRatio="none"></svg>
      <div class="chart-foot"><span id="cfL"></span><span id="cfR"></span></div>
    </div>
  </div>

  <!-- ============ 关键指标 ============ -->
  <div class="sec">
    <div class="sec-hd"><h2>基金概况</h2></div>
    <div class="kv" id="kv"></div>
  </div>

  <!-- ============ 同系列 ============ -->
  <div class="sec" id="sibSec" style="display:none">
    <div class="sec-hd"><h2>同系列份额</h2><span class="hint">A/C 费率不同，可对比</span></div>
    <div class="sibs" id="sibs"></div>
  </div>

  <div class="foot">
    <div class="disc">
      <b>说明</b>：本页数据来源于天天基金公开接口，仅供信息参考，不构成投资建议。
      A/C 份额通常管理费相同、销售服务费不同（A 收申购费、C 收销售服务费），长期持有 A 通常更划算，短期持有 C 通常更划算。
    </div>
    <div>数据更新于 __GEN_TIME__</div>
    <div>QDII Morning Report · 自动生成</div>
  </div>
</div>

<script>
const FUND = __FUND_JSON__;
const ALL  = __ALL_JSON__;   /* 同系列成员（含自身） */
const GEN  = "__GEN_TIME__";

/* ---------- 日涨跌样式 ---------- */
const chgCls = v => v>0 ? 'c-up' : (v<0 ? 'c-down' : 'c-flat');

/* ---------- 阶段涨幅 ---------- */
(function renderPerf(){
  const items = [
    {l:'近1月',  v:FUND.r1m, s:'约21个交易日'},
    {l:'近半年', v:FUND.r6m, s:'约125个交易日'},
    {l:'近1年',  v:FUND.r1y, s:'约250个交易日'},
  ];
  document.getElementById('perf').innerHTML = items.map(it=>
    `<div class="perf-cell">
       <div class="perf-lbl">${it.l}</div>
       <div class="perf-val ${chgCls(it.v)}">${fmtPct(it.v)}</div>
       <div class="perf-sub">${it.s}</div>
     </div>`).join('');
})();

/* ---------- 走势图（纯 SVG） ---------- */
const HIST = FUND.hist || [];
const RANGES = {'1m':21,'6m':125,'1y':250,'all':99999};
let curRange = '1y';

function drawChart(){
  const svg = document.getElementById('chart');
  const n = RANGES[curRange];
  let seq = HIST.length > n ? HIST.slice(HIST.length - n) : HIST.slice();
  if(seq.length < 2){
    svg.innerHTML = '<text x="160" y="78" text-anchor="middle" fill="#9ca3af" font-size="11">暂无足够数据</text>';
    document.getElementById('cfL').textContent = '';
    document.getElementById('cfR').textContent = '';
    document.getElementById('chartHint').textContent = '';
    return;
  }
  const W = 320, H = 150, PL = 4, PR = 4, PT = 12, PB = 12;
  const vals = seq.map(x=>x[1]);
  const min = Math.min(...vals), max = Math.max(...vals);
  const span = (max - min) || 1;
  const px = i => PL + (W - PL - PR) * (i / (seq.length - 1));
  const py = v => PT + (H - PT - PB) * (1 - (v - min) / span);

  const rise = vals[vals.length-1] >= vals[0];
  const line = rise ? '#d93025' : '#0f9d58';
  const pts = seq.map((x,i)=>`${px(i).toFixed(2)},${py(x[1]).toFixed(2)}`).join(' ');
  const area = `${PL},${H-PB} ${pts} ${(W-PR).toFixed(2)},${H-PB}`;

  const pct = ((vals[vals.length-1] - vals[0]) / vals[0] * 100);
  const gid = 'g' + Math.random().toString(36).slice(2,8);

  svg.innerHTML = `
    <defs>
      <linearGradient id="${gid}" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="${line}" stop-opacity=".22"/>
        <stop offset="100%" stop-color="${line}" stop-opacity="0"/>
      </linearGradient>
    </defs>
    <line x1="0" y1="${py(max).toFixed(2)}" x2="${W}" y2="${py(max).toFixed(2)}" stroke="#f1f3f4" stroke-width="1"/>
    <line x1="0" y1="${py(min).toFixed(2)}" x2="${W}" y2="${py(min).toFixed(2)}" stroke="#f1f3f4" stroke-width="1"/>
    <polygon points="${area}" fill="url(#${gid})"/>
    <polyline points="${pts}" fill="none" stroke="${line}" stroke-width="1.8"
      stroke-linejoin="round" stroke-linecap="round" vector-effect="non-scaling-stroke"/>
    <circle cx="${px(seq.length-1).toFixed(2)}" cy="${py(vals[vals.length-1]).toFixed(2)}" r="2.6" fill="${line}"/>
  `;
  document.getElementById('cfL').textContent = seq[0][0];
  document.getElementById('cfR').textContent = seq[seq.length-1][0];
  document.getElementById('chartHint').innerHTML =
    `<span class="${chgCls(pct)}" style="font-weight:700">区间 ${fmtPct(pct)}</span>`;
}
document.querySelectorAll('.ctab').forEach(t=>{
  t.onclick = ()=>{
    document.querySelectorAll('.ctab').forEach(x=>x.classList.remove('on'));
    t.classList.add('on'); curRange = t.dataset.r; drawChart();
  };
});

/* ---------- 关键指标 ---------- */
(function renderKV(){
  const rows = [
    ['基金代码', FUND.code],
    ['基金简称', FUND.full_name || FUND.name],
    ['基金公司', FUND.company || '--'],
    ['基金类型', FUND.ftype || '--'],
    ['份额类别', FUND.share + ' 类'],
    ['申购状态', FUND.sgzt || '--'],
    ['单位净值', FUND.nav!=null ? FUND.nav.toFixed(4) : '--'],
    ['净值日期', FUND.nav_date || '--'],
    ['当日涨跌', fmtPct(FUND.chg)],
    ['近1月 / 近半年 / 近1年',
      `${fmtPct(FUND.r1m)}  /  ${fmtPct(FUND.r6m)}  /  ${fmtPct(FUND.r1y)}`],
    ['近3年', fmtPct(FUND.r3y)],
    ['成立日期', FUND.estab || '--'],
    ['基金规模', FUND.scale!=null ? fmtScale(FUND.scale) : '--'],
  ];
  document.getElementById('kv').innerHTML = rows.map(r=>
    `<div class="kv-row"><span class="kv-k">${esc(r[0])}</span><span class="kv-v">${esc(r[1])}</span></div>`
  ).join('');
})();

/* ---------- 同系列 A/C 互跳 ---------- */
(function renderSibs(){
  const sib = (ALL||[]).filter(x=>x.code !== FUND.code);
  if(!sib.length) return;
  document.getElementById('sibSec').style.display = '';
  document.getElementById('sibs').innerHTML = sib.map(x=>{
    const cls = chgCls(x.chg);
    return `<a class="sib" href="${x.code}.html">
      <span class="sh">${esc(x.share)} 类</span>
      <div class="sn">${esc(x.name)}</div>
      <div class="sv ${cls}">${fmtPct(x.chg)}</div>
      <div class="sc">净值 ${x.nav!=null?x.nav.toFixed(4):'--'} · ${x.nav_date||'--'}</div>
    </a>`;
  }).join('');
})();

/* ---------- 工具 ---------- */
function fmtPct(v){
  if(v==null) return '--';
  return (v>0?'+':'') + Number(v).toFixed(2) + '%';
}
function fmtScale(v){
  if(v >= 1e8) return (v/1e8).toFixed(2) + ' 亿元';
  if(v >= 1e4) return (v/1e4).toFixed(2) + ' 万元';
  return v.toFixed(0) + ' 元';
}
function esc(s){
  return String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
}

drawChart();
</script>
</body>
</html>
"""


# ============================================================ 渲染
def _light_fund(f):
    """首页用轻量字段（不含 hist）。"""
    return {k: f[k] for k in (
        "code", "name", "company", "nav", "nav_date", "chg",
        "sgzt", "status", "family", "share", "note") if k in f}


def _light_fam(fam):
    return {
        "family": fam["family"],
        "chg": fam.get("chg"),
        "on_sale": fam.get("on_sale"),
        "members": [_light_fund(m) for m in fam.get("members", [])],
        "primary": _light_fund(fam["primary"]) if fam.get("primary") else None,
    }


def _light_section(sec):
    return {
        "key": sec["key"], "name": sec["name"], "short": sec.get("short"),
        "index": sec.get("index"),
        "live": [_light_fam(x) for x in sec.get("live", [])],
        "hold": [_light_fam(x) for x in sec.get("hold", [])],
        "stats": sec.get("stats"),
        "count_families": sec.get("count_families"),
        "count_funds": sec.get("count_funds"),
    }


def _light_other(oth):
    return {
        "key": "OTHERS", "name": oth["name"], "short": oth.get("short"),
        "index": None,
        "groups": [{"name": g["name"], "funds": [_light_fund(x) for x in g["funds"]]}
                   for g in oth.get("groups", [])],
        "stats": oth.get("stats"),
        "count_families": oth.get("count_families"),
        "count_funds": oth.get("count_funds"),
    }


def render_index(snapshot):
    st = snapshot["stats"]
    idx_times = [i.get("time") for i in snapshot.get("indexes", []) if i.get("time")]
    idx_time = "截至 " + (idx_times[0] if idx_times else "—")
    nav_date = snapshot.get("latest_nav_date") or "—"
    nav_date_short = nav_date[5:] if len(nav_date) == 10 else nav_date

    # 首页只带轻量数据：去掉每只基金的 hist（体积从 895KB 降到 ~120KB）
    light = {
        "report_date": snapshot["report_date"],
        "weekday": snapshot["weekday"],
        "generated_at": snapshot["generated_at"],
        "latest_nav_date": nav_date,
        "stats": st,
        "indexes": snapshot.get("indexes", []),
        "sections": [_light_section(s) for s in snapshot.get("sections", [])],
        "other": _light_other(snapshot["other"]) if snapshot.get("other") else None,
    }

    html = INDEX_TEMPLATE
    html = html.replace("__COMMON_CSS__", COMMON_CSS)
    html = html.replace("__DATA__", json.dumps(light, ensure_ascii=False, separators=(",", ":")))
    html = html.replace("__REPORT_DATE__", snapshot["report_date"])
    html = html.replace("__WEEKDAY__", snapshot["weekday"])
    html = html.replace("__NAV_DATE_SHORT__", nav_date_short)
    html = html.replace("__NAV_DATE__", nav_date)
    html = html.replace("__TOTAL__", str(st["total"]))
    html = html.replace("__UP__", str(st["up"]))
    html = html.replace("__DOWN__", str(st["down"]))
    html = html.replace("__AVG__", ("+" if st["avg_chg"] > 0 else "") + str(st["avg_chg"]))
    html = html.replace("__IDX_TIME__", idx_time)
    html = html.replace("__GEN_TIME__", snapshot["generated_at"])
    try:
        html = html.replace("__MANIFEST__", make_manifest())
        html = html.replace("__ICON192__", make_icon_b64(192))
    except Exception as e:
        html = html.replace("__MANIFEST__", "data:application/manifest+json,{}")
        html = html.replace("__ICON192__", "")
        print(f"  [警告] PWA 图标生成失败: {e}")
    return html


def render_detail(fund, family_members, snapshot):
    """生成单只基金的详情页。familiy_members 为同系列全部成员（轻量）。"""
    others = [_light_fund(m) for m in family_members]

    # 若没有 C 份额，按钮指向首页
    sib = next((m for m in others if m["code"] != fund["code"]), None)
    sib_url = f"{sib['code']}.html" if sib else "../index.html"
    sib_share = sib["share"] if sib else "其他"

    # 状态 pill
    if fund.get("status") == "on_sale":
        status_pill = f'<span class="pill">申购中 · {fund.get("sgzt") or "开放"}</span>'
    else:
        status_pill = '<span class="pill warn">暂停申购 · 可赎回</span>'
    if fund.get("note"):
        status_pill += f'<span class="pill">{fund["note"]}</span>'

    chg = fund.get("chg")
    chg_cls = "up" if (chg or 0) > 0 else ("down" if (chg or 0) < 0 else "flat")
    chg_bg = {"up": "#d93025", "down": "#0f9d58", "flat": "#9aa0a6"}[chg_cls]
    chg_txt = ("--" if chg is None else (("+" if chg > 0 else "") + f"{chg:.2f}%"))

    html = DETAIL_TEMPLATE
    html = html.replace("__COMMON_CSS__", COMMON_CSS)
    html = html.replace("__NAME__", fund["name"])
    html = html.replace("__CODE__", fund["code"])
    html = html.replace("__COMPANY__", fund.get("company") or "—")
    html = html.replace("__SHARE__", fund.get("share") or "A")
    html = html.replace("__STATUS_PILL__", status_pill)
    html = html.replace("__NAV__", f"{fund['nav']:.4f}" if fund.get("nav") is not None else "--")
    html = html.replace("__CHG_CLS__", chg_cls)
    html = html.replace("__CHG_BG__", chg_bg)
    html = html.replace("__CHG__", chg_txt)
    html = html.replace("__NAV_DATE__", fund.get("nav_date") or "—")
    html = html.replace("__SIB_URL__", sib_url)
    html = html.replace("__SIB_SHARE__", sib_share)
    html = html.replace("__GEN_TIME__", snapshot["generated_at"])
    html = html.replace("__FUND_JSON__", json.dumps(fund, ensure_ascii=False, separators=(",", ":")))
    html = html.replace("__ALL_JSON__", json.dumps(others, ensure_ascii=False, separators=(",", ":")))
    return html


# ============================================================ 主流程
DATA_DIR_ARCHIVE = os.path.join(BASE_DIR, "data", "archive")


def main():
    snap_path = os.path.join(BASE_DIR, "data", "snapshot.json")
    with open(snap_path, encoding="utf-8") as f:
        snapshot = json.load(f)

    os.makedirs(OUT_DIR, exist_ok=True)
    detail_dir = os.path.join(OUT_DIR, "f")
    os.makedirs(detail_dir, exist_ok=True)

    # ---- 首页 ----
    html = render_index(snapshot)
    out = os.path.join(OUT_DIR, "index.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"首页已生成 -> {out}  ({len(html)//1024} KB)")

    # ---- 详情页 ----
    funds = snapshot.get("funds", {})
    # family -> [轻量成员] 映射
    fam_map = {}
    for f in funds.values():
        fam_map.setdefault(f["family"], []).append(_light_fund(f))
    for v in fam_map.values():
        v.sort(key=lambda x: (x["share"] != "A", x["code"]))

    n = 0
    for code, fund in funds.items():
        page = render_detail(fund, fam_map.get(fund["family"], []), snapshot)
        with open(os.path.join(detail_dir, f"{code}.html"), "w", encoding="utf-8") as f:
            f.write(page)
        n += 1
    print(f"详情页已生成 -> {detail_dir}/  ({n} 个)")

    # ---- 归档 ----
    os.makedirs(DATA_DIR_ARCHIVE, exist_ok=True)
    arc = os.path.join(DATA_DIR_ARCHIVE, f"{snapshot['report_date']}.html")
    with open(arc, "w", encoding="utf-8") as f:
        f.write(html)

    # 体积汇总
    total = sum(os.path.getsize(os.path.join(detail_dir, x))
                for x in os.listdir(detail_dir))
    print(f"详情页合计 {total//1024} KB | 站点合计 {(os.path.getsize(out)+total)//1024} KB")
    return out


if __name__ == "__main__":
    main()
