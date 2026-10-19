"""Kho token Zalo OA dung chung (skill chatbot-tu-van va viet-bai-zalo-oa). Chi dung thu vien chuan.

Refresh token cua Zalo chi dung duoc 1 LAN: hai tien trinh tu lam moi rieng se lam hong nhau.
Vi vay moi noi deu doc/ghi cung 1 file ($ZALO_TOKEN_FILE, mac dinh ~/.hermes/zalo/tokens.json)
va khoa file (fcntl) khi lam moi. Giu file nay giong nhau o ca 2 skill.

Dong lenh (ket noi OA, xem token):
    python3 -I zalo_tokens.py auth-url --redirect https://bot.shop.vn/zalo/callback
    python3 -I zalo_tokens.py auth-code "<URL callback day du sau khi chu OA bam Dong y>"
    python3 -I zalo_tokens.py list | refresh --oa <oa_id>

Cau truc file:
{"app_id": "...", "oas": {"<oa_id>": {"name": "...", "access_token": "...", "refresh_token": "...",
                                       "expires_at": 1730000000}}}
"""
import base64, fcntl, hashlib, json, os, secrets, sys, time, urllib.parse, urllib.request, urllib.error
from pathlib import Path

OAUTH = os.getenv("ZALO_OAUTH_BASE") or "https://oauth.zaloapp.com/v4/oa"  # env de test voi API gia lap
REFRESH_MARGIN = 300  # lam moi truoc khi het han 5 phut


class ZaloAuthError(Exception):
    pass


def token_file() -> Path:
    return Path(os.getenv("ZALO_TOKEN_FILE") or Path.home() / ".hermes" / "zalo" / "tokens.json").expanduser()


def app_credentials(app_id=None, secret=None):
    app_id = app_id or os.getenv("ZALO_APP_ID")
    secret = secret or os.getenv("ZALO_APP_SECRET")
    if not app_id or not secret:
        raise ZaloAuthError("Thieu ZALO_APP_ID / ZALO_APP_SECRET (app tren developers.zalo.me).")
    return app_id, secret


def _write_private(path: Path, text: str):
    """Ghi file bi mat: tao voi quyen 600 ngay tu dau roi doi ten (khong co luc nao file lo ra)."""
    tmp = path.with_suffix(".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.chmod(tmp, 0o600)
    tmp.replace(path)


class _Locked:
    def __enter__(self):
        f = token_file()
        f.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.lock = open(f.with_suffix(".lock"), "w")
        fcntl.flock(self.lock, fcntl.LOCK_EX)
        self.data = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {"oas": {}}
        self.data.setdefault("oas", {})
        return self

    def save(self):
        f = token_file()
        _write_private(f, json.dumps(self.data, ensure_ascii=False, indent=2))

    def __exit__(self, *exc):
        fcntl.flock(self.lock, fcntl.LOCK_UN)
        self.lock.close()


def _oauth_post(secret, params):
    body = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(OAUTH + "/access_token", body, method="POST", headers={
        "Content-Type": "application/x-www-form-urlencoded", "secret_key": secret})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise ZaloAuthError(f"OAuth HTTP {e.code}: {e.read()[:300]!r}")
    if not data.get("access_token"):
        raise ZaloAuthError(f"Zalo khong tra access_token: {data}")
    return data


def _store(entry, data):
    entry["access_token"] = data["access_token"]
    entry["refresh_token"] = data.get("refresh_token", entry.get("refresh_token"))
    entry["expires_at"] = int(time.time()) + int(data.get("expires_in") or 3600)
    entry["updated_at"] = int(time.time())


def exchange_code(oa_id, code, code_verifier, name=None, app_id=None, secret=None):
    """Doi authorization code (tu callback ?code=&oa_id=) lay token, luu vao kho."""
    app_id, secret = app_credentials(app_id, secret)
    params = {"code": code, "app_id": app_id, "grant_type": "authorization_code"}
    if code_verifier:
        params["code_verifier"] = code_verifier
    data = _oauth_post(secret, params)
    with _Locked() as s:
        s.data["app_id"] = app_id
        entry = s.data["oas"].setdefault(str(oa_id), {})
        if name:
            entry["name"] = name
        _store(entry, data)
        s.save()
    return {"oa_id": str(oa_id), "expires_at": entry["expires_at"]}


def access_token(oa_id, stale=None, app_id=None, secret=None, force=False):
    """Tra access token con han; tu lam moi (co khoa) neu sap het han.
    stale = token vua bi Zalo tu choi: lam moi ngay, tru khi tien trinh khac da lam moi roi."""
    with _Locked() as s:
        entry = s.data["oas"].get(str(oa_id))
        if not entry or not entry.get("refresh_token"):
            raise ZaloAuthError(f"OA {oa_id} chua ket noi. Chay: python3 -I zalo_tokens.py auth-url --redirect <URL callback>")
        fresh = entry.get("access_token") and entry.get("expires_at", 0) - time.time() > REFRESH_MARGIN
        if fresh and not force and (stale is None or entry["access_token"] != stale):
            return entry["access_token"]
        app_id, secret = app_credentials(app_id or s.data.get("app_id"), secret)
        try:
            data = _oauth_post(secret, {"refresh_token": entry["refresh_token"], "app_id": app_id,
                                        "grant_type": "refresh_token"})
        except ZaloAuthError as e:
            raise ZaloAuthError(f"Lam moi token OA {oa_id} that bai ({e}). Refresh token het han (3 thang) "
                                "hoac bi thu hoi: ket noi lai OA bang auth-url.")
        _store(entry, data)
        s.save()
        return entry["access_token"]


def list_oas():
    with _Locked() as s:
        return {k: {"name": v.get("name"), "expires_at": v.get("expires_at"), "has_refresh": bool(v.get("refresh_token"))}
                for k, v in s.data["oas"].items()}


# ---------------------------------------------------------------- ket noi OA (OAuth v4 + PKCE)

def _pending_file() -> Path:
    return token_file().with_name("pending_auth.json")


def auth_url(redirect_uri, app_id=None):
    """Tao link cho chu OA bam Dong y. Luu code_verifier theo state (het han 30 phut)."""
    app_id = app_id or os.getenv("ZALO_APP_ID")
    if not app_id:
        raise ZaloAuthError("Thieu ZALO_APP_ID.")
    verifier = secrets.token_urlsafe(48)[:64]
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    state = secrets.token_urlsafe(16)
    with _Locked():
        f = _pending_file()
        pending = json.loads(f.read_text()) if f.exists() else {}
        pending = {k: v for k, v in pending.items() if v["t"] > time.time() - 1800}
        pending[state] = {"verifier": verifier, "redirect": redirect_uri, "t": time.time()}
        _write_private(f, json.dumps(pending))
    q = urllib.parse.urlencode({"app_id": app_id, "redirect_uri": redirect_uri,
                                "code_challenge": challenge, "state": state})
    return {"url": f"{OAUTH}/permission?{q}", "state": state, "redirect_uri": redirect_uri}


def complete(query, name=None):
    """query = chuoi ?code=..&oa_id=..&state=.. (hoac ca URL callback). Doi code lay token va luu."""
    qs = urllib.parse.parse_qs(urllib.parse.urlparse(query).query or query.lstrip("?"))
    code, oa_id, state = (qs.get(k, [""])[0] for k in ("code", "oa_id", "state"))
    if not code or not oa_id:
        raise ZaloAuthError("URL callback thieu code/oa_id (chu OA da bam Dong y chua?).")
    with _Locked():
        f = _pending_file()
        pending = json.loads(f.read_text()) if f.exists() else {}
        item = pending.pop(state, None)
        _write_private(f, json.dumps(pending))
    if not item:
        raise ZaloAuthError("state khong khop hoac da qua 30 phut: tao link moi bang auth-url.")
    return exchange_code(oa_id, code, item["verifier"], name=name)


def _cli():
    import argparse
    ap = argparse.ArgumentParser(description="Ket noi Zalo OA va quan ly token (dung chung cac skill).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("auth-url", help="Tao link cho chu OA cap quyen")
    a.add_argument("--redirect", required=True, help="Callback URL da khai bao trong app (muc Official Account)")
    c = sub.add_parser("auth-code", help="Dan URL callback (co code, oa_id, state) de luu token")
    c.add_argument("callback")
    c.add_argument("--name", help="Ten goi nho cua OA")
    sub.add_parser("list", help="Cac OA da ket noi")
    r = sub.add_parser("refresh", help="Lam moi token ngay (kiem tra ket noi)")
    r.add_argument("--oa", required=True)
    args = ap.parse_args()
    try:
        if args.cmd == "auth-url":
            res = auth_url(args.redirect)
            res["next"] = "Gui link cho chu OA (dang nhap Zalo quan tri OA) bam Dong y, roi dan URL callback vao auth-code."
        elif args.cmd == "auth-code":
            res = complete(args.callback, args.name)
        elif args.cmd == "list":
            res = {"token_file": str(token_file()), "oas": list_oas()}
        else:
            access_token(args.oa, force=True)
            res = {"oa_id": args.oa, "refreshed": True, "oas": list_oas()}
        print(json.dumps({"ok": True, **res}, ensure_ascii=False, indent=2))
    except ZaloAuthError as e:
        print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    _cli()
