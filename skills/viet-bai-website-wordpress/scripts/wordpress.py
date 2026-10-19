#!/usr/bin/env python3
"""Cong cu cho skill viet-bai-website-wordpress. Chi dung thu vien chuan.

Lenh: sites | check | terms | upload | draft | update | status | schedule
Dang nhap bang Application Password (WordPress 5.6+): Basic auth "user:app password".
KHONG co lenh dang ngay: bai luon la draft (hoac "pending" cho duyet). Len lich chi khi user duyet ro rang.
Ket qua in ra JSON de agent doc.
"""
import argparse, base64, html, json, mimetypes, os, re, sys, urllib.error, urllib.parse, urllib.request, unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

SKILL = Path(__file__).resolve().parents[1]
SETTINGS = SKILL / "settings.json"
UA = "Mozilla/5.0 (compatible; agoobi-wordpress-skill/0.1; +https://github.com/Agoobi/skills-hubs)"
MAX_MEDIA = 20 * 1024 * 1024
EDITABLE = {"draft", "pending", "auto-draft"}

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def out(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def die(msg, code=1, **extra):
    out({"ok": False, "error": msg, **extra})
    sys.exit(code)


# ---------------------------------------------------------------- cau hinh

def load():
    if not SETTINGS.exists():
        die(f"Chua co {SETTINGS}. Copy settings.example.json -> settings.json roi dien site.")
    return json.loads(SETTINGS.read_text(encoding="utf-8"))


def env_key(alias):
    return "WP_APP_PASSWORD_" + re.sub(r"[^A-Z0-9]", "_", alias.upper())


def site_of(cfg, alias):
    alias = alias or cfg.get("default_site")
    s = (cfg.get("sites") or {}).get(alias)
    if not s:
        die(f"Khong co site '{alias}'. Site da cau hinh: {list(cfg.get('sites') or {})}")
    s = dict(s, alias=alias)
    s["url"] = (s.get("url") or "").rstrip("/")
    s["app_password"] = os.environ.get(env_key(alias)) or s.get("app_password") or ""
    if not s["url"].startswith(("https://", "http://")) or "example" in s["url"]:
        die(f"Site '{alias}': url chua dung (vd https://shop.vn).")
    if not s.get("username") or not s["app_password"] or "DAN_" in s["app_password"]:
        die(f"Site '{alias}': thieu username/app_password (hoac env {env_key(alias)}).")
    return s


# ---------------------------------------------------------------- HTTP

class WPError(Exception):
    def __init__(self, status, code, message, body=None):
        super().__init__(f"HTTP {status} {code}: {message}")
        self.status, self.code, self.message, self.body = status, code, message, body


def _auth(s):
    pw = s["app_password"].replace(" ", "")  # WordPress hien mat khau co dau cach; bo hay giu deu duoc
    return "Basic " + base64.b64encode(f"{s['username']}:{pw}".encode()).decode()


def _url(s, route, params=None):
    """route vd '/wp/v2/posts'. Dung /wp-json/ hoac ?rest_route= (permalink 'Plain' hoac /wp-json bi chan)."""
    params = {k: v for k, v in (params or {}).items() if v is not None}
    if s.get("_rest_route"):
        return s["url"] + "/?" + urllib.parse.urlencode({"rest_route": route, **params})
    q = ("?" + urllib.parse.urlencode(params)) if params else ""
    return s["url"] + "/wp-json" + route + q


def request(s, method, route, params=None, body=None, raw=None, headers=None, auth=True):
    h = {"User-Agent": UA, "Accept": "application/json", **(headers or {})}
    if auth:
        h["Authorization"] = _auth(s)
    data = None
    if raw is not None:
        data = raw
    elif body is not None:
        data = json.dumps(body).encode()
        h["Content-Type"] = "application/json; charset=utf-8"
    req = urllib.request.Request(_url(s, route, params), data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            txt = r.read()
            ctype = r.headers.get("Content-Type", "")
            if "json" not in ctype:
                raise WPError(r.status, "not_json", f"Khong phai JSON ({ctype or 'khong ro'}): {txt[:120]!r}")
            return json.loads(txt) if txt else {}, r.headers
    except urllib.error.HTTPError as e:
        raw_body = e.read().decode(errors="replace")
        try:
            j = json.loads(raw_body)
            raise WPError(e.code, j.get("code", ""), j.get("message", ""), j)
        except (ValueError, AttributeError):
            raise WPError(e.code, "http", raw_body[:300])
    except urllib.error.URLError as e:
        raise WPError(0, "network", str(e.reason))


def api(s, method, route, **kw):
    """Goi REST; tu chuyen sang ?rest_route= neu /wp-json khong dung duoc. Loi -> die() co goi y."""
    try:
        try:
            return request(s, method, route, **kw)[0]
        except WPError as e:
            # /wp-json tra trang HTML (permalink Plain, rewrite tat): thu ?rest_route=. Loi JSON cua WP thi giu nguyen.
            if not s.get("_rest_route") and e.code in ("not_json", "http") and e.status in (200, 404):
                s["_rest_route"] = True
                return request(s, method, route, **kw)[0]
            raise
    except WPError as e:
        die(str(e), hint=hint(e), route=route)


def hint(e):
    if e.status == 401 or e.code in ("rest_not_logged_in", "incorrect_password", "invalid_username"):
        return ("Sai user/app password; hoac host xoa header Authorization (Apache CGI/FastCGI: them vao .htaccess "
                "'SetEnvIf Authorization \"(.*)\" HTTP_AUTHORIZATION=$1'); hoac plugin bao mat (Wordfence, iThemes) "
                "tat Application Passwords / REST API.")
    if e.status == 403 or e.code.startswith("rest_cannot"):
        return "Tai khoan khong du quyen (can Editor/Administrator de dang bai, upload anh, tao tag)."
    if e.code == "not_json":
        return "REST API bi chan hoac tra ve trang HTML (firewall, Cloudflare, plugin tat REST)."
    if e.status == 0:
        return "Khong ket noi duoc site (sai domain, site sap, chan IP)."
    return ""


# ---------------------------------------------------------------- markdown -> HTML

def _inline(t):
    t = html.escape(t, quote=False)
    # t da escape (& < >), chi con phai thay dau nhay trong thuoc tinh
    t = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)",
               lambda m: f'<img src="{m[2].replace(chr(34), "%22")}" alt="{m[1].replace(chr(34), "&quot;")}" />', t)
    t = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", lambda m: f'<a href="{m[2].replace(chr(34), "%22")}">{m[1]}</a>', t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    return t


def md_to_html(md):
    """Markdown co ban -> HTML (hien trong khoi Classic cua Gutenberg; bam 'Convert to blocks' neu muon)."""
    lines, outp, para, lst = md.replace("\r\n", "\n").split("\n"), [], [], None

    def flush():
        nonlocal para, lst
        if para:
            outp.append("<p>" + "<br />".join(_inline(x) for x in para) + "</p>")
            para = []
        if lst:
            tag, items = lst
            outp.append(f"<{tag}>" + "".join(f"<li>{_inline(i)}</li>" for i in items) + f"</{tag}>")
            lst = None

    for line in lines:
        st = line.strip()
        if not st:
            flush()
            continue
        if st.startswith("<") and st.endswith(">"):  # dong HTML co san: giu nguyen
            flush()
            outp.append(st)
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", st)
        if m:
            flush()
            level = max(2, len(m[1]))  # H1 la tieu de bai, noi dung bat dau tu H2
            outp.append(f"<h{level}>{_inline(m[2])}</h{level}>")
            continue
        m = re.match(r"^([-*+]|\d+[.)])\s+(.*)$", st)
        if m:
            tag = "ol" if m[1][0].isdigit() else "ul"
            if para:
                flush()
            if lst and lst[0] != tag:
                flush()
            lst = lst or (tag, [])
            lst[1].append(m[2])
            continue
        if st.startswith(">"):
            flush()
            outp.append(f"<blockquote><p>{_inline(st.lstrip('> '))}</p></blockquote>")
            continue
        if re.match(r"^(-{3,}|\*{3,})$", st):
            flush()
            outp.append("<hr />")
            continue
        if lst:
            flush()
        para.append(st)
    flush()
    return "\n".join(outp)


def read_content(path):
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if p.suffix.lower() in (".html", ".htm"):
        return text, None
    title = None
    m = re.match(r"^\s*#\s+(.+)\n", text)
    if m:  # dong "# Tieu de" dau file la tieu de bai, khong dua vao noi dung
        title, text = m[1].strip(), text[m.end():]
    return md_to_html(text), title


# ---------------------------------------------------------------- media

def _load_media(src):
    if re.match(r"^https?://", src):
        req = urllib.request.Request(src, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read(MAX_MEDIA + 1)
                ctype = (r.headers.get("Content-Type") or "").split(";")[0]
        except (urllib.error.URLError, OSError) as e:
            die(f"Khong tai duoc anh {src}: {e}")
        name = Path(urllib.parse.urlparse(src).path).name or "anh"
    else:
        p = Path(src).expanduser()
        if not p.is_file():
            die(f"Khong thay file {src}")
        data = p.read_bytes()[:MAX_MEDIA + 1]
        ctype, name = mimetypes.guess_type(p.name)[0] or "", p.name
    if len(data) > MAX_MEDIA:
        die(f"Anh qua lon (> {MAX_MEDIA // 1024 // 1024}MB): {src}")
    if not ctype.startswith("image/"):
        die(f"Khong phai anh ({ctype or 'khong ro loai'}): {src}")
    if "." not in name:
        name += mimetypes.guess_extension(ctype) or ".jpg"
    return data, ctype, safe_name(name)


def safe_name(name):
    stem, ext = os.path.splitext(name)
    stem = unicodedata.normalize("NFKD", stem.replace("đ", "d").replace("Đ", "D")).encode("ascii", "ignore").decode()
    stem = re.sub(r"[^A-Za-z0-9_-]+", "-", stem).strip("-")[:60] or "anh"
    return stem + ext.lower()


def upload(s, src, alt=None, caption=None, title=None):
    if str(src).isdigit():  # da la media id
        m = api(s, "GET", f"/wp/v2/media/{src}", params={"context": "edit"})
        return {"id": m["id"], "url": m.get("source_url")}
    data, ctype, name = _load_media(src)
    m = api(s, "POST", "/wp/v2/media", raw=data, headers={
        "Content-Type": ctype, "Content-Disposition": f'attachment; filename="{name}"'})
    meta = {k: v for k, v in {"alt_text": alt, "caption": caption, "title": title}.items() if v}
    if meta:
        api(s, "POST", f"/wp/v2/media/{m['id']}", body=meta)
    return {"id": m["id"], "url": m.get("source_url"), "file": name}


def upload_inline_images(s, content, base_dir="."):
    """Anh local/URL ngoai trong noi dung -> upload vao Media Library, thay src. Anh da tren site giu nguyen."""
    host = urllib.parse.urlparse(s["url"]).netloc
    done = {}

    def repl(m):
        src = html.unescape(m[2])
        if urllib.parse.urlparse(src).netloc == host or src.startswith("data:"):
            return m[0]
        if not re.match(r"^https?://", src):
            src = str((Path(base_dir) / src).expanduser())
        if src not in done:
            done[src] = upload(s, src, alt=html.unescape(m[4] or "") or None)
        return f'{m[1]}{html.escape(done[src]["url"])}{m[3]}'

    content = re.sub(r'(<img\s[^>]*?src=")([^"]+)("[^>]*?(?:\salt="([^"]*)")?[^>]*>)', repl, content)
    return content, list(done.values())


# ---------------------------------------------------------------- terms

def all_terms(s, tax):
    items, page = [], 1
    while True:
        batch = api(s, "GET", f"/wp/v2/{tax}", params={"per_page": 100, "page": page, "context": "view",
                                                       "_fields": "id,name,slug,count,parent"})
        items += batch
        if len(batch) < 100:
            return items
        page += 1


def norm(t):
    t = unicodedata.normalize("NFKD", html.unescape(str(t)).lower().replace("đ", "d"))
    return "".join(c for c in t if not unicodedata.combining(c)).strip()


def resolve_terms(s, tax, wanted, create=False):
    """wanted: danh sach ten/slug/id. Category khong tu tao (sai chinh ta tao rac); tag tao khi create=True."""
    if not wanted:
        return []
    existing = all_terms(s, tax)
    ids, missing = [], []
    for w in wanted:
        w = str(w).strip()
        if not w:
            continue
        hit = next((t for t in existing if str(t["id"]) == w or norm(t["name"]) == norm(w) or t["slug"] == w), None)
        if hit:
            ids.append(hit["id"])
        elif create:
            ids.append(api(s, "POST", f"/wp/v2/{tax}", body={"name": w})["id"])
        else:
            missing.append(w)
    if missing:
        die(f"Khong co {tax}: {missing}. Chon trong danh sach (lenh terms) hoac nho user tao tren WordPress.",
            available=[t["name"] for t in existing][:50])
    return ids


# ---------------------------------------------------------------- bai viet

def links(s, post):
    pid = post["id"]
    return {"edit_url": f"{s['url']}/wp-admin/post.php?post={pid}&action=edit",
            "preview_url": f"{s['url']}/?p={pid}&preview=true", "link": post.get("link")}


def summary(s, post, extra=None):
    r = {"ok": True, "site": s["alias"], "id": post["id"], "status": post.get("status"),
         "title": (post.get("title") or {}).get("raw") or (post.get("title") or {}).get("rendered"),
         "date": post.get("date"), "modified": post.get("modified"), **links(s, post)}
    return {**r, **(extra or {})}


def build_body(s, a, creating):
    body, extra = {}, {}
    title_from_file = None
    if a.content_file:
        content, title_from_file = read_content(a.content_file)
        content, imgs = upload_inline_images(s, content, Path(a.content_file).parent)
        body["content"] = content
        if imgs:
            extra["inline_images"] = imgs
    title = a.title or title_from_file
    if title:
        body["title"] = title
    if a.excerpt is not None:
        body["excerpt"] = a.excerpt
    if a.slug:
        body["slug"] = a.slug
    if a.categories is not None:
        body["categories"] = resolve_terms(s, "categories", a.categories)
    elif creating and s.get("default_category"):
        body["categories"] = resolve_terms(s, "categories", [s["default_category"]])
    if a.tags is not None:
        body["tags"] = resolve_terms(s, "tags", a.tags, create=True)
    if a.featured is not None:
        if a.featured == "":
            body["featured_media"] = 0
        else:
            m = upload(s, a.featured, alt=a.featured_alt or title)
            body["featured_media"] = m["id"]
            extra["featured"] = m
    if creating and not body.get("title"):
        die("Thieu tieu de: --title hoac dong '# Tieu de' dau file noi dung.")
    if creating and not body.get("content"):
        die("Thieu noi dung: --content-file <file.md|.html>.")
    return body, extra


def cmd_sites(a):
    cfg = load()
    rows = []
    for alias, s in (cfg.get("sites") or {}).items():
        pw = os.environ.get(env_key(alias)) or s.get("app_password") or ""
        rows.append({"alias": alias, "label": s.get("label"), "url": s.get("url"), "username": s.get("username"),
                     "app_password": "da co" if pw and "DAN_" not in pw else "THIEU",
                     "default_category": s.get("default_category"), "timezone": s.get("timezone")})
    out({"default_site": cfg.get("default_site"), "sites": rows})


def cmd_check(a):
    s = site_of(load(), a.site)
    info = {}
    try:
        root, _ = request(s, "GET", "/", auth=False)
    except WPError:
        s["_rest_route"] = True
        try:
            root, _ = request(s, "GET", "/", auth=False)
        except WPError as e:
            die(f"Khong goi duoc REST API: {e}", hint=hint(e))
    ns = root.get("namespaces") or []
    info["site_name"] = html.unescape(root.get("name") or "")
    info["rest"] = "?rest_route=" if s.get("_rest_route") else "/wp-json"
    info["timezone"] = root.get("timezone_string") or f"UTC{root.get('gmt_offset')}"
    info["application_passwords"] = "application-passwords" in json.dumps(root.get("authentication") or {})
    info["seo_plugin"] = [n for n in ns if n.startswith(("yoast", "rankmath", "aioseo", "seopress"))]
    me = api(s, "GET", "/wp/v2/users/me", params={"context": "edit"})
    caps = me.get("capabilities") or {}
    need = ["edit_posts", "publish_posts", "upload_files", "manage_categories"]
    info["user"] = {"username": me.get("username"), "roles": me.get("roles"),
                    "thieu_quyen": [c for c in need if not caps.get(c)]}
    tz_cfg = s.get("timezone")
    if tz_cfg and root.get("timezone_string") and tz_cfg != root["timezone_string"]:
        info["canh_bao_timezone"] = f"settings ({tz_cfg}) khac site ({root['timezone_string']})"
    ok = not info["user"]["thieu_quyen"] or info["user"]["thieu_quyen"] == ["manage_categories"]
    out({"ok": ok, "site": s["alias"], **info,
         "note": "manage_categories thieu thi khong tao duoc tag moi (chi gan tag co san)." if ok and info["user"]["thieu_quyen"] else None})


def cmd_terms(a):
    s = site_of(load(), a.site)
    res = {}
    for tax in ("categories", "tags"):
        items = all_terms(s, tax)
        if a.search:
            items = [t for t in items if norm(a.search) in norm(t["name"])]
        items.sort(key=lambda t: -t.get("count", 0))
        res[tax] = [{"id": t["id"], "name": html.unescape(t["name"]), "slug": t["slug"], "count": t.get("count")}
                    for t in items[: a.limit]]
    out({"ok": True, "site": s["alias"], **res})


def cmd_upload(a):
    s = site_of(load(), a.site)
    out({"ok": True, "site": s["alias"], **upload(s, a.file, a.alt, a.caption, a.title)})


def cmd_draft(a):
    s = site_of(load(), a.site)
    body, extra = build_body(s, a, creating=True)
    body["status"] = "pending" if a.pending else "draft"
    post = api(s, "POST", "/wp/v2/posts", body=body)
    out(summary(s, post, {**extra, "next": "Gui user edit_url/preview_url. User tu bam Publish tren WordPress."}))


def get_post(s, pid):
    return api(s, "GET", f"/wp/v2/posts/{pid}", params={"context": "edit"})


def cmd_update(a):
    s = site_of(load(), a.site)
    post = get_post(s, a.id)
    if post.get("status") not in EDITABLE:
        die(f"Bai {a.id} dang '{post.get('status')}' (da dang/len lich): khong sua bang skill. Nho user sua tren WordPress.")
    body, extra = build_body(s, a, creating=False)
    if not body:
        die("Khong co gi de sua (dung --title/--content-file/--excerpt/--categories/--tags/--featured/--slug).")
    body["status"] = post["status"] if post["status"] != "auto-draft" else "draft"
    post = api(s, "POST", f"/wp/v2/posts/{a.id}", body=body)
    out(summary(s, post, {**extra, "changed": sorted(k for k in body if k != "status")}))


def cmd_status(a):
    s = site_of(load(), a.site)
    post = get_post(s, a.id)
    out(summary(s, post, {"categories": post.get("categories"), "tags": post.get("tags"),
                          "featured_media": post.get("featured_media"), "date_gmt": post.get("date_gmt")}))


def cmd_schedule(a):
    if not a.i_have_user_approval:
        die("Len lich can user duyet ro rang. Them --i-have-user-approval sau khi user dong y gio dang.")
    s = site_of(load(), a.site)
    tz = ZoneInfo(a.timezone or s.get("timezone") or "Asia/Ho_Chi_Minh")
    try:
        local = datetime.strptime(a.time, "%Y-%m-%d %H:%M").replace(tzinfo=tz)
    except ValueError:
        die("--time dang 'YYYY-MM-DD HH:MM' theo gio cua site.")
    utc = local.astimezone(timezone.utc)
    if utc < datetime.now(timezone.utc) + timedelta(minutes=5):  # WordPress dang NGAY neu gio da qua
        die(f"Gio {a.time} ({tz.key}) da qua hoac con duoi 5 phut: WordPress se dang ngay. Chon gio khac.")
    post = get_post(s, a.id)
    if post.get("status") not in EDITABLE:
        die(f"Bai {a.id} dang '{post.get('status')}': chi len lich bai draft/pending.")
    post = api(s, "POST", f"/wp/v2/posts/{a.id}", body={"status": "future", "date_gmt": utc.strftime("%Y-%m-%dT%H:%M:%S")})
    if post.get("status") != "future":
        die(f"WordPress tra ve status '{post.get('status')}' thay vi 'future'.", post=summary(s, post))
    out(summary(s, post, {"scheduled_local": local.isoformat(), "scheduled_gmt": post.get("date_gmt"),
                          "note": "Bai se TU DANG vao gio nay. Muon huy: tren WordPress doi lai thanh Draft."}))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("sites", help="Liet ke site da cau hinh").set_defaults(f=cmd_sites)

    def site_arg(p):
        p.add_argument("--site", help="alias site (mac dinh default_site)")
        return p

    site_arg(sp.add_parser("check", help="Kiem tra ket noi, quyen, REST, plugin SEO")).set_defaults(f=cmd_check)
    p = site_arg(sp.add_parser("terms", help="Chuyen muc va the"))
    p.add_argument("--search")
    p.add_argument("--limit", type=int, default=50)
    p.set_defaults(f=cmd_terms)
    p = site_arg(sp.add_parser("upload", help="Upload anh vao Media Library"))
    p.add_argument("file", help="file local hoac URL")
    p.add_argument("--alt")
    p.add_argument("--caption")
    p.add_argument("--title")
    p.set_defaults(f=cmd_upload)

    def post_args(p, creating):
        site_arg(p)
        p.add_argument("--title")
        p.add_argument("--content-file", help=".md (dong '# Tieu de' dau file = tieu de) hoac .html")
        p.add_argument("--excerpt", help="Tom tat / mo ta ngan (cung dung lam meta description neu theme/SEO plugin lay excerpt)")
        p.add_argument("--slug")
        p.add_argument("--categories", nargs="*", help="Ten/slug/id chuyen muc CO SAN")
        p.add_argument("--tags", nargs="*", help="Ten the (chua co thi tao)")
        p.add_argument("--featured", help="Anh dai dien: file, URL hoac media id; '' de bo")
        p.add_argument("--featured-alt")
        if creating:
            p.add_argument("--pending", action="store_true", help="Trang thai 'Cho duyet' thay vi Draft")

    p = sp.add_parser("draft", help="Tao bai DRAFT")
    post_args(p, True)
    p.set_defaults(f=cmd_draft)
    p = sp.add_parser("update", help="Sua bai draft/pending (khong doi trang thai)")
    p.add_argument("id", type=int)
    post_args(p, False)
    p.set_defaults(f=cmd_update)
    p = site_arg(sp.add_parser("status"))
    p.add_argument("id", type=int)
    p.set_defaults(f=cmd_status)
    p = site_arg(sp.add_parser("schedule", help="Len lich dang (chi khi user duyet ro rang)"))
    p.add_argument("id", type=int)
    p.add_argument("--time", required=True, help="YYYY-MM-DD HH:MM theo gio site")
    p.add_argument("--timezone")
    p.add_argument("--i-have-user-approval", action="store_true")
    p.set_defaults(f=cmd_schedule)
    a = ap.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
