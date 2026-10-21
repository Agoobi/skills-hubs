#!/usr/bin/env python3
"""Cong cu cho skill viet-bai-zalo-oa. Chi dung thu vien chuan.

Lenh: oas | connect | connect-finish | connect-import | check | draft | update | list | detail
Bai luon tao o trang thai AN (status=hide): chu OA tu kiem tra va bat hien thi tren oa.zalo.me.
KHONG co lenh dang/hien bai, khong co lenh xoa. Ket qua in ra JSON de agent doc.
Token OA luu qua zalo_tokens.py (file ~/.hermes/zalo/tokens.json).
"""
import argparse, html, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import zalo_tokens as zt  # noqa: E402

SKILL = Path(__file__).resolve().parents[1]
SETTINGS = SKILL / "settings.json"
STATE = SKILL / "drafts"  # luu noi dung da gui de update (API update can gui lai du truong)
API = os.getenv("ZALO_ARTICLE_API") or "https://openapi.zalo.me/v2.0"  # env de test voi API gia lap
LIMITS = {"title": 150, "author": 50, "description": 300}
TOKEN_ERRORS = {-216, -124, -230}
LIST_ITEM = re.compile(r"^([-*+]|\d+[.)])\s+")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def out(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def die(msg, code=1, **extra):
    out({"ok": False, "error": msg, **extra})
    sys.exit(code)


def article_id(v):
    # id bai Zalo chi gom chu/so; chan ky tu nhu ../ vi id dung lam ten file drafts/<alias>-<id>.json
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", v):
        raise argparse.ArgumentTypeError("id bai khong hop le")
    return v


def load():
    if not SETTINGS.exists():
        die(f"Chua co {SETTINGS}. Copy settings.example.json -> settings.json roi dien OA.")
    try:
        os.chmod(SETTINGS, 0o600)
    except OSError:
        pass
    try:
        return json.loads(SETTINGS.read_text(encoding="utf-8"))
    except ValueError as e:
        die(f"{SETTINGS} khong phai JSON hop le: {e}")


def oa_of(cfg, alias):
    alias = alias or cfg.get("default_oa")
    o = (cfg.get("oas") or {}).get(alias)
    if not o:
        die(f"Khong co OA '{alias}'. OA da cau hinh: {list(cfg.get('oas') or {})}")
    if not str(o.get("oa_id", "")).isdigit():
        die(f"OA '{alias}': oa_id chua dung. Ket noi OA (connect) roi xem oa_id bang lenh oas.")
    return dict(o, alias=alias, oa_id=str(o["oa_id"]))


# ---------------------------------------------------------------- goi API

def call(oa, method, path, params=None, body=None):
    """Zalo tra loi HTTP 200 kem error != 0. Token bi tu choi -> lam moi 1 lan roi thu lai."""
    token = None
    for attempt in (0, 1):
        try:
            token = zt.access_token(oa["oa_id"], stale=token)
        except zt.ZaloAuthError as e:
            die(str(e))
        url = API + path + ("?" + urllib.parse.urlencode(params) if params else "")
        data = json.dumps(body, ensure_ascii=False).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method, headers={
            "access_token": token, "Content-Type": "application/json", "User-Agent": "agoobi-zalooa-skill/0.1"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                res = json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as e:
            die(f"HTTP {e.code} {path}: {e.read()[:300]!r}")
        except (urllib.error.URLError, OSError, ValueError) as e:
            die(f"Loi mang {path}: {e}")
        if res.get("error", 0) in TOKEN_ERRORS and attempt == 0:
            continue
        return res
    return res


def ok_or_die(res, what):
    if res.get("error", 0) != 0:
        die(f"Zalo tu choi {what}: error {res.get('error')} {res.get('message')}", hint=hint(res.get("error")))
    return res.get("data") or {}


def hint(code):
    return {-216: "Token sai/het han: chay lai connect.", -124: "Token het han: chay lai connect.",
            -230: "OA chua cap quyen cho app: chay lai connect va bat quyen quan ly bai viet.",
            -201: "Tham so sai (tieu de qua dai, anh bia khong tai duoc, thieu truong).",
            -224: "Goi API cua OA bi gioi han (OA chua xac thuc hoac het han muc)."}.get(code, "")


# ---------------------------------------------------------------- noi dung

def _inline(t):
    """Bai tao qua API: Zalo bo moi the HTML va doi xuong dong thanh dau cach (da kiem voi OA that),
    nen chi gui chu tron. Entity duoc giai ma, nen escape < > & de chu khong bi nuot nhu the."""
    t = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", lambda m: m[1] if m[1] == m[2] else f"{m[1]} ({m[2]})", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"\1", t)
    t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"\1", t)
    return html.escape(t, quote=False)


def md_to_body(md):
    """Markdown -> body cua bai Zalo. Moi doan, dong tieu de, y danh sach la 1 khoi text rieng
    (cach duy nhat de xuong dong); dong chi co anh la 1 khoi image (URL cong khai)."""
    items, para = [], []

    def text(t):
        items.append({"type": "text", "content": t})

    def flush():
        if para:
            text(_inline(" ".join(para)))
            para.clear()

    for line in md.replace("\r\n", "\n").split("\n"):
        st = line.strip()
        if not st:
            flush()
            continue
        img = re.fullmatch(r"!\[([^\]]*)\]\(([^)\s]+)\)", st)
        if img:
            if not img[2].startswith("https://"):
                die(f"Anh trong bai phai la URL https cong khai (Zalo tu tai ve): {img[2]}")
            flush()
            items.append({"type": "image", "url": img[2], "caption": img[1]})
            continue
        m = re.match(r"^#{1,6}\s+(.*)$", st)
        if m:
            flush()
            text(_inline(m[1]).upper())
            continue
        m = LIST_ITEM.match(st)
        if m:
            flush()
            mark = m[1] if st[0].isdigit() else "•"
            text(f"{mark} {_inline(LIST_ITEM.sub('', st))}")
            continue
        if st.startswith(">"):
            flush()
            text(f"“{_inline(st.lstrip('> '))}”")
            continue
        para.append(st)
    flush()
    return items


def read_content(path):
    text = Path(path).read_text(encoding="utf-8")
    title = None
    m = re.match(r"^\s*#\s+(.+)\n", text)
    if m:
        title, text = m[1].strip(), text[m.end():]
    return title, md_to_body(text)


def check_limits(art):
    for k, n in LIMITS.items():
        v = art.get(k) or ""
        if len(v) > n:
            die(f"{k} dai {len(v)} ky tu, toi da {n}: rut gon lai.")
    if not art.get("title"):
        die("Thieu tieu de: --title hoac dong '# Tieu de' dau file.")
    if not art.get("body"):
        die("Thieu noi dung: --content-file <file.md>.")
    cover = (art.get("cover") or {}).get("photo_url", "")
    if not cover.startswith("https://"):
        die("Anh bia (--cover) bat buoc va phai la URL https cong khai. Anh o may: upload len website "
            "(vd skill viet-bai-website-wordpress, lenh upload) roi dung source_url.")


def build(oa, a, base=None):
    art = dict(base or {"type": "normal", "author": oa.get("author") or oa.get("label") or "",
                        "comment": oa.get("comment", "show")})
    if a.content_file:
        title, body = read_content(a.content_file)
        art["body"] = body
        if title and not a.title:
            art["title"] = title
    if a.title:
        art["title"] = a.title
    if a.description is not None:
        art["description"] = a.description
    if a.author:
        art["author"] = a.author
    if a.cover:
        if not re.match(r"^https?://", a.cover):
            die("--cover phai la URL https cong khai (khong nhan file tren may).")
        art["cover"] = {"cover_type": "photo", "photo_url": a.cover, "status": "show"}
    if a.comment:
        art["comment"] = a.comment
    art["status"] = "hide"  # luon an: chu OA tu bat hien thi
    check_limits(art)
    return art


def save_state(oa, art_id, art):
    STATE.mkdir(exist_ok=True)
    (STATE / f"{oa['alias']}-{art_id}.json").write_text(json.dumps(art, ensure_ascii=False, indent=2), encoding="utf-8")


def verify(oa, token):
    """Zalo xu ly bai bat dong bo: create tra token, verify tra id khi xu ly xong."""
    last = {}
    for _ in range(8):
        last = call(oa, "POST", "/article/verify", body={"token": token})
        if last.get("error", 0) == 0 and (last.get("data") or {}).get("id"):
            return last["data"]["id"]
        time.sleep(2)
    die(f"Bai da gui nhung chua xac nhan duoc id: {last}. Kiem tra danh sach bai (list) sau it phut.",
        token=token)


def manage_url(oa):
    return "https://oa.zalo.me/manage/article"  # trang quan ly bai viet (dang nhap quyen admin OA)


# ---------------------------------------------------------------- lenh

def cmd_oas(a):
    cfg = load() if SETTINGS.exists() else {}
    connected = zt.list_oas()
    rows = [{"alias": k, "label": v.get("label"), "oa_id": v.get("oa_id"),
             "ket_noi": "co" if str(v.get("oa_id")) in connected else "CHUA"} for k, v in (cfg.get("oas") or {}).items()]
    out({"default_oa": cfg.get("default_oa"), "oas": rows, "token_file": str(zt.token_file()),
         "da_ket_noi": connected})


def cmd_connect(a):
    try:
        res = zt.auth_url(a.redirect)
    except zt.ZaloAuthError as e:
        die(str(e))
    out({"ok": True, **res, "next": "Gui link cho chu OA bam Dong y (chon OA, bat quyen quan ly bai viet). "
                                     "Sau do chay connect-finish \"<URL tren thanh dia chi>\"."})


def cmd_connect_finish(a):
    try:
        res = zt.complete(a.callback, a.name)
    except zt.ZaloAuthError as e:
        die(str(e))
    out({"ok": True, **res, "next": f"Dien oa_id {res['oa_id']} vao settings.json > oas."})


def cmd_connect_import(a):
    try:
        res = zt.import_from_env(a.oa_id)
    except zt.ZaloAuthError as e:
        die(str(e))
    out({"ok": True, **res, "next": f"Dien oa_id {res['oa_id']} vao settings.json > oas roi chay check."})


def cmd_check(a):
    oa = oa_of(load(), a.oa)
    info = ok_or_die(call(oa, "GET", "/oa/getoa"), "lay thong tin OA")
    arts = call(oa, "GET", "/article/getslice", params={"offset": 0, "limit": 1, "type": "normal"})
    out({"ok": True, "oa": oa["alias"], "oa_id": oa["oa_id"], "ten_oa": info.get("name"),
         "xac_thuc": info.get("is_verified"), "doc_bai_viet": arts.get("error", 0) == 0,
         "loi_bai_viet": None if arts.get("error", 0) == 0 else f"{arts.get('error')} {arts.get('message')}"})


def cmd_draft(a):
    oa = oa_of(load(), a.oa)
    art = build(oa, a)
    data = ok_or_die(call(oa, "POST", "/article/create", body=art), "tao bai")
    token = data.get("token")
    if not token:
        die(f"Zalo khong tra token: {data}")
    art_id = verify(oa, token)
    save_state(oa, art_id, art)
    out({"ok": True, "oa": oa["alias"], "id": art_id, "status": "hide", "title": art["title"],
         "manage_url": manage_url(oa),
         "next": "Bai dang AN. Chu OA vao trang quan ly bai viet, kiem tra roi bat Hien thi / gui broadcast."})


def cmd_update(a):
    oa = oa_of(load(), a.oa)
    f = STATE / f"{oa['alias']}-{a.id}.json"
    if not f.exists():
        die(f"Khong co ban luu cua bai {a.id} (chi sua duoc bai tao bang skill nay). Sua tren oa.zalo.me.")
    detail = ok_or_die(call(oa, "GET", "/article/getdetail", params={"id": a.id}), "doc bai")
    if detail.get("status") == "show":
        die(f"Bai {a.id} dang HIEN THI: khong sua bang skill. Chu OA an bai truoc hoac sua tren oa.zalo.me.")
    art = build(oa, a, json.loads(f.read_text(encoding="utf-8")))
    data = ok_or_die(call(oa, "POST", "/article/update", body={**art, "id": a.id}), "sua bai")
    if data.get("token"):
        verify(oa, data["token"])
    save_state(oa, a.id, art)
    out({"ok": True, "oa": oa["alias"], "id": a.id, "status": "hide", "title": art["title"], "manage_url": manage_url(oa)})


def cmd_list(a):
    oa = oa_of(load(), a.oa)
    data = ok_or_die(call(oa, "GET", "/article/getslice",
                          params={"offset": a.offset, "limit": min(a.limit, 50), "type": "normal"}), "lay danh sach")
    rows = [{k: m.get(k) for k in ("id", "title", "status", "total_view", "total_share", "create_date")}
            for m in data.get("medias") or []]
    out({"ok": True, "oa": oa["alias"], "total": data.get("total"), "articles": rows})


def cmd_detail(a):
    oa = oa_of(load(), a.oa)
    out({"ok": True, "oa": oa["alias"], **ok_or_die(call(oa, "GET", "/article/getdetail", params={"id": a.id}), "doc bai")})


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("oas", help="OA da cau hinh / da ket noi").set_defaults(f=cmd_oas)
    p = sp.add_parser("connect", help="Tao link cho chu OA cap quyen")
    p.add_argument("--redirect", required=True, help="Callback URL da khai bao trong app Zalo")
    p.set_defaults(f=cmd_connect)
    p = sp.add_parser("connect-finish", help="Dan URL callback sau khi chu OA dong y")
    p.add_argument("callback")
    p.add_argument("--name")
    p.set_defaults(f=cmd_connect_finish)
    p = sp.add_parser("connect-import", help="Nap token co san tu env ZALO_ACCESS_TOKEN, ZALO_REFRESH_TOKEN")
    p.add_argument("--oa-id", help="Bo trong thi doc tu access token")
    p.set_defaults(f=cmd_connect_import)

    def oa_arg(p):
        p.add_argument("--oa", help="alias OA (mac dinh default_oa)")
        return p

    oa_arg(sp.add_parser("check", help="Kiem tra token, thong tin OA, quyen bai viet")).set_defaults(f=cmd_check)

    def art_args(p):
        oa_arg(p)
        p.add_argument("--title")
        p.add_argument("--content-file", help=".md, dong '# Tieu de' dau file = tieu de")
        p.add_argument("--description", help="Mo ta ngan (<= 300 ky tu)")
        p.add_argument("--author")
        p.add_argument("--cover", help="URL https anh bia")
        p.add_argument("--comment", choices=["show", "hide"])

    p = sp.add_parser("draft", help="Tao bai (trang thai AN)")
    art_args(p)
    p.set_defaults(f=cmd_draft)
    p = sp.add_parser("update", help="Sua bai dang an da tao bang skill")
    p.add_argument("id", type=article_id)
    art_args(p)
    p.set_defaults(f=cmd_update)
    p = oa_arg(sp.add_parser("list"))
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--limit", type=int, default=10)
    p.set_defaults(f=cmd_list)
    p = oa_arg(sp.add_parser("detail"))
    p.add_argument("id", type=article_id)
    p.set_defaults(f=cmd_detail)
    a = ap.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
