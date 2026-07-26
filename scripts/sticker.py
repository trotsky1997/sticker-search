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
# Capture image URL + title (for brand/emotion matching)
IMG_PATTERN = re.compile(r'data-original="(https?://img\.soutula\.com/[^"]+\.(?:jpg|png|gif|webp))"[^>]*title="([^"]*)"')

# === Brand / Character aliases ===
# Maps user search terms to canonical brand names for better matching
# Covers both fabiaoqing and ChineseBQB sources
BRAND_ALIASES = {
    # Animals
    "水豚噜噜": ["水豚"],
    "水豚": ["水豚"],
    "卡皮巴拉": ["水豚", "卡皮巴拉"],
    "capybara": ["水豚", "capybara"],
    "猫": ["猫", "喵", "Cat", "猫咪"],
    "猫咪": ["猫", "喵", "Cat", "猫咪"],
    "狗": ["狗", "Dog"],
    "柴犬": ["柴犬", "doge"],
    "doge": ["doge", "柴犬"],
    "仓鼠": ["仓鼠", "Hamster"],
    "鹦鹉": ["鹦鹉", "Parrot"],
    "猪": ["猪", "Pig"],
    "小猪佩奇": ["小猪佩奇", "PigPecs"],
    "青蛙": ["青蛙", "Frog", "旅行青蛙"],
    "乌龟": ["乌龟", "Turtle"],
    "鸽子": ["鸽子", "Pigeon"],
    "企鹅": ["企鹅", "Penguin"],
    "鸡": ["鸡", "Chicken", "小幺鸡"],
    # Characters / IP
    "兔斯基": ["兔斯基"],
    "tuzki": ["兔斯基", "tuzki"],
    "滑稽": ["滑稽", "Funny", "小黄脸"],
    "小黄脸": ["小黄脸", "滑稽", "Emoji"],
    "熊猫": ["熊猫", "Panda", "金馆长"],
    "熊猫头": ["熊猫头", "熊猫", "Panda"],
    "金馆长": ["金馆长", "Panda"],
    "白色小人": ["白色小人", "WhiteVillain"],
    "火柴人": ["火柴人", "MatchstickMen"],
    "海绵宝宝": ["海绵宝宝", "SpongeBob"],
    "皮卡丘": ["皮卡丘", "Pikachu"],
    "哆啦A梦": ["哆啦A梦", "Doraemon"],
    "杰尼龟": ["杰尼龟", "Squirtle"],
    "奥特曼": ["奥特曼", "Altman"],
    "柯南": ["柯南", "KeNan"],
    "熊本熊": ["熊本熊", "KumamotoBear"],
    "胖虎": ["胖虎", "Tiger"],
    "汪蛋": ["汪蛋", "WangEgg"],
    "开心鸭": ["开心鸭", "HappyDuck"],
    "小刘鸭": ["小刘鸭", "HappyDuck"],
    "假笑男孩": ["假笑男孩", "SmirkBoy"],
    "莲蓬头男孩": ["莲蓬头男孩", "ShowerheadBoy"],
    "苏大强": ["苏大强", "SuDaqiang"],
    "猫眼三姐妹": ["猫眼三姐妹", "CatEyesThreeSisters"],
    "猫和老鼠": ["猫和老鼠", "TomAndJerry"],
    "天线宝宝": ["天线宝宝", "AntennaBaby"],
    # Anime / Game
    "原神": ["原神", "GenShin"],
    "进击的巨人": ["进击的巨人", "AttackOnTitan"],
    "鬼灭之刃": ["鬼灭之刃", "GuiMie"],
    "电锯人": ["电锯人", "ChainsawMan"],
    "美少女战士": ["美少女战士", "SailorMoon"],
    "间谍过家家": ["间谍过家家", "spyxfamily"],
    "黑神话悟空": ["黑神话悟空", "BlackMythWuKong"],
    "芙莉莲": ["芙莉莲", "Frieren"],
    "葫芦兄弟": ["葫芦兄弟", "LittleBrother"],
    # Celebrities
    "蔡徐坤": ["蔡徐坤", "CaiXvKun"],
    "罗翔": ["罗翔", "LuoXiang"],
    "黄仁勋": ["黄仁勋", "JensenHuang"],
    "特朗普": ["特朗普", "Trump"],
    # Emotions / Actions
    "打电话": ["打电话", "Call"],
    "吃": ["吃", "Eat"],
    "心心": ["心心", "AllHeart"],
    "表情符号": ["表情符号", "Emoji"],
    # Generic
    "表情包": [],  # generic, no brand filter
}

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


def search_bqb(keyword: str, limit: int = 10, brand_keywords: list = None) -> list[dict]:
    """Search ChineseBQB by keyword in filename/category, with brand alias support"""
    items = load_bqb_index()
    results = []
    # Build search keywords: original + brand aliases
    search_kws = [keyword.lower()]
    if brand_keywords:
        search_kws.extend(kw.lower() for kw in brand_keywords)
    search_kws = list(set(search_kws))
    
    for item in items:
        name = item.get("name", "")
        category = item.get("category", "")
        text = (name + " " + category).lower()
        # Match if any keyword appears in name or category
        if any(kw in text for kw in search_kws):
            results.append({
                "source": "ChineseBQB",
                "name": name,
                "category": category,
                "url": item["url"],
                "filename": name,
                "title": category,  # Use category as title for display
                "tags": [category],
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
    """Search fabiaoqing.com for stickers, with title/brand extraction"""
    try:
        html = fetch_fabi_html(keyword)
    except Exception as e:
        print(f"⚠️  fabiaoqing 搜索失败: {e}")
        return []
    matches = IMG_PATTERN.findall(html)
    results = []
    for url, title in matches[:limit]:
        # Parse title for tags: "兔斯基哭泣 - 兔斯基搞怪表情_兔斯基表情"
        # Split by _ and - to get individual tags
        tags = re.split(r'[_\-]', title)
        tags = [t.strip() for t in tags if t.strip()]
        results.append({
            "source": "fabiaoqing",
            "name": title if title else url.split("/")[-1],
            "category": tags[0] if tags else "",
            "url": url,
            "filename": url.split("/")[-1],
            "title": title,
            "tags": tags,
        })
    return results


# === Combined search ===

def _brand_match_score(item: dict, brand_keywords: list[str]) -> int:
    """Score how well an item matches the brand keywords. Higher = better match."""
    if not brand_keywords:
        return 0
    score = 0
    text = (item.get("title", "") + " " + item.get("name", "") + " " + item.get("category", "")).lower()
    tags = item.get("tags", [])
    for kw in brand_keywords:
        kw_lower = kw.lower()
        if kw_lower in text:
            score += 10
        for tag in tags:
            if kw_lower in tag.lower():
                score += 5  # tag match is strong signal
    return score


def search_all(keyword: str, limit_per_source: int = 10) -> list[dict]:
    """Search both sources, return combined results with brand-aware ranking"""
    # Resolve brand aliases
    brand_keywords = BRAND_ALIASES.get(keyword, [])
    # Also use the keyword itself as a brand keyword if not in aliases
    if not brand_keywords and keyword:
        brand_keywords = [keyword]
    
    print(f"🔍 搜索「{keyword}」... (品牌匹配: {brand_keywords})")
    bqb_results = search_bqb(keyword, limit_per_source, brand_keywords=brand_keywords)
    fabi_results = search_fabi(keyword, limit_per_source)
    
    all_results = bqb_results + fabi_results
    
    # Brand-aware sorting: items matching brand keywords get higher priority
    if brand_keywords:
        for r in all_results:
            r["_brand_score"] = _brand_match_score(r, brand_keywords)
        # Sort by brand score desc, keep original order for ties
        all_results.sort(key=lambda x: (-x["_brand_score"],))
        # Clean up temp field
        for r in all_results:
            r.pop("_brand_score", None)
    
    for i, r in enumerate(all_results):
        r["index"] = i + 1
    
    if not all_results:
        print(f"❌ 没找到「{keyword}」相关的表情包")
    else:
        brand_count = sum(1 for r in all_results if any(kw.lower() in (r.get("title", "") + r.get("name", "")).lower() for kw in brand_keywords))
        print(f"   ChineseBQB: {len(bqb_results)} 个 | fabiaoqing: {len(fabi_results)} 个 | 品牌匹配: {brand_count} 个")
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
        title = r.get("title", "") or r["name"]
        # Truncate long titles
        if len(title) > 50:
            title = title[:47] + "..."
        cat = f" [{r['category']}]" if r["category"] else ""
        print(f"  [{r['index']:2d}] {tag} {title}{cat}")
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
