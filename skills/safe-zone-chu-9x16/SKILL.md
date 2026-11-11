---
name: safe-zone-chu-9x16
description: "Quy tắc cỡ chữ và vùng an toàn (safe zone) cho mọi video dọc 9:16 (Reels, TikTok, Shorts): dùng kèm mọi skill edit-* khi đặt phụ đề, tiêu đề, thẻ chữ, CTA."
---

# Cỡ chữ và safe zone cho video 9:16

Áp dụng cho MỌI skill dựng video dọc (edit-remotion-ai-agent-vn, edit-ads-talking-head-9x16, edit-talking-head-v06, edit-gym-broll-9x16, edit-spa-text, edit-before-after-9x16, edit-ahmad-ali, edit-onetake, talking-head-capcut, video-factory…). Người dùng đã duyệt sau khi so với video mẫu (kênh Javis) ở KB 06–07: chữ cũ quá to, cấn vùng giao diện của app.

## Nguyên tắc ưu tiên
1. **Giữ nguyên style của skill đang dùng** (màu, font, bố cục, chuyển động). Skill này chỉ quy định cỡ chữ và vùng đặt chữ.
2. Nếu skill riêng ghi cỡ chữ lớn hơn bảng dưới đây vì đó là đặc trưng của style (vd từ khoá khổng lồ của edit-ahmad-ali, tiêu đề 136 px của edit-spa-text): giữ đặc trưng đó, nhưng vẫn phải nằm trọn trong safe zone; dài quá thì thu nhỏ cho vừa thay vì tràn.
3. Mọi thứ khác (phụ đề thường, chữ trong thẻ, nhãn, CTA) theo bảng cỡ chữ bên dưới.
4. Khi người dùng chỉ yêu cầu chỉnh cỡ chữ: chỉ đổi cỡ chữ (và bề rộng khung phụ đề nếu cần để tránh cột nút), không đổi gì khác.
5. **Ngoại lệ khung hook/thumbnail:** khung tiêu đề mở đầu (người dùng chụp làm thumbnail) giữ chữ lớn theo skill riêng (vd edit-remotion-ai-agent-vn: 118 px, 3–4 dòng), không thu theo bảng dưới; chỉ cần không tràn ngang. Chữ to nhiều dòng tiếng Việt luôn giãn dòng ≥ 1.2 để dấu dòng dưới không dính dòng trên.

## Safe zone (khung 1080×1920)
- **Trên:** chừa 220 px (thanh tiêu đề, nút của app). Chỉ chip nhỏ/logo nhỏ được nằm sát vùng này.
- **Dưới:** chừa 420 px (tên kênh, caption, thanh nhạc). Chữ quan trọng giữ trên y ≈ 1500. Watermark nhỏ ở đáy chấp nhận được (không quan trọng nếu bị che).
- **Phải:** chừa ~120 px (cột nút tim/bình luận/chia sẻ, khoảng y 900–1600). Chữ không vượt x ≈ 960.
- **Trái:** chừa ≥ 60 px.
- Vùng chữ an toàn: x 60–960, y 220–1500. Phụ đề đặt giữa theo chiều ngang trong khung rộng ≤ 800 px (x 140–940).

## Bảng cỡ chữ (1080×1920)

| Thành phần | Cỡ | Ghi chú |
|---|---|---|
| Phụ đề chạy theo lời | 54–60 px | 1 dòng, 1–3 từ; viền/bóng mỏng theo tỉ lệ (~9 px khi dùng stroke) |
| Tiêu đề mở đầu / hook | 72–90 px | ≤ 3 dòng ngắn; khung hook dùng làm thumbnail theo skill riêng (xem nguyên tắc 5) |
| Tiêu đề cảnh | 40–64 px | |
| Chữ trong thẻ, dòng danh sách | 30–40 px | |
| Nhãn, chữ phụ | 28–34 px | |
| Số lớn / con số nhấn | 110–160 px | |
| Nút CTA | 48–64 px | |
| Dòng nguồn, chip, watermark | 28 px | tối thiểu, dưới 28 px khó đọc trên điện thoại |

Số đo từ video mẫu: phụ đề chữ ~56 px một dòng 1–3 từ; tiêu đề ~62 px; chữ trong thẻ 26–40 px; số nhấn ~70–120 px; nội dung cách mép trái/phải ~44 px. Video mẫu đặt phụ đề ở y ≈ 1660; kênh này giữ phụ đề cao hơn (trong vùng y ≤ 1500) trừ khi skill riêng quy định khác.

## Cách áp dụng nhanh
- Dựng bằng HTML/CSS (HyperFrames): sau khi có CSS/HTML, chạy một lượt nhân mọi `font-size` với hệ số (≈ 0,72 nếu bản gốc theo cỡ cũ của kênh), tối thiểu 28 px, TRỪ khung hook/thumbnail; rồi ghi đè riêng cỡ phụ đề và bề rộng khung phụ đề.
- Dựng bằng Pillow/ffmpeg (drawtext, ASS): đặt thẳng cỡ theo bảng; ASS dùng PlayResX=1080, PlayResY=1920 để cỡ chữ tính theo pixel khung; MarginR ≥ 140, MarginL ≥ 140 cho phụ đề.
- Cụm từ không ngắt giữa chừng (bọc trong một khối); phụ đề vượt 800 px thì tách cụm ngắn hơn chứ không xuống 2 dòng.

## Kiểm tra trước khi giao
1. Chụp 5–8 khung (hook, giữa mỗi phần, CTA), xem thật: không chữ nào vượt x 960 hay xuống dưới y 1500 (trừ watermark và khung hook), phụ đề một dòng, không chữ nào dưới 28 px, dấu tiếng Việt không dính dòng trên.
2. Nếu có thể, đặt thử lớp phủ mô phỏng giao diện Reels/TikTok (ô trên 220 px, ô dưới 420 px, cột phải 120 px từ y 900–1600) lên một khung để nhìn chữ có bị che không.
3. Báo người dùng chỗ nào phải giữ chữ lớn vì style đặc trưng.