---
name: edit-caption-karaoke
description: Phụ đề nhảy theo từng từ (karaoke, kiểu TikTok/Hormozi) cho video dọc 9:16 tiếng Việt: chép lời có mốc từng từ, từ đang nói đổi màu/nền, pop theo nhịp, nằm trong safe zone; xuất MP4 đã cháy chữ, lớp phụ đề trong suốt và file SRT. Chạy hoàn toàn trên Claude.
---

# Edit Caption Karaoke

Ghép từ hướng dẫn `caption-animation` của iart.ai (MIT) với template canvas tự dựng cho tiếng Việt. Dùng riêng, hoặc làm bước phụ đề cho các skill edit khác (`edit-talking-head-broll`, `edit-talking-head-v06`, `edit-ads-talking-head-9x16`, `video-factory`) khi người dùng muốn phụ đề kiểu karaoke.

## Hai quy tắc bắt buộc
1. **Mốc theo từng từ, không chia đều câu.** Lấy mốc từ ASR; không bao giờ chia thời gian một câu đều cho các từ — lệch là thấy ngay.
2. **Đọc được trước, đẹp sau.** Xem trên điện thoại, ngoài nắng, tắt tiếng: chữ đậm, viền + bóng, tương phản cao.

## Quy trình
`<skill>` là thư mục chứa file này. Template cần thư mục `fonts/` nằm cạnh thư mục `templates/` (giữ nguyên cấu trúc skill, không chép riêng template).

1. **Chép lời có mốc từng từ**
   ```bash
   pip install --break-system-packages -q sherpa-onnx numpy
   python3 <skill>/scripts/transcribe_vi.py video.mp4 transcript.json
   ```
   Model zipformer-vi tự tải từ GitHub releases lần đầu. Đã có `transcript.json` (từ skill edit khác) thì dùng luôn. Có kịch bản thì **sửa chính tả trong `words[].text`** (dấu, tên riêng, tiếng Anh, số), giữ nguyên `start/end`. Ghi các chữ chưa chắc vào ghi chú khi giao.

2. **Viết `cap.json`**
   ```json
   { "words": [ {"text":"Chủ","start":0.20,"end":0.40}, ... ],
     "style": { "preset": "pop", "size": 58, "y": 1380, "maxWords": 3, "upper": true,
                "text": "#F5F7FA", "accent": "#3FD6A6", "boxText": "#06121F", "stroke": "#060E22",
                "emphasis": ["miễn phí"], "warn": "#FF6B6B" } }
   ```
   - `preset`: `pop` (từng từ nảy vào, từ đang nói đổi màu nhấn) · `box` (cả cụm hiện, từ đang nói nằm trong ô màu nhấn) · `underline` (gạch chân chạy dưới từ đang nói).
   - Trang 1–3 từ (`maxWords`); sang trang mới khi nghỉ ≥ `gap` (0,45 s) hoặc gặp dấu câu.
   - `emphasis`: từ khoá tô màu `warn` — dùng tiết kiệm, chỉ từ thật sự quan trọng/cảnh báo.
   - Màu mặc định theo preset `aiagentvn`; dự án có `palette.json` thì lấy `text/accent/warn` từ đó.

3. **Xem trước**
   ```bash
   python3 <skill>/scripts/render.py <skill>/templates/caption.html sheet.jpg --data cap.json --video video.mp4 --sheet 0.5
   ```
   Xem thật contact sheet: từ được tô ở mỗi khung có đúng từ đang nói không, dấu tiếng Việt không bị viền nuốt, không tràn ngang.

4. **Xuất**
   ```bash
   python3 <skill>/scripts/render.py <skill>/templates/caption.html final.mp4 --data cap.json --video video.mp4   # cháy chữ, giữ tiếng gốc
   python3 <skill>/scripts/render.py <skill>/templates/caption.html captions.mov --data cap.json --alpha --dur <giây>  # lớp trong suốt
   ```
   Kèm file SRT từ cùng các từ (gom theo trang) cho YouTube/Facebook:
   ```python
   import json; w=json.load(open('cap.json'))['words']
   def ts(x): ms=int(round(x*1000)); return f"{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d},{ms%1000:03d}"
   pages=[w[i:i+3] for i in range(0,len(w),3)]
   open('captions.srt','w').write('\n'.join(f"{i+1}\n{ts(p[0]['start'])} --> {ts(p[-1]['end'])}\n{' '.join(x['text'] for x in p)}\n" for i,p in enumerate(pages)))
   ```

## Vị trí và cỡ chữ (theo `safe-zone-chu-9x16`)
- Cỡ 54–60 px trên khung 1080×1920, một dòng, 1–3 từ, khung rộng ≤ 800 px.
- Tâm dòng chữ y ≈ 1300–1450 (không xuống dưới 1500). Khi skill dựng chính đã có thẻ/overlay ở vùng đó thì đẩy phụ đề lên (`style.y`) hoặc tắt phụ đề trong đoạn có thẻ chữ lớn.
- Không đặt phụ đề lên mặt người nói; kiểm khung có mặt ở vùng dưới (người ngồi thấp) và đổi `y` nếu cần.

## Kiểm tra trước khi giao
1. Contact sheet và 3 still (đầu, giữa, cuối) đã xem thật.
2. Từ tô màu khớp lời ở các khung kiểm; không có trang trống giữa câu liền mạch.
3. Chính tả đã đối chiếu kịch bản; chữ ASR không chắc đã báo.
4. Probe file xuất: thời lượng, fps, có audio.
Giao: `final.mp4` (hoặc lớp `.mov`), `captions.srt`, `cap.json`.
