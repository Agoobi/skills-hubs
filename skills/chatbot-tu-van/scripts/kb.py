#!/usr/bin/env python3
"""Kho tai lieu cho skill chatbot-tu-van. Chi dung thu vien chuan.

Lenh: ingest | list | search | remove | mcp
- ingest: doi file khach gui (docx, xlsx, pdf, txt, md, csv) sang Markdown trong thu muc knowledge/.
- search: tim BM25 (co dau va khong dau deu khop), in JSON.
- mcp: chay MCP server qua stdio cho Hermes (tool tim/doc tai lieu, luu khach, chuyen nhan vien).

Thu muc du lieu: --home, hoac env CHATBOT_HOME, mac dinh $HERMES_HOME/chatbot (hoac ~/.hermes/chatbot).
Module nay cung duoc plugin chatbot_guard import (setup.py chep vao plugin).
"""
import argparse, csv, hashlib, hmac, io, json, math, os, re, shutil, subprocess, sys, time, unicodedata
import urllib.request, urllib.error, zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

CHUNK_CHARS = 900
SERVER_NAME = "kb"
PROTOCOL = "2025-06-18"


def home(arg=None):
    if arg:
        return Path(arg).expanduser()
    if os.environ.get("CHATBOT_HOME"):
        return Path(os.environ["CHATBOT_HOME"]).expanduser()
    hh = os.environ.get("HERMES_HOME")
    return (Path(hh).expanduser() if hh else Path.home() / ".hermes") / "chatbot"


def settings(h):
    f = h / "settings.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def out(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def die(msg):
    out({"ok": False, "error": msg})
    sys.exit(1)


# ---------------------------------------------------------------- chuan hoa tieng Viet

def fold(text):
    """'Bảo hành ĐỔI trả' -> 'bao hanh doi tra'"""
    t = unicodedata.normalize("NFKD", text.replace("đ", "d").replace("Đ", "D"))
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def tokens(text):
    words = re.findall(r"[a-z0-9]+", fold(text))
    return words + [a + "_" + b for a, b in zip(words, words[1:])]


def slug(text):
    return "-".join(re.findall(r"[a-z0-9]+", fold(text)))[:60] or "tai-lieu"


# ---------------------------------------------------------------- doc file

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
S = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def read_docx(path):
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read("word/document.xml"))
    lines = []
    body = root.find(W + "body")
    for el in body:
        if el.tag == W + "p":
            text = "".join(t.text or "" for t in el.iter(W + "t")).strip()
            style = el.find(f"{W}pPr/{W}pStyle")
            level = 0
            if style is not None:
                m = re.search(r"(\d)$", style.get(W + "val", ""))
                if "heading" in style.get(W + "val", "").lower() and m:
                    level = int(m.group(1))
            if text:
                lines.append(("#" * min(level, 4) + " " if level else "") + text)
        elif el.tag == W + "tbl":
            rows = [["".join(t.text or "" for t in c.iter(W + "t")).strip() for c in row.iter(W + "tc")]
                    for row in el.iter(W + "tr")]
            rows = [r for r in rows if any(r)]
            if rows:
                lines.append(rows_to_md(rows))
    return "\n\n".join(lines)


def read_xlsx(path):
    with zipfile.ZipFile(path) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).iter(S + "si"):
                shared.append("".join(t.text or "" for t in si.iter(S + "t")))
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        names = [s.get("name") for s in wb.iter(S + "sheet")]
        sheets = sorted(n for n in z.namelist() if re.match(r"xl/worksheets/sheet\d+\.xml$", n))
        parts = []
        for i, sheet in enumerate(sorted(sheets, key=lambda n: int(re.search(r"(\d+)", n.rsplit("/", 1)[1]).group(1)))):
            rows = []
            for row in ET.fromstring(z.read(sheet)).iter(S + "row"):
                vals = []
                for c in row.iter(S + "c"):
                    v = c.find(S + "v")
                    if c.get("t") == "s" and v is not None:
                        vals.append(shared[int(v.text)])
                    elif c.get("t") == "inlineStr":
                        vals.append("".join(t.text or "" for t in c.iter(S + "t")))
                    else:
                        vals.append(v.text if v is not None and v.text else "")
                if any(x.strip() for x in vals):
                    rows.append(vals)
            if rows:
                title = names[i] if i < len(names) else f"Sheet {i + 1}"
                parts.append(f"## {title}\n\n" + rows_to_md(rows))
    return "\n\n".join(parts)


def rows_to_md(rows):
    """Moi dong thanh 1 cau 'Cot: gia tri' de tim kiem va trich dan chinh xac."""
    head = [h.strip() for h in rows[0]]
    lines = []
    for r in rows[1:]:
        pairs = [f"{head[j] if j < len(head) and head[j] else 'Cot ' + str(j + 1)}: {v.strip()}"
                 for j, v in enumerate(r) if v.strip()]
        if pairs:
            lines.append("- " + "; ".join(pairs))
    return "\n".join(lines) if lines else "\n".join("- " + " | ".join(r) for r in rows)


def read_csv(path):
    text = Path(path).read_text(encoding="utf-8-sig", errors="replace")
    return rows_to_md(list(csv.reader(io.StringIO(text))))


def read_pdf(path):
    if not shutil.which("pdftotext"):
        die("Can cai pdftotext (goi poppler-utils) de doc PDF, hoac doi PDF sang Word truoc.")
    res = subprocess.run(["pdftotext", "-layout", str(path), "-"], capture_output=True, text=True)
    if res.returncode != 0:
        die(f"pdftotext loi: {res.stderr[:300]}")
    text = res.stdout.strip()
    if len(re.sub(r"\s", "", text)) < 50:
        die(f"{Path(path).name}: PDF gan nhu khong co chu (anh scan). Xin khach ban Word/Excel hoac file chu.")
    return text


READERS = {".docx": read_docx, ".xlsx": read_xlsx, ".csv": read_csv, ".pdf": read_pdf,
           ".md": lambda p: Path(p).read_text(encoding="utf-8"), ".txt": lambda p: Path(p).read_text(encoding="utf-8")}


def kdir(h):
    d = h / "knowledge"
    d.mkdir(parents=True, exist_ok=True)
    return d


def cmd_ingest(a):
    h = home(a.home)
    done = []
    for f in a.files:
        p = Path(f)
        reader = READERS.get(p.suffix.lower())
        if not reader:
            die(f"Khong ho tro {p.suffix}. Dung: {', '.join(READERS)} (doi .doc/.xls sang .docx/.xlsx).")
        body = reader(p).strip()
        if not body:
            die(f"{p.name}: khong doc duoc noi dung.")
        name = slug(a.title or p.stem) + ".md"
        title = a.title or p.stem
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        dst = kdir(h) / name
        replaced = dst.exists()
        dst.write_text(f"# {title}\n\n<!-- nguon: {p.name}, cap nhat {stamp} -->\n\n{body}\n", encoding="utf-8")
        done.append({"file": p.name, "saved": name, "chars": len(body), "chunks": len(chunk(body)), "replaced": replaced})
    out({"ok": True, "knowledge_dir": str(kdir(h)), "ingested": done,
         "note": "Doc lai file .md da tao de kiem tra bang/so lieu truoc khi bat chatbot."})


def cmd_list(a):
    d = kdir(home(a.home))
    out({"knowledge_dir": str(d), "files": [{"file": f.name, "chars": f.stat().st_size} for f in sorted(d.glob("*.md"))]})


def cmd_remove(a):
    d = kdir(home(a.home)).resolve()
    f = (d / a.file).resolve()
    if f.parent != d or f.suffix != ".md":  # chi xoa file .md nam ngay trong knowledge/
        die(f"Chi xoa duoc file .md trong {d} (vd: bang-gia.md)")
    if not f.exists():
        die(f"Khong co {a.file}")
    f.unlink()
    out({"ok": True, "removed": a.file})


# ---------------------------------------------------------------- tim kiem

def chunk(text):
    """Cat theo doan, gom den ~CHUNK_CHARS, giu tieu de gan nhat lam ngu canh."""
    chunks, cur, heading = [], "", ""
    for para in re.split(r"\n\s*\n", text):
        para = para.strip()
        if not para or para.startswith("<!--"):
            continue
        if para.startswith("#"):
            heading = para.lstrip("# ").strip()
        if cur and len(cur) + len(para) > CHUNK_CHARS:
            chunks.append(cur)
            cur = (f"[{heading}]\n" if heading and not para.startswith("#") else "")
        cur = (cur + "\n\n" + para).strip()
        while len(cur) > CHUNK_CHARS * 2:  # doan qua dai (bang lon): cat theo dong
            cut = cur.rfind("\n", 0, CHUNK_CHARS) or CHUNK_CHARS
            chunks.append(cur[:cut])
            cur = (f"[{heading}]\n" if heading else "") + cur[cut:].strip()
    if cur:
        chunks.append(cur)
    return chunks


class Index:
    def __init__(self, h):
        self.dir = kdir(h)
        self.sig = None
        self.docs = []

    def _load(self):
        files = sorted(self.dir.glob("*.md"))
        sig = tuple((f.name, f.stat().st_mtime_ns) for f in files)
        if sig == self.sig:
            return
        docs = []
        for f in files:
            for i, c in enumerate(chunk(f.read_text(encoding="utf-8"))):
                toks = tokens(c)
                tf = {}
                for t in toks:
                    tf[t] = tf.get(t, 0) + 1
                docs.append({"source": f.name, "chunk": i, "text": c, "tf": tf, "len": len(toks)})
        self.df = {}
        for d in docs:
            for t in d["tf"]:
                self.df[t] = self.df.get(t, 0) + 1
        self.avg = sum(d["len"] for d in docs) / len(docs) if docs else 1
        self.docs, self.sig = docs, sig

    def search(self, query, k=5):
        self._load()
        q = set(tokens(query))
        n = len(self.docs)
        scored = []
        for d in self.docs:
            s = 0.0
            for t in q:
                f = d["tf"].get(t)
                if f:
                    idf = math.log(1 + (n - self.df[t] + 0.5) / (self.df[t] + 0.5))
                    s += idf * f * 2.5 / (f + 1.5 * (0.25 + 0.75 * d["len"] / self.avg))
            if s > 0:
                scored.append((s, d))
        scored.sort(key=lambda x: -x[0])
        return [{"source": d["source"], "chunk": d["chunk"], "score": round(s, 3), "text": d["text"]} for s, d in scored[:k]]

    def get(self, source, chunk_no=None):
        self._load()
        parts = [d for d in self.docs if d["source"] == source and (chunk_no is None or d["chunk"] == chunk_no)]
        return "\n\n".join(d["text"] for d in parts)


def cmd_search(a):
    out({"query": a.query, "results": Index(home(a.home)).search(a.query, a.limit)})


# ---------------------------------------------------------------- lead / chuyen nhan vien

def record(h, kind, data):
    """Ghi vao leads.jsonl va day qua webhook (ky HMAC) neu co cau hinh."""
    evt = {"type": kind, "time": datetime.now(timezone.utc).isoformat(), **data}
    # SDT khach la du lieu ca nhan: file chi chu so huu doc duoc
    fd = os.open(h / "leads.jsonl", os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    with os.fdopen(fd, "a", encoding="utf-8") as f:
        f.write(json.dumps(evt, ensure_ascii=False) + "\n")
    hook = settings(h).get("lead_webhook") or {}
    if not hook.get("url"):
        return {"saved": True, "webhook": "chua cau hinh"}
    body = json.dumps(evt, ensure_ascii=False).encode()
    ts = str(int(time.time()))
    headers = {"Content-Type": "application/json", "X-Chatbot-Timestamp": ts}
    if hook.get("secret"):
        sig = hmac.new(hook["secret"].encode(), ts.encode() + b"." + body, hashlib.sha256).hexdigest()
        headers["X-Chatbot-Signature"] = "sha256=" + sig
    try:
        with urllib.request.urlopen(urllib.request.Request(hook["url"], body, headers, method="POST"), timeout=15) as r:
            return {"saved": True, "webhook": r.status}
    except (urllib.error.URLError, OSError, ValueError) as e:  # ValueError: URL webhook sai dinh dang
        return {"saved": True, "webhook": f"loi: {e}"}


# ---------------------------------------------------------------- MCP server (stdio, JSON-RPC 2.0)

TOOLS = [
    {"name": "tim_kien_thuc",
     "description": "Tim trong tai lieu cua doanh nghiep (san pham, gia, chinh sach, FAQ). Bat buoc goi truoc khi tra loi. "
                    "Goi lai voi cach dien dat khac neu ket qua chua du.",
     "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer", "default": 5}},
                     "required": ["query"]}},
    {"name": "doc_tai_lieu",
     "description": "Doc nguyen van mot tai lieu hoac mot doan (source, chunk lay tu ket qua tim_kien_thuc).",
     "inputSchema": {"type": "object", "properties": {"source": {"type": "string"}, "chunk": {"type": "integer"}},
                     "required": ["source"]}},
    {"name": "luu_khach_hang",
     "description": "Luu thong tin khach de nhan vien lien he. Chi goi khi khach tu cung cap so dien thoai hoac email.",
     "inputSchema": {"type": "object", "properties": {"ten": {"type": "string"}, "sdt": {"type": "string"},
                                                      "email": {"type": "string"}, "nhu_cau": {"type": "string"}},
                     "required": ["nhu_cau"]}},
    {"name": "chuyen_nhan_vien",
     "description": "Bao nhan vien vao ho tro: khieu nai, bao gia dac biet, cau hoi ngoai tai lieu, khach yeu cau gap nguoi.",
     "inputSchema": {"type": "object", "properties": {"ly_do": {"type": "string"}, "tom_tat": {"type": "string"},
                                                      "lien_he": {"type": "string"}},
                     "required": ["ly_do", "tom_tat"]}},
]


def call_tool(h, idx, name, args):
    if name == "tim_kien_thuc":
        res = idx.search(args.get("query", ""), int(args.get("limit") or 5))
        if not res:
            return "KHONG TIM THAY trong tai lieu. Thu cach dien dat khac; neu van khong co thi noi chua co thong tin va chuyen nhan vien."
        return "\n\n---\n\n".join(f"[{r['source']}#{r['chunk']}]\n{r['text']}" for r in res)
    if name == "doc_tai_lieu":
        text = idx.get(args.get("source", ""), args.get("chunk"))
        return text or "Khong co tai lieu/doan nay."
    if name in ("luu_khach_hang", "chuyen_nhan_vien"):
        res = record(h, "lead" if name == "luu_khach_hang" else "handoff", args)
        return json.dumps({"ok": True, **res}, ensure_ascii=False)
    raise KeyError(name)


def cmd_mcp(a):
    h = home(a.home)
    idx = Index(h)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        mid, method, params = msg.get("id"), msg.get("method"), msg.get("params") or {}
        if mid is None:  # notification (initialized, cancelled...)
            continue
        if method == "initialize":
            result = {"protocolVersion": params.get("protocolVersion") or PROTOCOL,
                      "capabilities": {"tools": {}}, "serverInfo": {"name": SERVER_NAME, "version": "0.1.0"}}
        elif method == "tools/list":
            result = {"tools": TOOLS}
        elif method == "tools/call":
            try:
                text = call_tool(h, idx, params.get("name"), params.get("arguments") or {})
                result = {"content": [{"type": "text", "text": text}], "isError": False}
            except KeyError:
                reply = {"jsonrpc": "2.0", "id": mid, "error": {"code": -32602, "message": f"Unknown tool {params.get('name')}"}}
                print(json.dumps(reply, ensure_ascii=False), flush=True)
                continue
            except Exception as e:  # loi doc file... van tra ve cho agent
                result = {"content": [{"type": "text", "text": f"Loi: {e}"}], "isError": True}
        elif method == "ping":
            result = {}
        else:
            print(json.dumps({"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": "Method not found"}}), flush=True)
            continue
        print(json.dumps({"jsonrpc": "2.0", "id": mid, "result": result}, ensure_ascii=False), flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--home", help="Thu muc du lieu chatbot (mac dinh $HERMES_HOME/chatbot)")
    sp = ap.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("ingest")
    s.add_argument("files", nargs="+")
    s.add_argument("--title", help="Ten tai lieu (chi dung khi ingest 1 file)")
    s.set_defaults(f=cmd_ingest)
    sp.add_parser("list").set_defaults(f=cmd_list)
    s = sp.add_parser("remove")
    s.add_argument("file")
    s.set_defaults(f=cmd_remove)
    s = sp.add_parser("search")
    s.add_argument("query")
    s.add_argument("--limit", type=int, default=5)
    s.set_defaults(f=cmd_search)
    sp.add_parser("mcp").set_defaults(f=cmd_mcp)
    a = ap.parse_args()
    if a.cmd == "ingest" and a.title and len(a.files) > 1:
        die("--title chi dung khi ingest 1 file.")
    a.f(a)


if __name__ == "__main__":
    main()
