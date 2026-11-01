#!/usr/bin/env python3
"""Turn a raw recording into a HyperFrames project with a presenter character.

Commands (run from the skill folder):
  check                       settings, tools, keys
  init <name> --raw <file>    create tmp/<name>/ with project.json, plan.json, package.json
  analyze <project>           silences, still spans, scene changes, contact sheets
  frame <project> <seconds>   one full-size frame, to measure a zoom or highlight
  transcribe <project>        Vietnamese transcript with word timings (faster-whisper)
  tts <project>               read every beat's `vo` (cached by text, only changed lines are billed)
  cut <project>               clips, freeze frames, audio, mouth data, timeline.json, decisions.md
"""
from __future__ import annotations

import argparse
import array
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
SETTINGS_PATH = SKILL_DIR / "settings.json"
TMP_DIR = SKILL_DIR / "tmp"
TEMPLATES = SKILL_DIR / "templates"

FPS = 30
MAX_CLIP_WIDTH = 2560  # keeps text sharp under a 2.6x zoom without carrying 4K through the render
MOUTH_RATE = 15
LEAD_PAUSE = 0.75  # stage shrinks and the presenter walks in before the first word
TAIL_PAUSE = 0.75  # presenter leaves and the stage grows back after the last word
LEAD_PLAY = 0.12
TAIL_PLAY = 0.3
SPEED_MIN = 0.8
SPEED_MAX = 6.0
SPEED_BADGE = 1.3  # any faster than this is shown on screen, never hidden
RAW_UNDER_VO = 0.16  # volume of the recorded sound when a voice reads over it
VIENEU_PREFIX = "vieneu:"
DEFAULT_VIENEU_URL = "https://api.vieneu.io/api/v1"
DEFAULT_OPENROUTER_URL = "https://openrouter.ai/api/v1"
DEFAULT_TTS_MODEL = "google/gemini-3.1-flash-tts-preview"


def die(message: str, code: int = 1) -> "None":
    print(message, file=sys.stderr)
    raise SystemExit(code)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_settings() -> dict:
    return read_json(SETTINGS_PATH) if SETTINGS_PATH.exists() else {}


def run(cmd: list[str], *, check: bool = True, binary: bool = False, timeout: int = 7200) -> subprocess.CompletedProcess:
    done = subprocess.run(cmd, capture_output=True, text=not binary, encoding=None if binary else "utf-8",
                          errors=None if binary else "replace", timeout=timeout)
    if check and done.returncode != 0:
        tail = done.stderr[-600:] if isinstance(done.stderr, str) else done.stderr[-600:].decode("utf-8", "replace")
        die(f"{Path(cmd[0]).name} lỗi: {tail.strip()}")
    return done


def ffmpeg(*args: str) -> None:
    run(["ffmpeg", "-y", "-v", "error", *args])


def probe(path: Path) -> dict:
    done = run(["ffprobe", "-v", "error", "-show_entries",
                "stream=codec_type,width,height,avg_frame_rate:stream_tags=rotate:stream_side_data=rotation:format=duration",
                "-of", "json", str(path)])
    info = json.loads(done.stdout)
    video = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), None)
    has_audio = any(s.get("codec_type") == "audio" for s in info.get("streams", []))
    result = {"duration": round(float(info.get("format", {}).get("duration", 0)), 3), "has_audio": has_audio}
    if video:
        width, height = int(video["width"]), int(video["height"])
        rotation = int(video.get("tags", {}).get("rotate", 0) or 0)
        for side in video.get("side_data_list", []):
            rotation = int(side.get("rotation", rotation) or rotation)
        if abs(rotation) % 180 == 90:  # phones store portrait video as landscape plus a flag
            width, height = height, width
        num, _, den = video.get("avg_frame_rate", "0/1").partition("/")
        fps = float(num) / float(den or 1) if float(den or 1) else 0.0
        result.update(width=width, height=height, fps=round(fps, 3))
    return result


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFD", value.replace("đ", "d").replace("Đ", "D"))
    value = "".join(c for c in value if unicodedata.category(c) != "Mn").lower()
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-") or "video"


def load_project(path: str) -> tuple[Path, dict]:
    root = Path(path)
    if not (root / "project.json").exists():
        root = TMP_DIR / path
    if not (root / "project.json").exists():
        die(f"Không thấy project.json trong {path}. Chạy init trước.")
    return root.resolve(), read_json(root / "project.json")


# --- check / init -----------------------------------------------------------------------------

def cmd_check(args: argparse.Namespace) -> None:
    settings = load_settings()
    report: dict = {"settings": SETTINGS_PATH.exists(), "tools": {}, "problems": []}
    for tool in ("ffmpeg", "ffprobe", "node", "npm"):
        report["tools"][tool] = bool(shutil.which(tool))
        if not report["tools"][tool]:
            report["problems"].append(f"Thiếu {tool}.")
    try:
        import faster_whisper  # noqa: F401
        report["tools"]["faster_whisper"] = True
    except ImportError:
        report["tools"]["faster_whisper"] = False
        report["problems"].append("Thiếu faster-whisper (pip install faster-whisper), cần cho lệnh transcribe.")
    voice = str(settings.get("voice", ""))
    if voice.startswith(VIENEU_PREFIX):
        if not (os.environ.get("VIENEU_API_KEY") or usable(settings.get("vieneu", {}).get("api_key"))):
            report["problems"].append("Giọng vieneu: nhưng thiếu VieNeu API key.")
    elif voice and not (os.environ.get("OPENROUTER_API_KEY") or usable(settings.get("openrouter", {}).get("api_key"))):
        report["problems"].append("Thiếu OpenRouter API key cho giọng đọc.")
    if not voice:
        report["problems"].append("Chưa chọn `voice`. Không có giọng AI thì chỉ dùng được giọng thu sẵn (voFile).")
    print(json.dumps(report, ensure_ascii=False, indent=2))


def usable(key: str | None) -> bool:
    return bool(key) and "DAN_KEY" not in key


def cmd_init(args: argparse.Namespace) -> None:
    raw = Path(args.raw).expanduser().resolve()
    if not raw.exists():
        die(f"Không thấy file thô: {raw}")
    settings = load_settings()
    info = probe(raw)
    if "width" not in info:
        die("File không có hình.")
    landscape = info["width"] >= info["height"]
    fmt = args.format or ("16:9" if landscape else "9:16")
    root = TMP_DIR / slugify(args.name)
    if (root / "project.json").exists() and not args.force:
        die(f"Dự án đã có: {root}. Dùng --force để tạo lại phần khung (plan.json được giữ).")
    for sub in ("assets/overlays", "audio", "analysis"):
        (root / sub).mkdir(parents=True, exist_ok=True)
    write_json(root / "project.json", {"name": args.name, "raw": str(raw), "format": fmt, "source": info,
                                       "presenter": settings.get("presenter", {}), "theme": settings.get("theme", {})})
    if not (root / "plan.json").exists():
        write_json(root / "plan.json", {"captions": True, "music": None, "blur": [], "beats": []})
    for name in ("package.json", "hyperframes.json"):
        shutil.copy(TEMPLATES / name, root / name)
    write_json(root / "meta.json", {"id": root.name, "name": args.name, "createdAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
    print(json.dumps({"project": str(root), "format": fmt, **info}, ensure_ascii=False, indent=2))


# --- analyze / transcribe ---------------------------------------------------------------------

def spans(log: str, start: str, end: str) -> list[list[float]]:
    found, current = [], None
    for match in re.finditer(rf"({start}|{end})[:=]\s*([\d.]+)", log):
        if match.group(1) == start:
            current = float(match.group(2))
        elif current is not None:
            found.append([round(current, 2), round(float(match.group(2)), 2)])
            current = None
    return found


def font_option() -> str:
    """Windows ffmpeg builds have no fontconfig, so drawtext needs an explicit font file."""
    for path in ("C:/Windows/Fonts/arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if Path(path).exists():
            return "fontfile='" + path.replace(":", "\\:") + "':"
    return ""


def cmd_analyze(args: argparse.Namespace) -> None:
    root, project = load_project(args.project)
    raw, src = project["raw"], project["source"]
    out = root / "analysis"
    result: dict = {"duration": src["duration"], "width": src["width"], "height": src["height"], "has_audio": src["has_audio"]}
    if src["has_audio"]:
        log = run(["ffmpeg", "-hide_banner", "-nostats", "-vn", "-i", raw, "-af", f"silencedetect=noise={args.noise}dB:d={args.silence}",
                   "-f", "null", "-"], check=False).stderr
        result["silences"] = spans(log, "silence_start", "silence_end")
    # One light copy, so a long 4K recording is decoded once rather than once per analysis.
    proxy = out / "proxy.mp4"
    if not proxy.exists():
        ffmpeg("-hwaccel", "auto", "-i", raw, "-an", "-vf", "fps=5,scale=480:-2", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "30", str(proxy))
    # Screen recordings sit still while the speaker waits or thinks: those spans are the natural cuts.
    log = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(proxy), "-vf", f"freezedetect=n=0.003:d={args.still}",
               "-f", "null", "-"], check=False).stderr
    result["still_spans"] = spans(log, "freeze_start", "freeze_end")
    log = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(proxy), "-vf", "select='gt(scene,0.3)',showinfo",
               "-f", "null", "-"], check=False).stderr
    result["scene_changes"] = [round(float(m), 2) for m in re.findall(r"pts_time:([\d.]+)", log)]
    step = args.step or max(2.0, round(src["duration"] / 96, 1))
    for old in out.glob("sheet-*.jpg"):
        old.unlink()
    tile = "drawtext=" + font_option() + "text='%{pts\\:hms}':x=8:y=8:fontsize=26:fontcolor=white:box=1:boxcolor=black@0.7:boxborderw=6"
    size = "scale=480:-2" if src["width"] >= src["height"] else "scale=270:-2"
    sheets = run(["ffmpeg", "-y", "-v", "error", "-i", str(proxy), "-vf", f"fps=1/{step},{tile},{size},tile=4x4:padding=4",
                  "-q:v", "4", str(out / "sheet-%02d.jpg")], check=False)
    if sheets.returncode != 0:  # ffmpeg built without a usable font: sheets without timestamps
        ffmpeg("-i", str(proxy), "-vf", f"fps=1/{step},{size},tile=4x4:padding=4", "-q:v", "4", str(out / "sheet-%02d.jpg"))
        result["sheet_timestamps"] = False
    result["sheets"] = sorted(p.name for p in out.glob("sheet-*.jpg"))
    result["sheet_step"] = step
    write_json(out / "analysis.json", result)
    print(json.dumps({k: (len(v) if isinstance(v, list) else v) for k, v in result.items()}, ensure_ascii=False, indent=2))


def cmd_frame(args: argparse.Namespace) -> None:
    """One full-size frame, to read a screen and measure the `rect` of a zoom or highlight."""
    root, project = load_project(args.project)
    dst = root / "analysis" / f"frame-{args.time:.2f}.jpg"
    ffmpeg("-ss", f"{args.time:.3f}", "-i", project["raw"], "-frames:v", "1", "-q:v", "2", str(dst))
    print(dst)


def cmd_transcribe(args: argparse.Namespace) -> None:
    root, project = load_project(args.project)
    if not project["source"]["has_audio"]:
        die("Video thô không có tiếng.")
    try:
        import numpy
        from faster_whisper import WhisperModel
    except ImportError:
        die("Thiếu faster-whisper: pip install faster-whisper")
    # Decoded by ffmpeg because faster-whisper's own PyAV decoder breaks on mismatched `av` versions.
    pcm = run(["ffmpeg", "-v", "error", "-i", project["raw"], "-vn", "-f", "s16le", "-ac", "1", "-ar", "16000", "-"], binary=True).stdout
    speech = numpy.frombuffer(pcm, numpy.int16).astype(numpy.float32) / 32768
    model = WhisperModel(args.model, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(speech, language=args.language, word_timestamps=True, vad_filter=True)
    lines, words = [], []
    for segment in segments:
        lines.append({"start": round(segment.start, 2), "end": round(segment.end, 2), "text": segment.text.strip()})
        words += [{"word": w.word.strip(), "start": round(w.start, 2), "end": round(w.end, 2)} for w in segment.words or []]
        print(f"{segment.start:7.2f} {segment.end:7.2f}  {segment.text.strip()}", flush=True)
    write_json(root / "analysis" / "transcript.json", {"lines": lines, "words": words})


# --- voice ------------------------------------------------------------------------------------

def http(url: str, *, method: str = "GET", headers: dict | None = None, body: bytes | None = None,
         timeout: int = 120) -> tuple[int, dict, bytes]:
    request = urllib.request.Request(url, data=body, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, dict(response.headers), response.read()
    except urllib.error.HTTPError as error:
        return error.code, dict(error.headers), error.read()


def vieneu_tts(settings: dict, voice_id: str, text: str) -> bytes:
    """The POST is billed, so it is never retried; only the status poll is."""
    block = settings.get("vieneu", {})
    key = os.environ.get("VIENEU_API_KEY") or block.get("api_key", "")
    if not usable(key):
        die("Thiếu VieNeu API key (settings.json > vieneu.api_key hoặc biến VIENEU_API_KEY).")
    base = block.get("base_url", DEFAULT_VIENEU_URL).rstrip("/")
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload: dict = {"text": text.strip(), "voiceId": voice_id}
    if settings.get("emotion"):
        payload["emotion"] = settings["emotion"]
    status, _, body = http(f"{base}/tts", method="POST", headers=headers, body=json.dumps(payload).encode("utf-8"))
    if status not in (200, 201):
        die(f"VieNeu từ chối yêu cầu. HTTP {status}: {body[:300].decode('utf-8', 'replace')}")
    job = json.loads(body).get("jobId")
    if not job:
        die(f"VieNeu không trả jobId: {body[:200].decode('utf-8', 'replace')}")
    for _ in range(100):
        time.sleep(2)
        status, _, body = http(f"{base}/tts/{job}", headers=headers, timeout=60)
        if status != 200:
            continue
        info = json.loads(body)
        if info.get("status") == "completed" and info.get("audioUrl"):
            code, _, audio = http(info["audioUrl"], timeout=300)
            if code != 200 or not audio:
                die(f"Không tải được âm thanh VieNeu (HTTP {code}). Job {job} đã tính phí, tải lại từ GET {base}/tts/{job}.")
            return audio
        if info.get("status") in ("failed", "error"):
            die(f"VieNeu tạo âm thanh thất bại. Job {job}: {info}")
    die(f"VieNeu chưa xong sau 200 giây. Đừng tạo lại; lấy kết quả bằng GET {base}/tts/{job}.")


def openrouter_tts(settings: dict, voice: str, text: str) -> tuple[bytes, str]:
    block = settings.get("openrouter", {})
    key = os.environ.get("OPENROUTER_API_KEY") or block.get("api_key", "")
    if not usable(key):
        die("Thiếu OpenRouter API key (settings.json > openrouter.api_key hoặc biến OPENROUTER_API_KEY).")
    style = settings.get("voice_style", "").strip()
    payload = {"model": block.get("tts_model", DEFAULT_TTS_MODEL), "voice": voice, "response_format": "wav",
               "input": f"{style}: {text.strip()}" if style else text.strip()}
    status, headers, body = http(f"{block.get('base_url', DEFAULT_OPENROUTER_URL)}/audio/speech", method="POST", timeout=300,
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                                          "X-Title": "dung-video-tho-nhan-vat-dan"}, body=json.dumps(payload).encode("utf-8"))
    if status != 200 or not body:
        die(f"OpenRouter TTS lỗi. HTTP {status}: {body[:300].decode('utf-8', 'replace')}")
    return body, headers.get("Content-Type", headers.get("content-type", "")).lower()


def cmd_tts(args: argparse.Namespace) -> None:
    root, _ = load_project(args.project)
    settings = load_settings()
    plan = read_json(root / "plan.json")
    voice = args.voice or settings.get("voice", "")
    speed = float(settings.get("speed", 1.0) or 1.0)
    manifest_path = root / "audio" / "manifest.json"
    manifest = read_json(manifest_path) if manifest_path.exists() else {}
    todo = [b for b in plan["beats"] if b.get("vo") and not b.get("voFile")]
    if not voice and todo:
        die("Chưa có `voice` trong settings.json, hoặc truyền --voice.")
    billed = 0
    for beat in todo:
        key = hashlib.sha256(f"{voice}|{speed}|{beat['vo'].strip()}".encode("utf-8")).hexdigest()[:16]
        out = root / "audio" / f"{beat['id']}.wav"
        if manifest.get(beat["id"], {}).get("key") == key and out.exists():
            continue
        billed += len(beat["vo"])
        if args.dry:
            print(f"{beat['id']}: {len(beat['vo'])} ký tự", flush=True)
            continue
        if voice.startswith(VIENEU_PREFIX):
            data, kind = vieneu_tts(settings, voice[len(VIENEU_PREFIX):], beat["vo"]), "audio/wav"
        else:
            data, kind = openrouter_tts(settings, voice, beat["vo"])
        temp = out.with_suffix(".mp3" if "mpeg" in kind or "mp3" in kind else ".src.wav")
        temp.write_bytes(data)
        tempo = f"atempo={speed}," if abs(speed - 1.0) > 1e-6 else ""
        ffmpeg("-i", str(temp), "-af", f"{tempo}aresample=48000", "-ac", "1", str(out))
        temp.unlink()
        manifest[beat["id"]] = {"key": key, "chars": len(beat["vo"]), "duration": probe(out)["duration"]}
        write_json(manifest_path, manifest)
        print(f"{beat['id']}: {manifest[beat['id']]['duration']:.2f}s", flush=True)
    print(json.dumps({"voice": voice, "chars_to_bill": billed, "dry": args.dry}, ensure_ascii=False))


# --- cut --------------------------------------------------------------------------------------

def clip_width(project: dict) -> int:
    return min(project["source"]["width"], MAX_CLIP_WIDTH) // 2 * 2


def blur_chain(blurs: list[dict], base: float) -> tuple[str, str]:
    """Returns a filter_complex prefix that blurs private areas, plus the label of its output."""
    if not blurs:
        return "", "0:v"
    chain, last = [], "0:v"
    for i, item in enumerate(blurs):
        x, y, w, h = [float(v) / 100 for v in item["rect"]]
        enable = ""
        if "from" in item:
            enable = f":enable='between(t,{max(0, item['from'] - base):.3f},{item['to'] - base:.3f})'"
        chain.append(f"[{last}]split[b{i}a][b{i}b];[b{i}b]crop=iw*{w}:ih*{h}:iw*{x}:ih*{y},boxblur=18:2[b{i}c];"
                     f"[b{i}a][b{i}c]overlay=W*{x}:H*{y}{enable}[b{i}d]")
        last = f"b{i}d"
    return ";".join(chain) + ";", last


def blurs_for(plan: dict, start: float, end: float) -> list[dict]:
    return [b for b in plan.get("blur", []) if "from" not in b or (b["from"] < end and b["to"] > start)]


def render_clip(project: dict, plan: dict, beat: dict, dst: Path, speed: float, freeze: float, duration: float) -> None:
    a, b = beat["src"]
    width = clip_width(project)
    prefix, label = blur_chain(blurs_for(plan, a, b), a)
    pad = f",tpad=stop_mode=clone:stop_duration={freeze:.3f}" if freeze > 0 else ""
    graph = f"{prefix}[{label}]setpts=PTS/{speed:.5f},scale={width}:-2:flags=lanczos,fps={FPS},format=yuv420p{pad}[out]"
    ffmpeg("-ss", f"{a:.3f}", "-t", f"{b - a:.3f}", "-i", project["raw"], "-filter_complex", graph, "-map", "[out]", "-an",
           "-t", f"{duration:.3f}", "-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-g", "15", "-movflags", "+faststart", str(dst))


def render_still(project: dict, plan: dict, at: float, dst: Path) -> None:
    width = clip_width(project)
    prefix, label = blur_chain(blurs_for(plan, at, at + 0.1), at)
    graph = f"{prefix}[{label}]scale={width}:-2:flags=lanczos[out]"
    ffmpeg("-ss", f"{at:.3f}", "-i", project["raw"], "-filter_complex", graph, "-map", "[out]", "-frames:v", "1", "-q:v", "2", str(dst))


def atempo(speed: float) -> str:
    steps = []
    while speed > 2.0:
        steps.append("atempo=2")
        speed /= 2
    while speed < 0.5:
        steps.append("atempo=0.5")
        speed *= 2
    return ",".join(steps + [f"atempo={speed:.5f}"])


def raw_audio(project: dict, beat: dict, speed: float, dst: Path) -> None:
    a, b = beat["src"]
    ffmpeg("-ss", f"{a:.3f}", "-t", f"{b - a:.3f}", "-i", project["raw"], "-vn", "-ac", "1",
           "-af", f"{atempo(speed)},afade=t=in:d=0.02,areverse,afade=t=in:d=0.04,areverse,loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000", str(dst))


def voice_audio(src: Path, dst: Path) -> None:
    ffmpeg("-i", str(src), "-ac", "1", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000", str(dst))


def envelope(path: Path) -> list[int]:
    """Voice loudness at MOUTH_RATE, scaled so the 95th percentile is 100. Drives the mouth."""
    pcm = run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "s16le", "-ac", "1", "-ar", "16000", "-"], binary=True).stdout
    samples = array.array("h")
    samples.frombytes(pcm[: len(pcm) // 2 * 2])
    if sys.byteorder == "big":
        samples.byteswap()
    size = 16000 // MOUTH_RATE
    levels = [math.sqrt(sum(v * v for v in samples[i:i + size]) / size) for i in range(0, len(samples) - size + 1, size)]
    peak = sorted(levels)[int(len(levels) * 0.95)] if levels else 1.0
    return [min(100, round(v / (peak or 1.0) * 100)) for v in levels]


def make_sfx(root: Path) -> None:
    """Synthesised here, so the skill carries no sound files and no licence to track."""
    out = root / "assets" / "sfx"
    out.mkdir(parents=True, exist_ok=True)
    recipes = {
        "whoosh": ("anoisesrc=d=0.42:c=pink:a=0.5:r=48000", "highpass=f=500,lowpass=f=6000,afade=t=in:d=0.16,afade=t=out:st=0.2:d=0.22"),
        "pop": ("sine=f=720:d=0.11:r=48000", "vibrato=f=8:d=0.2,afade=t=out:st=0.02:d=0.09"),
        "tick": ("sine=f=1500:d=0.035:r=48000", "afade=t=out:st=0.005:d=0.03"),
        "chime": ("sine=f=880:d=0.5:r=48000", "afade=t=out:st=0.02:d=0.48"),
    }
    for name, (source, chain) in recipes.items():
        dst = out / f"{name}.wav"
        if not dst.exists():
            ffmpeg("-f", "lavfi", "-i", source, "-af", chain, "-ac", "1", str(dst))


def plan_beat(beat: dict, voice_len: float, source: dict, warnings: list[str]) -> dict:
    kind = beat.get("type", "play")
    info: dict = {"id": beat["id"], "type": kind, "voice_len": round(voice_len, 3), "speed": 1.0, "freeze": 0.0, "vo_start": 0.0}
    if kind == "play":
        a, b = beat["src"]
        if not 0 <= a < b <= source["duration"] + 0.05:
            die(f"{beat['id']}: src {beat['src']} nằm ngoài video thô ({source['duration']}s).")
        length = b - a
        if voice_len and not beat.get("keepAudio"):
            need = voice_len + LEAD_PLAY + TAIL_PLAY
            speed = float(beat.get("speed") or max(SPEED_MIN, min(SPEED_MAX, length / need)))
            played = length / speed
            if played < need:
                info["freeze"] = round(need - played, 3)
            elif played > need + 0.5:
                warnings.append(f"{beat['id']}: đoạn hình dài hơn lời {played - need:.1f}s dù đã tua x{speed:.1f}. Nên cắt ngắn src.")
            info["speed"], info["duration"], info["vo_start"] = round(speed, 4), round(max(played, need), 3), LEAD_PLAY
        else:
            speed = float(beat.get("speed") or 1.0)
            info["speed"], info["duration"] = speed, round(length / speed, 3)
            if voice_len > info["duration"]:
                die(f"{beat['id']}: giữ tiếng gốc mà lời đọc ({voice_len:.1f}s) dài hơn đoạn hình ({info['duration']:.1f}s).")
    elif kind == "pause":
        if not 0 <= beat["at"] <= source["duration"]:
            die(f"{beat['id']}: at {beat['at']} nằm ngoài video thô.")
        info["duration"] = round(max(beat.get("hold", 0), voice_len + LEAD_PAUSE + TAIL_PAUSE), 3)
        info["vo_start"] = LEAD_PAUSE
    elif kind == "cutaway":
        info["duration"] = round(max(beat.get("hold", 0), voice_len + 0.9), 3)
        info["vo_start"] = 0.45
    elif kind == "chapter":
        info["duration"] = float(beat.get("hold", 1.6))
    else:
        die(f"{beat['id']}: không có loại nhịp `{kind}`.")
    return info


def cmd_cut(args: argparse.Namespace) -> None:
    root, project = load_project(args.project)
    plan = read_json(root / "plan.json")
    if not plan["beats"]:
        die("plan.json chưa có nhịp nào.")
    ids = [b.get("id") for b in plan["beats"]]
    if None in ids or len(set(ids)) != len(ids) or any(not re.fullmatch(r"[a-z][a-z0-9-]*", i) for i in ids):
        die("Mỗi nhịp cần `id` riêng, chữ thường và số, bắt đầu bằng chữ cái.")
    for sub in ("clips", "stills", "audio", "mouth"):
        (root / "assets" / sub).mkdir(parents=True, exist_ok=True)
    make_sfx(root)
    cache_path = root / "analysis" / "cut-cache.json"
    cache = read_json(cache_path) if cache_path.exists() else {}
    source, warnings, timeline, clock = project["source"], [], [], 0.0
    for beat in plan["beats"]:
        vo_src = None
        if beat.get("voFile"):
            vo_src = root / beat["voFile"]
            if not vo_src.exists():
                die(f"{beat['id']}: không thấy {beat['voFile']}.")
        elif beat.get("vo"):
            vo_src = root / "audio" / f"{beat['id']}.wav"
            if not vo_src.exists():
                die(f"{beat['id']}: chưa có giọng đọc. Chạy tts trước.")
        voice_len = probe(vo_src)["duration"] if vo_src else 0.0
        info = plan_beat(beat, voice_len, source, warnings)
        info["start"] = round(clock, 3)
        clock += info["duration"]
        stamp = hashlib.sha256(json.dumps([project["raw"], beat.get("src"), beat.get("at"), info["speed"], info["freeze"],
                                           info["duration"], beat.get("keepAudio"), plan.get("blur"),
                                           vo_src.stat().st_mtime if vo_src else 0, MAX_CLIP_WIDTH]).encode("utf-8")).hexdigest()
        fresh = cache.get(beat["id"]) == stamp
        audio_dir = root / "assets" / "audio"
        if info["type"] == "play":
            info["clip"] = f"assets/clips/{beat['id']}.mp4"
            if not fresh:
                render_clip(project, plan, beat, root / info["clip"], info["speed"], info["freeze"], info["duration"])
            keep = source["has_audio"] and (beat.get("keepAudio") or not vo_src)
            if keep:
                info["raw_audio"] = f"assets/audio/{beat['id']}-raw.wav"
                info["raw_volume"] = RAW_UNDER_VO if vo_src else 1.0
                if not fresh:
                    raw_audio(project, beat, info["speed"], root / info["raw_audio"])
        elif info["type"] == "pause":
            info["still"] = f"assets/stills/{beat['id']}.jpg"
            if not fresh:
                render_still(project, plan, beat["at"], root / info["still"])
        speech = None
        if vo_src:
            info["voice"] = f"assets/audio/{beat['id']}.wav"
            if not fresh:
                voice_audio(vo_src, root / info["voice"])
            speech = root / info["voice"]
        elif info.get("raw_audio"):
            speech = root / info["raw_audio"]
        if speech:
            info["mouth"] = f"assets/mouth/{beat['id']}.json"
            if not fresh:
                write_json(root / info["mouth"], {"rate": MOUTH_RATE, "levels": envelope(speech)})
        cache[beat["id"]] = stamp
        write_json(cache_path, cache)
        timeline.append(info)
        print(f"{beat['id']}: {info['duration']:.2f}s", flush=True)
    total = round(clock, 3)
    if plan.get("music"):
        music = plan["music"]
        path = root / music["file"]
        if not path.exists():
            die(f"Không thấy nhạc {music['file']}.")
        ffmpeg("-stream_loop", "-1", "-i", str(path), "-t", f"{total:.3f}", "-ac", "2",
               "-af", f"afade=t=in:d=1,afade=t=out:st={max(0, total - 2):.3f}:d=2,aresample=48000", str(root / "assets" / "audio" / "music.wav"))
    write_json(root / "timeline.json", {"fps": FPS, "duration": total, "badge_from": SPEED_BADGE, "beats": timeline})
    lines = [f"# Quyết định dựng, tổng {total:.1f}s", ""]
    for item in timeline:
        note = [f"{item['duration']:.1f}s"]
        if item["speed"] != 1.0:
            note.append(f"tốc độ x{item['speed']:.2f}")
        if item["freeze"]:
            note.append(f"giữ khung cuối {item['freeze']:.1f}s để đủ lời")
        lines.append(f"- {item['id']} ({item['type']}): {', '.join(note)}")
    lines += ["", *[f"- CẢNH BÁO {w}" for w in warnings]]
    (root / "decisions.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"duration": total, "beats": len(timeline), "warnings": warnings}, ensure_ascii=False, indent=2))


def main() -> None:
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")  # Vietnamese messages on a Windows console
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check").set_defaults(run=cmd_check)
    p = sub.add_parser("init")
    p.add_argument("name")
    p.add_argument("--raw", required=True)
    p.add_argument("--format", choices=["16:9", "9:16"])
    p.add_argument("--force", action="store_true")
    p.set_defaults(run=cmd_init)
    p = sub.add_parser("analyze")
    p.add_argument("project")
    p.add_argument("--noise", type=int, default=-35)
    p.add_argument("--silence", type=float, default=0.7)
    p.add_argument("--still", type=float, default=2.0)
    p.add_argument("--step", type=float)
    p.set_defaults(run=cmd_analyze)
    p = sub.add_parser("frame")
    p.add_argument("project")
    p.add_argument("time", type=float)
    p.set_defaults(run=cmd_frame)
    p = sub.add_parser("transcribe")
    p.add_argument("project")
    p.add_argument("--model", default="small")
    p.add_argument("--language", default="vi")
    p.set_defaults(run=cmd_transcribe)
    p = sub.add_parser("tts")
    p.add_argument("project")
    p.add_argument("--voice")
    p.add_argument("--dry", action="store_true")
    p.set_defaults(run=cmd_tts)
    p = sub.add_parser("cut")
    p.add_argument("project")
    p.set_defaults(run=cmd_cut)
    args = parser.parse_args()
    args.run(args)


if __name__ == "__main__":
    main()
