# Triển khai chatbot-tu-van

## Sơ đồ

```
Website khách ──<script widget.js>──► https://bot.shop.vn ──► 127.0.0.1:8650 (plugin webchat) ─┐
Zalo (khách nhắn OA) ──webhook──────► https://bot.shop.vn/zalo/webhook ► 127.0.0.1:8651 (zalo_oa) ┤
                                                                                                 ▼
                                          Hermes gateway (profile khách) + hook chatbot_guard + MCP kb
                                                                                                 │
                              Open WebUI của khách ◄── chép từng tin (API /api/v1/chats) ────────┘
```

Hai cổng chỉ nghe `127.0.0.1`; ra Internet qua reverse proxy có HTTPS. Mỗi khách hàng (profile) dùng cặp cổng riêng (`webchat.port`, `zalo.port` trong `settings.json`) nếu chạy nhiều profile trên cùng máy.

## settings.json

| Khóa | Ý nghĩa |
|---|---|
| `business` | Tên, hotline, zalo, giờ làm việc, website. Được coi là thông tin chuẩn (bot được nhắc lại các số này). |
| `fallback_text` | Câu thay thế khi câu trả lời bị chặn vì có số liệu không có căn cứ. |
| `guard.enabled / platforms / max_passages` | Bật hook, kênh áp dụng (mặc định `webchat`, `zalo_oa`), số đoạn tài liệu chèn mỗi lượt. |
| `open_webui.url / api_key / model_label` | Nơi chép hội thoại. Chat thuộc tài khoản sở hữu API key. `model_label` là tên hiển thị của bot. |
| `lead_webhook.url / secret` | Nhận sự kiện `lead`, `handoff`, `guard_blocked` (JSON). Header `X-Chatbot-Timestamp`, `X-Chatbot-Signature: sha256=HMAC_SHA256(secret, timestamp + "." + body)`. |
| `webchat.allowed_origins` | Danh sách origin website được nhúng (đủ cả `www`). Thiếu thì kênh không bật. |
| `webchat.title / color / greeting` | Giao diện khung chat. |
| `zalo.oa_ids` | OA nào được chatbot trả lời (webhook của OA khác bị bỏ qua). |
| `zalo.oa_secret_key` | "OA Secret Key" ở mục Webhook của app, dùng kiểm tra chữ ký `X-ZEvent-Signature`. |
| `zalo.verify_files` | `{"zalo_verifier_xxx.html": "<nội dung file>"}` để xác thực domain với Zalo. |

Biến môi trường (`.env` của profile, setup.py ghi sẵn): `CHATBOT_HOME`, `ZALO_APP_ID`, `ZALO_APP_SECRET`, `WEBCHAT_ALLOW_ALL_USERS=true`, `ZALO_OA_ALLOW_ALL_USERS=true` (khách vãng lai không cần ghép cặp), `WEBCHAT_HOME_CHANNEL=none`, `ZALO_OA_HOME_CHANNEL=none` (không có kênh nhà: Hermes không nhắn "/sethome" cho khách). Tùy chọn: `ZALO_TOKEN_FILE`.

## Reverse proxy

Caddy (tự lấy HTTPS):

```
bot.shop.vn {
    handle /zalo* {
        reverse_proxy 127.0.0.1:8651
    }
    handle {
        reverse_proxy 127.0.0.1:8650
    }
}
```

Nginx:

```
location /zalo { proxy_pass http://127.0.0.1:8651; proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; }
location /     { proxy_pass http://127.0.0.1:8650; proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                 proxy_read_timeout 60s; proxy_buffering off; }
```

`X-Forwarded-For` cần cho giới hạn tốc độ theo IP (plugin chỉ tin header này khi kết nối đến từ 127.0.0.1). Long-poll giữ kết nối tối đa 25 giây.

Kiểm tra từ ngoài: `https://bot.shop.vn/health` và `https://bot.shop.vn/zalo/webhook` (GET) đều phải trả `ok`.

## Zalo (developers.zalo.me)

1. App của mình (admin có quyền sửa) > **Official Account**: thêm callback URL `https://bot.shop.vn/zalo/callback`; bật các quyền gửi tin tư vấn, đọc thông tin người quan tâm, quản lý bài viết (nếu dùng chung với skill viết bài).
2. **Xác thực domain** `bot.shop.vn`: Zalo đưa file `zalo_verifier….html`; đặt tên + nội dung vào `zalo.verify_files`, restart gateway, bấm xác thực.
3. **Webhook**: URL `https://bot.shop.vn/zalo/webhook`, bật sự kiện "Người dùng gửi tin nhắn văn bản" (`user_send_text`). Chép "OA Secret Key" vào `zalo.oa_secret_key`.
4. Chủ OA cấp quyền: `zalo_tokens.py auth-url ...` (Gate 6 trong SKILL.md). Lấy OA id từ `zalo_tokens.py list` điền vào `zalo.oa_ids`.

Ghi chú: tin tư vấn (`/v3.0/oa/message/cs`) chỉ gửi được trong khoảng thời gian Zalo cho phép sau tin nhắn gần nhất của khách; bot luôn trả lời ngay nên không vướng. Chỉ tin văn bản được xử lý; ảnh, sticker khách gửi bị bỏ qua. Refresh token hết hạn sau khoảng 3 tháng nếu không dùng.

## Open WebUI

1. Admin Panel > Settings > General: bật **API Keys** (Enable API Key).
2. Đăng nhập tài khoản sẽ xem hội thoại > Settings > Account > API keys > tạo key, dán vào `open_webui.api_key`.
3. Mỗi khách 1 chat trong sidebar: `Web · khách <mã>` hoặc `Zalo · <tên Zalo>`. Đổi tên chat trong Open WebUI thì plugin không ghi đè. Xóa chat thì tin tiếp theo của khách tạo chat mới.
4. Chỉ để xem. Gõ trả lời trong Open WebUI sẽ gửi cho model của Open WebUI, **không** tới khách. Muốn nhân viên trả lời khách: dùng Zalo OA trực tiếp (Zalo) hoặc gọi lại theo số khách để lại.

## Dữ liệu trên máy

```
$HERMES_HOME/chatbot/
  settings.json        cấu hình (quyền 600)
  knowledge/*.md       tài liệu đã nạp (sửa tay được, bot đọc lại ngay)
  kb.py                MCP server + công cụ nạp/tìm
  leads.jsonl          lead, yêu cầu gặp người thật, câu trả lời bị chặn
  owui_chats.json      khách ↔ chat Open WebUI
~/.hermes/zalo/tokens.json   token OA (quyền 600, dùng chung các skill Zalo)
```
