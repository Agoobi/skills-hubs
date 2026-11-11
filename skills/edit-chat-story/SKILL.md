---
name: edit-chat-story
description: Dựng video dọc 9:16 kể chuyện bằng khung chat (khách nhắn ↔ chatbot AI/nhân viên trả lời): bong bóng hiện lần lượt, chấm "đang soạn", thẻ sản phẩm, thả tim, hook mở đầu và cảnh CTA — hợp quảng cáo chatbot chốt đơn, demo agent CSKH. Dữ liệu từ JSON, render trên Claude, kèm bảng mốc SFX.
---

# Edit Chat Story

Dựa trên hướng dẫn `text-message-animation` của iart.ai (MIT), viết lại thành template canvas tiếng Việt cho AI Agent VN. Dùng cho video demo chatbot/agent trả lời khách, video "khách nhắn lúc 23h", kịch bản so sánh trước/sau có chatbot.

## Nguyên tắc
1. **Từng tin một, có nhịp.** Tin của bot luôn có chấm "đang soạn" trước; sau mỗi tin có khoảng đọc (template tự tính theo độ dài, 0,7–2,2 s). Không đổ cả đoạn chat ở khung đầu.
2. **Giao diện chat chung, không giả app thật.** Template vẽ điện thoại với khung chat trung tính (header tên trợ lý, ô nhập). Không chép nguyên logo/giao diện Zalo, Messenger, iMessage. Khách muốn đúng màu kênh của họ thì đổi màu, không dựng lại thương hiệu của app.
3. **Kịch bản minh hoạ, ghi rõ là minh hoạ.** Không dựng đoạn chat như thể là tin nhắn thật của một khách hàng có thật, không gắn tên/ảnh người thật. Giá, khuyến mãi, tên sản phẩm phải là thông tin thật của doanh nghiệp người dùng đưa.

## Quy trình
`<skill>` là thư mục chứa file này (giữ nguyên cấu trúc: `templates/` cạnh `fonts/`).

1. **Kịch bản → `chat.json`**
   ```json
   {
     "hook": { "text": "Khách nhắn lúc 23h — ai trả lời?", "from": 0, "to": 2.6 },
     "header": { "name": "Trợ lý AI · Shop Lan", "status": "Đang hoạt động", "avatar": "AI" },
     "messages": [
       { "from": "khach", "text": "Shop ơi còn hàng không ạ?", "delay": 0.6 },
       { "from": "bot", "text": "Dạ còn ạ! Chị dùng cho da dầu hay da khô?", "typing": 1.2 },
       { "from": "bot", "card": { "title": "Kem chống nắng SPF50", "price": "289.000đ", "button": "Đặt ngay", "badge": "SẢN PHẨM" }, "typing": 1.0 },
       { "from": "bot", "text": "Đặt trước 0h được freeship nha!", "typing": 0.9, "emphasis": true },
       { "from": "khach", "text": "Lấy chị 2 hộp", "delay": 0.8, "reaction": "❤️" }
     ],
     "end": { "text": "Chatbot trả lời 24/7 — không bỏ sót đơn", "cta": "Inbox để dùng thử", "hold": 2.8 },
     "palette": { "me": "#2F6BFF", "accent": "#3FD6A6" }
   }
   ```
   - `from`: `khach` (bên phải, màu `me`) hoặc `bot` (bên trái, trắng).
   - `typing`: giây chấm soạn trước tin bot; `delay`: thêm thời gian trước tin khách.
   - `emphasis`: viền màu nhấn cho tin quan trọng (ưu đãi, cam kết). `reaction`: emoji thả lên bong bóng.
   - Tin nhắn ngắn như người thật nhắn (≤ ~90 ký tự); dài thì tách 2 tin. Bot xưng hô theo cách doanh nghiệp đó dùng.
   - Bỏ `hook`/`end` (để rỗng `text`) khi chỉ cần đoạn chat để chèn vào video khác.
   - Màu mặc định: nền preset `aiagentvn`; `palette` ghi đè từng khoá (`bg_top, bg_bottom, glow1, glow2, text, accent, accent2, warn, me, them, ...`).

2. **Xem trước và lấy mốc SFX**
   ```bash
   python3 <skill>/scripts/render.py <skill>/templates/chat.html sheet.jpg --data chat.json --sheet 1 --cues cues.json
   ```
   `cues.json` liệt kê mốc `send` / `receive` / `typing` / `pop` / `whoosh`. Xem contact sheet: chữ không tràn bong bóng, cuộn mượt, tin mới luôn nằm trong khung.

3. **Âm thanh** (tuỳ chọn): đặt SFX theo `cues.json` (tiếng gửi/nhận tin ngắn, gõ phím nhẹ khi soạn, whoosh ở cảnh kết) + nhạc nền nhỏ. Thư viện SFX ở máy người dùng thì lấy qua công cụ liên kết máy tính; theo quy tắc SFX của skill edit đang dùng (không lặp một file, không cắt đuôi). Trộn bằng ffmpeg (`adelay` + `amix`), rồi ghép:
   ```bash
   python3 <skill>/scripts/render.py <skill>/templates/chat.html chat.mp4 --data chat.json --audio mix.wav
   ```
   Có voice đọc thì canh mốc tin nhắn theo voice (chỉnh `typing`/`delay`), không kéo giãn voice.

4. **Xuất**
   - `chat.mp4` (nền đầy đủ) hoặc `chat.mov --alpha` (trong suốt, khi chèn vào video khác — nền gradient bị tắt, chỉ còn điện thoại).
   - Kích thước khác: `--w 1080 --h 1350` (4:5) — kiểm lại khung điện thoại trong still.

## Kiểm tra trước khi giao
- Contact sheet + still ở tin dài nhất và thẻ sản phẩm đã xem thật; dấu tiếng Việt rõ.
- Điện thoại nằm trong safe zone (x 110–970, y 250–1480); hook và CTA không xuống dưới y 1500.
- Giá, tên sản phẩm, ưu đãi đúng thông tin người dùng đưa.
- Probe: thời lượng, fps, có audio (nếu có mix).
Giao: video, `chat.json`, `cues.json`, ghi chú phần nào là minh hoạ.
