---
name: sticker-search
description: Search, download, verify, and send sticker/emoji images (表情包) from multiple sources. Use when providing emotional value in group chats — reacting to messages with stickers, celebrating achievements, encouraging others, or matching the mood of a conversation. Also use when a user explicitly asks for a sticker/表情包 by keyword (e.g. 加油, 谢谢, 庆祝, 开心, 无语).
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

## Emotional Value Response Framework

### Three Response Levels

| Level | Method | Trigger | Frequency |
|-------|--------|---------|-----------|
| L1 | Reaction emoji | Most messages | Max 1 per message, no more than 3 consecutive |
| L2 | Sticker image | Clear emotional moments (good news, venting, asking help) | Max 2-3 per group per day |
| L3 | Text reply | Can add real value, info, or specific praise | Unlimited, but must be substantive |

### Emotion Matching Logic

1. **Understand the message emotion first** — happy? sad? venting? showing off? asking help? chitchat?
2. **Then choose response level**:
   - Chitchat/water group → L1 reaction is enough
   - Clear emotional expression → L2 sticker
   - Discussion-worthy topic → L3 text
3. **Avoid mismatch** — don't send celebration when someone is venting; don't send haha when someone is sad

### Sticker Usage Rules

1. Search keyword → download → **read image to verify** → send
2. If image doesn't fit, retry max 2 times with different index/random
3. Prefer ChineseBQB (filenames are descriptive, easier to judge)
4. Prefer GIF (more lively)
5. **No duplicates** — never send the same image twice in the same group

### Frequency Limits

- ❌ Don't react to every message (becomes noise)
- ❌ Don't send multiple stickers in a row (spam)
- ❌ Don't suddenly send stickers during serious discussions
- ✅ Reduce interaction late night (23:00-07:00) unless @mentioned
- ✅ Can proactively send a sticker to warm up a dead chat

### Scene-based Guide

| Scene | Best Response |
|-------|--------------|
| Someone shares paper/link | 👀 reaction + summarize content |
| Someone shares achievement | 🎉/🔥 reaction + specific compliment |
| Someone vents about overtime | ❤️ reaction + "辛苦了" |
| Someone asks a question | 💡 reaction + help answer |
| Someone tells a joke | 😂 reaction (don't explain the joke) |
| Chat goes quiet | Send a sticker to warm up |
| Late night chatting | ❤️ reaction (sympathy) |

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

## Technical Notes

- ChineseBQB images are on GitHub raw URLs (stable, no auth needed)
- fabiaoqing images require `Referer: https://fabiaoqing.com/` (handled by script)
- Images saved to `/tmp/openclaw/stickers/`
- Index cached at `/tmp/openclaw/sticker_cache/chinesebqb_index.json`
- Always `read` the downloaded image before sending to verify content appropriateness
