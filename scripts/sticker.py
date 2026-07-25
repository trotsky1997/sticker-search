#!/usr/bin/env python3
"""
sticker.py - 表情包搜索下载 CLI (fabiaoqing.com)

Usage:
  python3 sticker.py search <关键词> [页码]       # 搜索表情包，列出结果
  python3 sticker.py download <关键词> [序号]     # 搜索并下载第 N 张（默认第1张）
  python3 sticker.py random <关键词>              # 随机下载一张匹配的表情包
  python3 sticker.py send <关键词> [chat_id]      # 搜索+下载+发送到飞书群

Examples:
  python3 sticker.py search 加油
  python3 sticker.py download 开心 3
  python3 sticker.py random 庆祝
  python3 sticker.py send 谢谢 oc_xxxxx
"""

import sys
import os
import re
import random
import urllib.request
import urllib.parse
import json
from pathlib import Path

SEARCH_URL = "https://fabiaoqing.com/search/bqb/keyword/{kw}/type/bq/page/{page}.html"
IMG_PATTERN = re.compile(r'data-original="(https?://img\.soutula\.com/[^"]+\.(?:jpg|png|gif|webp))"')
TITLE_PATTERN = re.compile(r'title="([^"]+)"[^>]*data-original=')
SAVE_DIR = Path("/tmp/openclaw/stickers")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://fabiaoqing.com/",
    "Accept-Language": "zh-CN,zh;q=0.9",
}


def fetch_html(keyword: str, page: int = 1) -> str:
    """搜索表情包，返回 HTML 内容"""
    kw_encoded = urllib.parse.quote(keyword)
    url = SEARCH_URL.format(kw=kw_encoded, page=page)
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = b""
        while True:
            chunk = resp.read(8192)
            if not chunk:
                break
            data += chunk
        return data.decode("utf-8", errors="replace")


def parse_results(html: str) -> list[dict]:
    """从 HTML 中解析表情包列表"""
    results = []
    for i, (url) in enumerate(IMG_PATTERN.findall(html)):
        results.append({"index": i + 1, "url": url, "filename": url.split("/")[-1]})
    return results


def download_image(url: str, save_path: Path | None = None) -> Path:
    """下载单张表情包"""
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    if save_path is None:
        save_path = SAVE_DIR / url.split("/")[-1]
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        save_path.write_bytes(resp.read())
    return save_path


def cmd_search(keyword: str, page: int = 1):
    """搜索并列出表情包"""
    html = fetch_html(keyword, page)
    results = parse_results(html)
    if not results:
        print(f"❌ 没找到「{keyword}」相关的表情包")
        return
    print(f"🔍 搜索「{keyword}」找到 {len(results)} 个表情包：\n")
    for r in results:
        print(f"  [{r['index']:2d}] {r['filename']}")
        print(f"       {r['url']}")
    print(f"\n💡 下载: python3 sticker.py download {keyword} <序号>")


def cmd_download(keyword: str, index: int = 1):
    """搜索并下载第 N 张"""
    html = fetch_html(keyword)
    results = parse_results(html)
    if not results:
        print(f"❌ 没找到「{keyword}」相关的表情包")
        return None
    if index < 1 or index > len(results):
        print(f"❌ 序号超出范围，共 {len(results)} 个结果")
        return None
    target = results[index - 1]
    path = download_image(target["url"])
    print(f"✅ 已下载: {path} ({path.stat().st_size} bytes)")
    return path


def cmd_random(keyword: str):
    """随机下载一张"""
    html = fetch_html(keyword)
    results = parse_results(html)
    if not results:
        print(f"❌ 没找到「{keyword}」相关的表情包")
        return None
    target = random.choice(results)
    path = download_image(target["url"])
    print(f"✅ 随机下载: {path} ({path.stat().st_size} bytes)")
    return path


def cmd_send(keyword: str, chat_id: str = ""):
    """搜索+下载+输出路径（供 OpenClaw message 工具发送）"""
    path = cmd_random(keyword)
    if path:
        # 输出 JSON 供调用方解析
        print(json.dumps({"ok": True, "path": str(path), "chat_id": chat_id}))
    else:
        print(json.dumps({"ok": False, "error": "no results"}))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "search":
        keyword = sys.argv[2] if len(sys.argv) > 2 else ""
        page = int(sys.argv[3]) if len(sys.argv) > 3 else 1
        if not keyword:
            print("❌ 请提供搜索关键词")
            sys.exit(1)
        cmd_search(keyword, page)

    elif cmd == "download":
        keyword = sys.argv[2] if len(sys.argv) > 2 else ""
        index = int(sys.argv[3]) if len(sys.argv) > 3 else 1
        if not keyword:
            print("❌ 请提供搜索关键词")
            sys.exit(1)
        cmd_download(keyword, index)

    elif cmd == "random":
        keyword = sys.argv[2] if len(sys.argv) > 2 else ""
        if not keyword:
            print("❌ 请提供搜索关键词")
            sys.exit(1)
        cmd_random(keyword)

    elif cmd == "send":
        keyword = sys.argv[2] if len(sys.argv) > 2 else ""
        chat_id = sys.argv[3] if len(sys.argv) > 3 else ""
        if not keyword:
            print("❌ 请提供搜索关键词")
            sys.exit(1)
        cmd_send(keyword, chat_id)

    else:
        print(f"❌ 未知命令: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
