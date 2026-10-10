#!/usr/bin/env python3
"""Helper CLI for the lam-video-huong-dan skill. Standard library only.

Commands:
  channels                      list configured channels (never prints the API key)
  check [--online]              verify settings, tools and (with --online) the OpenRouter key
  init <dir>                    create a video project skeleton
  theme --accent "#RRGGBB"      derive the full colour theme from one brand accent
  logo <brand-or-domain>        download real logo candidates and record their sources
  tts                           synthesise one piece of narration
  tts-script                    synthesise every scene of script.json and write the timing manifest
  voices                        list speech models available on OpenRouter
"""
from __future__ import annotations

import argparse
import colorsys
import hashlib
import html.parser
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import wave
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
SETTINGS_PATH = SKILL_DIR / "settings.json"
USER_AGENT = "lam-video-huong-dan/0.1 (+https://github.com/Agoobi/skills-hubs)"
DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_TTS_MODEL = "google/gemini-3.1-flash-tts-preview"
FORMATS = {
    "short": {"width": 1080, "height": 1920, "fps": 30, "gap": 0.15, "chapter_hold": 0.0},
    "long": {"width": 1920, "height": 1080, "fps": 30, "gap": 0.3, "chapter_hold": 2.8},
}

for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="replace")


def die(message: str, code: int = 1) -> "None":
    print(f"LỖI: {message}", file=sys.stderr)
    raise SystemExit(code)


# ---------------------------------------------------------------- settings

def load_settings() -> dict:
    if not SETTINGS_PATH.exists():
        die(
            "Chưa có settings.json. Copy settings.example.json thành settings.json "
            "trong thư mục skill rồi điền openrouter.api_key và các kênh."
        )
    try:
        return json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        die(f"settings.json không phải JSON hợp lệ: {error}")


def api_key(settings: dict) -> str:
    key = os.environ.get("OPENROUTER_API_KEY") or settings.get("openrouter", {}).get("api_key", "")
    if not key or "DAN_KEY" in key:
        die("Thiếu OpenRouter API key (settings.json > openrouter.api_key hoặc biến OPENROUTER_API_KEY).")
    return key


def mask(key: str) -> str:
    return f"{key[:9]}…{key[-4:]}" if len(key) > 16 else "…"


def channel(settings: dict, alias: str | None) -> tuple[str, dict]:
    channels = settings.get("channels", {})
    alias = alias or settings.get("default_channel")
    if not alias or alias not in channels:
        die(f"Không có kênh '{alias}'. Các kênh hiện có: {', '.join(channels) or '(trống)'}")
    return alias, channels[alias]


# ---------------------------------------------------------------- http

def http(url: str, *, method: str = "GET", headers: dict | None = None, body: bytes | None = None,
         timeout: int = 120) -> tuple[int, dict, bytes]:
    request = urllib.request.Request(url, data=body, method=method)
    request.add_header("User-Agent", USER_AGENT)
    for name, value in (headers or {}).items():
        request.add_header(name, value)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, dict(response.headers), response.read()
    except urllib.error.HTTPError as error:
        return error.code, dict(error.headers or {}), error.read()
    except urllib.error.URLError as error:
        die(f"Không kết nối được {urllib.parse.urlsplit(url).netloc}: {error.reason}")


# ---------------------------------------------------------------- commands: channels / check / init

def cmd_channels(args: argparse.Namespace) -> None:
    settings = load_settings()
    default = settings.get("default_channel")
    rows = []
    for alias, cfg in settings.get("channels", {}).items():
        rows.append({
            "alias": alias,
            "default": alias == default,
            "label": cfg.get("label", ""),
            "platforms": cfg.get("platforms", []),
            "language": cfg.get("language", "vi"),
            "default_format": cfg.get("default_format", ""),
            "voice": cfg.get("voice", ""),
            "accent": cfg.get("accent", ""),
        })
    print(json.dumps({"channels": rows}, ensure_ascii=False, indent=2))


def tool_version(command: list[str]) -> str | None:
    executable = shutil.which(command[0])
    if not executable:
        return None
    try:
        out = subprocess.run([executable, *command[1:]], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    text = (out.stdout or out.stderr).strip().splitlines()
    return text[0][:80] if text else "ok"


def cmd_check(args: argparse.Namespace) -> None:
    settings = load_settings()
    report: dict = {"settings": str(SETTINGS_PATH), "ok": True, "problems": []}
    key = os.environ.get("OPENROUTER_API_KEY") or settings.get("openrouter", {}).get("api_key", "")
    report["openrouter_key"] = mask(key) if key and "DAN_KEY" not in key else None
    if not report["openrouter_key"]:
        report["problems"].append("Thiếu OpenRouter API key.")
    report["tts_model"] = settings.get("openrouter", {}).get("tts_model", DEFAULT_TTS_MODEL)
    channels = settings.get("channels", {})
    report["channels"] = list(channels)
    if not channels:
        report["problems"].append("Chưa có kênh nào trong settings.json > channels.")
    if settings.get("default_channel") not in channels:
        report["problems"].append("default_channel không trỏ tới kênh nào.")
    for alias, cfg in channels.items():
        for field in ("label", "language", "voice", "persona", "cta"):
            if not cfg.get(field):
                report["problems"].append(f"Kênh '{alias}' thiếu '{field}'.")
    report["tools"] = {
        "python": sys.version.split()[0],
        "node": tool_version(["node", "--version"]),
        "ffmpeg": tool_version(["ffmpeg", "-version"]),
        "ffprobe": tool_version(["ffprobe", "-version"]),
    }
    for name in ("node", "ffmpeg", "ffprobe"):
        if not report["tools"][name]:
            report["problems"].append(f"Không tìm thấy '{name}' trong PATH.")
    if args.online and report["openrouter_key"]:
        base = settings.get("openrouter", {}).get("base_url", DEFAULT_BASE_URL)
        status, _, body = http(f"{base}/key", headers={"Authorization": f"Bearer {key}"}, timeout=30)
        if status == 200:
            data = json.loads(body).get("data", {})
            report["openrouter_online"] = {
                "ok": True,
                "usage_usd": data.get("usage"),
                "limit_usd": data.get("limit"),
                "limit_remaining_usd": data.get("limit_remaining"),
            }
        else:
            report["openrouter_online"] = {"ok": False, "status": status}
            report["problems"].append(f"OpenRouter từ chối key (HTTP {status}).")
    report["ok"] = not report["problems"]
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["ok"]:
        raise SystemExit(1)


def cmd_init(args: argparse.Namespace) -> None:
    settings = load_settings()
    alias, cfg = channel(settings, args.channel)
    fmt = args.format or cfg.get("default_format")
    if fmt not in FORMATS:
        die("Cần --format short hoặc long (hoặc đặt default_format cho kênh).")
    root = Path(args.dir).resolve()
    for sub in ("assets/logos", "assets/fonts", "captures", "audio", "renders"):
        (root / sub).mkdir(parents=True, exist_ok=True)
    project = {"channel": alias, "format": fmt, **{k: FORMATS[fmt][k] for k in ("width", "height", "fps")},
               "language": cfg.get("language", "vi"), "created": time.strftime("%Y-%m-%d")}
    project_file = root / "project.json"
    if project_file.exists() and not args.force:
        die(f"{project_file} đã tồn tại. Thêm --force để ghi đè.")
    project_file.write_text(json.dumps(project, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ledger = root / "assets" / "ledger.json"
    if not ledger.exists():
        ledger.write_text("[]\n", encoding="utf-8")
    print(json.dumps({"project": str(root), **project}, ensure_ascii=False, indent=2))


# ---------------------------------------------------------------- theme

def hex_to_rgb(value: str) -> tuple[float, float, float]:
    value = value.strip().lstrip("#")
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    if not re.fullmatch(r"[0-9a-fA-F]{6}", value):
        die(f"Màu không hợp lệ: #{value}")
    return tuple(int(value[i:i + 2], 16) / 255 for i in (0, 2, 4))  # type: ignore[return-value]


def rgb_to_hex(rgb: tuple[float, float, float]) -> str:
    return "#" + "".join(f"{round(max(0, min(1, c)) * 255):02X}" for c in rgb)


def hsl(hue: float, saturation: float, lightness: float) -> str:
    return rgb_to_hex(colorsys.hls_to_rgb(hue, lightness, saturation))


def mix(a: tuple[float, float, float], b: tuple[float, float, float], amount: float) -> str:
    return rgb_to_hex(tuple(x + (y - x) * amount for x, y in zip(a, b)))  # type: ignore[arg-type]


def build_theme(accent_hex: str) -> dict:
    """Ratios below reproduce the measured Metics Media palette when given their coral accent."""
    accent = hex_to_rgb(accent_hex)
    hue, _lightness, saturation = colorsys.rgb_to_hls(*accent)
    white = (1.0, 1.0, 1.0)
    # Near-grey accents get neutral surfaces instead of a tinted wash.
    tint = min(1.0, saturation / 0.5)
    return {
        "accent": rgb_to_hex(accent),
        "accent-soft": mix(white, accent, 0.72),
        "canvas": hsl(hue, 0.30 * tint, 0.975),
        "canvas-glow": mix(white, accent, 0.33),
        "card": hsl(hue, 0.40 * tint, 0.988),
        "card-tile": hsl(hue, 0.22 * tint, 0.91),
        "ink": hsl(hue, 0.10 * tint, 0.10),
        "ink-soft": hsl(hue, 0.05 * tint, 0.40),
        "chapter-bg": hsl(hue, 0.37 * tint, 0.075),
        "chapter-glow": hsl(hue, 0.48 * tint, 0.44),
        "chapter-numeral": hsl(hue, 0.37 * tint, 0.12),
        "chapter-label": hsl(hue, 0.25 * tint, 0.60),
        "chapter-title": "#FEFCFB",
        "chapter-title-dim": hsl(hue, 0.26 * tint, 0.35),
        "screen-bg": "#141414",
    }


def cmd_theme(args: argparse.Namespace) -> None:
    theme = build_theme(args.accent)
    css = ":root {\n" + "".join(f"  --{name}: {value};\n" for name, value in theme.items()) + "}\n"
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(css, encoding="utf-8")
        out.with_suffix(".json").write_text(json.dumps(theme, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"theme": theme, "css": str(args.out) if args.out else None}, indent=2))


# ---------------------------------------------------------------- logo

class HeadParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.candidates: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k: (v or "") for k, v in attrs}
        if tag == "link" and "icon" in a.get("rel", "").lower() and a.get("href"):
            self.candidates.append((a["rel"].lower(), a["href"]))
        if tag == "img":
            hint = " ".join(a.get(k, "") for k in ("src", "alt", "class", "id")).lower()
            if "logo" in hint and a.get("src") and not a["src"].startswith("data:"):
                self.candidates.append(("img-logo", a["src"]))


def record(ledger_path: Path, entry: dict) -> None:
    entries = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.exists() else []
    entries = [e for e in entries if e.get("file") != entry["file"]] + [entry]
    ledger_path.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def save_asset(url: str, out_dir: Path, name: str, kind: str, ledger_path: Path) -> dict | None:
    status, headers, body = http(url, timeout=40)
    content_type = headers.get("Content-Type", headers.get("content-type", "")).split(";")[0].strip().lower()
    if status != 200 or not body:
        return None
    extension = {"image/svg+xml": "svg", "image/png": "png", "image/jpeg": "jpg", "image/webp": "webp",
                 "image/x-icon": "ico", "image/vnd.microsoft.icon": "ico", "image/gif": "gif"}.get(content_type)
    if not extension:
        if body.lstrip()[:5].lower() in (b"<svg ", b"<?xml"):
            extension = "svg"
        else:
            return None
    file = out_dir / f"{name}.{extension}"
    file.write_bytes(body)
    entry = {"file": str(file.relative_to(ledger_path.parent.parent)).replace("\\", "/"), "kind": kind,
             "source": url, "bytes": len(body), "fetched": time.strftime("%Y-%m-%dT%H:%M:%S")}
    record(ledger_path, entry)
    return entry


def cmd_logo(args: argparse.Namespace) -> None:
    query = args.brand.strip()
    is_domain = "." in query and " " not in query
    domain = re.sub(r"^https?://", "", query).split("/")[0] if is_domain else None
    brand = (domain.split(".")[-2] if domain and domain.count(".") >= 1 else query).lower()
    slug = re.sub(r"[^a-z0-9]+", "", brand)
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = out_dir.parent / "ledger.json"
    found: list[dict] = []

    status, _, body = http(f"https://api.svgl.app?search={urllib.parse.quote(brand)}", timeout=30)
    if status == 200:
        try:
            items = json.loads(body)
        except json.JSONDecodeError:
            items = []
        for index, item in enumerate(items[:3] if isinstance(items, list) else []):
            routes = item.get("route")
            routes = routes if isinstance(routes, dict) else {"default": routes}
            for variant, route in routes.items():
                if isinstance(route, str):
                    title = re.sub(r"[^a-z0-9]+", "-", item.get("title", brand).lower()).strip("-")
                    entry = save_asset(route, out_dir, f"{title}-svgl-{variant}", "logo", ledger_path)
                    if entry:
                        found.append({**entry, "title": item.get("title"), "brand_url": item.get("url")})

    entry = save_asset(f"https://cdn.simpleicons.org/{slug}", out_dir, f"{slug}-simpleicons", "logo-mono", ledger_path)
    if entry:
        found.append(entry)

    if domain:
        status, _, body = http(f"https://{domain}/", timeout=40,
                               headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                                                      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"})
        if status == 200:
            parser = HeadParser()
            parser.feed(body.decode("utf-8", errors="replace"))
            seen: set[str] = set()
            ranked = sorted(parser.candidates, key=lambda c: (0 if "apple" in c[0] else 1 if c[0] == "img-logo" else 2))
            for index, (rel, href) in enumerate(ranked):
                url = urllib.parse.urljoin(f"https://{domain}/", href)
                if url in seen or len(seen) >= 6:
                    continue
                seen.add(url)
                kind = "logo-site" if rel == "img-logo" else "icon-site"
                entry = save_asset(url, out_dir, f"{slug}-site-{len(seen)}", kind, ledger_path)
                if entry:
                    found.append({**entry, "rel": rel})

    print(json.dumps({"brand": brand, "candidates": found, "ledger": str(ledger_path),
                      "next": "Mở từng file ra xem, chọn bản đúng. Không có bản đạt thì hỏi người dùng xin file; không vẽ lại."},
                     ensure_ascii=False, indent=2))
    if not found:
        raise SystemExit(2)


# ---------------------------------------------------------------- tts

def pcm_to_wav(pcm: bytes, sample_rate: int, channels: int) -> bytes:
    block = channels * 2
    header = b"RIFF" + struct.pack("<I", 36 + len(pcm)) + b"WAVEfmt " + struct.pack(
        "<IHHIIHH", 16, 1, channels, sample_rate, sample_rate * block, block, 16) + b"data" + struct.pack("<I", len(pcm))
    return header + pcm


def audio_duration(path: Path) -> float:
    if path.suffix == ".wav":
        with wave.open(str(path), "rb") as handle:
            return handle.getnframes() / handle.getframerate()
    probe = shutil.which("ffprobe")
    if not probe:
        die("Cần ffprobe để đo thời lượng file mp3.")
    out = subprocess.run([probe, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, timeout=60)
    return float(out.stdout.strip())


def synthesize(settings: dict, cfg: dict, text: str, out_base: Path, *, voice: str | None = None,
               style: str | None = None, speed: float | None = None) -> dict:
    openrouter = settings.get("openrouter", {})
    model = cfg.get("tts_model") or openrouter.get("tts_model", DEFAULT_TTS_MODEL)
    voice = voice or cfg.get("voice") or "Kore"
    style = style if style is not None else cfg.get("voice_style", "")
    speed = speed if speed is not None else cfg.get("speed")
    # Gemini speech models take delivery direction as a natural-language lead-in to the text.
    spoken = f"{style.strip()}: {text.strip()}" if style and style.strip() else text.strip()
    payload: dict = {"model": model, "input": spoken, "voice": voice,
                     "response_format": openrouter.get("response_format", "pcm")}
    if speed and abs(float(speed) - 1.0) > 1e-6:
        payload["speed"] = float(speed)
    last_error = ""
    for attempt in range(3):
        status, headers, body = http(
            f"{openrouter.get('base_url', DEFAULT_BASE_URL)}/audio/speech", method="POST",
            headers={"Authorization": f"Bearer {api_key(settings)}", "Content-Type": "application/json",
                     "X-Title": "lam-video-huong-dan"},
            body=json.dumps(payload).encode("utf-8"), timeout=300)
        if status == 200 and body:
            break
        last_error = f"HTTP {status}: {body[:300].decode('utf-8', errors='replace')}"
        if status in (400, 401, 402, 403, 404):
            die(f"OpenRouter TTS từ chối yêu cầu. {last_error}")
        time.sleep(2 * (attempt + 1))
    else:
        die(f"OpenRouter TTS lỗi sau 3 lần thử. {last_error}")
    content_type = headers.get("Content-Type", headers.get("content-type", "")).lower()
    out_base.parent.mkdir(parents=True, exist_ok=True)
    if "audio/pcm" in content_type or "l16" in content_type:
        rate = int((re.search(r"rate=(\d+)", content_type) or [None, "24000"])[1])
        channels = int((re.search(r"channels=(\d+)", content_type) or [None, "1"])[1])
        out = out_base.with_suffix(".wav")
        out.write_bytes(pcm_to_wav(body, rate, channels))
    elif "wav" in content_type:
        out = out_base.with_suffix(".wav")
        out.write_bytes(body)
    else:
        out = out_base.with_suffix(".mp3")
        out.write_bytes(body)
    return {"file": str(out), "duration": round(audio_duration(out), 3), "model": model, "voice": voice,
            "style": style or "", "chars": len(text)}


def cmd_tts(args: argparse.Namespace) -> None:
    settings = load_settings()
    _, cfg = channel(settings, args.channel)
    text = args.text or (Path(args.text_file).read_text(encoding="utf-8") if args.text_file else "")
    if not text.strip():
        die('Cần --text "..." hoặc --text-file <file>.')
    result = synthesize(settings, cfg, text, Path(args.out).with_suffix(""), voice=args.voice, style=args.style,
                        speed=args.speed)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_tts_script(args: argparse.Namespace) -> None:
    settings = load_settings()
    script_path = Path(args.script).resolve()
    script = json.loads(script_path.read_text(encoding="utf-8"))
    alias, cfg = channel(settings, args.channel or script.get("channel"))
    fmt = script.get("format")
    if fmt not in FORMATS:
        die("script.json cần 'format' là short hoặc long.")
    out_dir = Path(args.out_dir).resolve() if args.out_dir else script_path.parent / "audio"
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "manifest.json"
    previous = {}
    if manifest_path.exists():
        previous = {s["id"]: s for s in json.loads(manifest_path.read_text(encoding="utf-8")).get("scenes", [])}
    gap = float(script.get("gap", FORMATS[fmt]["gap"]))
    voice = args.voice or script.get("voice") or cfg.get("voice")
    openrouter = settings.get("openrouter", {})
    model = cfg.get("tts_model") or openrouter.get("tts_model", DEFAULT_TTS_MODEL)
    cursor, scenes, generated, reused = 0.0, [], 0, 0
    ids = [scene.get("id") for scene in script.get("scenes", [])]
    if len(ids) != len(set(ids)) or not all(ids):
        die("Mỗi cảnh trong script.json cần một 'id' duy nhất.")
    for scene in script["scenes"]:
        text = (scene.get("vo") or "").strip()
        entry: dict = {"id": scene["id"], "kind": scene.get("kind", ""), "text": text}
        if text:
            digest = hashlib.sha256(json.dumps(
                [text, voice, model, cfg.get("voice_style", ""), cfg.get("speed")], ensure_ascii=False).encode()).hexdigest()[:16]
            old = previous.get(scene["id"])
            if old and old.get("hash") == digest and old.get("file") and (out_dir / old["file"]).exists() and not args.force:
                entry.update(file=old["file"], duration=old["duration"], hash=digest)
                reused += 1
            else:
                result = synthesize(settings, cfg, text, out_dir / scene["id"], voice=voice)
                entry.update(file=Path(result["file"]).name, duration=result["duration"], hash=digest)
                generated += 1
                print(f"  {scene['id']}: {result['duration']}s", file=sys.stderr)
            length = entry["duration"] + float(scene.get("pad", 0))
        else:
            length = float(scene.get("hold", FORMATS[fmt]["chapter_hold"] or 2.0))
            entry.update(file=None, duration=0.0)
        entry.update(start=round(cursor, 3), end=round(cursor + length, 3))
        cursor += length + gap
        scenes.append(entry)
    total = round(max(0.0, cursor - gap), 3)
    manifest = {"channel": alias, "format": fmt, "voice": voice, "model": model, "gap": gap, "total": total,
                "scenes": scenes}
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    words = sum(len(s["text"].split()) for s in scenes)
    spoken = sum(s["duration"] for s in scenes)
    print(json.dumps({"manifest": str(manifest_path), "total_seconds": total, "generated": generated,
                      "reused": reused, "words": words,
                      "words_per_minute": round(words / spoken * 60) if spoken else 0}, ensure_ascii=False, indent=2))


def cmd_voices(args: argparse.Namespace) -> None:
    settings = load_settings()
    base = settings.get("openrouter", {}).get("base_url", DEFAULT_BASE_URL)
    status, _, body = http(f"{base}/models?output_modalities=speech", timeout=40)
    if status != 200:
        die(f"Không lấy được danh sách model (HTTP {status}).")
    models = [{"id": m.get("id"), "name": m.get("name")} for m in json.loads(body).get("data", [])]
    print(json.dumps({"speech_models": models,
                      "current": settings.get("openrouter", {}).get("tts_model", DEFAULT_TTS_MODEL)},
                     ensure_ascii=False, indent=2))


# ---------------------------------------------------------------- cli

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("channels").set_defaults(run=cmd_channels)

    p = sub.add_parser("check")
    p.add_argument("--online", action="store_true")
    p.set_defaults(run=cmd_check)

    p = sub.add_parser("init")
    p.add_argument("dir")
    p.add_argument("--channel")
    p.add_argument("--format", choices=list(FORMATS))
    p.add_argument("--force", action="store_true")
    p.set_defaults(run=cmd_init)

    p = sub.add_parser("theme")
    p.add_argument("--accent", required=True)
    p.add_argument("--out")
    p.set_defaults(run=cmd_theme)

    p = sub.add_parser("logo")
    p.add_argument("brand")
    p.add_argument("--out", required=True)
    p.set_defaults(run=cmd_logo)

    p = sub.add_parser("tts")
    p.add_argument("--channel")
    p.add_argument("--text")
    p.add_argument("--text-file")
    p.add_argument("--out", required=True)
    p.add_argument("--voice")
    p.add_argument("--style")
    p.add_argument("--speed", type=float)
    p.set_defaults(run=cmd_tts)

    p = sub.add_parser("tts-script")
    p.add_argument("--script", required=True)
    p.add_argument("--channel")
    p.add_argument("--out-dir")
    p.add_argument("--voice")
    p.add_argument("--force", action="store_true")
    p.set_defaults(run=cmd_tts_script)

    sub.add_parser("voices").set_defaults(run=cmd_voices)

    args = parser.parse_args()
    args.run(args)


if __name__ == "__main__":
    main()
