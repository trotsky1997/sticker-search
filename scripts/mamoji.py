#!/usr/bin/env python3
"""
mamoji.py - Mamoji 贴纸生成 CLI

通过本地 mamoji 服务动态生成贴纸，支持情绪映射、自定义文字/颜色。

Usage:
  python3 mamoji.py generate <emotion> [text]          # 按情绪生成贴纸
  python3 mamoji.py custom <body> <face> <text> [fg] [bg]  # 自定义参数生成
  python3 mamoji.py list                               # 列出所有 body/face 预设
  python3 mamoji.py send <emotion> [text] [chat_id]    # 生成+输出 JSON

Examples:
  python3 mamoji.py generate happy 你好
  python3 mamoji.py generate sad 唉
  python3 mamoji.py custom soft-pink-sweet-delighted-tender-pleasure starry 牛 #ff4fa3 #ffe8ef
  python3 mamoji.py send celebrating 恭喜
"""

import sys
import json
import subprocess
import urllib.request
from pathlib import Path

# === Config ===
MAMOJI_URL = "http://localhost:4321/api/render"
# SVG format contains the macaron body correctly.
# GIF/WebP go through Lottie pipeline which drops embedded image assets.
# For PNG output, use puppeteer+chromium to render SVG (supports embedded WebP).
MAMOJI_FORMAT = "svg"
MAMOJI_RENDER_SCRIPT = """
import chromium from '@sparticuz/chromium';
import { launch } from 'puppeteer-core';

const execPath = await chromium.executablePath();
const browser = await launch({
  executablePath: execPath,
  headless: true,
  args: [...chromium.args, '--no-sandbox', '--disable-dev-shm-usage'],
});
const page = await browser.newPage();
await page.setViewport({ width: 512, height: 512, deviceScaleFactor: 1 });
const svg = await Bun.file(SVG_PATH).text();
await page.setContent('<html><head><style>*{margin:0;padding:0}body{width:512px;height:512px;overflow:hidden}</style></head><body>' + svg + '</body></html>', { waitUntil: 'networkidle0' });
await new Promise(r => setTimeout(r, 500));
const buffer = await page.screenshot({ type: 'png', omitBackground: false });
await Bun.write(PNG_PATH, buffer);
await browser.close();
console.log('OK', buffer.length, 'bytes');
"""
SAVE_DIR = Path("/tmp/openclaw/mamoji")
SHARP_PATH = None  # auto-detect

# === Emotion → Mamoji mapping ===
# Maps semantic emotions to mamoji body+face+color combinations
EMOTION_MAP = {
    "happy": {
        "body": "soft-pink-sweet-delighted-tender-pleasure",
        "face": "starry",
        "text": "开心",
        "fgcolor": "#c63d79",
        "bgcolor": "#ffe0ec",
        "bgstyle": "halftone",
    },
    "celebrating": {
        "body": "soft-pink-sweet-delighted-tender-pleasure",
        "face": "starry",
        "text": "恭喜",
        "fgcolor": "#ff4fa3",
        "bgcolor": "#ffe8ef",
        "bgstyle": "sunburst",
    },
    "encouraging": {
        "body": "orange-gold-driven-energized-determined-motivation",
        "face": "starry",
        "text": "加油",
        "fgcolor": "#8a5b00",
        "bgcolor": "#fff0c2",
        "bgstyle": "speedlines",
    },
    "sad": {
        "body": "pale-silver-flat-weary-letdown-disappoint",
        "face": "sad",
        "text": "唉",
        "fgcolor": "#4a5e84",
        "bgcolor": "#edf3ff",
        "bgstyle": "halftone",
    },
    "angry": {
        "body": "vivid-red-irritated-fierce-heated-angry",
        "face": "default",
        "text": "生气",
        "fgcolor": "#b12d2d",
        "bgcolor": "#ffe1e1",
        "bgstyle": "sunburst",
    },
    "shock": {
        "body": "salmon-coral-thrilled-amped-eager-excited",
        "face": "starry",
        "text": "啊？",
        "fgcolor": "#b65926",
        "bgcolor": "#ffe7db",
        "bgstyle": "sunburst",
    },
    "curious": {
        "body": "bright-azure-curious-alert-inquisitive-interest",
        "face": "squint",
        "text": "?",
        "fgcolor": "#27528f",
        "bgcolor": "#e1f1ff",
        "bgstyle": "halftone",
    },
    "proud": {
        "body": "lavender-purple-proud-poised-satisfied-pride",
        "face": "starry",
        "text": "不错",
        "fgcolor": "#6842af",
        "bgcolor": "#eee3ff",
        "bgstyle": "sunburst",
    },
    "relief": {
        "body": "light-sky-blue-released-relaxed-unburdened-relief",
        "face": "squint",
        "text": "呼",
        "fgcolor": "#2d6a91",
        "bgcolor": "#e1f7ff",
        "bgstyle": "halftone",
    },
    "ugh": {
        "body": "taupe-brown-repelled-averse-sour-disgust",
        "face": "squint",
        "text": "呃",
        "fgcolor": "#684a34",
        "bgcolor": "#f4e6d9",
        "bgstyle": "halftone",
    },
    "calm": {
        "body": "soft-pink-peach-calm-relaxed-neutral-default-base",
        "face": "default",
        "text": "Hi",
        "fgcolor": "#8f4f67",
        "bgcolor": "#ffe8ef",
        "bgstyle": "halftone",
    },
    "focus": {
        "body": "orange-gold-driven-energized-determined-motivation",
        "face": "default",
        "text": "Working",
        "fgcolor": "#8a5b00",
        "bgcolor": "#fff0c2",
        "bgstyle": "speedlines",
    },
    "done": {
        "body": "mint-green-calm-settled-fulfilled-content",
        "face": "squint",
        "text": "DONE",
        "fgcolor": "#167a58",
        "bgcolor": "#dcfff0",
        "bgstyle": "halftone",
    },
    "thanks": {
        "body": "soft-pink-sweet-delighted-tender-pleasure",
        "face": "starry",
        "text": "谢谢",
        "fgcolor": "#c63d79",
        "bgcolor": "#ffe0ec",
        "bgstyle": "halftone",
    },
    "love": {
        "body": "soft-pink-sweet-delighted-tender-pleasure",
        "face": "starry",
        "text": "❤",
        "fgcolor": "#ff4fa3",
        "bgcolor": "#ffe8ef",
        "bgstyle": "halftone",
    },
    "fear": {
        "body": "deep-indigo-tense-worried-uneasy-fear",
        "face": "sad",
        "text": "慌",
        "fgcolor": "#3a4a7a",
        "bgcolor": "#e8ebff",
        "bgstyle": "halftone",
    },
}

# === All available options ===
THEME_KINDS = [
    "bright-azure-curious-alert-inquisitive-interest",
    "deep-indigo-tense-worried-uneasy-fear",
    "lavender-purple-proud-poised-satisfied-pride",
    "light-sky-blue-released-relaxed-unburdened-relief",
    "mint-green-calm-settled-fulfilled-content",
    "orange-gold-driven-energized-determined-motivation",
    "pale-silver-flat-weary-letdown-disappoint",
    "salmon-coral-thrilled-amped-eager-excited",
    "soft-pink-peach-calm-relaxed-neutral-default-base",
    "soft-pink-sweet-delighted-tender-pleasure",
    "taupe-brown-repelled-averse-sour-disgust",
    "vivid-red-irritated-fierce-heated-angry",
]

FACE_KINDS = ["default", "squint", "starry"]  # AI-allowed faces
ALL_FACES = ["confused", "default", "happy", "motivated", "sad", "speechless", "squint", "starry", "surprised"]

BG_STYLES = ["sunburst", "halftone", "speedlines"]
EFFECTS = ["none", "pop", "float"]


def find_sharp():
    """Find sharp module in node/bun environments"""
    global SHARP_PATH
    if SHARP_PATH:
        return SHARP_PATH
    
    # Try node with mamoji's node_modules
    for node_modules in [
        "/tmp/mamoji/node_modules",
        "/usr/local/lib/node_modules/openclaw/node_modules",
    ]:
        if Path(f"{node_modules}/sharp").exists():
            SHARP_PATH = node_modules
            return SHARP_PATH
    
    # Try bun
    result = subprocess.run(
        ["bun", "-e", "import sharp from 'sharp'; console.log('ok')"],
        capture_output=True, text=True, timeout=5
    )
    if result.returncode == 0:
        SHARP_PATH = "bun"
        return SHARP_PATH
    
    return None


def svg_to_png(svg_path: str, png_path: str) -> bool:
    """Convert SVG to PNG using sharp"""
    sharp_path = find_sharp()
    if not sharp_path:
        print("⚠️  sharp not found, keeping SVG format")
        return False
    
    if sharp_path == "bun":
        script = f"""
import sharp from 'sharp';
await sharp('{svg_path}').png().toFile('{png_path}');
console.log('ok');
"""
        result = subprocess.run(
            ["bun", "-e", script],
            capture_output=True, text=True, timeout=10
        )
    else:
        script = f"""
const sharp = require('{sharp_path}/sharp');
sharp('{svg_path}').png().toFile('{png_path}')
  .then(() => console.log('ok'))
  .catch(e => {{ console.error(e.message); process.exit(1); }});
"""
        result = subprocess.run(
            ["node", "-e", script],
            capture_output=True, text=True, timeout=10
        )
    
    return result.returncode == 0 and "ok" in result.stdout


def svg_to_png_via_chromium(svg_path: str, png_path: str) -> bool:
    """Render SVG to PNG using puppeteer+chromium (supports embedded WebP images)"""
    import subprocess, os
    mamoji_dir = "/tmp/mamoji"
    if not os.path.exists(mamoji_dir):
        print("⚠️  mamoji repo not found at /tmp/mamoji")
        return False
    
    script = MAMOJI_RENDER_SCRIPT.replace("SVG_PATH", repr(svg_path)).replace("PNG_PATH", repr(png_path))
    result = subprocess.run(
        ["bun", "-e", script],
        capture_output=True, text=True, timeout=30,
        cwd=mamoji_dir,
        env={**os.environ, "PATH": os.environ.get("HOME", "/root") + "/.bun/bin:" + os.environ.get("PATH", "")}
    )
    if result.returncode == 0 and "OK" in result.stdout:
        return True
    print(f"⚠️  chromium render failed: {result.stderr[:200]}")
    return False


def render_mamoji(core: dict) -> Path:
    """Call mamoji render API, return path to saved file"""
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    
    text_slug = core.get("text", "mamoji").replace("/", "_")[:20]
    
    # Always get SVG from the API (contains macaron body correctly)
    data = json.dumps(core).encode("utf-8")
    req = urllib.request.Request(
        MAMOJI_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        svg_data = resp.read()
    
    svg_path = SAVE_DIR / f"{text_slug}.svg"
    svg_path.write_bytes(svg_data)
    
    # Convert to PNG via chromium (supports embedded WebP body image)
    png_path = SAVE_DIR / f"{text_slug}.png"
    if svg_to_png_via_chromium(str(svg_path), str(png_path)):
        return png_path
    return svg_path


def cmd_generate(emotion: str, text: str = ""):
    """Generate sticker by emotion keyword"""
    if emotion not in EMOTION_MAP:
        print(f"❌ 未知情绪: {emotion}")
        print(f"   可用: {', '.join(sorted(EMOTION_MAP.keys()))}")
        return None
    
    config = EMOTION_MAP[emotion].copy()
    if text:
        config["text"] = text
    
    # Ensure required fields
    core = {
        "body": config["body"],
        "face": config["face"],
        "text": config["text"],
        "fgcolor": config["fgcolor"],
        "bgcolor": config["bgcolor"],
        "effect": "pop",
    }
    if "bgstyle" in config:
        core["bgstyle"] = config["bgstyle"]
    
    path = render_mamoji(core)
    print(f"✅ 已生成: {path} ({path.stat().st_size} bytes) [mamoji:{emotion}]")
    return path


def cmd_custom(body: str, face: str, text: str, fg: str = "#ff4fa3", bg: str = "#ffe8ef"):
    """Generate sticker with custom parameters"""
    core = {
        "body": body,
        "face": face,
        "text": text,
        "fgcolor": fg,
        "bgcolor": bg,
        "effect": "pop",
    }
    path = render_mamoji(core)
    print(f"✅ 已生成: {path} ({path.stat().st_size} bytes) [mamoji:custom]")
    return path


def cmd_list():
    """List all available options"""
    print("🎨 Mamoji 预设\n")
    print("情绪预设 (generate):")
    for k, v in sorted(EMOTION_MAP.items()):
        print(f"  {k:15s} → {v['text']:6s}  body={v['body'][:30]}...  face={v['face']}")
    print(f"\nBody 主题 ({len(THEME_KINDS)}):")
    for t in THEME_KINDS:
        print(f"  {t}")
    print(f"\nFace 表情 (AI: {len(FACE_KINDS)} / 全部: {len(ALL_FACES)}):")
    print(f"  AI允许: {', '.join(FACE_KINDS)}")
    print(f"  全部:   {', '.join(ALL_FACES)}")
    print(f"\n背景风格: {', '.join(BG_STYLES)}")
    print(f"动效: {', '.join(EFFECTS)}")


def cmd_send(emotion: str, text: str = "", chat_id: str = ""):
    """Generate + output JSON for programmatic use"""
    path = cmd_generate(emotion, text)
    if path:
        print(json.dumps({"ok": True, "path": str(path), "emotion": emotion, "chat_id": chat_id}))
    else:
        print(json.dumps({"ok": False, "error": f"unknown emotion: {emotion}"}))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "generate":
        emotion = sys.argv[2] if len(sys.argv) > 2 else ""
        text = sys.argv[3] if len(sys.argv) > 3 else ""
        if not emotion:
            print("❌ 请提供情绪关键词")
            sys.exit(1)
        cmd_generate(emotion, text)

    elif cmd == "custom":
        if len(sys.argv) < 5:
            print("❌ 用法: custom <body> <face> <text> [fgcolor] [bgcolor]")
            sys.exit(1)
        body = sys.argv[2]
        face = sys.argv[3]
        text = sys.argv[4]
        fg = sys.argv[5] if len(sys.argv) > 5 else "#ff4fa3"
        bg = sys.argv[6] if len(sys.argv) > 6 else "#ffe8ef"
        cmd_custom(body, face, text, fg, bg)

    elif cmd == "list":
        cmd_list()

    elif cmd == "send":
        emotion = sys.argv[2] if len(sys.argv) > 2 else ""
        text = sys.argv[3] if len(sys.argv) > 3 else ""
        chat_id = sys.argv[4] if len(sys.argv) > 4 else ""
        if not emotion:
            print("❌ 请提供情绪关键词")
            sys.exit(1)
        cmd_send(emotion, text, chat_id)

    else:
        print(f"❌ 未知命令: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
