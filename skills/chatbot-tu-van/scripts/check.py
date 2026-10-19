#!/usr/bin/env python3
"""Tu kiem tra chatbot-tu-van sau khi cai / khi nghi co loi. Chi doc, khong sua gi.

    python3 scripts/check.py --profile shop-a                 # kiem tra cau hinh + dich vu
    python3 scripts/check.py --profile shop-a --ask "Gia goi A?"   # them 1 cau hoi that qua webchat

Chay bang python cua Hermes thi kiem tra them toolset thuc te cua kenh chat (khong co terminal/file/web).
Ket qua: JSON {"ok": bool, "checks": [{"name", "ok", "detail", "fix"}]}. ok=false neu co muc "fail".
"""
import argparse, hashlib, json, os, subprocess, sys, time, urllib.error, urllib.request
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
PLUGINS = {"webchat": ["owui_mirror.py"], "chatbot_guard": ["kb.py"]}
KB_TOOLS = {"tim_kien_thuc", "doc_tai_lieu", "luu_khach_hang", "chuyen_nhan_vien"}
PLACEHOLDER = ("DAN_", "_CUA_KHACH", "example.com", "shopmau.vn", "OA_SECRET_KEY_TRONG")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

checks = []


def add(name, ok, detail="", fix="", level=None):
    checks.append({"name": name, "ok": bool(ok), "level": level or ("ok" if ok else "fail"), "detail": detail, "fix": fix})


def warn(name, detail, fix=""):
    add(name, False, detail, fix, "warn")


def hermes_home(a):
    if a.hermes_home:
        return Path(a.hermes_home).expanduser()
    base = Path(os.environ.get("HERMES_HOME") or Path.home() / ".hermes").expanduser()
    return base / "profiles" / a.profile if a.profile and a.profile != "default" else base


def read_env(f: Path):
    env = {}
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def http(method, url, body=None, headers=None, timeout=10):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data, method=method, headers={"Content-Type": "application/json", **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, json.loads(r.read() or b"{}")


def sha(p: Path):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def is_placeholder(v):
    return not v or any(x in str(v) for x in PLACEHOLDER)


def check_install(home, cfg):
    # plugin da chep va cung phien ban voi skill
    stale = []
    for name, shared in PLUGINS.items():
        dst = home / "plugins" / name
        if not (dst / "plugin.yaml").exists():
            add(f"plugin {name}", False, f"Khong co {dst}", "Chay scripts/setup.py")
            continue
        pairs = [(f, dst / f.name) for f in (SKILL / "templates" / "plugins" / name).iterdir() if f.is_file()]
        pairs += [(SKILL / "scripts" / f, dst / f) for f in shared]
        stale += [str(d.relative_to(home)) for src, d in pairs if sha(src) != sha(d)]
    if sha(SKILL / "scripts" / "kb.py") != sha(home / "chatbot" / "kb.py"):
        stale.append("chatbot/kb.py")
    if not stale:
        add("plugin da cai", True, ", ".join(PLUGINS))
    else:
        warn("plugin da cai", "Khac ban trong skill: " + ", ".join(stale), "Chay lai scripts/setup.py roi restart gateway")

    enabled = ((cfg.get("plugins") or {}).get("enabled")) or []
    miss = [p for p in PLUGINS if p not in enabled]
    add("plugins.enabled", not miss, "thieu: " + ", ".join(miss) if miss else "du 2 plugin", "Chay scripts/setup.py")

    kb = (cfg.get("mcp_servers") or {}).get("kb") or {}
    inc = set(((kb.get("tools") or {}).get("include")) or [])
    add("mcp_servers.kb", bool(kb) and inc == KB_TOOLS, f"tools: {sorted(inc)}", "Chay scripts/setup.py")

    pt = cfg.get("platform_toolsets") or {}
    bad = {p: pt.get(p) for p in ("webchat",) if pt.get(p) != ["kb"]}
    add("platform_toolsets", not bad, f"khac ['kb']: {bad}" if bad else "webchat = ['kb']",
        "Dat platform_toolsets.webchat = [kb] (setup.py lam san)")

    try:
        from gateway.display_config import resolve_display_setting
    except ImportError:
        pass
    else:
        for p in ("webchat",):
            loud = {k: resolve_display_setting(cfg, p, k) for k in ("tool_progress", "interim_assistant_messages",
                                                                   "long_running_notifications", "streaming")}
            bad = {k: v for k, v in loud.items() if v not in ("off", False, None)}
            add(f"chi gui cau tra loi cuoi ({p})", not bad, f"dang bat: {bad}" if bad else "tat tin trung gian",
                "Chay lai setup.py (ghi display.platforms) roi restart gateway")

    # toolset thuc te (chi khi chay bang python cua Hermes)
    try:
        from hermes_cli.tools_config import _get_platform_tools
    except ImportError:
        warn("toolset thuc te", "Khong import duoc hermes_cli (dang chay python he thong)",
             "Chay check.py bang python cua Hermes de kiem tra muc nay")
    else:
        import logging
        logging.disable(logging.WARNING)  # Hermes canh bao "kb" khong phai toolset tinh: dung, vi la ten MCP server
        from model_tools import get_tool_definitions
        for p in ("webchat",):
            got = set(_get_platform_tools(cfg, p))
            extra = sorted(got - {"kb"})
            # toolset co the duoc bat nhung tool tu tat (vd kanban chi hien khi chay kanban): dem tool thuc te
            tools = [t["function"]["name"] for t in get_tool_definitions(enabled_toolsets=extra, quiet_mode=True)] if extra else []
            add(f"tool kenh {p}", not tools, f"MCP kb + tool khac: {tools or 'khong co'} (toolset {sorted(got)})",
                "Kenh chat chi duoc co MCP kb. Bo toolset thua trong platform_toolsets hoac tat plugin co tool")
    for mod, why in (("aiohttp", "kenh webchat"), ("mcp", "tool tra tai lieu")):
        try:
            __import__(mod)
            add(f"goi {mod}", True, why)
        except ImportError:
            if "hermes_cli" in sys.modules:
                add(f"goi {mod}", False, f"Thieu {mod} ({why})", f"{sys.executable} -m pip install {mod}")


def check_data(home, chat, s, env):
    add("settings.json", bool(s), str(chat / "settings.json"), "Chay scripts/setup.py roi dien settings.json")
    biz = s.get("business") or {}
    if is_placeholder(biz.get("ten")) or biz.get("ten") == "Shop Mẫu" or is_placeholder(biz.get("hotline")) or "234 567" in str(biz.get("hotline")):
        warn("business", "Van la thong tin mau", "Dien ten, hotline, gio lam viec that")
    else:
        add("business", True, biz.get("ten"))
    files = sorted((chat / "knowledge").glob("*.md"))
    add("kho tai lieu", bool(files), f"{len(files)} file: " + ", ".join(f.name for f in files[:8]),
        "Nap tai lieu: kb.py --home <chatbot> ingest <file...>")

    # MCP kb tra loi dung giao thuc
    kb_py = chat / "kb.py"
    try:
        msgs = [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}},
                {"jsonrpc": "2.0", "method": "notifications/initialized"},
                {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}]
        r = subprocess.run([sys.executable, "-I", str(kb_py), "--home", str(chat), "mcp"], timeout=20,
                           input="\n".join(json.dumps(m) for m in msgs) + "\n", capture_output=True, text=True)
        names = set()
        for line in r.stdout.splitlines():
            res = json.loads(line).get("result") or {}
            names |= {t["name"] for t in res.get("tools", [])}
        add("MCP kb", names == KB_TOOLS, f"tools: {sorted(names)}", "Chay lai setup.py (chep kb.py)")
    except (OSError, subprocess.SubprocessError, ValueError) as e:
        add("MCP kb", False, str(e), "Chay lai setup.py (chep kb.py)")

    ow = s.get("open_webui") or {}
    if is_placeholder(ow.get("url")) or is_placeholder(ow.get("api_key")):
        warn("Open WebUI", "Chua dien open_webui.url/api_key: hoi thoai se khong hien ben Open WebUI",
             "Open WebUI > Settings > Account > API keys, dan vao settings.json")
    else:
        try:
            code, me = http("GET", ow["url"].rstrip("/") + "/api/v1/auths/", headers={"Authorization": f"Bearer {ow['api_key']}"})
            add("Open WebUI", True, f"API key cua: {me.get('name') or me.get('email')}")
        except (urllib.error.URLError, OSError, ValueError) as e:
            add("Open WebUI", False, f"{ow['url']}: {e}", "Kiem tra URL va API key (Admin phai bat API keys)")

    wc = s.get("webchat") or {}
    if not wc.get("allowed_origins") or any(is_placeholder(o) for o in wc["allowed_origins"]):
        add("webchat.allowed_origins", False, str(wc.get("allowed_origins")), "Dien domain website, vd https://shop.vn")



def check_running(s, env):
    c = s.get("webchat") or {}
    url = f"http://{c.get('host') or '127.0.0.1'}:{c.get('port') or 8650}/health"
    url = url.replace("0.0.0.0", "127.0.0.1")
    try:
        add("webchat dang chay", http("GET", url, timeout=5)[1].get("ok"), url)
    except (urllib.error.URLError, OSError, ValueError) as e:
        add("webchat dang chay", False, f"{url}: {e}", "hermes [-p profile] gateway restart; xem logs/agent.log")


def ask(s, question):
    c = s.get("webchat") or {}
    base = f"http://{(c.get('host') or '127.0.0.1').replace('0.0.0.0', '127.0.0.1')}:{c.get('port') or 8650}"
    origin = (c.get("allowed_origins") or [""])[0]
    vid = "check" + hashlib.md5(str(time.time()).encode()).hexdigest()[:10]
    h = {"Origin": origin}
    try:
        seq = http("POST", base + "/api/chat", {"vid": vid, "text": question}, h)[1]["seq"]
        t0 = time.time()
        while time.time() - t0 < 120:
            r = http("GET", f"{base}/api/messages?vid={vid}&after={seq}&typing=1", headers=h, timeout=40)[1]
            if r.get("messages"):
                ans = "\n".join(m["text"] for m in r["messages"])
                add("hoi thu", True, f"Hoi: {question}\nDap: {ans}")
                return
        add("hoi thu", False, "Khong co tra loi sau 120 giay", "Xem logs/agent.log cua profile (model, MCP kb)")
    except (urllib.error.URLError, OSError, ValueError, KeyError) as e:
        add("hoi thu", False, str(e), "Gateway chua chay hoac allowed_origins sai")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--profile")
    ap.add_argument("--hermes-home")
    ap.add_argument("--ask", help="Gui 1 cau hoi that qua webchat va in cau tra loi")
    a = ap.parse_args()
    home = hermes_home(a)
    chat = home / "chatbot"
    os.environ.setdefault("HERMES_HOME", str(home))
    try:
        import yaml
        cfg = yaml.safe_load((home / "config.yaml").read_text(encoding="utf-8")) or {}
    except ImportError:
        cfg = None
    except OSError as e:
        add("config.yaml", False, str(e), "Sai --profile / --hermes-home?")
        cfg = {}
    s = json.loads((chat / "settings.json").read_text(encoding="utf-8")) if (chat / "settings.json").exists() else {}
    env = {**read_env(home / ".env")}
    if cfg is None:
        warn("config.yaml", "Khong co PyYAML: bo qua kiem tra config", "Chay bang python cua Hermes")
    else:
        check_install(home, cfg)
    check_data(home, chat, s, env)
    check_running(s, env)
    if a.ask:
        ask(s, a.ask)
    fails = [c["name"] for c in checks if c["level"] == "fail"]
    print(json.dumps({"ok": not fails, "hermes_home": str(home), "fail": fails,
                      "warn": [c["name"] for c in checks if c["level"] == "warn"], "checks": checks},
                     ensure_ascii=False, indent=2))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
