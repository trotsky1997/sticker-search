#!/usr/bin/env python3
"""
sticker.py - 表情包搜索下载 CLI (多数据源)

Data sources:
  - fabiaoqing.com (online search, trending stickers)
  - ChineseBQB (GitHub open-source sticker pack, curated)

Usage:
  python3 sticker.py search <关键词>          # 搜索两个数据源，列出结果
  python3 sticker.py download <关键词> [序号]  # 搜索并下载第 N 张
  python3 sticker.py random <关键词>           # 随机下载一张匹配的
  python3 sticker.py send <关键词> [chat_id]   # 搜索+下载+输出 JSON
  python3 sticker.py update                    # 更新 ChineseBQB 本地索引

Examples:
  python3 sticker.py search 加油
  python3 sticker.py download 开心 3
  python3 sticker.py random 庆祝
  python3 sticker.py send 谢谢 oc_xxxxx
"""

import sys
import os
import re
import json
import random
import urllib.request
import urllib.parse
from pathlib import Path

# === Config ===
SAVE_DIR = Path("/tmp/openclaw/stickers")
CACHE_DIR = Path("/tmp/openclaw/sticker_cache")
BQB_INDEX_URL = "https://raw.githubusercontent.com/zhaoolee/ChineseBQB/master/chinesebqb_github.json"
BQB_INDEX_CACHE = CACHE_DIR / "chinesebqb_index.json"
FABIAOQING_SEARCH_URL = "https://fabiaoqing.com/search/bqb/keyword/{kw}/type/bq/page/{page}.html"
IMG_PATTERN = re.compile(r'data-original="(https?://img\.soutula\.com/[^"]+\.(?:jpg|png|gif|webp))"')

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9",
}
FABI_HEADERS = {**HEADERS, "Referer": "https://fabiaoqing.com/"}


# === ChineseBQB (GitHub open-source) ===

def update_bqb_index():
    """Download/update ChineseBQB index from GitHub"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    print("⬇️  正在下载 ChineseBQB 索引...")
    req = urllib.request.Request(BQB_INDEX_URL, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = b""
        while True:
            chunk = resp.read(8192)
            if not chunk:
                break
            data += chunk
    parsed = json.loads(data)
    items = parsed.get("data", parsed) if isinstance(parsed, dict) else parsed
    BQB_INDEX_CACHE.write_bytes(data)
    print(f"✅ 索引已更新: {len(items)} 个表情包")
    return items


def load_bqb_index():
    """Load cached ChineseBQB index, download if missing"""
    if not BQB_INDEX_CACHE.exists():
        return update_bqb_index()
    try:
        parsed = json.loads(BQB_INDEX_CACHE.read_text("utf-8"))
        return parsed.get("data", parsed) if isinstance(parsed, dict) else parsed
    except (json.JSONDecodeError, UnicodeDecodeError):
        return update_bqb_index()


def search_bqb(keyword: str, limit: int = 10) -> list[dict]:
    """Search ChineseBQB by keyword in filename/category"""
    items = load_bqb_index()
    results = []
    kw = keyword.lower()
    for item in items:
        name = item.get("name", "")
        category = item.get("category", "")
        # Match if keyword appears in name or category
        if kw in name.lower() or kw in category.lower():
            results.append({
                "source": "ChineseBQB",
                "name": name,
                "category": category,
                "url": item["url"],
                "filename": name,
            })
            if len(results) >= limit:
                break
    return results


# === fabiaoqing.com (online search) ===

def fetch_fabi_html(keyword: str, page: int = 1) -> str:
    """Search fabiaoqing.com, return HTML"""
    kw_encoded = urllib.parse.quote(keyword)
    url = FABIAOQING_SEARCH_URL.format(kw=kw_encoded, page=page)
    req = urllib.request.Request(url, headers=FABI_HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = b""
        while True:
            chunk = resp.read(8192)
            if not chunk:
                break
            data += chunk
        return data.decode("utf-8", errors="replace")


def search_fabi(keyword: str, limit: int = 10) -> list[dict]:
    """Search fabiaoqing.com for stickers"""
    try:
        html = fetch_fabi_html(keyword)
    except Exception as e:
        print(f"⚠️  fabiaoqing 搜索失败: {e}")
        return []
    urls = IMG_PATTERN.findall(html)
    results = []
    for i, url in enumerate(urls[:limit]):
        results.append({
            "source": "fabiaoqing",
            "name": url.split("/")[-1],
            "category": "",
            "url": url,
            "filename": url.split("/")[-1],
        })
    return results


# === Combined search ===

def search_all(keyword: str, limit_per_source: int = 10) -> list[dict]:
    """Search both sources, return combined results"""
    print(f"🔍 搜索「{keyword}」...")
    bqb_results = search_bqb(keyword, limit_per_source)
    fabi_results = search_fabi(keyword, limit_per_source)
    
    all_results = bqb_results + fabi_results
    for i, r in enumerate(all_results):
        r["index"] = i + 1
    
    if not all_results:
        print(f"❌ 没找到「{keyword}」相关的表情包")
    else:
        print(f"   ChineseBQB: {len(bqb_results)} 个 | fabiaoqing: {len(fabi_results)} 个")
    return all_results


# === Download ===

def download_image(url: str, source: str = "") -> Path:
    """Download a sticker image, return local path"""
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    filename = urllib.parse.unquote(url.split("/")[-1])
    save_path = SAVE_DIR / filename
    
    # URL-encode the path portion for non-ASCII filenames (ChineseBQB)
    parsed = urllib.parse.urlparse(url)
    encoded_path = urllib.parse.quote(parsed.path, safe="/")
    url = urllib.parse.urlunparse(parsed._replace(path=encoded_path))
    
    headers = FABI_HEADERS if source == "fabiaoqing" else HEADERS
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        save_path.write_bytes(resp.read())
    return save_path


# === Commands ===

def cmd_search(keyword: str):
    results = search_all(keyword)
    if not results:
        return
    print()
    for r in results:
        tag = "📦" if r["source"] == "ChineseBQB" else "🌐"
        cat = f" [{r['category']}]" if r["category"] else ""
        print(f"  [{r['index']:2d}] {tag} {r['name']}{cat}")
    print(f"\n💡 下载: python3 sticker.py download {keyword} <序号>")


def cmd_download(keyword: str, index: int = 1):
    results = search_all(keyword)
    if not results:
        return None
    if index < 1 or index > len(results):
        print(f"❌ 序号超出范围，共 {len(results)} 个结果")
        return None
    target = results[index - 1]
    path = download_image(target["url"], target["source"])
    print(f"✅ 已下载: {path} ({path.stat().st_size} bytes) [{target['source']}]")
    return path


def cmd_random(keyword: str):
    results = search_all(keyword)
    if not results:
        return None
    target = random.choice(results)
    path = download_image(target["url"], target["source"])
    print(f"✅ 随机下载: {path} ({path.stat().st_size} bytes) [{target['source']}]")
    return path


def cmd_send(keyword: str, chat_id: str = ""):
    results = search_all(keyword)
    if not results:
        print(json.dumps({"ok": False, "error": "no results"}))
        return
    target = random.choice(results)
    path = download_image(target["url"], target["source"])
    print(json.dumps({"ok": True, "path": str(path), "chat_id": chat_id, "source": target["source"]}))


def cmd_update():
    update_bqb_index()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "search":
        keyword = sys.argv[2] if len(sys.argv) > 2 else ""
        if not keyword:
            print("❌ 请提供搜索关键词")
            sys.exit(1)
        cmd_search(keyword)

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

    elif cmd == "update":
        cmd_update()

    else:
        print(f"❌ 未知命令: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
