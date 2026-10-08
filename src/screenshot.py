# -*- coding: utf-8 -*-
"""
QDII 早报 —— 长图生成器
把 index.html 渲染成竖版长图（发公众号 / 微信群 / 朋友圈用）
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)


def main():
    html = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PROJECT_ROOT, "site", "index.html")
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(PROJECT_ROOT, "site", "report.png")

    if not os.path.exists(html):
        print(f"[长图] 跳过：找不到 {html}")
        return 0

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[长图] 跳过：未安装 playwright")
        return 0

    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": 1080, "height": 1920}, device_scale_factor=1)
        page.goto("file://" + os.path.abspath(html))
        page.wait_for_timeout(800)
        page.add_style_tag(content=".bar{display:none!important}")
        page.wait_for_timeout(100)
        page.screenshot(path=out, full_page=True)
        browser.close()

    size_kb = os.path.getsize(out) // 1024
    print(f"长图已生成 -> {out}  ({size_kb} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
