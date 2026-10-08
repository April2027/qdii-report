# -*- coding: utf-8 -*-
"""
QDII 早报 —— 基金池配置
数据源：天天基金（净值）+ 新浪财经（海外指数）
"""

FUND_POOL = [
    {"code": "270042", "group": "纳斯达克100", "name": "广发纳斯达克100ETF联接(QDII)A"},
    {"code": "040046", "group": "纳斯达克100", "name": "华安纳斯达克100ETF联接(QDII)A"},
    {"code": "000834", "group": "纳斯达克100", "name": "大成纳斯达克100ETF联接(QDII)A"},
    {"code": "161130", "group": "纳斯达克100", "name": "易方达纳斯达克100ETF联接(QDII-LOF)A"},
    {"code": "160213", "group": "纳斯达克100", "name": "国泰纳斯达克100指数(QDII)"},
    {"code": "161125", "group": "标普500", "name": "易方达标普500指数(QDII-LOF)A"},
    {"code": "050025", "group": "标普500", "name": "博时标普500ETF联接(QDII)A"},
    {"code": "017641", "group": "标普500", "name": "摩根标普500指数(QDII)A"},
    {"code": "000071", "group": "港股中概", "name": "华夏恒生ETF联接(QDII)A"},
    {"code": "006327", "group": "港股中概", "name": "易方达中证海外互联网50ETF联接(QDII)A"},
    {"code": "164906", "group": "港股中概", "name": "交银中证海外中国互联网指数(LOF)A"},
    {"code": "013171", "group": "港股中概", "name": "华夏恒生互联网科技业ETF联接(QDII)A"},
    {"code": "161128", "group": "科技半导体", "name": "易方达标普信息科技指数(QDII-LOF)A"},
    {"code": "160216", "group": "商品能源", "name": "国泰大宗商品(QDII-LOF)A"},
    {"code": "162411", "group": "商品能源", "name": "华宝标普油气上游股票(QDII)A"},
    {"code": "006282", "group": "其他区域", "name": "摩根欧洲动力策略股票(QDII)A"},
    {"code": "008763", "group": "其他区域", "name": "天弘越南市场股票发起(QDII)A"},
    {"code": "164824", "group": "其他区域", "name": "工银印度基金人民币(QDII)"},
]

INDEX_BOARD = [
    {"key": "gb_$ndx", "name": "纳斯达克100", "region": "美股"},
    {"key": "gb_$inx", "name": "标普500", "region": "美股"},
    {"key": "gb_$dji", "name": "道琼斯", "region": "美股"},
    {"key": "gb_$sox", "name": "费城半导体", "region": "美股"},
    {"key": "int_hangseng", "name": "恒生指数", "region": "港股"},
    {"key": "int_nikkei", "name": "日经225", "region": "日股"},
]

GROUP_ORDER = ["纳斯达克100", "标普500", "港股中概", "科技半导体", "商品能源", "其他区域"]
