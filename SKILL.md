---
name: sticker-search
description: Search, download, and send sticker/emoji images (表情包) from multiple sources. Use when the user wants to find/send stickers for emotional expression in chats, when responding to group chat messages with stickers, or when searching for reaction images by keyword (e.g. 加油, 谢谢, 庆祝, 开心, 无语).
---

# Sticker Search

Search and download 表情包 from two complementary sources:

- **ChineseBQB** (📦): Open-source GitHub repo, 5800+ curated stickers with Chinese filenames. No Referer needed.
- **fabiaoqing.com** (🌐): Online search, trending/hot stickers. Requires Referer header.

## Usage

```bash
# Search both sources (lists results with index numbers)
python3 scripts/sticker.py search <keyword>

# Download a specific sticker by index
python3 scripts/sticker.py download <keyword> [index]

# Randomly download one sticker matching keyword
python3 scripts/sticker.py random <keyword>

# Search + download + output JSON (for programmatic use)
python3 scripts/sticker.py send <keyword> [chat_id]

# Update ChineseBQB local index (run once, cached afterwards)
python3 scripts/sticker.py update
```

## Workflow

1. Run `update` once to cache the ChineseBQB index (5800+ items)
2. Pick a keyword matching the emotional context
3. Run `random <keyword>` to get a sticker path
4. **Read the image** with the `read` tool to verify content is appropriate and on-topic
5. If the image doesn't fit, try another `random` or `download` with a different index
6. Send the verified image via the `message` tool with `media=<path>`

### Why verify?
fabiaoqing filenames are opaque IDs — you can't judge content from the name. Always read the image before sending to avoid sending inappropriate or off-topic stickers.

## Keyword Guide

| Context | Keywords |
|---------|----------|
| Celebrating | 庆祝, 撒花, 牛逼 |
| Encouraging | 加油, 冲, 你可以的 |
| Thanking | 谢谢, 感谢, 比心, 心心 |
| Happy | 开心, 哈哈, 高兴, 开心鸭 |
| Sad/sympathy | 哭, 难过, 抱抱, 可怜 |
| Speechless | 无语, 汗, 尴尬, 懵逼 |
| Angry | 生气, 怒, 气死 |
| Greeting | 你好, 嗨, 早安 |

## Notes

- ChineseBQB images are on GitHub raw URLs (stable, no auth needed)
- fabiaoqing images require `Referer: https://fabiaoqing.com/` (handled by script)
- Images saved to `/tmp/openclaw/stickers/`
- Index cached at `/tmp/openclaw/sticker_cache/chinesebqb_index.json`
