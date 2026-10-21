"""Hop thu chatbot tren Open WebUI: moi khach 1 chat co the khach, tu chuyen nhom theo trang thai.

Hermes la ben DUY NHAT ghi vao Open WebUI. Moi viec (tin khach, tin bot, lead, nut bam tren the) xep vao 1 hang doi,
1 luong rieng xu ly lan luot -> dung thu tu, Open WebUI loi thi thu lai, khong lam cham khach.
Sau moi lan ghi: phat su kien chat:reload (tab dang mo hien tin moi) va chat:title (sidebar sap lai, cham chua doc).

Trong Open WebUI (tai khoan so huu API key):
- 3 folder: "Can xu ly" (khach de lai thong tin / can nhan vien / bot bi chan), "Dang chat", "Da xong".
- Chat "Tong quan hop thu" (ghim): so lieu hom nay + bang khach can xu ly, tu lam moi.
- Moi chat khach: tin dau la THE KHACH (HTML nhung, co nut "Da goi" / "Xong" / "Mo lai"), sau do la hoi thoai
  va the su kien (lead, can nhan vien, bot bi chan).
Nut tren the goi POST {webchat.public_url}/owui/action (ky HMAC theo tung chat), khong can dang nhap.

Du lieu: $CHATBOT_HOME/owui_inbox.json (trang thai tung khach), owui_secret (khoa ky nut bam), quyen 600.
Chi dung thu vien chuan; setup.py chep file nay vao 2 plugin, get_inbox() bao dam chi 1 ban chay.
"""
import hashlib, hmac, html, json, logging, os, queue, secrets, sys, threading, time, types, uuid
import urllib.error, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

logger = logging.getLogger("chatbot_owui_inbox")

FOLDERS = {"can_xu_ly": "Cần xử lý", "dang_chat": "Đang chat", "da_xong": "Đã xong"}
STATUS = {"can_xu_ly": ("Cần xử lý", "warn"), "dang_chat": ("Đang chat", "acc"), "da_xong": ("Đã xong", "ok")}
EVENTS = {"lead": ("Khách để lại thông tin", "warn"), "handoff": ("Khách cần gặp nhân viên", "warn"),
          "guard_blocked": ("Bot không trả lời được", "bad"), "action": ("Cập nhật", "acc")}
ACTIONS = {"da_goi": "Đã gọi", "xong": "Xong", "mo_lai": "Mở lại"}
PROFILE = [("ten", "Tên"), ("sdt", "SĐT"), ("zalo", "Zalo"), ("email", "Email"), ("cong_ty", "Công ty"),
           ("dia_chi", "Địa chỉ"), ("thoi_gian", "Giờ tiện gọi"), ("nhu_cau", "Nhu cầu")]
OVERVIEW_KEY = "__overview__"
OVERVIEW_EVERY = 600  # giay: lam moi tong quan dinh ky (va 30 giay sau moi thay doi)
TZ = timezone(timedelta(hours=7))
RETRY = (2, 5, 15, 30, 60)
NS = uuid.UUID("6f1c2a52-6a0e-4d7c-9a51-0c0ffee0a11b")


def get_inbox(home: Path, settings: dict):
    """1 ban Inbox cho ca tien trinh (2 plugin import 2 ban sao cua module nay)."""
    holder = sys.modules.setdefault("_chatbot_owui_inbox", types.ModuleType("_chatbot_owui_inbox"))
    with holder.__dict__.setdefault("lock", threading.Lock()):  # dict.setdefault la nguyen tu
        if getattr(holder, "inbox", None) is None:
            holder.inbox = Inbox(home, settings)
        return holder.inbox


def _now():
    return int(time.time())


def _hhmm(ts):
    return datetime.fromtimestamp(ts, TZ).strftime("%H:%M %d/%m") if ts else "—"


def _esc(v):
    return html.escape(str(v or ""), quote=True)


class Inbox:
    def __init__(self, home: Path, settings: dict):
        ow = settings.get("open_webui") or {}
        self.home = Path(home)
        self.url = (ow.get("url") or "").rstrip("/")
        self.key = ow.get("api_key") or ""
        self.model = ow.get("model_label") or "Chatbot"
        self.public_url = ((settings.get("webchat") or {}).get("public_url") or "").rstrip("/")
        self.shop = (settings.get("business") or {}).get("ten") or ""
        self.enabled = bool(self.url and self.key)
        self.state_file = self.home / "owui_inbox.json"
        self.secret = self._secret()
        self.q = queue.Queue(maxsize=5000)
        self._folders = {}
        self._dirty_at = 0.0
        self._overview_at = 0.0
        if self.enabled:
            threading.Thread(target=self._worker, name="owui-inbox", daemon=True).start()

    # ---------------------------------------------------------------- API cho plugin (khong bao gio raise)

    def message(self, conv, role, text, page=None):
        self._put(("message", conv, {"role": role, "text": text, "page": page, "t": _now()}))

    def event(self, conv, kind, data):
        self._put(("event", conv, {"kind": kind, "data": dict(data or {}), "t": _now()}))

    def action(self, conv, action, sig):
        """Nut tren the khach. Tra False neu chu ky sai (khong xep hang)."""
        if action not in ACTIONS or not hmac.compare_digest(sig or "", self.sign(conv)):
            return False
        self._put(("action", conv, {"action": action, "t": _now()}))
        return True

    def sign(self, conv):
        return hmac.new(self.secret, conv.encode(), hashlib.sha256).hexdigest()[:32]

    def _put(self, item):
        if not self.enabled:
            return
        try:
            self.q.put_nowait(item)
        except queue.Full:
            logger.warning("[owui-inbox] hang doi day, bo 1 viec: %s %s", item[0], item[1])

    # ---------------------------------------------------------------- luong xu ly

    def _worker(self):
        while True:
            try:
                item = self.q.get(timeout=5)
            except queue.Empty:
                item = None
            if item:
                for i, wait in enumerate((0,) + RETRY):
                    time.sleep(wait)
                    try:
                        self._apply(*item)
                        break
                    except Exception as e:  # Open WebUI loi/tat: thu lai, giu dung thu tu
                        logger.warning("[owui-inbox] %s %s loi (lan %d): %s", item[0], item[1], i + 1, e)
                else:
                    logger.error("[owui-inbox] bo qua %s %s sau %d lan thu", item[0], item[1], len(RETRY) + 1)
                    self._folders = {}
                self.q.task_done()
            due = self._dirty_at and time.time() - self._dirty_at > 30
            if self.q.empty() and (due or time.time() - self._overview_at > OVERVIEW_EVERY):
                try:
                    self._overview()
                except Exception as e:
                    logger.warning("[owui-inbox] khong lam moi duoc tong quan: %s", e)
                self._dirty_at, self._overview_at = 0.0, time.time()

    # ---------------------------------------------------------------- trang thai tren dia

    def _secret(self):
        f = self.home / "owui_secret"
        try:
            if f.exists():
                return f.read_bytes().strip()
            self.home.mkdir(parents=True, exist_ok=True)
            val = secrets.token_hex(32).encode()
            fd = os.open(f, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "wb") as fh:
                fh.write(val)
            return val
        except OSError:
            return secrets.token_hex(32).encode()  # khong ghi duoc: nut chi dung den lan khoi dong sau

    def _load(self):
        try:
            return json.loads(self.state_file.read_text(encoding="utf-8")) if self.state_file.exists() else {}
        except ValueError:
            return {}

    def _save(self, data):
        tmp = self.state_file.with_suffix(".tmp")
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=1)
        tmp.replace(self.state_file)

    # ---------------------------------------------------------------- Open WebUI API

    def _req(self, method, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.url + path, data, method=method, headers={
            "Authorization": f"Bearer {self.key}", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=20) as r:
            raw = r.read()
            return json.loads(raw) if raw else {}

    def _folder(self, status):
        if status not in self._folders:
            name = FOLDERS[status]
            hit = [f for f in (self._req("GET", "/api/v1/folders/") or [])
                   if (f.get("name") or "").strip() == name and not f.get("parent_id")]
            self._folders[status] = hit[0]["id"] if hit else self._req("POST", "/api/v1/folders/", {"name": name})["id"]
        return self._folders[status]

    def _emit(self, chat_id, message_id, title):
        for ev in ({"type": "chat:reload", "data": {}}, {"type": "chat:title", "data": title}):
            try:
                self._req("POST", f"/api/v1/chats/{chat_id}/messages/{message_id}/event", ev)
            except (urllib.error.URLError, OSError, ValueError) as e:  # khong ai dang mo: bo qua
                logger.debug("[owui-inbox] emit %s: %s", ev["type"], e)

    def _msg(self, mid, role, content, parent, ts, embeds=None):
        m = {"id": mid, "parentId": parent, "childrenIds": [], "role": role, "content": content, "timestamp": ts}
        if role == "assistant":
            m.update({"model": self.model, "modelName": self.model, "done": True})
        else:
            m["models"] = [self.model]
        if embeds:
            m["embeds"] = embeds
        return m

    def _mid(self, conv, n):
        return str(uuid.uuid5(NS, f"{conv}#{n}"))

    # ---------------------------------------------------------------- xu ly 1 viec

    def _apply(self, kind, conv, p):
        data = self._load()
        if conv == OVERVIEW_KEY:
            return
        st = data.get(conv) or {"status": "dang_chat", "first_at": p["t"], "n": 0, "msgs": 0, "blocked": 0,
                                "profile": {}, "events": []}
        new = []  # (role, content, embeds)
        old_status = st["status"]
        if kind == "message":
            st["msgs"] += 1
            st["last_at"] = p["t"]
            if p.get("page") and not st.get("page"):
                st["page"] = str(p["page"])[:300]
            if p["role"] == "user" and not st.get("first_q"):
                st["first_q"] = p["text"][:60]
            new.append((p["role"], p["text"], None))
            if st["status"] == "da_xong" and p["role"] == "user":
                st["status"] = "dang_chat"  # khach quay lai: mo lai
        elif kind == "event":
            d, ev = p["data"], p["kind"]
            for k, _ in PROFILE:
                if d.get(k):
                    st["profile"][k] = str(d[k])[:200]
            if d.get("ly_do") or d.get("tom_tat"):
                st["profile"]["nhu_cau"] = str(d.get("tom_tat") or d.get("ly_do"))[:200]
            if ev == "guard_blocked":
                st["blocked"] += 1
            st["status"] = "can_xu_ly"
            st.pop("note", None)
            new.append(("assistant", self._event_text(ev, d), [self._event_html(ev, d, p["t"])]))
        elif kind == "action":
            a = p["action"]
            st["status"] = {"da_goi": "can_xu_ly", "xong": "da_xong", "mo_lai": "dang_chat"}[a]
            st["note"] = f"{ACTIONS[a]} lúc {_hhmm(p['t'])}"
            new.append(("assistant", f"Chủ shop bấm: {ACTIONS[a]}",
                        [self._event_html("action", {"tom_tat": st["note"]}, p["t"])]))
        st["events"] = (st["events"] + ([{"kind": p.get("kind") or p.get("action"), "t": p["t"]}]
                                         if kind != "message" else []))[-20:]
        title = self._title(conv, st)

        if not st.get("chat_id"):
            card_id = self._mid(conv, 0)
            card = self._msg(card_id, "assistant", self._card_text(conv, st), None, st["first_at"],
                             [self._card_html(conv, st)])
            chat = {"title": title, "models": [self.model], "messages": [card],
                    "history": {"messages": {card_id: card}, "currentId": card_id}}
            res = self._req("POST", "/api/v1/chats/new", {"chat": chat, "folder_id": self._folder(st["status"])})
            st.update(chat_id=res["id"], folder=st["status"], title=title)
            data[conv] = st
            self._save(data)  # luu chat_id ngay: lan thu lai sau khong tao chat trung
        chat_id = st["chat_id"]
        try:
            chat = self._req("GET", f"/api/v1/chats/{chat_id}").get("chat") or {}
        except urllib.error.HTTPError as e:
            if e.code not in (401, 404):
                raise
            st.pop("chat_id", None)  # chu shop xoa chat: tao lai o lan sau
            data[conv] = st
            self._save(data)
            raise RuntimeError("chat da bi xoa ben Open WebUI, tao lai") from e
        hist = chat.setdefault("history", {"messages": {}, "currentId": None})
        msgs = hist.setdefault("messages", {})
        card_id = self._mid(conv, 0)
        if card_id in msgs:  # the khach luon la tin dau, cap nhat tai cho
            msgs[card_id]["content"] = self._card_text(conv, st)
            msgs[card_id]["embeds"] = [self._card_html(conv, st)]
        for role, content, embeds in new:
            st["n"] += 1
            mid = self._mid(conv, st["n"])
            if mid in msgs:  # lan thu lai: tin da ghi roi
                continue
            parent = hist.get("currentId")
            m = self._msg(mid, role, content, parent, p["t"], embeds)
            if parent in msgs:
                msgs[parent].setdefault("childrenIds", []).append(mid)
            msgs[mid] = m
            hist["currentId"] = mid
        chat["messages"] = self._linear(hist)
        if st.get("title") != title:
            chat["title"] = st["title"] = title
        self._req("POST", f"/api/v1/chats/{chat_id}", {"chat": chat})
        if st["status"] != st.get("folder") or st["status"] != old_status:
            self._req("POST", f"/api/v1/chats/{chat_id}/folder", {"folder_id": self._folder(st["status"])})
            st["folder"] = st["status"]
        data[conv] = st
        self._save(data)
        self._emit(chat_id, hist.get("currentId") or card_id, title)
        if kind != "message" or st["msgs"] <= 2:
            self._dirty_at = self._dirty_at or time.time()

    @staticmethod
    def _linear(hist):
        out, cur, seen = [], hist.get("currentId"), set()
        while cur and cur in hist["messages"] and cur not in seen:
            seen.add(cur)
            out.append(hist["messages"][cur])
            cur = hist["messages"][cur].get("parentId")
        return out[::-1]

    def _title(self, conv, st):
        pr = st["profile"]
        who = pr.get("ten") or f"Khách {conv.split(':')[-1][:4]}"
        tail = pr.get("sdt") or pr.get("zalo") or pr.get("nhu_cau") or st.get("first_q") or "mới nhắn"
        return f"{who} · {tail}"[:80]

    # ---------------------------------------------------------------- noi dung

    def _event_text(self, ev, d):
        label = EVENTS.get(ev, (ev, ""))[0]
        bits = [f"{lbl}: {d[k]}" for k, lbl in PROFILE if d.get(k)]
        bits += [f"Lý do: {d['ly_do']}"] if d.get("ly_do") else []
        bits += [f"Khách hỏi: {d['khach_hoi']}"] if d.get("khach_hoi") else []
        return f"🔔 {label}" + (" — " + "; ".join(bits) if bits else "")

    def _event_html(self, ev, d, t):
        label, tone = EVENTS.get(ev, (ev, "acc"))
        rows = [(lbl, d[k]) for k, lbl in PROFILE if d.get(k)]
        for k, lbl in (("ly_do", "Lý do"), ("tom_tat", "Tóm tắt"), ("lien_he", "Liên hệ"), ("khach_hoi", "Khách hỏi"),
                       ("so_lieu_khong_co_can_cu", "Số liệu không có trong tài liệu")):
            if d.get(k):
                rows.append((lbl, ", ".join(d[k]) if isinstance(d[k], list) else d[k]))
        body = "".join(f'<div class="f"><span class="k">{_esc(a)}</span><span class="v">{_esc(b)}</span></div>' for a, b in rows)
        return (f"<!doctype html><meta charset=utf-8><style>{CSS}</style>"
                f'<div class="ev {tone}"><div class="eh"><span class="eb">{_esc(label)}</span>'
                f'<span class="t">{_esc(_hhmm(t))}</span></div>{body and f"<div class=fs>{body}</div>"}</div>')

    def _card_text(self, conv, st):
        pr = st["profile"]
        bits = [f"{lbl}: {pr[k]}" for k, lbl in PROFILE if pr.get(k)]
        return f"Thẻ khách · {STATUS[st['status']][0]}" + (" · " + "; ".join(bits) if bits else "")

    def _card_html(self, conv, st):
        label, tone = STATUS[st["status"]]
        pr = st["profile"]
        fields = [(lbl, pr.get(k)) for k, lbl in PROFILE if pr.get(k)] or [("Thông tin", "Khách chưa để lại thông tin")]
        fields += [("Trang đang xem", st.get("page")), ("Lần đầu nhắn", _hhmm(st.get("first_at"))),
                   ("Tin nhắn", st.get("msgs", 0)), ("Bot bị chặn", st.get("blocked", 0))]
        grid = "".join(f'<div class="f"><span class="k">{_esc(a)}</span><span class="v">{_esc(b if b not in (None, "") else "—")}</span></div>'
                       for a, b in fields)
        buttons = {"can_xu_ly": ["da_goi", "xong"], "dang_chat": ["xong"], "da_xong": ["mo_lai"]}[st["status"]]
        btns = "".join(f'<button data-a="{a}" class="{"p" if i == 0 else ""}">{ACTIONS[a]}</button>'
                       for i, a in enumerate(buttons))
        note = f'<span class="t">{_esc(st["note"])}</span>' if st.get("note") else ""
        cfg = json.dumps({"url": self.public_url + "/owui/action", "conv": conv, "sig": self.sign(conv)})
        actions = (f'<div class="ac">{btns}{note}<span class="msg" id="m"></span></div>' if self.public_url else "")
        return (f"<!doctype html><meta charset=utf-8><style>{CSS}</style>"
                f'<div class="card"><div class="ch"><span class="eb">Khách hàng · website</span>'
                f'<span class="b {tone}">{_esc(label)}</span></div><div class="fs">{grid}</div>{actions}</div>'
                f"<script>const C={cfg};{ACTION_JS}</script>")

    # ---------------------------------------------------------------- tong quan

    def _overview(self):
        data = self._load()
        convs = {k: v for k, v in data.items() if k != OVERVIEW_KEY and v.get("chat_id")}
        day0 = datetime.now(TZ).replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
        today = [v for v in convs.values() if (v.get("last_at") or 0) >= day0]
        leads = [v for v in convs.values() if any(e["kind"] in ("lead", "handoff") and e["t"] >= day0 for e in v["events"])]
        blocked = [v for v in convs.values() if any(e["kind"] == "guard_blocked" and e["t"] >= day0 for e in v["events"])]
        todo = sorted((v for v in convs.values() if v["status"] == "can_xu_ly"), key=lambda v: v.get("last_at") or 0)
        recent = sorted(convs.values(), key=lambda v: -(v.get("last_at") or 0))
        rows = (todo + [v for v in recent if v["status"] != "can_xu_ly"])[:30]
        stats = [("Hội thoại hôm nay", len(today)), ("Lead hôm nay", len(leads)),
                 ("Cần xử lý", len(todo)), ("Bot bị chặn hôm nay", len(blocked))]
        st_html = "".join(f'<div class="s"><span class="k">{_esc(a)}</span><span class="n">{b}</span></div>' for a, b in stats)

        def row(v):
            pr, (lbl, tone) = v["profile"], STATUS[v["status"]]
            wait = ""
            if v["status"] == "can_xu_ly" and v["events"]:
                mins = int((time.time() - v["events"][-1]["t"]) // 60)
                wait = f"{mins} phút" if mins < 120 else f"{mins // 60} giờ"
            return (f'<tr data-c="{_esc(v["chat_id"])}"><td>{_esc(v.get("title"))}</td><td class="m">{_esc(pr.get("sdt") or pr.get("zalo") or "—")}</td>'
                    f'<td>{_esc(pr.get("nhu_cau") or v.get("first_q") or "—")}</td><td><span class="b {tone}">{_esc(lbl)}</span></td>'
                    f'<td class="m">{_esc(wait or _hhmm(v.get("last_at")))}</td></tr>')

        table = ("<div class=tw><table><thead><tr><th>Khách</th><th>SĐT</th><th>Nhu cầu</th><th>Trạng thái</th>"
                 "<th>Chờ / lần cuối</th></tr></thead><tbody>" + "".join(row(v) for v in rows) + "</tbody></table></div>"
                 if rows else '<p class="empty">Chưa có khách nào nhắn qua website.</p>')
        page = (f"<!doctype html><meta charset=utf-8><style>{CSS}</style><div class=card>"
                f'<div class="ch"><span class="eb">Tổng quan hộp thư{(" · " + _esc(self.shop)) if self.shop else ""}</span>'
                f'<span class="t">Cập nhật {_esc(_hhmm(_now()))}</span></div><div class=st>{st_html}</div>{table}</div>'
                f"<script>{OPEN_JS}</script>")
        text = " · ".join(f"{a}: {b}" for a, b in stats)

        ov = data.get(OVERVIEW_KEY) or {}
        mid = self._mid(OVERVIEW_KEY, 0)
        msg = self._msg(mid, "assistant", text, None, _now(), [page])
        chat = {"title": "Tổng quan hộp thư", "models": [self.model], "messages": [msg],
                "history": {"messages": {mid: msg}, "currentId": mid}}
        if ov.get("chat_id"):
            try:
                self._req("POST", f"/api/v1/chats/{ov['chat_id']}", {"chat": chat})
            except urllib.error.HTTPError as e:
                if e.code not in (401, 404):
                    raise
                ov = {}
        if not ov.get("chat_id"):
            res = self._req("POST", "/api/v1/chats/new", {"chat": chat})
            ov = {"chat_id": res["id"]}
            self._req("POST", f"/api/v1/chats/{res['id']}/pin")
        data = self._load()
        data[OVERVIEW_KEY] = ov
        self._save(data)
        self._emit(ov["chat_id"], mid, "Tổng quan hộp thư")


# HTML nhung chay trong iframe sandbox cua Open WebUI (khong cung origin): moi chu cua khach da escape.
CSS = """
:root{--bg:#fff;--line:#d5dcd9;--soft:#e7ecea;--ink:#18211e;--ink2:#4b5853;--ink3:#86928d;--acc:#0e7466;--accs:#e1f2ee;
--warn:#b45309;--warns:#fdf1e3;--bad:#b42318;--bads:#fcebea;--ok:#157f3d;--oks:#e6f4ea}
@media (prefers-color-scheme:dark){:root{--bg:#171c1b;--line:#323c39;--soft:#262f2c;--ink:#e6ece9;--ink2:#aab6b1;--ink3:#75827d;
--acc:#3cc2ae;--accs:#123a34;--warn:#f0a24b;--warns:#3a2a16;--bad:#f2867d;--bads:#3d1d1b;--ok:#5ccb83;--oks:#173322}}
*{box-sizing:border-box}html,body{margin:0;background:transparent;color:var(--ink);
font:13px/1.5 ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.card,.ev{background:var(--bg);border:1px solid var(--line);border-radius:6px;overflow:hidden}
.ch,.eh{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:8px 12px;border-bottom:1px solid var(--soft);flex-wrap:wrap}
.eb{font-size:10.5px;font-weight:600;text-transform:uppercase;letter-spacing:.1em;color:var(--ink3)}
.t{font-size:11.5px;color:var(--ink3)}
.b{font-size:11px;font-weight:600;padding:1px 8px;border-radius:999px;white-space:nowrap}
.b.warn{background:var(--warns);color:var(--warn)}.b.acc{background:var(--accs);color:var(--acc)}
.b.ok{background:var(--oks);color:var(--ok)}.b.bad{background:var(--bads);color:var(--bad)}
.fs{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:8px 16px;padding:10px 12px}
.f{display:flex;flex-direction:column;min-width:0}.k{font-size:10.5px;font-weight:600;text-transform:uppercase;letter-spacing:.06em;color:var(--ink3)}
.v{overflow-wrap:anywhere}
.ac{display:flex;align-items:center;gap:6px;flex-wrap:wrap;padding:8px 12px;border-top:1px solid var(--soft)}
button{font:inherit;font-weight:600;font-size:12.5px;padding:4px 10px;border-radius:4px;border:1px solid var(--line);background:var(--bg);color:var(--ink);cursor:pointer}
button.p{background:var(--acc);border-color:var(--acc);color:var(--bg)}button:disabled{opacity:.6;cursor:default}
button:focus-visible{outline:2px solid var(--acc);outline-offset:1px}
.msg{font-size:12px;color:var(--ink3)}
.ev{border-left:3px solid var(--acc)}.ev.warn{border-left-color:var(--warn)}.ev.bad{border-left-color:var(--bad)}
.ev.warn .eb{color:var(--warn)}.ev.bad .eb{color:var(--bad)}.ev.acc .eb{color:var(--acc)}
.st{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));border-bottom:1px solid var(--soft)}
.s{padding:10px 12px;display:flex;flex-direction:column;border-right:1px solid var(--soft)}.s:last-child{border-right:0}
.n{font-size:22px;font-weight:700;font-variant-numeric:tabular-nums}
.tw{overflow-x:auto}table{border-collapse:collapse;width:100%;min-width:560px}
th{text-align:left;font-size:10.5px;font-weight:600;text-transform:uppercase;letter-spacing:.06em;color:var(--ink3);padding:7px 12px;border-bottom:1px solid var(--soft)}
td{padding:7px 12px;border-bottom:1px solid var(--soft);vertical-align:top}tr:last-child td{border-bottom:0}
tbody tr{cursor:pointer}tbody tr:hover{background:var(--soft)}
.m{font-variant-numeric:tabular-nums;white-space:nowrap}.empty{padding:14px 12px;margin:0;color:var(--ink3)}
"""

ACTION_JS = """
document.querySelectorAll('button[data-a]').forEach(b=>b.addEventListener('click',async()=>{
 const all=document.querySelectorAll('button[data-a]');all.forEach(x=>x.disabled=true);
 const m=document.getElementById('m');m.textContent='Đang cập nhật…';
 try{const r=await fetch(C.url,{method:'POST',headers:{'Content-Type':'text/plain'},
  body:JSON.stringify({conv:C.conv,sig:C.sig,action:b.dataset.a})});
  if(!r.ok)throw new Error(r.status);m.textContent='Đã ghi nhận, thẻ sẽ tự cập nhật.';}
 catch(e){m.textContent='Không gửi được, thử lại.';all.forEach(x=>x.disabled=false);}
}));
"""

OPEN_JS = """
document.querySelectorAll('tr[data-c]').forEach(r=>r.addEventListener('click',()=>
 parent.postMessage({type:'cqf-open-chat',chatId:r.dataset.c},'*')));
"""
