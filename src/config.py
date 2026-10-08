# -*- coding: utf-8 -*-
"""
QDII 早报 —— 基金池配置（v2）
数据源：天天基金（净值 / 阶段涨幅）+ 新浪财经（海外指数）

结构：
  NASDAQ100  纳斯达克100 场外人民币 A/C 份额
  SP500      标普500     场外人民币 A/C 份额
  OTHERS     其他热门 QDII（港股中概 / 科技半导体 / 商品能源 / 其他区域）

字段说明：
  code      基金代码
  name      展示名称（短名，用于列表）
  company   基金公司（详情页显示）
  status    销售开关：on_sale（可买）/ paused（暂停申购，仍可赎回）
  family    同系列键：同一只基金的 A/C 归为一组，详情页可互跳
  share     份额类别：A / C
"""

# ============ 一、纳斯达克100（场外人民币 A/C） ============
NASDAQ100 = [
    # ---- 广发 ----
    {"code": "270042", "name": "广发纳斯达克100ETF联接A", "company": "广发基金",
     "status": "paused", "family": "广发纳斯达克100ETF联接", "share": "A"},
    {"code": "006479", "name": "广发纳斯达克100ETF联接C", "company": "广发基金",
     "status": "paused", "family": "广发纳斯达克100ETF联接", "share": "C"},
    # ---- 大成 ----
    {"code": "000834", "name": "大成纳斯达克100ETF联接A", "company": "大成基金",
     "status": "on_sale", "family": "大成纳斯达克100ETF联接", "share": "A"},
    {"code": "008971", "name": "大成纳斯达克100ETF联接C", "company": "大成基金",
     "status": "on_sale", "family": "大成纳斯达克100ETF联接", "share": "C"},
    # ---- 华安 ----
    {"code": "040046", "name": "华安纳斯达克100ETF联接A", "company": "华安基金",
     "status": "on_sale", "family": "华安纳斯达克100ETF联接", "share": "A"},
    {"code": "014978", "name": "华安纳斯达克100ETF联接C", "company": "华安基金",
     "status": "on_sale", "family": "华安纳斯达克100ETF联接", "share": "C"},
    # ---- 南方 ----
    {"code": "016452", "name": "南方纳斯达克100指数发起A", "company": "南方基金",
     "status": "on_sale", "family": "南方纳斯达克100指数发起", "share": "A"},
    {"code": "016453", "name": "南方纳斯达克100指数发起C", "company": "南方基金",
     "status": "on_sale", "family": "南方纳斯达克100指数发起", "share": "C"},
    # ---- 建信 ----
    {"code": "539001", "name": "建信纳斯达克100指数A", "company": "建信基金",
     "status": "on_sale", "family": "建信纳斯达克100指数", "share": "A"},
    {"code": "012752", "name": "建信纳斯达克100指数C", "company": "建信基金",
     "status": "on_sale", "family": "建信纳斯达克100指数", "share": "C"},
    # ---- 摩根 ----
    {"code": "019172", "name": "摩根纳斯达克100指数A", "company": "摩根基金",
     "status": "on_sale", "family": "摩根纳斯达克100指数", "share": "A"},
    {"code": "019173", "name": "摩根纳斯达克100指数C", "company": "摩根基金",
     "status": "on_sale", "family": "摩根纳斯达克100指数", "share": "C"},
    # ---- 万家 ----
    {"code": "019441", "name": "万家纳斯达克100指数发起式A", "company": "万家基金",
     "status": "on_sale", "family": "万家纳斯达克100指数发起式", "share": "A"},
    {"code": "019442", "name": "万家纳斯达克100指数发起式C", "company": "万家基金",
     "status": "on_sale", "family": "万家纳斯达克100指数发起式", "share": "C"},
    # ---- 华泰柏瑞 ----
    {"code": "019524", "name": "华泰柏瑞纳斯达克100ETF发起式联接A", "company": "华泰柏瑞基金",
     "status": "on_sale", "family": "华泰柏瑞纳斯达克100ETF发起式联接", "share": "A"},
    {"code": "019525", "name": "华泰柏瑞纳斯达克100ETF发起式联接C", "company": "华泰柏瑞基金",
     "status": "on_sale", "family": "华泰柏瑞纳斯达克100ETF发起式联接", "share": "C"},
    # ---- 招商 ----
    {"code": "019547", "name": "招商纳斯达克100ETF发起式联接A", "company": "招商基金",
     "status": "on_sale", "family": "招商纳斯达克100ETF发起式联接", "share": "A"},
    {"code": "019548", "name": "招商纳斯达克100ETF发起式联接C", "company": "招商基金",
     "status": "on_sale", "family": "招商纳斯达克100ETF发起式联接", "share": "C"},
    # ---- 宝盈 ----
    {"code": "019736", "name": "宝盈纳斯达克100指数发起A", "company": "宝盈基金",
     "status": "on_sale", "family": "宝盈纳斯达克100指数发起", "share": "A"},
    {"code": "019737", "name": "宝盈纳斯达克100指数发起C", "company": "宝盈基金",
     "status": "on_sale", "family": "宝盈纳斯达克100指数发起", "share": "C"},
    # ---- 华夏 ----
    {"code": "015299", "name": "华夏纳斯达克100ETF发起式联接A", "company": "华夏基金",
     "status": "paused", "family": "华夏纳斯达克100ETF发起式联接", "share": "A"},
    {"code": "015300", "name": "华夏纳斯达克100ETF发起式联接C", "company": "华夏基金",
     "status": "paused", "family": "华夏纳斯达克100ETF发起式联接", "share": "C"},
    # ---- 博时 ----
    {"code": "016055", "name": "博时纳斯达克100ETF发起式联接A", "company": "博时基金",
     "status": "paused", "family": "博时纳斯达克100ETF发起式联接", "share": "A"},
    {"code": "016057", "name": "博时纳斯达克100ETF发起式联接C", "company": "博时基金",
     "status": "paused", "family": "博时纳斯达克100ETF发起式联接", "share": "C"},
    # ---- 嘉实 ----
    {"code": "016532", "name": "嘉实纳斯达克100ETF发起联接A", "company": "嘉实基金",
     "status": "paused", "family": "嘉实纳斯达克100ETF发起联接", "share": "A"},
    {"code": "016533", "name": "嘉实纳斯达克100ETF发起联接C", "company": "嘉实基金",
     "status": "paused", "family": "嘉实纳斯达克100ETF发起联接", "share": "C"},
    # ---- 天弘 ----
    {"code": "018043", "name": "天弘纳斯达克100指数发起A", "company": "天弘基金",
     "status": "paused", "family": "天弘纳斯达克100指数发起", "share": "A"},
    {"code": "018044", "name": "天弘纳斯达克100指数发起C", "company": "天弘基金",
     "status": "paused", "family": "天弘纳斯达克100指数发起", "share": "C"},
    # ---- 汇添富 ----
    {"code": "018966", "name": "汇添富纳斯达克100ETF发起式联接A", "company": "汇添富基金",
     "status": "paused", "family": "汇添富纳斯达克100ETF发起式联接", "share": "A"},
    {"code": "018967", "name": "汇添富纳斯达克100ETF发起式联接C", "company": "汇添富基金",
     "status": "paused", "family": "汇添富纳斯达克100ETF发起式联接", "share": "C"},
]

# ============ 二、标普500（场外人民币 A/C） ============
SP500 = [
    # ---- 博时 ----
    {"code": "050025", "name": "博时标普500ETF联接A", "company": "博时基金",
     "status": "paused", "family": "博时标普500ETF联接", "share": "A"},
    {"code": "006075", "name": "博时标普500ETF联接C", "company": "博时基金",
     "status": "paused", "family": "博时标普500ETF联接", "share": "C"},
    # ---- 易方达 ----
    {"code": "161125", "name": "易方达标普500指数人民币A", "company": "易方达基金",
     "status": "paused", "family": "易方达标普500指数", "share": "A"},
    {"code": "012860", "name": "易方达标普500指数人民币C", "company": "易方达基金",
     "status": "paused", "family": "易方达标普500指数", "share": "C"},
    # ---- 摩根 ----
    {"code": "017641", "name": "摩根标普500指数A", "company": "摩根基金",
     "status": "on_sale", "family": "摩根标普500指数", "share": "A"},
    {"code": "019305", "name": "摩根标普500指数C", "company": "摩根基金",
     "status": "on_sale", "family": "摩根标普500指数", "share": "C"},
    # ---- 大成（等权重，注意：非市值加权，跟踪标普500等权重指数） ----
    {"code": "096001", "name": "大成标普500等权重指数A", "company": "大成基金",
     "status": "on_sale", "family": "大成标普500等权重指数", "share": "A", "note": "等权重"},
    {"code": "008401", "name": "大成标普500等权重指数C", "company": "大成基金",
     "status": "on_sale", "family": "大成标普500等权重指数", "share": "C", "note": "等权重"},
    # ---- 国泰 ----
    {"code": "017028", "name": "国泰标普500ETF发起联接A", "company": "国泰基金",
     "status": "paused", "family": "国泰标普500ETF发起联接", "share": "A"},
    {"code": "017030", "name": "国泰标普500ETF发起联接C", "company": "国泰基金",
     "status": "paused", "family": "国泰标普500ETF发起联接", "share": "C"},
    # ---- 华夏 ----
    {"code": "018064", "name": "华夏标普500ETF发起式联接A", "company": "华夏基金",
     "status": "paused", "family": "华夏标普500ETF发起式联接", "share": "A"},
    {"code": "018065", "name": "华夏标普500ETF发起式联接C", "company": "华夏基金",
     "status": "paused", "family": "华夏标普500ETF发起式联接", "share": "C"},
    # ---- 天弘（FOF） ----
    {"code": "007721", "name": "天弘标普500发起(FOF)A", "company": "天弘基金",
     "status": "paused", "family": "天弘标普500发起", "share": "A", "note": "FOF"},
    {"code": "007722", "name": "天弘标普500发起(FOF)C", "company": "天弘基金",
     "status": "paused", "family": "天弘标普500发起", "share": "C", "note": "FOF"},
]

# ============ 三、其他热门 QDII（补充板块） ============
OTHERS = [
    {"code": "000071", "name": "华夏恒生ETF联接A", "company": "华夏基金",
     "status": "on_sale", "family": "华夏恒生ETF联接", "share": "A", "group": "港股中概"},
    {"code": "006327", "name": "易方达中证海外互联网50ETF联接A", "company": "易方达基金",
     "status": "on_sale", "family": "易方达中证海外互联网50ETF联接", "share": "A", "group": "港股中概"},
    {"code": "164906", "name": "交银中证海外中国互联网指数A", "company": "交银施罗德基金",
     "status": "on_sale", "family": "交银中证海外中国互联网指数", "share": "A", "group": "港股中概"},
    {"code": "013171", "name": "华夏恒生互联网科技业ETF联接A", "company": "华夏基金",
     "status": "on_sale", "family": "华夏恒生互联网科技业ETF联接", "share": "A", "group": "港股中概"},
    {"code": "161128", "name": "易方达标普信息科技指数A", "company": "易方达基金",
     "status": "paused", "family": "易方达标普信息科技指数", "share": "A", "group": "科技半导体"},
    {"code": "160216", "name": "国泰大宗商品A", "company": "国泰基金",
     "status": "on_sale", "family": "国泰大宗商品", "share": "A", "group": "商品能源"},
    {"code": "162411", "name": "华宝标普油气上游股票人民币A", "company": "华宝基金",
     "status": "paused", "family": "华宝标普油气上游股票", "share": "A", "group": "商品能源"},
    {"code": "006282", "name": "摩根欧洲动力策略股票A", "company": "摩根基金",
     "status": "on_sale", "family": "摩根欧洲动力策略股票", "share": "A", "group": "其他区域"},
    {"code": "008763", "name": "天弘越南市场股票发起A", "company": "天弘基金",
     "status": "on_sale", "family": "天弘越南市场股票发起", "share": "A", "group": "其他区域"},
    {"code": "164824", "name": "工银印度基金人民币", "company": "工银瑞信基金",
     "status": "on_sale", "family": "工银印度基金", "share": "A", "group": "其他区域"},
]

# ============ 汇总 ============
ALL_FUNDS = NASDAQ100 + SP500 + OTHERS

# 顶层区块
SECTIONS = [
    {"key": "NASDAQ100", "name": "纳斯达克100", "short": "纳指100",
     "funds": NASDAQ100, "track": "gb_$ndx"},
    {"key": "SP500", "name": "标普500", "short": "标普500",
     "funds": SP500, "track": "gb_$inx"},
]

# 其他板块内的分组顺序
OTHER_GROUP_ORDER = ["港股中概", "科技半导体", "商品能源", "其他区域"]

# ============ 海外指数看板 ============
INDEX_BOARD = [
    {"key": "gb_$ndx", "name": "纳斯达克100", "region": "美股"},
    {"key": "gb_$inx", "name": "标普500", "region": "美股"},
    {"key": "gb_$dji", "name": "道琼斯", "region": "美股"},
    {"key": "gb_$sox", "name": "费城半导体", "region": "美股"},
    {"key": "int_hangseng", "name": "恒生指数", "region": "港股"},
    {"key": "int_nikkei", "name": "日经225", "region": "日股"},
]
