#!/usr/bin/env python3
"""Lich dang: dua bai vao lich dang cua Open WebUI (openwebui-custom), xem truoc trong chat, hen gio dang.

Bai nam trong Lich dang cua Open WebUI; dung gio, may chu gui di: WordPress qua REST API (Dang that / Luu nhap) hoac
Zalo OA (Hien ngay / Tao bai an). Nguoi dung xem, doi gio, huy lich ngay tren trang "Lich dang" cua Open WebUI.
Cung 1 file trong skill viet-bai-website-wordpress va viet-bai-zalo-oa (tu chua, khong import file khac).

Lenh: status | sites | categories | slots | save | media | preview | schedule | unschedule | mode | get | list
Ket qua in JSON de agent doc. Chi dung thu vien chuan (Python 3.9+).

Token: <DATA_DIR cua Open WebUI>/cqf/lich/agent.json (doc truc tiep, cung may). Dia chi API: env LICH_API, mac dinh
http://127.0.0.1:8080/api/v1/cqf/lich. Agent KHONG duoc sua ket noi WordPress hay Cai dat (API tu choi).
"""
from __future__ import annotations

import argparse, html, json, mimetypes, os, re, sys, unicodedata, urllib.error, urllib.parse, urllib.request, uuid
from html.parser import HTMLParser
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]

API = os.environ.get("LICH_API", "http://127.0.0.1:8080/api/v1/cqf/lich")
AGENT_FILES = [os.environ.get("LICH_AGENT_FILE", ""), "/opt/open-webui/data/cqf/lich/agent.json",
               "/app/backend/data/cqf/lich/agent.json"]
MEDIA_PREFIX = "/api/v1/cqf/lich/media/"
UA = "lich-dang-agent/1.0 (+viet-bai-website-wordpress)"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def out(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def die(msg, **extra):
    out({"ok": False, "error": msg, **extra})
    sys.exit(1)


def token():
    for f in AGENT_FILES:
        if f and Path(f).is_file():
            try:
                return json.loads(Path(f).read_text())["token"]
            except (ValueError, KeyError, OSError):
                continue
    die("Chua co Lich dang tren may nay (khong thay agent.json). Cai openwebui-custom ban co Lich dang, hoac dung "
        "wordpress.py draft nhu cu.", hint="https://github.com/Agoobi/openwebui-custom")


def call(method, path, body=None, raw=None, ctype=None):
    headers = {"X-Lich-Agent-Token": token(), "User-Agent": UA, "Accept": "application/json"}
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    elif raw is not None:
        data, headers["Content-Type"] = raw, ctype
    req = urllib.request.Request(API + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            text = r.read().decode()
            return json.loads(text) if text else {}
    except urllib.error.HTTPError as e:
        try:
            detail = json.loads(e.read().decode()).get("detail")
        except ValueError:
            detail = None
        if isinstance(detail, list):
            detail = "; ".join(str(x.get("msg")) for x in detail)
        die(detail or f"Lich dang tra loi {e.code}", status=e.code)
    except (urllib.error.URLError, OSError) as e:
        die(f"Khong goi duoc Lich dang ({API}): {e}. Open WebUI co dang chay khong?")


def multipart(field, filename, data, ctype):
    boundary = uuid.uuid4().hex
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{field}\"; filename=\"{filename}\"\r\n"
            f"Content-Type: {ctype}\r\n\r\n").encode() + data + f"\r\n--{boundary}--\r\n".encode()
    return body, f"multipart/form-data; boundary={boundary}"


def load_image(src):
    if re.match(r"^https?://", src):
        req = urllib.request.Request(src, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read(8 * 1024 * 1024 + 1)
                ctype = (r.headers.get("Content-Type") or "").split(";")[0]
        except (urllib.error.URLError, OSError) as e:
            die(f"Khong tai duoc anh {src}: {e}")
        name = Path(urllib.parse.urlparse(src).path).name or "anh"
    else:
        p = Path(src).expanduser()
        if not p.is_file():
            die(f"Khong thay file anh {src}")
        data, ctype, name = p.read_bytes(), mimetypes.guess_type(p.name)[0] or "", p.name
    if not ctype.startswith("image/"):
        die(f"Khong phai anh ({ctype or 'khong ro loai'}): {src}")
    if "." not in name:
        name += mimetypes.guess_extension(ctype) or ".jpg"
    return data, ctype, safe_name(name)


# ------------------------------------------------------------------ Markdown -> HTML (Lich dang luu HTML)

def _inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)",
               lambda m: f'<img src="{m[2].replace(chr(34), "%22")}" alt="{m[1].replace(chr(34), "&quot;")}" />', t)
    t = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", lambda m: f'<a href="{m[2].replace(chr(34), "%22")}">{m[1]}</a>', t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    return t


def md_to_html(md):
    """Markdown co ban -> HTML. Dong chi co anh la 1 khoi anh rieng (Zalo OA can vay)."""
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
        if re.fullmatch(r"!\[[^\]]*\]\([^)\s]+\)", st):
            flush()
            outp.append(_inline(st))
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


def safe_name(name):
    stem, ext = os.path.splitext(name)
    stem = unicodedata.normalize("NFKD", stem.replace("đ", "d").replace("Đ", "D")).encode("ascii", "ignore").decode()
    stem = re.sub(r"[^A-Za-z0-9_-]+", "-", stem).strip("-")[:60] or "anh"
    return stem + ext.lower()


# ------------------------------------------------------------------ noi dang (alias cua skill -> site / OA trong Lich dang)

def skill_sites():
    """alias -> {"url": ...} (site WordPress) hoac {"oa_id": ...} (Zalo OA), tu settings.json cua skill."""
    f = SKILL / "settings.json"
    if not f.is_file():
        return {}, None
    cfg = json.loads(f.read_text(encoding="utf-8"))
    return {**cfg.get("sites", {}), **cfg.get("oas", {})}, cfg.get("default_site") or cfg.get("default_oa")


def lich_site(wanted):
    """wanted: alias trong settings.json cua skill, ten / url / id site trong Lich dang, hoac rong (mac dinh)."""
    me = call("GET", "/me")
    sites = me["sites"]
    if not sites:
        die("Lich dang chua co noi dang nao. Nho nguoi dung vao Open WebUI > Lich dang > Cai dat > Ket noi de them "
            "site WordPress hoac Zalo OA (agent khong tu them duoc).")
    aliases, default_alias = skill_sites()
    wanted = wanted or default_alias
    if not wanted:
        default = me["settings"].get("default_site_id")
        return next((s for s in sites if s["id"] == default), sites[0]), me
    entry = aliases.get(wanted) or {}
    url = entry.get("url", "").rstrip("/")
    oa_id = str(entry.get("oa_id") or "")
    for s in sites:
        if (wanted in (s["id"], s["name"]) or (url and s["url"].rstrip("/") == url)
                or (oa_id and s.get("oa_id") == oa_id) or s["url"].rstrip("/") == wanted.rstrip("/")):
            return s, me
    die(f"Khong thay site '{wanted}' trong Lich dang.", sites=[{"name": s["name"], "url": s["url"]} for s in sites])


def site_view(s):
    where = f"Zalo OA {s.get('oa_id')}" if s.get("kind") == "zalo_oa" else s["url"]
    return {"name": s["name"], "kenh": s.get("kind_label", "WordPress"), "dia_chi": where,
            "ket_noi": "ok" if s["check_ok"] else (s["check_error"] or "chua kiem tra")}


# ------------------------------------------------------------------ HTML -> Markdown (xem truoc trong chat)

class _ToMd(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.href, self.lists, self.cell, self.row, self.rows = [], None, [], None, None, None

    def emit(self, text):
        if self.cell is not None:
            self.cell.append(text)
        else:
            self.out.append(text)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("h1", "h2", "h3", "h4"):
            self.emit("\n\n" + "#" * max(2, int(tag[1])) + " ")
        elif tag == "p":
            self.emit("\n\n")
        elif tag == "br":
            self.emit("  \n")
        elif tag in ("strong", "b"):
            self.emit("**")
        elif tag in ("em", "i"):
            self.emit("*")
        elif tag == "a":
            self.href = a.get("href")
            self.emit("[")
        elif tag == "img":
            self.emit(f"\n\n![{a.get('alt', '')}]({a.get('src', '')})\n\n")
        elif tag in ("ul", "ol"):
            self.lists.append([tag, 0])
            self.emit("\n")
        elif tag == "li" and self.lists:
            self.lists[-1][1] += 1
            mark = f"{self.lists[-1][1]}." if self.lists[-1][0] == "ol" else "-"
            self.emit("\n" + "  " * (len(self.lists) - 1) + mark + " ")
        elif tag == "blockquote":
            self.emit("\n\n> ")
        elif tag == "table":
            self.rows = []
        elif tag == "tr" and self.rows is not None:
            self.row = []
        elif tag in ("td", "th") and self.row is not None:
            self.cell = []
        elif tag == "hr":
            self.emit("\n\n---\n\n")

    def handle_endtag(self, tag):
        if tag in ("strong", "b"):
            self.emit("**")
        elif tag in ("em", "i"):
            self.emit("*")
        elif tag == "a":
            self.emit(f"]({self.href or ''})")
            self.href = None
        elif tag in ("ul", "ol") and self.lists:
            self.lists.pop()
            self.emit("\n")
        elif tag in ("td", "th") and self.cell is not None and self.row is not None:
            self.row.append(" ".join("".join(self.cell).split()).replace("|", "\\|"))
            self.cell = None
        elif tag == "tr" and self.row is not None and self.rows is not None:
            self.rows.append(self.row)
            self.row = None
        elif tag == "table" and self.rows is not None:
            rows, self.rows = self.rows, None
            if rows:
                width = max(len(r) for r in rows)
                rows = [r + [""] * (width - len(r)) for r in rows]
                lines = ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * width]
                lines += ["| " + " | ".join(r) + " |" for r in rows[1:]]
                self.out.append("\n\n" + "\n".join(lines) + "\n\n")

    def handle_data(self, data):
        if self.rows is not None and self.cell is None:
            return
        self.emit(re.sub(r"\s+", " ", data))


def html_to_md(text):
    p = _ToMd()
    p.feed(text)
    md = "".join(p.out)
    return re.sub(r"\n{3,}", "\n\n", md).strip()


def zalo_preview_md(post, me, site, when):
    """Bai Zalo nhu tren ung dung: chu thuong tung doan, anh rieng dong (Zalo bo chu dam, link)."""
    blocks = call("GET", f"/posts/{post['id']}/zalo")["blocks"]
    author = ((site or {}).get("options") or {}).get("author") or (site or {}).get("name", "")
    rows = [
        ("Zalo OA", site["name"] if site else "chưa chọn"),
        ("Giờ đăng", when),
        ("Chế độ", post["mode_label"]),
        ("Trạng thái", post["state_label"]),
        ("Tác giả", author),
        ("Mô tả ngắn", f"{post['excerpt'] or '—'} ({len(post['excerpt'] or '')}/300 ký tự)"),
        ("Tiêu đề", f"{len(post['title'])}/150 ký tự"),
    ]
    head = "\n".join(f"| {k} | {str(v).replace('|', '/')} |" for k, v in rows)
    cover = f"![Ảnh bìa](/api/v1/cqf/lich/posts/{post['id']}/cover)\n\n" if post["has_cover"] else "**Chưa có ảnh bìa (Zalo bắt buộc).**\n\n"
    body = []
    for b in blocks:
        if b["type"] == "image":
            body.append(f"![{b.get('caption', '')}]({b['url']})")
        else:
            body.append(html.unescape(b["content"]).replace("*", "\\*"))
    return (f"**Xem trước bài Zalo OA · {post['title']}**\n\n| | |\n|---|---|\n{head}\n\n{cover}"
            f"### {post['title']}\n\n" + "\n\n".join(body) + "\n\n---\n"
            f"Trên Zalo bài chỉ có chữ thường và ảnh. [Mở trong Lịch đăng](/#lich-dang/post={post['id']}) để xem như trên "
            f"Zalo, đổi giờ, đổi chế độ, huỷ lịch · múi giờ {me['settings']['timezone']}")


def preview_md(post, me):
    tz = me["settings"]["timezone"]
    site = next((s for s in me["sites"] if s["id"] == post["site_id"]), None)
    when = post.get("publish_at_label") or ("chưa có giờ đăng" if not post["publish_at"] else post["publish_at"])
    if post.get("channel") == "zalo_oa":
        return zalo_preview_md(post, me, site, when)
    rows = [
        ("Site", f"{site['name']} ({site['url']})" if site else "chưa chọn"),
        ("Giờ đăng", when),
        ("Chế độ", post["mode_label"]),
        ("Trạng thái", post["state_label"]),
        ("Đường dẫn", f"/{post['slug']}/"),
        ("Chuyên mục", ", ".join(post["categories"]) or "—"),
        ("Thẻ", ", ".join(post["tags"]) or "—"),
        ("Mô tả ngắn", post["excerpt"] or "—"),
        ("Độ dài", f"{post['words']} chữ"),
    ]
    head = "\n".join(f"| {k} | {str(v).replace('|', '/')} |" for k, v in rows)
    cover = f"![{post['cover_alt'] or 'Ảnh bìa'}](/api/v1/cqf/lich/posts/{post['id']}/cover)\n\n" if post["has_cover"] else ""
    return (f"**Xem trước bài · {post['title']}**\n\n| | |\n|---|---|\n{head}\n\n{cover}"
            f"# {post['title']}\n\n{html_to_md(post['html'])}\n\n---\n"
            f"[Mở trong Lịch đăng](/#lich-dang/post={post['id']}) để xem như trên web, đổi giờ, đổi chế độ, huỷ lịch · múi giờ {tz}")


def with_label(post, me):
    """Gio dang doc duoc, theo mui gio trong Cai dat cua Lich dang (API tra UTC)."""
    if post.get("publish_at"):
        from datetime import datetime
        from zoneinfo import ZoneInfo
        tz = me["settings"]["timezone"]
        t = datetime.fromisoformat(post["publish_at"].replace("Z", "+00:00")).astimezone(ZoneInfo(tz))
        days = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"]
        post["publish_at_label"] = f"{t:%H:%M} {days[t.weekday()]}, {t:%d/%m/%Y} ({tz})"
    return post


def brief(post):
    keep = ("id", "title", "state_label", "mode_label", "publish_at", "publish_at_label", "slug", "categories", "tags",
            "has_cover", "wp_url", "wp_edit_url", "error", "attempts")
    return {k: post.get(k) for k in keep if post.get(k) not in (None, [], "")} | {"lich_dang": f"/#lich-dang/post={post['id']}"}


# ------------------------------------------------------------------ lenh

def cmd_status(a):
    me = call("GET", "/me")
    s = me["settings"]
    days = {1: "T2", 2: "T3", 3: "T4", 4: "T5", 5: "T6", 6: "T7", 7: "CN"}
    out({"ok": True, "mui_gio": s["timezone"],
         "che_do_mac_dinh": me["modes"][s["default_mode"]],
         "khung_gio": [", ".join(days[d] for d in x["days"]) + " " + x["time"] for x in s["slots"]],
         "sites": [site_view(x) for x in me["sites"]], "may_chu_ip": me.get("server_ip")})


def cmd_sites(a):
    me = call("GET", "/me")
    aliases, default = skill_sites()
    by_url = {v.get("url", "").rstrip("/"): k for k, v in aliases.items()}
    out({"ok": True, "sites": [{**site_view(s), "alias_skill": by_url.get(s["url"].rstrip("/")),
                                "mac_dinh": s["id"] == me["settings"].get("default_site_id")} for s in me["sites"]]})


def cmd_categories(a):
    site, _ = lich_site(a.site)
    cats = call("GET", f"/sites/{site['id']}/categories")
    out({"ok": True, "site": site["name"], "categories": [c["name"] for c in cats]})


def cmd_slots(a):
    out({"ok": True, "gio_trong": [s["label"] for s in call("GET", f"/slots/next?count={a.count}")]})


def _upload_inline(post_id, content, base_dir):
    """Anh local / URL ngoai trong noi dung -> tai vao Lich dang (hien trong chat va trang), dung gio dang moi len site."""
    done = {}

    def repl(m):
        src = html.unescape(m[2])
        if src.startswith(MEDIA_PREFIX) or src.startswith("data:"):
            return m[0]
        if not re.match(r"^https?://", src):
            src = str((Path(base_dir) / src).expanduser())
        if src not in done:
            data, ctype, name = load_image(src)
            body, ct = multipart("file", name, data, ctype)
            done[src] = call("POST", f"/posts/{post_id}/media", raw=body, ctype=ct)["url"]
        return f"{m[1]}{html.escape(done[src])}{m[3]}"

    return re.sub(r'(<img\s[^>]*?src=")([^"]+)("[^>]*>)', repl, content), len(done)


def cmd_save(a):
    content, title = read_content(a.content_file)
    title = a.title or title
    if not title:
        die("Thieu tieu de: dong dau file la '# Tieu de' hoac them --title.")
    site, me = lich_site(a.site)
    fields = {"title": title, "html": "<p></p>" if not content.strip() else content}
    for key in ("slug", "excerpt"):
        if getattr(a, key) is not None:
            fields[key] = getattr(a, key)
    if a.categories is not None:
        fields["categories"] = a.categories
    if a.tags is not None:
        fields["tags"] = a.tags
    if a.mode:
        fields["mode"] = a.mode
    if a.id:
        fields.pop("mode", None)
        post = call("PATCH", f"/posts/{a.id}", body={**fields, "site_id": site["id"]})
        if a.mode:
            post = call("POST", f"/posts/{a.id}/mode", body={"mode": a.mode})
    else:
        post = call("POST", "/posts", body={**fields, "site_id": site["id"]})
    html_with_media, count = _upload_inline(post["id"], content, Path(a.content_file).parent)
    if count:
        post = call("PATCH", f"/posts/{post['id']}", body={"html": html_with_media})
    if a.featured:
        data, ctype, name = load_image(a.featured)
        body, ct = multipart("file", name, data, ctype)
        post = call("POST", f"/posts/{post['id']}/cover", raw=body, ctype=ct)
    post = with_label(call("GET", f"/posts/{post['id']}"), me)
    out({"ok": True, "post": brief(post), "anh_trong_bai": count, "preview_markdown": preview_md(post, me),
         "nhac": "Dan NGUYEN VAN preview_markdown vao chat (giu bang, anh bia, chu dam, anh trong bai, link). "
                 "Chua hen gio: chi hen khi nguoi dung dong y."})


def cmd_media(a):
    data, ctype, name = load_image(a.file)
    body, ct = multipart("file", name, data, ctype)
    out({"ok": True, **call("POST", f"/posts/{a.id}/media", raw=body, ctype=ct)})


def cmd_preview(a):
    me = call("GET", "/me")
    post = with_label(call("GET", f"/posts/{a.id}"), me)
    out({"ok": True, "post": brief(post), "preview_markdown": preview_md(post, me),
         "nhac": "Dan NGUYEN VAN preview_markdown vao chat (giu bang, anh bia, chu dam, anh trong bai, link)."})


def cmd_schedule(a):
    if not a.i_have_user_approval:
        die("Chi hen gio khi nguoi dung da dong y ro rang trong chat (them --i-have-user-approval).")
    body = {"publish_at": "next" if a.next else a.time}
    if a.mode:
        body["mode"] = a.mode
    me = call("GET", "/me")
    post = with_label(call("POST", f"/posts/{a.id}/schedule", body=body), me)
    if post.get("channel") == "zalo_oa":
        verb = ("hiện trên Zalo OA (không gửi cho người quan tâm)" if post["mode"] == "publish"
                else "được tạo ẩn trên Zalo OA (chủ OA tự bật hiển thị)")
    else:
        verb = "tự đăng lên site" if post["mode"] == "publish" else "vào WordPress dạng nháp (bạn tự bấm Đăng trong WordPress)"
    out({"ok": True, "post": brief(post),
         "bao_nguoi_dung": f"Đã hẹn: {post['publish_at_label']}, bài sẽ {verb}. Đổi giờ hay huỷ: "
                           f"[mở trong Lịch đăng](/#lich-dang/post={post['id']})"})


def cmd_unschedule(a):
    out({"ok": True, "post": brief(call("POST", f"/posts/{a.id}/unschedule"))})


def cmd_mode(a):
    out({"ok": True, "post": brief(call("POST", f"/posts/{a.id}/mode", body={"mode": a.mode}))})


def cmd_get(a):
    me = call("GET", "/me")
    post = with_label(call("GET", f"/posts/{a.id}"), me)
    out({"ok": True, "post": brief(post), "lich_su": post.get("history", [])[:10]})


def cmd_list(a):
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    start, end = (now - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ"), (now + timedelta(days=a.days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    me = call("GET", "/me")
    posts = [with_label(p, me) for p in call("GET", f"/posts?start={start}&end={end}")]
    out({"ok": True, "posts": [brief(p) for p in posts]})


def main():
    ap = argparse.ArgumentParser(description="Lich dang (Open WebUI) cho skill viet-bai-website-wordpress")
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("status", help="Agent lam cho ai, mui gio, khung gio, site").set_defaults(f=cmd_status)
    sp.add_parser("sites", help="Site WordPress trong Lich dang").set_defaults(f=cmd_sites)
    p = sp.add_parser("categories", help="Chuyen muc co san cua site (chi chon trong nay)")
    p.add_argument("--site")
    p.set_defaults(f=cmd_categories)
    p = sp.add_parser("slots", help="Khung gio trong ke tiep")
    p.add_argument("--count", type=int, default=5)
    p.set_defaults(f=cmd_slots)
    p = sp.add_parser("save", help="Tao / sua bai trong Lich dang (Chua len lich) va in preview")
    p.add_argument("--content-file", required=True)
    p.add_argument("--site")
    p.add_argument("--id", help="sua bai da co")
    p.add_argument("--title")
    p.add_argument("--slug")
    p.add_argument("--excerpt", "--description", dest="excerpt", help="mo ta ngan (Zalo OA: toi da 300 ky tu)")
    p.add_argument("--categories", nargs="*")
    p.add_argument("--tags", nargs="*")
    p.add_argument("--featured", help="anh dai dien: file hoac URL")
    p.add_argument("--mode", choices=["publish", "draft"],
                   help="publish = Dang that / Hien ngay tren Zalo OA, draft = Luu nhap tren WordPress / Tao bai an tren Zalo OA")
    p.set_defaults(f=cmd_save)
    p = sp.add_parser("media", help="Tai 1 anh vao bai, tra url de chen")
    p.add_argument("id")
    p.add_argument("file")
    p.set_defaults(f=cmd_media)
    p = sp.add_parser("preview", help="In preview Markdown de dan vao chat")
    p.add_argument("id")
    p.set_defaults(f=cmd_preview)
    p = sp.add_parser("schedule", help="Hen gio dang (chi khi nguoi dung dong y)")
    p.add_argument("id")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--time", help="'YYYY-MM-DD HH:MM' theo mui gio trong Cai dat cua Lich dang")
    g.add_argument("--next", action="store_true", help="khung gio trong ke tiep")
    p.add_argument("--mode", choices=["publish", "draft"])
    p.add_argument("--i-have-user-approval", action="store_true")
    p.set_defaults(f=cmd_schedule)
    p = sp.add_parser("unschedule", help="Huy lich, bai ve Chua len lich")
    p.add_argument("id")
    p.set_defaults(f=cmd_unschedule)
    p = sp.add_parser("mode", help="Doi Dang that / Luu nhap")
    p.add_argument("id")
    p.add_argument("--mode", required=True, choices=["publish", "draft"])
    p.set_defaults(f=cmd_mode)
    p = sp.add_parser("get", help="Trang thai 1 bai + lich su")
    p.add_argument("id")
    p.set_defaults(f=cmd_get)
    p = sp.add_parser("list", help="Bai trong 7 ngay qua toi N ngay toi (kem bai chua len lich)")
    p.add_argument("--days", type=int, default=30)
    p.set_defaults(f=cmd_list)
    a = ap.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
