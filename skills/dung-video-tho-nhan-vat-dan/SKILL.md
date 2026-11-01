---
name: dung-video-tho-nhan-vat-dan
description: Dựng video thô, chèn nhân vật dẫn giải thích.
version: 0.1.0
author: Agoobi
license: MIT
metadata:
  hermes:
    category: coquifly
    tags: [video, edit, screen-recording, presenter, hyperframes, vietnamese]
---

# dung-video-tho-nhan-vat-dan

Biến một video quay thô (quay màn hình hoặc quay máy) thành video hoàn chỉnh có **nhân vật hoạt hình dẫn chuyện**. Người dùng chỉ cần quay và đưa file. Agent đọc video, chọn chỗ cắt, chỗ tua nhanh, chỗ **dừng hình để nhân vật vào giải thích**, chỗ zoom, chỗ chèn ảnh minh hoạ, rồi lồng giọng và dựng bằng HyperFrames.

Dùng skill này khi người dùng nói "tôi quay raw rồi bạn edit", "chèn nhân vật vào thuyết trình", "dừng lại giải thích", "chèn giọng và minh hoạ vào video quay màn hình", hoặc đưa một file quay thô và muốn thành video đăng được.

Không dùng cho video chưa quay gì (dùng `lam-video-kieu-metics-media`).

## Quy tắc không được phá

1. **Mỗi cổng dừng lại chờ duyệt**, trừ khi người dùng nói rõ "autopilot". Autopilot thì tự quyết và ghi lý do vào `decisions.md`; các quy tắc 2–6 giữ nguyên.
2. **Hình thật là chính, nhân vật là phụ.** Không dựng giả màn hình sản phẩm. Thiếu cảnh thì nhờ người dùng quay thêm, hoặc đổi lời để không cần cảnh đó.
3. **Không bịa.** Số liệu, tên nút, kết quả phải thấy trong video thô hoặc do người dùng đưa. Câu hook "tiết kiệm 2 giờ" chỉ được dùng khi có số đo thật.
4. **Không để lộ thông tin riêng tư.** Trước khi dựng, rà khung hình tìm email, số điện thoại, tên khách, số dư, API key, tab cá nhân. Che bằng `blur` trong `plan.json`, không che bằng hình dán. Không chắc thì hỏi.
5. **Không có logic ẩn.** Tua nhanh thì hiện nhãn "Tua nhanh x…". Dừng hình thì hiện nhãn "Tạm dừng". Mọi đoạn đổi tốc độ hoặc giữ khung nằm trong `decisions.md`.
6. **Không in API key ra chat, không tự đăng video.** Skill kết thúc ở file mp4.

## Cài đặt (một lần)

Chạy từ thư mục skill. Riêng `transcribe` chạy bằng `python`, các lệnh khác dùng `python -I`.

1. Copy `settings.example.json` thành `settings.json` (đã `.gitignore`). Điền `voice` và key tương ứng. Giọng `vieneu:<voiceId>` dùng VieNeu, tên giọng khác dùng OpenRouter. Biến môi trường `VIENEU_API_KEY`, `OPENROUTER_API_KEY` được ưu tiên.
2. Máy cần `ffmpeg`, `ffprobe`, `node`, `npm`. Video có lời thì cài thêm `pip install faster-whisper`.
3. Chạy `python -I scripts/raw.py check`, sửa hết mục trong `problems`. Thiếu `voice` vẫn làm được nếu người dùng tự thu giọng (`voFile`).

`settings.json > presenter` là ngoại hình nhân vật, `theme` là màu kênh. Xem `references/nhan-vat.md`.

## Quy trình (các cổng)

**Cổng 1 — Nhận video.**
Hỏi gọn trong một lượt: file thô ở đâu; video cho ai xem, xem xong họ phải làm gì; ngang hay dọc; lời trong video giữ nguyên hay đọc lại bằng giọng AI; có câu kêu gọi nào cuối video. Rồi tạo dự án:

```bash
python -I scripts/raw.py init "<tên video>" --raw "<file thô>" [--format 16:9|9:16]
cd tmp/<ten-video> && npm i
```

Mặc định định dạng theo chiều của video thô.

**Cổng 2 — Xem hết video.**

```bash
python -I scripts/raw.py analyze <ten-video>
python scripts/raw.py transcribe <ten-video>   # chỉ khi video có lời
```

`analysis/` có `analysis.json` (khoảng im lặng, đoạn màn hình đứng yên, chỗ đổi cảnh), `sheet-*.jpg` (ảnh tổng hợp có mốc thời gian), `transcript.json`. Mở từng sheet ra xem thật, không đoán từ số liệu. Cần đọc chữ trên màn hình hoặc đo vùng thì lấy khung đủ nét: `python -I scripts/raw.py frame <ten-video> <giây>`. Báo lại cho người dùng: video đang kể chuyện gì, đoạn nào bỏ được, đoạn nào đáng giữ, thông tin riêng tư nào đã thấy.

**Cổng 3 — Bản dựng trên giấy.**
Đọc `references/ke-hoach.md`, viết `plan.json`: từng nhịp là đoạn nào, dừng ở đâu, nhân vật nói gì, zoom và ảnh minh hoạ nào. Trình bày dạng bảng: nhịp, loại, thời lượng ước tính, hình, lời đọc nguyên văn. Lặp tới khi người dùng nói ổn. Từ đây không đổi lời mà không hỏi.

**Cổng 4 — Tài sản phụ.**
Ảnh minh hoạ đặt vào `assets/overlays/`. Ảnh chụp hoặc số liệu thật thì lấy từ người dùng; sơ đồ thì tự dựng thành ảnh. Nhân vật không cần tài sản, ráp sẵn lúc build. Gửi bảng: file, dùng ở nhịp nào, nguồn. Chưa có đủ thì không sang cổng sau.

**Cổng 5 — Giọng đọc.**

```bash
python -I scripts/raw.py tts <ten-video> --dry   # xem số ký tự sẽ tính phí
python -I scripts/raw.py tts <ten-video>
```

Lệnh chỉ đọc lại câu đã đổi, nên sửa một câu không tốn cả video. Cho người dùng nghe vài câu. Sai dấu hay đọc sai số thì sửa cách viết trong `vo` rồi chạy lại. Người dùng tự thu thì đặt file vào dự án và điền `voFile`, không cần `tts`. Cần giọng tạm để duyệt hình mà chưa muốn tốn phí thì tạo bằng gói pip `vieneu` chạy trên máy rồi cũng điền `voFile`.

**Cổng 6 — Dựng và xem trước.**

```bash
python -I scripts/raw.py cut <ten-video>
cd tmp/<ten-video>
node ../../scripts/build.mjs
npm run check
npm run preview
```

`cut` chỉ làm lại nhịp đã đổi và ghi `decisions.md`. Sửa hết lỗi của `check`; cảnh báo `line_unread` về phụ đề thì do tốc độ đọc, chỉ sửa khi câu thật sự chớp qua. Tự xem trước: trích khung ở từng nhịp dừng, zoom, ảnh phụ. Xem nhân vật có che nội dung không, khung chỉ có đúng vùng không, vùng che có đủ không. Gửi người dùng bản xem trước hoặc bản nháp `npx --yes hyperframes@0.8.226 render --quality draft --output draft.mp4`. Sửa theo góp ý, lặp lại `cut` và `build.mjs`.

**Cổng 7 — Xuất file.**

```bash
npx --yes hyperframes@0.8.226 render --quality delivery --output final.mp4
```

Kiểm tra `ffprobe` (độ dài, có tiếng), nghe một đoạn, xem khung đầu và khung cuối. Gửi đường dẫn file kèm tiêu đề và mô tả gợi ý.

## Thư mục video

`tmp/<ten-video>/` trong thư mục skill: `project.json`, `plan.json`, `timeline.json`, `decisions.md`, `analysis/`, `audio/`, `assets/`, `compositions/`, `index.html`. File thô không bị chép hay sửa. Không sửa tay `index.html` hay `compositions/`, vì `build.mjs` ghi đè; sửa ở `plan.json`.

## Khi có lỗi

- `render` báo Chrome không khởi động hoặc `icu_util`: chạy `npx --yes hyperframes@0.8.226 browser ensure --force`.
- Video dài hoặc nét cao: `analyze` chạy khoảng hai phần ba thời lượng video (file 3K 60 fps), `render` khoảng gấp đôi thời lượng thành phẩm. Chạy nền, đừng hiểu là treo.
- `transcribe` không cài được trên Python 3.14: dùng Python 3.11–3.13.
- `cut` báo chưa có giọng đọc: chạy `tts`, hoặc điền `voFile`.
- `build.mjs` báo lệch `timeline.json`: chạy lại `cut`.
- Video thô ngang xuất dọc: hình nhỏ, chữ khó đọc. Thêm zoom ở mọi chỗ cần đọc, hoặc nhờ người dùng quay lại với cửa sổ nhỏ hơn.
