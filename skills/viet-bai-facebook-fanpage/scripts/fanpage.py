#!/usr/bin/env python3
"""Cong cu cho skill viet-bai-facebook-fanpage. Chi dung thu vien chuan.

Lenh: pages | sync-accounts | search-images | download | upload | check | validate | draft | update | schedule | status
KHONG co lenh publish ngay: bai luon dung o draft (hoac scheduled khi user da duyet ro rang).
Ket qua in ra JSON de agent doc.
"""
import argparse, json, mimetypes, os, sys, urllib.parse, urllib.request, urllib.error, unicodedata, uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

SKILL = Path(__file__).resolve().parents[1]
SETTINGS = SKILL / "settings.json"
UA = "agoobi-fanpage-skill/0.1 (https://github.com/Agoobi/skills-hubs)"
POST_URL = "https://zernio.com/dashboard/posts-all?post={post_id}"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def out(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def die(msg, code=1):
    out({"ok": False, "error": msg})
    sys.exit(code)


def load():
    if not SETTINGS.exists():
        die(f"Chua co {SETTINGS}. Copy settings.example.json -> settings.json roi dien key Zernio.")
    return json.loads(SETTINGS.read_text(encoding="utf-8"))


def save(cfg):
    SETTINGS.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")


def zcfg(cfg):
    z = cfg.get("zernio", {})
    key = os.environ.get("ZERNIO_API_KEY") or z.get("api_key", "")
    if not key.startswith("sk_") or "DAN_KEY" in key:
        die("Thieu API key Zernio hop le (sk_...). Dien vao settings.json > zernio.api_key hoac env ZERNIO_API_KEY.")
    return key, z.get("base_url", "https://zernio.com/api/v1").rstrip("/"), z.get("post_url_template", POST_URL)


def http(method, url, headers=None, body=None, raw=False):
    """raw=True: body la bytes, tra ve bytes. Nguoc lai body la JSON, tra ve JSON."""
    h = {"User-Agent": UA, **(headers or {})}
    data = None
    if raw:
        data = body
    elif body is not None:
        data = json.dumps(body).encode()
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            txt = r.read()
            if raw:
                return r.status, txt
            return r.status, (json.loads(txt) if txt else {})
    except urllib.error.HTTPError as e:
        die(f"HTTP {e.code} {url.split('?')[0]}: {e.read().decode(errors='replace')[:500]}")
    except urllib.error.URLError as e:
        die(f"Loi mang {url.split('?')[0]}: {e.reason}")


def zapi(cfg, method, path, body=None, headers=None):
    key, base, _ = zcfg(cfg)
    return http(method, base + path, {"Authorization": f"Bearer {key}", **(headers or {})}, body)[1]


def page_of(cfg, alias):
    alias = alias or cfg.get("default_page")
    p = cfg.get("pages", {}).get(alias)
    if not p:
        die(f"Khong co page '{alias}'. Page da cau hinh: {list(cfg.get('pages', {}))}")
    if not p.get("account_id") or "ZERNIO_ACCOUNT_ID" in p["account_id"]:
        die(f"Page '{alias}' chua co account_id. Chay: sync-accounts --write")
    return alias, p


def cmd_pages(a):
    cfg = load()
    keys = ("label", "account_id", "timezone", "brand_voice", "audience", "default_cta", "hashtags", "avoid", "best_times")
    out({"default": cfg.get("default_page"),
         "pages": {k: {kk: v.get(kk) for kk in keys} for k, v in cfg.get("pages", {}).items()}})


def slug(text):
    """'ĐỨC DƯƠNG' -> 'duc-duong'"""
    t = unicodedata.normalize("NFKD", text.replace("đ", "d").replace("Đ", "D"))
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    return "-".join("".join(c if c.isascii() and c.isalnum() else " " for c in t).split())[:40]


def cmd_sync(a):
    cfg = load()
    res = zapi(cfg, "GET", "/accounts?platform=facebook")
    accs = [{"account_id": x["_id"], "name": x.get("displayName") or x.get("username"),
             "username": x.get("username"), "active": x.get("isActive")} for x in res.get("accounts", [])]
    if a.write:
        pages = cfg.setdefault("pages", {})
        known = {p.get("account_id") for p in pages.values()}
        for x in accs:
            if x["account_id"] in known:
                continue
            alias = slug(x["username"] or x["name"] or "") or x["account_id"]
            pages[alias] = {"label": x["name"], "account_id": x["account_id"], "timezone": "Asia/Ho_Chi_Minh",
                            "brand_voice": "", "audience": "", "default_cta": "", "hashtags": [], "avoid": [], "best_times": []}
        if not cfg.get("default_page") and pages:
            cfg["default_page"] = next(iter(pages))
        save(cfg)
    out({"facebook_accounts": accs, "written": a.write})


def cmd_search(a):
    res = []
    if a.source == "commons":
        q = urllib.parse.urlencode({"action": "query", "format": "json", "generator": "search", "gsrnamespace": 6,
                                    "gsrsearch": a.query, "gsrlimit": a.limit, "prop": "imageinfo",
                                    "iiprop": "url|extmetadata|size", "iiurlwidth": 1200})
        _, d = http("GET", "https://commons.wikimedia.org/w/api.php?" + q)
        for p in (d.get("query", {}).get("pages", {}) or {}).values():
            ii = (p.get("imageinfo") or [{}])[0]
            m = ii.get("extmetadata", {})
            if not ii.get("thumburl"):
                continue
            res.append({"title": p["title"], "url": ii["thumburl"], "width": ii.get("thumbwidth"),
                        "license": m.get("LicenseShortName", {}).get("value"),
                        "author": m.get("Artist", {}).get("value"), "page": ii.get("descriptionurl"),
                        "source": "wikimedia-commons"})
    else:
        q = urllib.parse.urlencode({"q": a.query, "page_size": a.limit, "license_type": "commercial"})
        _, d = http("GET", "https://api.openverse.org/v1/images/?" + q)
        for r in d.get("results", []):
            res.append({"title": r.get("title"), "url": r.get("url"),
                        "license": f"{r.get('license')} {r.get('license_version')}", "author": r.get("creator"),
                        "page": r.get("foreign_landing_url"), "source": "openverse/" + str(r.get("source"))})
    out({"query": a.query,
         "note": "Kiem tra giay phep; ghi credit neu CC-BY/CC-BY-SA. Anh co nguoi/thuong hieu: can than quyen hinh anh.",
         "results": res})


def cmd_download(a):
    dest = SKILL / "downloads"
    dest.mkdir(exist_ok=True)
    name = a.name or Path(urllib.parse.urlparse(a.url).path).name or "image.jpg"
    _, data = http("GET", a.url, raw=True)
    f = dest / name
    f.write_bytes(data)
    out({"path": str(f), "bytes": len(data)})


def upload(cfg, path):
    p = Path(path)
    ctype = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
    pre = zapi(cfg, "POST", "/media/presign", {"filename": p.name, "contentType": ctype, "size": p.stat().st_size})
    http("PUT", pre["uploadUrl"], {"Content-Type": ctype}, p.read_bytes(), raw=True)
    # Docs API ghi publicUrl, skill chinh thuc cua Zernio ghi fileUrl: nhan ca hai
    url = pre.get("publicUrl") or pre.get("fileUrl")
    if not url:
        die(f"Presign khong tra ve publicUrl/fileUrl: {list(pre)}")
    return {"type": "video" if ctype.startswith("video") else "image", "url": url}


def cmd_upload(a):
    out({"mediaItem": upload(load(), a.file)})


def build_post(cfg, a, state):
    alias, page = page_of(cfg, a.page)
    content = Path(a.content_file).read_text(encoding="utf-8").strip()
    if not content:
        die("Noi dung bai rong.")
    media = [upload(cfg, m) if Path(m).exists() else {"type": "image", "url": m} for m in (a.media or [])]
    target = {"platform": "facebook", "accountId": page["account_id"]}
    if a.first_comment:
        target["platformSpecificData"] = {"firstComment": a.first_comment}
    body = {"content": content, "platforms": [target]}
    if media:
        body["mediaItems"] = media
    body.update(state)
    return alias, body


def post_url(cfg, post_id):
    return zcfg(cfg)[2].replace("{post_id}", str(post_id))


def finish(cfg, alias, post, extra=None):
    p = post.get("post", post)
    out({"ok": True, "page": alias, "post_id": p.get("_id"), "status": p.get("status"),
         "post_url": post_url(cfg, p.get("_id")),
         "note": "Gui post_url cho user de mo bai tren Zernio, kiem tra va Publish bang tay.", **(extra or {})})


def create_post(cfg, body):
    # Idempotency-Key: retry trong 24h tra ve post cu, khong tao trung
    return zapi(cfg, "POST", "/posts", body, {"Idempotency-Key": str(uuid.uuid4())})


def cmd_validate(a):
    """Dry-run qua /tools/validate/post: khong tao post, khong dang."""
    cfg = load()
    a.media = [m for m in (a.media or []) if not Path(m).exists()]  # validate khong xu ly file local
    alias, body = build_post(cfg, a, {})
    out({"page": alias, "result": zapi(cfg, "POST", "/tools/validate/post", body)})


def cmd_draft(a):
    cfg = load()
    # isDraft: true thang publishNow va scheduledFor -> post chi duoc luu, khong bao gio dang
    alias, body = build_post(cfg, a, {"isDraft": True})
    finish(cfg, alias, create_post(cfg, body), {"intended_time": a.intended_time})


def cmd_schedule(a):
    """Chi chay SAU KHI user da duyet ro rang viec len lich."""
    if not a.i_have_user_approval:
        die("Tu choi: len lich can user duyet ro rang. Mac dinh chi tao draft.")
    cfg = load()
    _, page = page_of(cfg, a.page)
    tz = a.timezone or page.get("timezone", "Asia/Ho_Chi_Minh")
    # Zernio dang NGAY neu scheduledFor da qua -> phai chan
    try:
        when = datetime.fromisoformat(a.time.replace("Z", "+00:00"))
        if when.tzinfo is None:
            when = when.replace(tzinfo=ZoneInfo(tz))
    except (ValueError, KeyError) as e:
        die(f"Gio khong hop le ({a.time}, {tz}): {e}")
    if when <= datetime.now(timezone.utc) + timedelta(minutes=5):
        die(f"Tu choi: {when.isoformat()} da qua hoac qua sat hien tai; Zernio se dang ngay lap tuc.")
    alias, body = build_post(cfg, a, {"scheduledFor": when.isoformat(), "timezone": tz})
    finish(cfg, alias, create_post(cfg, body), {"scheduled_for": when.isoformat()})


def cmd_check(a):
    """Kiem tra key, goi cuoc va tinh trang ket noi cac page. Chi doc."""
    cfg = load()
    out({"usage": zapi(cfg, "GET", "/usage-stats"), "health": zapi(cfg, "GET", "/accounts/health")})


def cmd_update(a):
    """Sua draft da tao (noi dung, anh, first comment). Chi ap dung cho post dang o trang thai draft."""
    if not (a.content_file or a.media is not None or a.first_comment is not None):
        die("Khong co gi de cap nhat: can --content-file, --media hoac --first-comment.")
    cfg = load()
    cur = zapi(cfg, "GET", f"/posts/{a.post_id}")
    cur = cur.get("post", cur)
    if cur.get("status") != "draft":
        die(f"Tu choi: post {a.post_id} dang o trang thai '{cur.get('status')}', chi duoc sua draft.")
    # isDraft: true giu post o trang thai draft; khong bao gio gui scheduledFor/publishNow
    body = {"isDraft": True}
    if a.content_file:
        content = Path(a.content_file).read_text(encoding="utf-8").strip()
        if not content:
            die("Noi dung bai rong.")
        body["content"] = content
    if a.media is not None:  # --media khong kem gia tri = xoa het anh
        body["mediaItems"] = [upload(cfg, m) if Path(m).exists() else {"type": "image", "url": m} for m in a.media]
    if a.first_comment is not None:  # --first-comment "" = xoa comment
        platforms = []
        for p in cur.get("platforms", []):
            acc = p.get("accountId")
            psd = dict(p.get("platformSpecificData") or {})
            if p.get("platform") == "facebook":
                if a.first_comment:
                    psd["firstComment"] = a.first_comment
                else:
                    psd.pop("firstComment", None)
            platforms.append({"platform": p.get("platform"), "accountId": acc.get("_id") if isinstance(acc, dict) else acc,
                              **({"platformSpecificData": psd} if psd else {})})
        body["platforms"] = platforms
    res = zapi(cfg, "PUT", f"/posts/{a.post_id}", body)
    p = res.get("post", res)
    if p.get("status") != "draft":
        die(f"Canh bao: sau khi cap nhat post o trang thai '{p.get('status')}', kiem tra ngay tren Zernio.")
    out({"ok": True, "post_id": a.post_id, "status": p.get("status"), "post_url": post_url(cfg, a.post_id),
         "updated": [k for k in ("content", "mediaItems", "platforms") if k in body],
         "note": "Draft da duoc cap nhat tai cho, khong tao post moi."})


def cmd_status(a):
    cfg = load()
    out({"post_url": post_url(cfg, a.post_id), **zapi(cfg, "GET", f"/posts/{a.post_id}")})


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("pages").set_defaults(f=cmd_pages)
    s = sp.add_parser("sync-accounts")
    s.add_argument("--write", action="store_true")
    s.set_defaults(f=cmd_sync)
    s = sp.add_parser("search-images")
    s.add_argument("query")
    s.add_argument("--source", choices=["commons", "openverse"], default="commons")
    s.add_argument("--limit", type=int, default=8)
    s.set_defaults(f=cmd_search)
    s = sp.add_parser("download")
    s.add_argument("url")
    s.add_argument("--name")
    s.set_defaults(f=cmd_download)
    s = sp.add_parser("upload")
    s.add_argument("file")
    s.set_defaults(f=cmd_upload)
    sp.add_parser("check").set_defaults(f=cmd_check)
    for n, f in (("validate", cmd_validate), ("draft", cmd_draft), ("schedule", cmd_schedule)):
        s = sp.add_parser(n)
        s.add_argument("--page")
        s.add_argument("--content-file", required=True)
        s.add_argument("--media", nargs="*", help="Duong dan file local hoac URL anh")
        s.add_argument("--first-comment")
        if n == "draft":
            s.add_argument("--intended-time", help="Gio user muon dang (chi ghi chu, KHONG len lich)")
        elif n == "schedule":
            s.add_argument("--time", required=True, help="ISO 8601, vd 2026-10-10T20:00:00")
            s.add_argument("--timezone")
            s.add_argument("--i-have-user-approval", action="store_true")
        s.set_defaults(f=f)
    s = sp.add_parser("update", help="Sua draft da tao, giu nguyen trang thai draft")
    s.add_argument("post_id")
    s.add_argument("--content-file")
    s.add_argument("--media", nargs="*", help="Thay toan bo anh; de trong de xoa anh")
    s.add_argument("--first-comment", help='Dat first comment; "" de xoa')
    s.set_defaults(f=cmd_update)
    s = sp.add_parser("status")
    s.add_argument("post_id")
    s.set_defaults(f=cmd_status)
    a = ap.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
