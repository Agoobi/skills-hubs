---
name: chatbot-tu-van
description: Chatbot tư vấn trên website, chủ shop xem khách ở trang Hộp thư trong Open WebUI.
version: 0.1.0
author: Agoobi
license: MIT
metadata:
  hermes:
    category: coquifly
    tags: [chatbot, website, open-webui, vietnamese]
---

# chatbot-tu-van

Biến một profile Hermes thành chatbot tư vấn khách hàng trên **website** (khung chat nhúng 1 dòng script), trả lời **chỉ từ tài liệu doanh nghiệp**. Mỗi khách là một cuộc trò chuyện riêng; chủ shop xem và xử lý khách ở **trang Hộp thư** mở trong Open WebUI (Hermes lưu dữ liệu, không ghi chat nào vào Open WebUI).

Skill này dành cho **admin cài đặt và bảo trì**. Lúc chatbot chạy, các quy tắc không nằm ở file này mà nằm trong code (plugin), nên vẫn có hiệu lực dù model có đọc skill hay không:

| Thành phần (cài vào `$HERMES_HOME/plugins/`) | Việc làm |
|---|---|
| `webchat` (kênh) | Phục vụ `widget.js`, nhận tin khách qua `/api/chat`, trả lời qua long-poll. Chặn domain lạ (CORS), giới hạn tốc độ. |
| `chatbot_guard` (hook) | Mỗi lượt: chèn vai trò + quy tắc + đoạn tài liệu tìm được; chặn câu trả lời có giá, %, SĐT, số tài khoản, thời hạn (ngày/tháng/năm…) không có trong tài liệu (thay bằng câu xin thông tin liên hệ và ghi sự kiện); không có thông tin thì nói chưa có và xin khách các thông tin trong `thu_thap_khach`; đưa khách cần tư vấn vào mục Cần xử lý của Hộp thư; bỏ dấu `/` để khách không gọi lệnh Hermes. |
| MCP `kb` (`chatbot/kb.py`) | 4 tool duy nhất của kênh chat: `tim_kien_thuc`, `doc_tai_lieu`, `luu_khach_hang`, `chuyen_nhan_vien`. Kênh chat **không có** terminal, file, web. Chỉ tìm trong file kiến thức **đã `verify`** và chưa bị sửa sau đó. |

## Quy tắc sắt

1. **Không tắt hoặc sửa `chatbot_guard`** để "cho bot trả lời được". Bot thiếu thông tin thì bổ sung tài liệu.
2. **Không thêm toolset nào** vào `platform_toolsets.webchat` ngoài `kb`. `check.py` báo lỗi nếu có.
3. Chỉ nạp tài liệu **khách hàng đã gửi và duyệt**. Kiến thức soạn ra chỉ lấy từ file nguồn, **không thêm, không suy đoán**; nguồn mâu thuẫn hoặc thiếu thì **hỏi lại user**, không tự chọn. Không sửa con số cho qua `verify`: sai thì sửa theo nguồn.
4. Không in API key, secret ra chat. Không commit `settings.json`.
5. Mọi việc chỉ dừng ở **cấu hình + kiểm tra**. Không tự nhắn tin cho khách, không xóa lịch sử chat.

## Cài đặt (một lần cho mỗi khách hàng / profile)

Lệnh chạy từ thư mục skill. `setup.py` và `check.py` cần Python của Hermes (có PyYAML), ví dụ `~/.hermes/hermes-agent/venv/bin/python`; gọi tắt là `HPY` bên dưới. `kb.py`, `eval.py` chỉ cần Python 3.

**Gate 1 — Thu thập (hỏi user 1 lượt, thiếu thì hỏi lại, không đoán).**
Tên profile Hermes; tên doanh nghiệp, hotline, số Zalo liên hệ, giờ làm việc, website; domain website sẽ gắn khung chat; domain cho bot (vd `bot.shop.vn`, trỏ về máy chạy Hermes); URL Open WebUI (nơi mở trang Hộp thư) và vai trò được xem (mặc định admin); khi bot không có thông tin thì xin khách gì (`ten`, `sdt`, `email`, `zalo`, `dia_chi`, `cong_ty`, `thoi_gian`, hoặc không xin mà mời gọi hotline); tài liệu (docx, xlsx, csv, md, txt, pdf có chữ).

**Gate 2 — Cài.**

```
HPY scripts/setup.py --profile <ten>
```

Script chép plugin, ghi `config.yaml` (bật plugin, MCP `kb`, giới hạn toolset kênh chat, tắt onboarding), ghi `.env` (quyền 600) và tạo `chatbot/settings.json` từ mẫu. Chạy lại an toàn (giữ `settings.json`, sao lưu `config.yaml.bak-chatbot`). Có `warnings` về thiếu `aiohttp` / `mcp` thì cài theo lệnh in ra.

**Gate 3 — Điền `chatbot/settings.json`** (xem `references/trien-khai.md`): `business`, `webchat.allowed_origins` (đủ `https://shop.vn` và `https://www.shop.vn`), `webchat.public_url` (URL https của bot, cho nút trên thẻ khách), `open_webui` (URL, API key), `thu_thap_khach`, `lead_webhook` nếu có. `fallback_text` để trống thì tự ghép theo `thu_thap_khach`. Cho user xem lại (che key) trước khi lưu.

**Gate 4 — Soạn kiến thức** (chi tiết: `references/kien-thuc.md`). Gọi `KB="python3 -I scripts/kb.py --home <HERMES_HOME>/chatbot"`.

1. `$KB ingest <file...>`: mỗi file thành `nguon/<ten>.md` (bản gốc, bot **không** đọc). Đọc lại, báo chỗ lỗi (bảng vỡ, PDF scan không có chữ).
2. Soạn `knowledge/<chu-de>.md` theo chủ đề khách hay hỏi (giá, sản phẩm, chính sách, FAQ...), dòng 2 ghi `<!-- nguon: a.md, b.md -->`.
3. Cho user xem từng file, sửa đến khi user đồng ý.
4. `$KB verify`: mọi con số (giá, %, số ngày, SĐT, mã...) phải có trong file nguồn đã ghi. File lỗi thì bot không dùng; sửa theo nguồn rồi chạy lại.
5. `$KB status` phải `ok`. Không cần restart.

**Gate 5 — Hạ tầng** (admin làm theo `references/trien-khai.md`): reverse proxy HTTPS cho `bot.shop.vn` vào cổng 8650; cài `Agoobi/openwebui-custom` lên Open WebUI với `HERMES_INBOX_URL=https://bot.shop.vn`.

**Gate 6 — Khởi động và kiểm tra.**

```
hermes -p <ten> gateway restart
HPY scripts/check.py --profile <ten> --ask "<một câu hỏi có trong tài liệu>"
```

Mọi mục `fail` phải sửa xong (mỗi mục có `fix`). `warn` thì báo user. Sau đó chạy bộ chấm:

```
python3 scripts/eval.py --profile <ten> [--cases <file-cau-hoi-rieng.json>]
```

`templates/cau-hoi-mau.json` là bộ chung (tấn công, bịa số, ngoài tài liệu). Viết thêm 10-20 câu riêng từ tài liệu của shop, mỗi câu có `phai_co` là con số/chính sách đúng nguyên văn, lưu cạnh `settings.json`. Báo user tỷ lệ đạt và các câu trượt kèm câu trả lời thật.

**Gate 7 — Bàn giao.** Gửi user đúng 1 dòng để dán vào website (WordPress: plugin chèn header/footer hoặc theme):

```
<script src="https://bot.shop.vn/widget.js" defer></script>
```

Kèm: chủ shop mở Open WebUI, bấm **Hộp thư** ở sidebar: danh sách khách (Cần xử lý / Đang chat / Đã xong), hội thoại, thông tin khách, nút Đã gọi / Xong / Mở lại (chi tiết: `references/trien-khai.md`). Chưa trả lời khách từ Hộp thư được: gọi lại theo số khách để lại. Lead còn lưu ở `chatbot/leads.jsonl` và được POST tới `lead_webhook` (ký HMAC).

## Cập nhật kiến thức (user gửi tài liệu mới bất cứ lúc nào)

1. `$KB ingest <file mới>` (cùng tên thì thay bản cũ, `changed: true` nếu nội dung khác).
2. `$KB status`: `nguon_da_doi` là file kiến thức cần soạn lại (bot vẫn dùng bản cũ đến khi verify bản mới); `nguon_chua_dung` là nguồn chưa có trong file kiến thức nào.
3. Soạn lại đúng các file đó, cho user xem phần thay đổi (cũ → mới), rồi `$KB verify`. Bỏ tài liệu: `$KB remove --nguon <file>` và sửa / `$KB remove <file kiến thức>`.

## Bảo trì

- Bot trả lời "chưa có thông tin" nhiều: xem mục Cần xử lý trong Hộp thư hoặc `leads.jsonl` (loại `guard_blocked`) để biết khách hỏi gì, hỏi user bổ sung tài liệu, chạy lại `eval.py`.
- Cập nhật skill: `HPY scripts/setup.py --profile <ten>` rồi restart gateway; `check.py` báo `plugin da cai: Khac ban trong skill` khi quên.

## Xử lý lỗi

- Kênh không bật (log `No messaging platforms enabled` / thiếu `webchat`): thiếu `aiohttp` hoặc thiếu `allowed_origins`; xem `logs/agent.log` của profile.
- Bot không có tool tra tài liệu: thiếu gói `mcp` trong Python của Hermes.
- Hộp thư báo chưa đăng nhập / 401: sai `open_webui.url` (Hermes không gọi được Open WebUI), tài khoản không có vai trò trong `open_webui.roles`, hoặc `open_webui.public_url` khác origin đang mở trang.
- Lỗi nào cũng báo nguyên văn cho user, không nói "đã xong" khi `check.py` còn `fail`.
