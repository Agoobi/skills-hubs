"""Chep hoi thoai cua chatbot sang Open WebUI de chu shop xem.

Moi khach (kenh + id) = 1 chat trong sidebar cua tai khoan Open WebUI so huu API key.
Dung API backend cua Open WebUI: POST /api/v1/chats/new, GET/POST /api/v1/chats/<id>.
Chi dung thu vien chuan; setup.py chep file nay vao plugin webchat.
"""
import asyncio, fcntl, json, logging, os, threading, time, uuid, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

logger = logging.getLogger(__name__)
_lock = threading.Lock()  # chi giu khi doc/ghi file map (nhanh)
_conv_locks: dict = {}  # moi cuoc tro chuyen 1 khoa: tin cung khach chep dung thu tu, khach khac khong cho nhau
_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="owui-mirror")  # khong chiem executor cua Hermes


class Mirror:
    def __init__(self, home: Path, cfg: dict):
        self.url = (cfg.get("url") or "").rstrip("/")
        self.key = cfg.get("api_key") or ""
        self.model = cfg.get("model_label") or "chatbot"
        self.map_file = home / "owui_chats.json"
        self.enabled = bool(self.url and self.key)

    def _req(self, method, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.url + path, data, method=method, headers={
            "Authorization": f"Bearer {self.key}", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read() or b"{}")

    def _map(self, conv_key, entry=None, write=False):
        """Doc (hoac ghi) 1 muc trong file map khach -> chat Open WebUI. Khoa ngan, khong goi mang khi dang khoa."""
        with _lock:
            self.map_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.map_file.with_suffix(".lock"), "w") as lk:
                fcntl.flock(lk, fcntl.LOCK_EX)
                data = json.loads(self.map_file.read_text()) if self.map_file.exists() else {}
                if not write:
                    return data.get(conv_key)
                data[conv_key] = entry
                tmp = self.map_file.with_suffix(".tmp")
                tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1))
                os.chmod(tmp, 0o600)
                tmp.replace(self.map_file)

    def add(self, conv_key: str, title: str, role: str, text: str):
        """Them 1 tin (role user/assistant) vao chat cua conv_key; tao chat neu chua co. Khong bao gio raise."""
        if not self.enabled or not text:
            return
        with _lock:
            lock = _conv_locks.setdefault(conv_key, threading.Lock())
        try:
            with lock:
                self._add(conv_key, title, role, text)
        except Exception as e:  # Open WebUI loi khong duoc lam hong kenh chat
            logger.warning("[owui-mirror] khong chep duoc vao Open WebUI: %s", e)

    def add_async(self, conv_key: str, title: str, role: str, text: str):
        """Chay add() tren pool rieng; tra ve asyncio future (co the khong await)."""
        return asyncio.get_running_loop().run_in_executor(_pool, self.add, conv_key, title, role, text)

    def _msg(self, role, text, parent):
        m = {"id": str(uuid.uuid4()), "parentId": parent, "childrenIds": [], "role": role,
             "content": text, "timestamp": int(time.time())}
        if role == "assistant":
            m.update({"model": self.model, "modelName": self.model, "done": True})
        else:
            m["models"] = [self.model]
        return m

    def _add(self, conv_key, title, role, text):
        entry = self._map(conv_key)
        if entry:
            try:
                chat = self._req("GET", f"/api/v1/chats/{entry['chat_id']}").get("chat") or {}
            except urllib.error.HTTPError as e:
                if e.code not in (401, 404):
                    raise
                chat, entry = {}, None  # chat bi xoa ben Open WebUI: tao lai
        if not entry:
            msg = self._msg(role, text, None)
            chat = {"title": title, "models": [self.model], "messages": [msg],
                    "history": {"messages": {msg["id"]: msg}, "currentId": msg["id"]}}
            res = self._req("POST", "/api/v1/chats/new", {"chat": chat})
            self._map(conv_key, {"chat_id": res["id"], "title": title}, write=True)
            return
        hist = chat.setdefault("history", {"messages": {}, "currentId": None})
        parent = hist.get("currentId")
        msg = self._msg(role, text, parent)
        if parent and parent in hist["messages"]:
            hist["messages"][parent].setdefault("childrenIds", []).append(msg["id"])
        hist["messages"][msg["id"]] = msg
        hist["currentId"] = msg["id"]
        chat.setdefault("messages", []).append(msg)
        if title and chat.get("title") != title and entry.get("title") != title:
            chat["title"] = title
            entry["title"] = title
            self._map(conv_key, entry, write=True)
        self._req("POST", f"/api/v1/chats/{entry['chat_id']}", {"chat": chat})
