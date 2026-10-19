"""Kenh chat website cho Hermes (plugin platform).

Khach dan 1 the script len website:
    <script src="https://bot.example.com/widget.js" defer></script>
widget.js goi:
    POST /api/chat       {"vid": "<id trinh duyet>", "text": "..."}  -> 202
    GET  /api/messages?vid=...&after=<seq>                          -> long-poll cau tra loi
Moi vid la 1 phien Hermes rieng. Cau tra loi duoc chep sang Open WebUI (owui_mirror.py).

Cau hinh: $CHATBOT_HOME/settings.json > webchat {host, port, allowed_origins, title, color, greeting}.
"""
import asyncio
import json
import logging
import os
import re
import time
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Dict, Optional

from gateway.config import Platform, PlatformConfig
from gateway.platforms.base import BasePlatformAdapter, MessageEvent, MessageType, SendResult

try:
    from .owui_mirror import Mirror
except ImportError:  # setup.py chua chep file
    Mirror = None

logger = logging.getLogger(__name__)

PLATFORM = "webchat"
VID_RE = re.compile(r"^[A-Za-z0-9_-]{8,64}$")
MAX_TEXT = 1000
MAX_BODY = 8 * 1024
POLL_SECONDS = 25
RATE = (20, 300)  # toi da 20 tin / 5 phut / vid
RATE_IP = (60, 300)  # / IP (nhieu khach chung mang van du)
IDLE_DROP = 6 * 3600  # bo trang thai cua vid khong hoat dong qua 6 gio


def chatbot_home() -> Path:
    if os.getenv("CHATBOT_HOME"):
        return Path(os.environ["CHATBOT_HOME"]).expanduser()
    hh = os.getenv("HERMES_HOME")
    return (Path(hh).expanduser() if hh else Path.home() / ".hermes") / "chatbot"


def load_settings() -> dict:
    f = chatbot_home() / "settings.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


class WebchatAdapter(BasePlatformAdapter):
    MAX_MESSAGE_LENGTH = 4000

    def __init__(self, config: PlatformConfig):
        super().__init__(config=config, platform=Platform(PLATFORM))
        s = load_settings()
        self.cfg = s.get("webchat") or {}
        self.host = os.getenv("WEBCHAT_HOST") or self.cfg.get("host") or "127.0.0.1"
        self.port = int(os.getenv("WEBCHAT_PORT") or self.cfg.get("port") or 8650)
        self.origins = set(self.cfg.get("allowed_origins") or [])
        self.mirror = Mirror(chatbot_home(), s.get("open_webui") or {}) if Mirror else None
        self._outbox: Dict[str, deque] = defaultdict(lambda: deque(maxlen=50))
        self._seq: Dict[str, int] = defaultdict(int)
        self._typing: Dict[str, float] = {}
        self._waiters: Dict[str, asyncio.Event] = defaultdict(asyncio.Event)
        self._hits: Dict[str, deque] = defaultdict(deque)
        self._last: Dict[str, float] = {}
        self._mirror_tasks: Dict[str, asyncio.Task] = {}
        self._gc_at = time.time()
        self._runner = None

    # ---------------------------------------------------------------- vong doi

    async def connect(self, *, is_reconnect: bool = False) -> bool:
        from aiohttp import web

        if not self.origins:
            msg = "[webchat] Chua co webchat.allowed_origins trong settings.json (vd https://shop.vn)."
            logger.error(msg)
            self._set_fatal_error("webchat_no_origins", msg, retryable=False)
            return False
        app = web.Application(client_max_size=MAX_BODY)
        app.router.add_get("/widget.js", self._widget)
        app.router.add_route("OPTIONS", "/api/{tail:.*}", self._preflight)
        app.router.add_post("/api/chat", self._chat)
        app.router.add_get("/api/messages", self._messages)
        app.router.add_get("/health", lambda _: web.json_response({"ok": True, "platform": PLATFORM}))
        self._runner = web.AppRunner(app)
        await self._runner.setup()
        await web.TCPSite(self._runner, self.host, self.port).start()
        self._mark_connected()
        self._running = True
        logger.info("[webchat] listening on %s:%d, origins=%s", self.host, self.port, sorted(self.origins))
        return True

    async def disconnect(self) -> None:
        if self._runner:
            await self._runner.cleanup()
            self._runner = None
        self._running = False

    # ---------------------------------------------------------------- gui tra loi

    async def send(self, chat_id: str, content: str, reply_to: Optional[str] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> SendResult:
        vid = chat_id.removeprefix("web-")
        if not chat_id.startswith("web-") or not VID_RE.match(vid):  # vd kenh nha "none" cua cron
            return SendResult(success=False, error=f"webchat: chat_id khong hop le {chat_id!r}")
        prev = self._mirror_tasks.get(vid)
        if prev and not prev.done():  # chep tin khach truoc, giu dung thu tu ben Open WebUI
            await asyncio.wait([prev], timeout=20)
        self._seq[vid] += 1
        self._outbox[vid].append({"seq": self._seq[vid], "role": "bot", "text": content, "time": int(time.time())})
        self._typing.pop(vid, None)
        self._waiters[vid].set()
        if self.mirror:
            await asyncio.to_thread(self.mirror.add, f"web:{vid}", f"Web · khách {vid[:6]}", "assistant", content)
        return SendResult(success=True, message_id=f"{vid}:{self._seq[vid]}")

    async def send_typing(self, chat_id: str, metadata=None) -> None:
        vid = chat_id.removeprefix("web-")
        self._typing[vid] = time.time()
        self._waiters[vid].set()

    async def get_chat_info(self, chat_id: str) -> Dict[str, Any]:
        return {"name": chat_id, "type": "dm"}

    # ---------------------------------------------------------------- HTTP

    def _cors(self, request, resp):
        origin = request.headers.get("Origin", "")
        if origin in self.origins:
            resp.headers["Access-Control-Allow-Origin"] = origin
            resp.headers["Vary"] = "Origin"
            resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return resp

    def _origin_ok(self, request) -> bool:
        return request.headers.get("Origin", "") in self.origins

    async def _preflight(self, request):
        from aiohttp import web
        return self._cors(request, web.Response(status=204 if self._origin_ok(request) else 403))

    async def _widget(self, request):
        from aiohttp import web
        js = (Path(__file__).parent / "widget.js").read_text(encoding="utf-8")
        conf = {"title": self.cfg.get("title") or "Tư vấn", "color": self.cfg.get("color") or "#0f5c8c",
                "greeting": self.cfg.get("greeting") or "Xin chào! Em có thể giúp gì cho anh/chị?"}
        js = js.replace("__WEBCHAT_CONFIG__", json.dumps(conf, ensure_ascii=False))
        return web.Response(text=js, content_type="application/javascript",
                            headers={"Cache-Control": "public, max-age=300"})

    def _rate_ok(self, key: str, rate=RATE) -> bool:
        now, q = time.time(), self._hits[key]
        while q and q[0] < now - rate[1]:
            q.popleft()
        if len(q) >= rate[0]:
            return False
        q.append(now)
        return True

    @staticmethod
    def _client_ip(request) -> str:
        """Sau reverse proxy cung may (nginx/caddy) thi IP that nam cuoi X-Forwarded-For."""
        remote = request.remote or ""
        fwd = request.headers.get("X-Forwarded-For", "")
        if fwd and remote in ("127.0.0.1", "::1"):
            return fwd.split(",")[-1].strip()
        return remote

    def _gc(self):
        now = time.time()
        if now - self._gc_at < 600:
            return
        self._gc_at = now
        for vid in [v for v, t in self._last.items() if now - t > IDLE_DROP]:
            for d in (self._last, self._outbox, self._seq, self._typing, self._waiters, self._hits, self._mirror_tasks):
                d.pop(vid, None)
        for k in [k for k, q in self._hits.items() if not q or q[-1] < now - RATE_IP[1]]:
            self._hits.pop(k, None)

    async def _chat(self, request):
        from aiohttp import web
        if not self._origin_ok(request):
            return web.json_response({"ok": False, "error": "origin"}, status=403)
        try:
            body = await request.json()
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
            return self._cors(request, web.json_response({"ok": False, "error": "json"}, status=400))
        vid, text = str(body.get("vid", "")), str(body.get("text", "")).strip()
        if not VID_RE.match(vid) or not text:
            return self._cors(request, web.json_response({"ok": False, "error": "vid/text"}, status=400))
        if len(text) > MAX_TEXT:
            return self._cors(request, web.json_response({"ok": False, "error": "qua dai"}, status=413))
        if not self._rate_ok(vid) or not self._rate_ok("ip:" + self._client_ip(request), RATE_IP):
            return self._cors(request, web.json_response({"ok": False, "error": "rate"}, status=429))

        self._gc()
        self._last[vid] = time.time()
        self._seq[vid] += 1
        seq = self._seq[vid]
        self._outbox[vid].append({"seq": seq, "role": "user", "text": text, "time": int(time.time())})
        if self.mirror:
            self._mirror_tasks[vid] = asyncio.create_task(
                asyncio.to_thread(self.mirror.add, f"web:{vid}", f"Web · khách {vid[:6]}", "user", text))
        source = self.build_source(chat_id=f"web-{vid}", chat_name=f"Web {vid[:6]}", chat_type="dm",
                                   user_id=f"web-{vid}", user_name=f"Khách web {vid[:6]}")
        event = MessageEvent(text=text, message_type=MessageType.TEXT, source=source,
                             raw_message={"vid": vid, "page": body.get("page")}, message_id=f"{vid}:{seq}")
        task = asyncio.create_task(self.handle_message(event))
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
        return self._cors(request, web.json_response({"ok": True, "seq": seq}, status=202))

    async def _messages(self, request):
        from aiohttp import web
        if not self._origin_ok(request):
            return web.json_response({"ok": False, "error": "origin"}, status=403)
        vid = request.query.get("vid", "")
        if not VID_RE.match(vid):
            return self._cors(request, web.json_response({"ok": False, "error": "vid"}, status=400))
        try:
            after = int(request.query.get("after", "0"))
        except ValueError:
            after = 0

        def pending():
            return [m for m in self._outbox.get(vid, ()) if m["seq"] > after and m["role"] == "bot"]

        def is_typing():
            return vid in self._typing and time.time() - self._typing[vid] < 30

        # Tra ve ngay khi co tin moi hoac trang thai "dang go" khac voi client dang hien
        client_typing = request.query.get("typing") == "1"
        deadline = time.time() + POLL_SECONDS
        while not pending() and is_typing() == client_typing and time.time() < deadline:
            ev = self._waiters[vid]
            ev.clear()
            try:
                await asyncio.wait_for(ev.wait(), timeout=min(5, max(0.1, deadline - time.time())))
            except asyncio.TimeoutError:
                pass
        typing = is_typing()
        return self._cors(request, web.json_response(
            {"ok": True, "messages": pending(), "last": self._seq.get(vid, 0), "typing": typing}))


# ---------------------------------------------------------------- dang ky plugin

def _check() -> bool:
    try:
        import aiohttp  # noqa: F401
    except ImportError:
        return False
    return True


def register(ctx) -> None:
    ctx.register_platform(
        name=PLATFORM,
        label="Chat website",
        adapter_factory=lambda cfg: WebchatAdapter(cfg),
        check_fn=_check,
        is_connected=lambda cfg: True,
        required_env=[],
        install_hint="pip install aiohttp",
        allow_all_env="WEBCHAT_ALLOW_ALL_USERS",
        max_message_length=WebchatAdapter.MAX_MESSAGE_LENGTH,
        emoji="💬",
    )
