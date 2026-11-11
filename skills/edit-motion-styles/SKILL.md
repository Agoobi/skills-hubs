---
name: edit-motion-styles
description: Bộ 7 khối motion dựng sẵn (kinetic type, particles chữ, neo-brutalism CTA, glassmorphism UI, bảng lật split-flap, isometric tăng trưởng, nền gradient mesh) render ra MP4 hoặc lớp trong suốt — dùng làm hook, thẻ CTA, chuyển chương, nền cho các skill edit-* khác. Chữ tiếng Việt, khung 9:16 mặc định, chạy trên Claude.
---

# Edit Motion Styles

Chọn lọc 7 trong 20 mẫu của gói "20 Claude Motion Styles" (khung đã chạy sẵn: `template.html` + renderer chính xác từng khung). Mỗi mẫu đã thử với chữ tiếng Việt. Không sinh motion từ đầu — chỉ đổi tham số, nên kết quả ổn định mọi lần.

**Vai trò:** khối ghép. Thường gọi từ skill dựng chính (`edit-remotion-ai-agent-vn`, `edit-talking-head-v06`, `edit-ads-talking-head-9x16`, `edit-onetake`, `video-factory`, `talking-head-capcut`) để làm hook 2–4 giây, thẻ CTA cuối, chuyển chương hoặc nền. Dùng riêng khi người dùng chỉ cần một clip motion ngắn.

## Bảng mẫu

| Mẫu (`styles/…`) | Hợp cho | `text` / `sub` | Màu |
|---|---|---|---|
| `kinetic-type` | Hook đập từng chữ, câu khẳng định, quote | Các từ cách nhau bằng dấu cách (2–6 từ hay nhất); `sub` dòng nhỏ dưới từ cuối | `bg`, `c1` từ nhấn, `c2` từ xen, `c3` từ cuối |
| `particles` | Hook "phép màu", hiện tên thương hiệu/từ khoá | Từ hình thành; `\|` để xuống dòng; `sub` chú thích giãn chữ | `bg`, `c1`–`c3` |
| `neo-brutalism` | CTA, ưu đãi, SaaS/khởi nghiệp | `text` thẻ tiêu đề; `sub` dòng số liệu (số đầu tiên tự đếm lên) | `bg`, `c1` nút, `c2` thẻ số, `c3` sticker; thêm `--set cta=…`, `--set badge=…` |
| `glassmorphism` | Khoe giao diện app, công nghệ hiện đại | `text` tiêu đề thẻ chính; `sub` dòng phụ | `bg`, `c1`–`c3` (c3 là nhấn) |
| `split-flap` | Thông báo, ra mắt, đếm ngược, tiết lộ | Các dòng cách nhau bằng `\|` (ngắn, ≤ 7 ký tự/dòng); `sub` dòng chân | `bg`, `c1` chữ, `c2` tấm lật, `c3` nhấn; `--set label=…` thay chữ "DEPARTURES" |
| `isometric` | Tăng trưởng, hệ thống, xây dựng, dữ liệu | Chú thích dưới lưới (tuỳ chọn) | `bg`, `c3` trời, `c1` mặt trên, `c2` mặt bên |
| `gradient-mesh` | Nền chuyển động, thẻ quote, nền sau b-roll | Tiêu đề tuỳ chọn (`\|` xuống dòng); `sub` chú thích | `c1`–`c4` lưới màu, `bg` |

Xem `styles/<mẫu>/preview.jpg` trước khi chọn. Hướng dẫn gốc từng mẫu (tiếng Anh: hợp đồng style, chuyển động, thông số) ở `styles/<mẫu>/GOC-SKILL.md` — đọc khi cần chỉnh sâu.

## Cách dùng
```bash
python3 <skill>/scripts/render.py <skill>/styles/kinetic-type/template.html hook.mp4 \
  --text "AI CHỐT ĐƠN THAY BẠN" --dur 3 --set bg=060E22 --set c1=3FD6A6 --set c2=F5F7FA --set c3=091833
python3 <skill>/scripts/render.py <skill>/styles/neo-brutalism/template.html cta.mov --alpha \
  --text "DÙNG THỬ 7 NGÀY" --sub "Nhanh gấp 10 lần" --set "cta=Inbox ngay →" --set badge=MỚI
python3 <skill>/scripts/render.py <skill>/styles/particles/template.html still.png --still 3 --text "AI AGENT|VN"
```
Tham số chung: `--w --h` (mặc định 1080×1920; 1080×1350, 1080×1080, 1920×1080 đều được), `--dur`, `--fps` (30; khớp fps video chính khi ghép), `--text`, `--sub` (`--sub ""` để ẩn — một số mẫu có `sub` mặc định tiếng Anh, **luôn truyền `--sub`**), `--set key=hex`, `--alpha` (`.mov` ProRes 4444 hoặc `.webm` VP9), `--still <giây>`, `--sheet <giây>` (contact sheet), `--audio file`.

## Màu theo thương hiệu
Mặc định mỗi mẫu có bảng màu riêng. Video kênh AI Agent VN: map preset `aiagentvn` vào khoá màu của mẫu — nền `060E22`/`091833`, chữ `F5F7FA`, nhấn `3FD6A6`, phụ `8A6BFF`, cảnh báo `FF6B6B`. Riêng `neo-brutalism` và `isometric` sống nhờ màu sáng tươi: giữ bảng gốc hoặc dùng màu nhận diện của khách, không ép về nền tối. Mỗi khối một màu nhấn chính.

## Quy tắc
- **Chữ:** theo `safe-zone-chu-9x16`. Hook/thumbnail được giữ chữ to theo mẫu nhưng phải nằm trọn ngang trong khung; chữ quá dài thì rút gọn câu, đừng để mẫu tự thu nhỏ quá mức. Sau khi render, xem still để kiểm dấu tiếng Việt (dấu nặng/hỏi đặt đúng chỗ, không bị cắt) — nếu font hệ thống thiếu dấu, đổi `SANS` trong bản sao template sang 'Be Vietnam Pro' bằng @font-face cục bộ.
- **Không sửa template gốc trong skill.** Cần đổi bố cục/chữ cố định thì chép `template.html` sang thư mục dự án rồi sửa bản sao.
- **Ghép vào video chính:** render `--alpha` đúng fps/kích thước rồi overlay bằng ffmpeg, hoặc render MP4 làm cảnh riêng nối vào timeline. Khối hook ≤ 3–4 giây; không dùng quá 2 mẫu khác nhau trong một video ngắn.
- Chỉ dùng chữ/số có thật (lời thoại, ưu đãi thật); không bịa chỉ số như "96% FASTER".

## Kiểm tra
Xem `--sheet 0.5` hoặc 3 still (đầu, giữa, cuối) trước khi render đầy đủ; probe file xuất (thời lượng, fps, kích thước, alpha nếu cần).
