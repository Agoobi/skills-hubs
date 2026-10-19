"""Kenh Zalo Official Account cho Hermes (plugin platform).

- Nhan webhook tin nhan cua Zalo tai POST /zalo/webhook (dien URL nay o developers.zalo.me > Webhook).
- Kiem tra chu ky X-ZEvent-Signature: mac = sha256(app_id + body + timestamp + OA secret key).
- Tra loi bang tin tu van: POST https://openapi.zalo.me/v3.0/oa/message/cs.
- Token OA lay tu kho dung chung zalo_tokens.py (tu lam moi, co khoa file).
- Hoi thoai duoc chep sang Open WebUI (owui_mirror.py).

Cau hinh: $CHATBOT_HOME/settings.json > zalo {host, port, oa_ids, oa_secret_key, verify_signature, verify_files}
va env ZALO_APP_ID / ZALO_APP_SECRET.
"""
import asyncio
import hashlib
import hmac
import json
import logging
import os
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, Optional

from gateway.config import Platform, PlatformConfig
from gateway.platforms.base import BasePlatformAdapter, MessageEvent, MessageType, SendResult
from gateway.platforms.helpers import strip_markdown

from .zalo_tokens import ZaloAuthError, access_token, complete

try:
    from .owui_mirror import Mirror
except ImportError:
    Mirror = None

logger = logging.getLogger(__name__)

PLATFORM = "zalo_oa"
API = os.getenv("ZALO_API_BASE") or "https://openapi.zalo.me/v3.0/oa"  # env de test voi API gia lap
MAX_TEXT = 2000
MAX_BODY = 64 * 1024
TOKEN_ERRORS = {-216, -124, -230}  # token sai / het han


def chatbot_home() -> Path:
    if os.getenv("CHATBOT_HOME"):
        return Path(os.environ["CHATBOT_HOME"]).expanduser()
    hh = os.getenv("HERMES_HOME")
    return (Path(hh).expanduser() if hh else Path.home() / ".hermes") / "chatbot"


def load_settings() -> dict:
    f = chatbot_home() / "settings.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def _esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def zalo_mac(app_id: str, body: bytes, timestamp: str, oa_secret: str) -> str:
    return hashlib.sha256(app_id.encode() + body + str(timestamp).encode() + oa_secret.encode()).hexdigest()


class ZaloOAAdapter(BasePlatformAdapter):
    MAX_MESSAGE_LENGTH = MAX_TEXT

    def __init__(self, config: PlatformConfig):
        super().__init__(config=config, platform=Platform(PLATFORM))
        s = load_settings()
        self.cfg = s.get("zalo") or {}
        self.host = os.getenv("ZALO_WEBHOOK_HOST") or self.cfg.get("host") or "127.0.0.1"
        self.port = int(os.getenv("ZALO_WEBHOOK_PORT") or self.cfg.get("port") or 8651)
        self.app_id = os.getenv("ZALO_APP_ID", "")
        self.oa_ids = {str(x) for x in self.cfg.get("oa_ids") or []}
        self.oa_secret = os.getenv("ZALO_OA_SECRET_KEY") or self.cfg.get("oa_secret_key") or ""
        self.verify = self.cfg.get("verify_signature", True)
        self.mirror = Mirror(chatbot_home(), s.get("open_webui") or {}) if Mirror else None
        self._seen: OrderedDict = OrderedDict()
        self._names: Dict[str, str] = {}
        self._runner = None
        self._http = None

    async def connect(self, *, is_reconnect: bool = False) -> bool:
        import aiohttp
        from aiohttp import web

        problems = []
        if not self.app_id:
            problems.append("ZALO_APP_ID")
        if not self.oa_ids:
            problems.append("zalo.oa_ids")
        if self.verify and not self.oa_secret:
            problems.append("zalo.oa_secret_key (hoac dat verify_signature=false khi test)")
        if problems:
            msg = "[zalo_oa] Thieu cau hinh: " + ", ".join(problems)
            logger.error(msg)
            self._set_fatal_error("zalo_config", msg, retryable=False)
            return False
        app = web.Application(client_max_size=MAX_BODY)
        app.router.add_post("/zalo/webhook", self._webhook)
        app.router.add_get("/zalo/webhook", lambda _: web.Response(text="ok"))
        app.router.add_get("/zalo/callback", self._oauth_callback)  # chu OA bam Dong y -> luu token
        app.router.add_get("/health", lambda _: web.json_response({"ok": True, "platform": PLATFORM}))
        for name in (self.cfg.get("verify_files") or {}):  # file xac thuc domain cua Zalo
            app.router.add_get("/" + name.lstrip("/"), self._verify_file)
        self._runner = web.AppRunner(app)
        await self._runner.setup()
        await web.TCPSite(self._runner, self.host, self.port).start()
        self._http = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30), trust_env=True)
        self._mark_connected()
        self._running = True
        logger.info("[zalo_oa] webhook on %s:%d/zalo/webhook, OA=%s", self.host, self.port, sorted(self.oa_ids))
        return True

    async def disconnect(self) -> None:
        if self._http:
            await self._http.close()
            self._http = None
        if self._runner:
            await self._runner.cleanup()
            self._runner = None
        self._running = False

    # ---------------------------------------------------------------- goi API Zalo

    async def _api(self, oa_id: str, method: str, path: str, **kw) -> dict:
        token = None
        for attempt in (0, 1):
            token = await asyncio.to_thread(access_token, oa_id, token)
            async with self._http.request(method, API + path, headers={"access_token": token}, **kw) as r:
                data = await r.json(content_type=None)
            if data.get("error", 0) in TOKEN_ERRORS and attempt == 0:
                continue  # token bi thu hoi som: lam moi 1 lan roi thu lai
            return data
        return data

    async def _display_name(self, oa_id: str, user_id: str) -> str:
        key = f"{oa_id}:{user_id}"
        if key not in self._names:
            name = ""
            try:
                data = await self._api(oa_id, "GET", "/user/detail",
                                       params={"data": json.dumps({"user_id": user_id})})
                name = (data.get("data") or {}).get("display_name") or ""
            except (ZaloAuthError, OSError, ValueError) as e:
                logger.debug("[zalo_oa] user/detail loi: %s", e)
            self._names[key] = name
        return self._names[key]

    async def send(self, chat_id: str, content: str, reply_to: Optional[str] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> SendResult:
        oa_id, _, user_id = chat_id.partition(":")
        if oa_id not in self.oa_ids or not user_id:  # vd kenh nha "none" cua cron
            return SendResult(success=False, error=f"zalo_oa: chat_id khong hop le {chat_id!r}")
        text = strip_markdown(content)
        last = SendResult(success=True)
        for part in self.truncate_message(text):
            try:
                data = await self._api(oa_id, "POST", "/message/cs",
                                       json={"recipient": {"user_id": user_id}, "message": {"text": part}})
            except (ZaloAuthError, OSError) as e:
                logger.error("[zalo_oa] gui tin loi: %s", e)
                return SendResult(success=False, error=str(e))
            if data.get("error", 0) != 0:
                logger.error("[zalo_oa] Zalo tu choi: %s", data)
                return SendResult(success=False, error=f"Zalo {data.get('error')}: {data.get('message')}")
            last = SendResult(success=True, message_id=(data.get("data") or {}).get("message_id"))
        if self.mirror:
            name = self._names.get(chat_id) or user_id[-6:]
            await asyncio.to_thread(self.mirror.add, f"zalo:{chat_id}", f"Zalo · {name}", "assistant", text)
        return last

    async def get_chat_info(self, chat_id: str) -> Dict[str, Any]:
        return {"name": self._names.get(chat_id) or chat_id, "type": "dm"}

    # ---------------------------------------------------------------- webhook

    async def _oauth_callback(self, request):
        from aiohttp import web
        try:
            res = await asyncio.to_thread(complete, request.query_string)
            ok = res["oa_id"] in self.oa_ids
            msg = (f"Đã kết nối Zalo OA {res['oa_id']}. Có thể đóng trang này." if ok else
                   f"Đã lưu token OA {res['oa_id']}, nhưng OA này chưa có trong zalo.oa_ids của chatbot.")
        except (ZaloAuthError, OSError) as e:
            logger.warning("[zalo_oa] callback loi: %s", e)
            msg = f"Kết nối chưa thành công: {e}"
        html = f"<!doctype html><meta charset=utf-8><title>Zalo OA</title><p style='font:16px sans-serif'>{_esc(msg)}</p>"
        return web.Response(text=html, content_type="text/html")

    async def _verify_file(self, request):
        from aiohttp import web
        name = request.path.lstrip("/")
        return web.Response(text=(self.cfg.get("verify_files") or {}).get(name, ""), content_type="text/html")

    async def _webhook(self, request):
        from aiohttp import web
        raw = await request.read()
        try:
            body = json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return web.json_response({"error": "json"}, status=400)
        if self.verify:
            sig = request.headers.get("X-ZEvent-Signature", "").strip()
            sig = sig.split("=", 1)[1] if sig.startswith("mac=") else sig
            expect = zalo_mac(self.app_id, raw, str(body.get("timestamp", "")), self.oa_secret)
            if not sig or not hmac.compare_digest(sig, expect):
                logger.warning("[zalo_oa] chu ky webhook sai, bo qua")
                return web.json_response({"error": "signature"}, status=401)

        event = body.get("event_name", "")
        oa_id = str((body.get("recipient") or {}).get("id", ""))
        user_id = str((body.get("sender") or {}).get("id", ""))
        msg = body.get("message") or {}
        msg_id = msg.get("msg_id") or f"{user_id}:{body.get('timestamp')}"
        if event != "user_send_text" or oa_id not in self.oa_ids or not user_id:
            return web.json_response({"ok": True, "ignored": event})
        if msg_id in self._seen:  # Zalo gui lai khi cham phan hoi
            return web.json_response({"ok": True, "duplicate": True})
        self._seen[msg_id] = 1
        while len(self._seen) > 2000:
            self._seen.popitem(last=False)

        text = (msg.get("text") or "").strip()
        if not text:
            return web.json_response({"ok": True})
        task = asyncio.create_task(self._dispatch(oa_id, user_id, text, msg_id, body))
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
        return web.json_response({"ok": True})

    async def _dispatch(self, oa_id, user_id, text, msg_id, body):
        chat_id = f"{oa_id}:{user_id}"
        name = await self._display_name(oa_id, user_id)
        self._names[chat_id] = name or self._names.get(chat_id, "")
        if self.mirror:
            await asyncio.to_thread(self.mirror.add, f"zalo:{chat_id}", f"Zalo · {name or user_id[-6:]}", "user", text)
        source = self.build_source(chat_id=chat_id, chat_name=name or chat_id, chat_type="dm",
                                   user_id=user_id, user_name=name or None)
        await self.handle_message(MessageEvent(text=text, message_type=MessageType.TEXT, source=source,
                                               raw_message=body, message_id=msg_id))


def _check() -> bool:
    try:
        import aiohttp  # noqa: F401
    except ImportError:
        return False
    return bool(os.getenv("ZALO_APP_ID") and os.getenv("ZALO_APP_SECRET"))


def register(ctx) -> None:
    ctx.register_platform(
        name=PLATFORM,
        label="Zalo OA",
        adapter_factory=lambda cfg: ZaloOAAdapter(cfg),
        check_fn=_check,
        is_connected=lambda cfg: bool(os.getenv("ZALO_APP_ID")),
        required_env=["ZALO_APP_ID", "ZALO_APP_SECRET"],
        install_hint="pip install aiohttp",
        allow_all_env="ZALO_OA_ALLOW_ALL_USERS",
        max_message_length=MAX_TEXT,
        emoji="🟦",
    )
