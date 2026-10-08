#!/usr/bin/env bash
# QDII 早报 —— 一键更新（抓数据 + 生成页面 + 生成公众号长图）
set -e
cd "$(dirname "$0")"

echo "==> $(date '+%F %T') 开始更新 QDII 早报"
python3 fetch.py
python3 build.py
python3 screenshot.py || echo "  [提示] 长图生成跳过，不影响网页版"
echo "==> $(date '+%F %T') 更新完成"
