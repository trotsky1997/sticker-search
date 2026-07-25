# sticker-search 🎭

表情包搜索下载 CLI，数据来源 [fabiaoqing.com](https://fabiaoqing.com)。

## 安装

```bash
# 直接使用 (Python 3.10+)
python3 scripts/sticker.py search 加油
```

## 使用

```bash
# 搜索表情包
python3 scripts/sticker.py search <关键词> [页码]

# 下载第 N 张（默认第1张）
python3 scripts/sticker.py download <关键词> [序号]

# 随机下载一张
python3 scripts/sticker.py random <关键词>

# 搜索+下载+输出 JSON
python3 scripts/sticker.py send <关键词> [chat_id]
```

### 关键词示例

| 场景 | 关键词 |
|------|--------|
| 庆祝 | 庆祝, 撒花, 牛逼 |
| 加油 | 加油, 冲, 你可以的 |
| 感谢 | 谢谢, 感谢, 比心 |
| 开心 | 开心, 哈哈, 高兴 |
| 难过 | 哭, 难过, 抱抱 |
| 无语 | 无语, 汗, 尴尬 |

## 注意

- 下载图片需带 `Referer: https://fabiaoqing.com/` 头（脚本已处理）
- 图片保存到 `/tmp/openclaw/stickers/`
- 支持 jpg/png/gif/webp

## License

MIT
