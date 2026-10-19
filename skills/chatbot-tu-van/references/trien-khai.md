# Triển khai chatbot-tu-van

## Sơ đồ

```
Website khách ──<script widget.js>──► https://bot.shop.vn ──► 127.0.0.1:8650 (plugin webchat)
                                                                            │
                                                                            ▼
                                 Hermes gateway (profile khách) + hook chatbot_guard + MCP kb
                                                                            │
                Open WebUI của khách ◄── chép từng tin (API /api/v1/chats) ─┘
```

Cổng chỉ nghe `127.0.0.1`; ra Internet qua reverse proxy có HTTPS. Mỗi khách hàng (profile) dùng cổng riêng (`webchat.port` trong `settings.json`) nếu chạy nhiều profile trên cùng máy.

## settings.json

| Khóa | Ý nghĩa |
|---|---|
| `business` | Tên, hotline, số Zalo liên hệ, giờ làm việc, website. Được coi là thông tin chuẩn (bot được nhắc lại các số này). |
| `fallback_text` | Câu thay thế khi câu trả lời bị chặn vì có số liệu không có căn cứ. |
| `guard.enabled / platforms / max_passages` | Bật hook, kênh áp dụng (mặc định `webchat`), số đoạn tài liệu chèn mỗi lượt. |
| `open_webui.url / api_key / model_label` | Nơi chép hội thoại. Chat thuộc tài khoản sở hữu API key. `model_label` là tên hiển thị của bot. |
| `lead_webhook.url / secret` | Nhận sự kiện `lead`, `handoff`, `guard_blocked` (JSON). Header `X-Chatbot-Timestamp`, `X-Chatbot-Signature: sha256=HMAC_SHA256(secret, timestamp + "." + body)`. |
| `webchat.allowed_origins` | Danh sách origin website được nhúng (đủ cả `www`). Thiếu thì kênh không bật. |
| `webchat.title / color / greeting` | Giao diện khung chat. |

Biến môi trường (`.env` của profile, setup.py ghi sẵn): `CHATBOT_HOME`, `WEBCHAT_ALLOW_ALL_USERS=true` (khách vãng lai không cần ghép cặp), `WEBCHAT_HOME_CHANNEL=none` (không có kênh nhà: Hermes không nhắn "/sethome" cho khách).

## Reverse proxy

Caddy (tự lấy HTTPS):

```
bot.shop.vn {
    reverse_proxy 127.0.0.1:8650
}
```

Nginx:

```
location / { proxy_pass http://127.0.0.1:8650; proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
             proxy_read_timeout 60s; proxy_buffering off; }
```

`X-Forwarded-For` cần cho giới hạn tốc độ theo IP (plugin chỉ tin header này khi kết nối đến từ 127.0.0.1). Long-poll giữ kết nối tối đa 25 giây.

Kiểm tra từ ngoài: `https://bot.shop.vn/health` phải trả `ok`.

## Open WebUI

1. Admin Panel > Settings > General: bật **API Keys** (Enable API Key).
2. Đăng nhập tài khoản sẽ xem hội thoại > Settings > Account > API keys > tạo key, dán vào `open_webui.api_key`.
3. Mỗi khách 1 chat trong sidebar: `Web · khách <mã>`. Đổi tên chat trong Open WebUI thì plugin không ghi đè. Xóa chat thì tin tiếp theo của khách tạo chat mới.
4. Chỉ để xem. Gõ trả lời trong Open WebUI sẽ gửi cho model của Open WebUI, **không** tới khách. Muốn nhân viên trả lời khách: gọi lại theo số khách để lại.

## Dữ liệu trên máy

```
$HERMES_HOME/chatbot/
  settings.json        cấu hình (quyền 600)
  knowledge/*.md       tài liệu đã nạp (sửa tay được, bot đọc lại ngay)
  kb.py                MCP server + công cụ nạp/tìm
  leads.jsonl          lead, yêu cầu gặp người thật, câu trả lời bị chặn
  owui_chats.json      khách ↔ chat Open WebUI
```
