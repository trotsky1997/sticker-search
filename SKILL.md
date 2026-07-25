---
name: sticker-search
description: Search, download, and send sticker/emoji images (表情包) from fabiaoqing.com. Use when the user wants to find/send stickers for emotional expression in chats, when responding to group chat messages with stickers, or when searching for reaction images by keyword (e.g. 加油, 谢谢, 庆祝, 开心, 无语).
---

# Sticker Search

Search and download 表情包 (sticker images) from fabiaoqing.com for use in chat conversations.

## Usage

```bash
# Search stickers by keyword (lists results)
python3 scripts/sticker.py search <keyword> [page]

# Download a specific sticker by index
python3 scripts/sticker.py download <keyword> [index]

# Randomly download one sticker matching keyword
python3 scripts/sticker.py random <keyword>

# Search + download + output JSON (for programmatic use)
python3 scripts/sticker.py send <keyword> [chat_id]
```

## Workflow

1. Pick a keyword matching the emotional context (see keyword guide below)
2. Run `random <keyword>` to get a sticker path
3. Send the image via the `message` tool with `media=<path>`

## Keyword Guide

| Context | Example keywords |
|---------|-----------------|
| Celebrating | 庆祝, 撒花, 牛逼 |
| Encouraging | 加油, 冲, 你可以的 |
| Thanking | 谢谢, 感谢, 比心 |
| Happy | 开心, 哈哈, 高兴 |
| Sad/sympathy | 哭, 难过, 抱抱 |
| Speechless | 无语, 汗, 尴尬 |
| Angry | 生气, 怒, 气死 |
| Greeting | 你好, 嗨, 早安 |

## Notes

- Images require `Referer: https://fabiaoqing.com/` header for download (handled by the script)
- Saved to `/tmp/openclaw/stickers/`
- Supports jpg, png, gif, webp formats
- Use `random` for quick one-off sends; use `search` + `download` when picking a specific one
