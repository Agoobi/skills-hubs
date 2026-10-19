#!/usr/bin/env python3
"""Cai chatbot-tu-van vao 1 profile Hermes (chay 1 lan, chay lai an toan).

    python3 scripts/setup.py --profile shop-a [--zalo-app-id ... --zalo-app-secret ...]

Viec lam:
1. Tao $HERMES_HOME/chatbot/ (settings.json tu mau, knowledge/, kb.py cho MCP).
2. Chep 3 plugin vao $HERMES_HOME/plugins/: webchat, zalo_oa, chatbot_guard (kem file dung chung).
3. Ghi config.yaml cua profile: plugins.enabled, mcp_servers.kb (chi tool tra tai lieu/lead),
   platform_toolsets cho webchat/zalo_oa = chi MCP server "kb" (KHONG terminal, file, web).
4. Ghi .env cua profile: CHATBOT_HOME, *_ALLOW_ALL_USERS, ZALO_APP_ID/SECRET neu truyen vao.
Sau do: khoi dong lai gateway cua profile va chay scripts/check.py.

Can PyYAML (co san trong moi truong cua Hermes). Neu chay bang python he thong khong co yaml,
dung python cua Hermes, vd: ~/.hermes/hermes-agent/venv/bin/python scripts/setup.py ...
"""
import argparse, json, os, shutil, sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
PLUGINS = {  # plugin -> file dung chung can chep kem
    "webchat": ["owui_mirror.py"],
    "zalo_oa": ["owui_mirror.py", "zalo_tokens.py"],
    "chatbot_guard": ["kb.py"],
}
CHAT_PLATFORMS = ["webchat", "zalo_oa"]
KB_TOOLS = ["tim_kien_thuc", "doc_tai_lieu", "luu_khach_hang", "chuyen_nhan_vien"]

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def out(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def hermes_home(a):
    if a.hermes_home:
        return Path(a.hermes_home).expanduser()
    base = Path(os.environ.get("HERMES_HOME") or Path.home() / ".hermes").expanduser()
    if a.profile and a.profile != "default":
        return base / "profiles" / a.profile
    return base


def set_env(env_file: Path, values: dict):
    lines = env_file.read_text(encoding="utf-8").splitlines() if env_file.exists() else []
    keep = [l for l in lines if l.split("=", 1)[0].strip() not in values]
    keep += [f"{k}={v}" for k, v in values.items()]
    env_file.write_text("\n".join(keep) + "\n", encoding="utf-8")
    os.chmod(env_file, 0o600)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--profile", help="Ten profile Hermes cua khach (bo trong = profile mac dinh)")
    ap.add_argument("--hermes-home", help="Duong dan HERMES_HOME cu the (thay cho --profile)")
    ap.add_argument("--zalo-app-id")
    ap.add_argument("--zalo-app-secret")
    ap.add_argument("--python", default=sys.executable, help="Python chay MCP kb (mac dinh python dang chay setup)")
    ap.add_argument("--dry-run", action="store_true", help="Chi in nhung gi se ghi")
    a = ap.parse_args()
    try:
        import yaml
    except ImportError:
        out({"ok": False, "error": "Thieu PyYAML. Chay bang python cua Hermes (vd ~/.hermes/hermes-agent/venv/bin/python)."})
        sys.exit(1)

    warnings = []
    # Ban cai Hermes day du ([all]) da co 2 goi nay; ban rut gon thi thieu.
    for mod, why in (("aiohttp", "kenh webchat/zalo_oa khong bat"), ("mcp", "chatbot khong co tool tra tai lieu")):
        try:
            __import__(mod)
        except ImportError:
            warnings.append(f"Thieu goi {mod} trong python cua Hermes ({why}). Cai: {sys.executable} -m pip install "
                            + ("'aiohttp>=3.9'" if mod == "aiohttp" else "'mcp>=1.2'"))
    home = hermes_home(a)
    if not (home / "config.yaml").exists() and not a.dry_run:
        out({"ok": False, "error": f"Khong thay {home}/config.yaml. Tao profile truoc: hermes profile create {a.profile or ''}"})
        sys.exit(1)
    chat = home / "chatbot"
    done = []

    # 1. thu muc du lieu
    if not a.dry_run:
        (chat / "knowledge").mkdir(parents=True, exist_ok=True)
        if not (chat / "settings.json").exists():
            shutil.copy(SKILL / "settings.example.json", chat / "settings.json")
            os.chmod(chat / "settings.json", 0o600)
            done.append("tao chatbot/settings.json tu mau (can dien)")
        shutil.copy(SKILL / "scripts" / "kb.py", chat / "kb.py")
    done.append(f"kb.py -> {chat / 'kb.py'}")

    # 2. plugin
    for name, shared in PLUGINS.items():
        dst = home / "plugins" / name
        if not a.dry_run:
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(SKILL / "templates" / "plugins" / name, dst, ignore=shutil.ignore_patterns("__pycache__"))
            for f in shared:
                shutil.copy(SKILL / "scripts" / f, dst / f)
        done.append(f"plugin {name} -> {dst}")

    # 3. config.yaml
    cfg_file = home / "config.yaml"
    cfg = (yaml.safe_load(cfg_file.read_text(encoding="utf-8")) or {}) if cfg_file.exists() else {}
    plugins = cfg.setdefault("plugins", {})
    enabled = plugins.get("enabled") if isinstance(plugins.get("enabled"), list) else []
    plugins["enabled"] = enabled + [p for p in PLUGINS if p not in enabled]
    if isinstance(plugins.get("disabled"), list):
        plugins["disabled"] = [p for p in plugins["disabled"] if p not in PLUGINS]
    cfg.setdefault("mcp_servers", {})["kb"] = {
        "command": a.python,
        "args": ["-I", str(chat / "kb.py"), "--home", str(chat), "mcp"],
        "tools": {"include": KB_TOOLS, "prompts": False, "resources": False},
    }
    cfg.setdefault("onboarding", {})["profile_build"] = "off"  # khong de bot hoi khach de "tao ho so"
    pt = cfg.setdefault("platform_toolsets", {})
    for p in CHAT_PLATFORMS:
        pt[p] = ["kb"]  # ten MCP server = allowlist; khong co toolset nao khac
    if not a.dry_run:
        if cfg_file.exists():
            shutil.copy(cfg_file, cfg_file.with_suffix(".yaml.bak-chatbot"))
        cfg_file.write_text(yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False), encoding="utf-8")
    done.append("config.yaml: plugins.enabled, mcp_servers.kb, platform_toolsets (webchat/zalo_oa = chi MCP kb)")

    # 4. .env
    env = {"CHATBOT_HOME": str(chat), "WEBCHAT_ALLOW_ALL_USERS": "true", "ZALO_OA_ALLOW_ALL_USERS": "true",
           # "none": khong co kenh nha -> Hermes khong nhan khach "No home channel... /sethome"
           "WEBCHAT_HOME_CHANNEL": "none", "ZALO_OA_HOME_CHANNEL": "none"}
    if a.zalo_app_id:
        env["ZALO_APP_ID"] = a.zalo_app_id
    if a.zalo_app_secret:
        env["ZALO_APP_SECRET"] = a.zalo_app_secret
    if not a.dry_run:
        set_env(home / ".env", env)
    done.append(".env: " + ", ".join(env))

    restart = f"hermes -p {a.profile} gateway restart" if a.profile else "hermes gateway restart"
    out({"ok": True, "hermes_home": str(home), "done": done, "warnings": warnings, "dry_run": a.dry_run,
         "next": [f"Dien {chat / 'settings.json'} (website, Open WebUI, Zalo OA, thong tin lien he)",
                  f"Nap tai lieu: python3 {SKILL / 'scripts' / 'kb.py'} --home {chat} ingest <file...>",
                  f"Khoi dong lai gateway: {restart}",
                  f"Kiem tra: python3 {SKILL / 'scripts' / 'check.py'} --hermes-home {home}"]})


if __name__ == "__main__":
    main()
