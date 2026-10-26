# Triển khai chatbot-tu-van

## Sơ đồ

```
Website khách ──<script widget.js>──► https://bot.shop.vn ──► 127.0.0.1:8650 (plugin webchat)
                                                                            │
                                                                            ▼
                                 Hermes gateway (profile khách) + hook chatbot_guard + MCP kb
                                                                            │  lưu hội thoại + lead
                                                                            ▼
                                             chatbot/inbox/ ──► /inbox/api/* (cùng cổng webchat)
                                                                            ▲
Open WebUI (chủ shop đăng nhập) ── trang /static/hop-thu ── token đăng nhập ┘  (Hermes hỏi Open WebUI token của ai)
```

Hermes **không ghi gì vào Open WebUI** (không chat, không folder, không cần API key). Open WebUI chỉ là nơi mở trang
Hộp thư (repo `Agoobi/openwebui-custom`) và đăng nhập.

Cổng chỉ nghe `127.0.0.1`; ra Internet qua reverse proxy có HTTPS. Mỗi khách hàng (profile) dùng cổng riêng (`webchat.port` trong `settings.json`) nếu chạy nhiều profile trên cùng máy.

## settings.json

| Khóa | Ý nghĩa |
|---|---|
| `business` | Tên, hotline, số Zalo liên hệ, giờ làm việc, website. Được coi là thông tin chuẩn (bot được nhắc lại các số này). |
| `thu_thap_khach` | Bot xin khách gì khi tài liệu không có câu trả lời, theo thứ tự: `ten`, `sdt`, `email`, `zalo`, `dia_chi`, `cong_ty`, `thoi_gian`. `[]`: không xin, mời liên hệ hotline. Mặc định `["ten", "sdt"]`. |
| `fallback_text` | Câu thay thế khi câu trả lời bị chặn vì có số liệu không có căn cứ. Để trống: tự ghép theo `thu_thap_khach`. |
| `guard.enabled / platforms / max_passages` | Bật hook, kênh áp dụng (mặc định `webchat`), số đoạn tài liệu chèn mỗi lượt. |
| `open_webui.url` | Địa chỉ Hermes gọi tới Open WebUI để xác thực người mở Hộp thư (vd `http://127.0.0.1:8080`). |
| `open_webui.public_url` | Origin https của Open WebUI (vd `https://chat.shop.vn`): trang Hộp thư chạy ở đây, chỉ origin này gọi được `/inbox/api`. |
| `open_webui.roles` | Vai trò Open WebUI được xem Hộp thư, mặc định `["admin"]` (thêm `"user"` cho nhân viên). |
| `webchat.public_url` | URL https của bot (vd `https://bot.shop.vn`); điền vào `install.sh` của openwebui-custom để trang Hộp thư biết gọi đâu. |
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

## Hộp thư (trang trong Open WebUI)

1. Cài `Agoobi/openwebui-custom` lên máy Open WebUI: `HERMES_INBOX_URL=https://bot.shop.vn deploy/install.sh`.
   Sidebar có thêm hàng **Hộp thư** (kèm số khách cần xử lý), mở trang `/static/hop-thu/index.html`.
2. Điền `open_webui.url`, `open_webui.public_url` trong settings.json rồi restart gateway.
3. Trang Hộp thư: danh sách khách (Tất cả / Cần xử lý / Đang chat / Đã xong, lọc kênh, tìm, sắp xếp), hội thoại,
   thông tin khách, nút **Đã gọi / Xong / Mở lại**. Khách để lại thông tin, cần gặp nhân viên hoặc bot bị chặn thì
   tự vào **Cần xử lý**; khách nhắn lại sau khi xong thì về **Đang chat**. Tự làm mới vài giây một lần.
4. Đăng nhập: trang gửi token phiên Open WebUI, Hermes hỏi `GET <open_webui.url>/api/v1/auths/` xem là ai (nhớ 60
   giây), chỉ nhận vai trò trong `open_webui.roles`. Không nhận API key `sk-…`.
5. Trả lời khách từ Hộp thư: chưa có. Gọi lại theo số khách để lại.

## Dữ liệu trên máy

```
$HERMES_HOME/chatbot/
  settings.json        cấu hình (quyền 600)
  nguon/*.md           file gốc đã chuyển sang Markdown (bot không đọc)
  knowledge/*.md       kiến thức đã soạn theo chủ đề; bot chỉ dùng file đã verify
  kiem_tra.json        kết quả verify (mã băm file kiến thức + nguồn)
  kb.py                MCP server + công cụ nạp/tìm
  leads.jsonl          lead, yêu cầu gặp người thật, câu trả lời bị chặn
  inbox/index.json     hộp thư: trạng thái, thông tin từng khách (quyền 600)
  inbox/<id>.jsonl     tin nhắn và sự kiện của từng khách
```
