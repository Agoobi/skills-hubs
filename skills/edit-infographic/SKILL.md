---
name: edit-infographic
description: Dựng cảnh infographic động 9:16 từ JSON — số lớn đếm lên, biểu đồ cột so sánh, quy trình từng bước, thẻ Trước/Sau — giá trị chốt đúng lúc lời nói nhắc tới; dùng làm cảnh phủ (cover) hoặc lớp trong suốt cho các skill edit khác. Chạy hoàn toàn trên Claude.
---

# Edit Infographic

Gộp cách làm của `animated-infographic` và `chart-animation` (iart.ai, MIT) thành một template canvas tiếng Việt, theo preset `aiagentvn`. Dùng khi một câu thoại có **số liệu, so sánh, quy trình** — thứ "nên cho xem hơn là nói".

## Nguyên tắc
1. **Không bịa số.** Mọi con số lấy từ lời thoại, tài liệu người dùng đưa hoặc nguồn đã kiểm. Có nguồn thì ghi `source`. Dữ liệu mẫu trong template ghi "VÍ DỤ" — không bao giờ giao bản còn chữ đó.
2. **Cấu trúc vào trước, giá trị chốt đúng lời.** Khung/cột/thẻ vào sớm; con số đọc được đúng lúc người nói nói ra (`at`). Không lộ đáp án trước câu tiết lộ.
3. **Một ý mỗi cảnh**, 3–8 giây, giữ đủ lâu để đọc. Biểu đồ cột tối đa ~5 hàng; nhiều hơn thì tách cảnh.
4. **Tỉ lệ thật.** Cột tỉ lệ đúng giá trị. Chênh lệch quá lớn khiến cột nhỏ gần như mất thì dùng `display` (vd "< 1") và nói rõ trong nhãn, không bóp méo trục.

## Các loại cảnh (`scenes[]`)
Mọi cảnh có `type`, `from`, `to` (giây). Mốc lấy từ `transcript.json` của video (khoảng nghỉ giữa hai từ).

| type | Trường | Hiện gì |
|---|---|---|
| `stat` | `value, decimals, prefix, suffix, label, source, at, size` | Số lớn đếm lên, chốt tại `at`, có glow |
| `bars` | `title, unit, decimals, at, items:[{label, value, highlight, display}]` | Cột ngang so sánh; khung vào sớm, cột chạy tới giá trị tại `at` |
| `steps` | `title, items:[{text, at}]` | Danh sách bước, mỗi bước sáng lên đúng lúc được nói, đường nối chạy theo |
| `compare` | `title, at, left:{title, lines[]}, right:{title, lines[]}, height` | Hai thẻ Trước (✕, đỏ) / Sau (✓, xanh), thẻ Sau sáng viền tại `at` |

Ví dụ `info.json`:
```json
{ "scenes": [
  { "type": "stat", "from": 0, "to": 3.2, "at": 1.2, "value": 3, "suffix": " giờ", "label": "mỗi ngày chủ shop trả lời tin nhắn", "source": "Khảo sát của khách, 10/2026" },
  { "type": "bars", "from": 3.2, "to": 7.4, "at": 4.6, "title": "Thời gian phản hồi", "unit": " phút",
    "items": [ {"label": "Nhân viên", "value": 18}, {"label": "Chatbot AI", "value": 0.2, "highlight": true, "display": "< 1"} ] }
 ],
 "palette": { "accent": "#3FD6A6" } }
```
`palette` ghi đè khoá màu (`bg_top, bg_bottom, glow1, glow2, text, muted, accent, accent2, warn, card, cardBorder, onAccent`). `region` đổi vùng đặt nội dung (mặc định theo safe zone: top 300, bottom 1480, left 80, right 960).

## Quy trình
`<skill>` là thư mục chứa file này (giữ `templates/` cạnh `fonts/`).
1. Đọc lời thoại/kịch bản, chọn câu đáng thành cảnh, ghi `info.json` với mốc thật.
2. Xem trước: `python3 <skill>/scripts/render.py <skill>/templates/infographic.html sheet.jpg --data info.json --sheet 0.5 --cues cues.json` → xem thật từng khung; `--still <giây>` để xem cỡ thật.
3. Xuất:
   - Cảnh đứng riêng: `render.py ... info.mp4 --data info.json [--audio voice.wav]`
   - Lớp chèn vào video khác: `render.py ... info.mov --data info.json --alpha` (nền tắt; nên bật nền khi dùng làm cover).
   - Phủ thẳng lên video có tiếng: `render.py ... out.mp4 --data info.json --video talk.mp4` (cảnh chỉ hiện trong `from–to`, ngoài đó thấy video).
4. `cues.json` cho mốc SFX: `whoosh` khi cảnh vào, `hit` khi giá trị chốt, `tick` mỗi bước.

## Mở rộng
Cần loại cảnh khác (đường tăng trưởng, bản đồ, bar chart race, timeline): thêm một hàm vào object `draw` trong bản sao template của dự án, cùng hợp đồng `(s, t, e)`, giữ nguyên quy tắc "cấu trúc trước, giá trị đúng lời". Không sửa template gốc trong skill.

## Kiểm tra trước khi giao
- Không còn chữ "VÍ DỤ"; mọi số có nguồn hoặc là lời người nói.
- Số chốt khớp mốc lời (kiểm still tại `at` và `at − 0,3 s`).
- Chữ ≥ 28 px, không vượt x 960 / y 1500, dấu tiếng Việt rõ.
- Probe file xuất.
