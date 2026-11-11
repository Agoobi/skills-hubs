---
name: edit-tech-tutorial
description: Dựng video hướng dẫn phần mềm / AI workflow / khoá học công nghệ dọc 9:16 hoàn toàn trên Claude bằng HyperFrames — hook nền sáng chữ cam nghiêng, đoạn hướng dẫn nền tối với screen recording lớn, zoom tới đúng nút, vòng sáng click, phụ đề trắng từ khoá vàng — từ voice/kịch bản/screen recording. Style "editviral".
---

# Edit Tech Tutorial

Bản chạy hoàn toàn trên Claude của `tech-educational-motion-editor` (style editviral đã học, bản v1.4 người dùng duyệt 27/10/2026). Không dùng Premiere/After Effects: dựng bằng **HyperFrames** (HTML + GSAP → MP4), chép lời bằng sherpa-onnx, trộn âm bằng HyperFrames/ffmpeg. Bàn giao MP4 + thư mục nguồn HyperFrames dựng lại được.

Thứ tự ưu tiên: **CÂU CHUYỆN > RÕ RÀNG > CHẤT LƯỢNG CHUYỂN ĐỘNG > SỐ LƯỢNG HIỆU ỨNG.**

**Dùng cho:** hướng dẫn phần mềm, AI workflow (ChatGPT, Claude, Codex, n8n…), bài trong khoá học (vd. 30 khoá AI cho CV), talking head + screen recording.
**Không dùng cho:** quảng cáo talking head cần cắt lỗi nói (`edit-ads-talking-head-9x16`), launch clip sản phẩm (`edit-onetake`), video giải thích nền tối AI Agent VN từ kịch bản (`edit-remotion-ai-agent-vn`).

## Tài liệu
- [style-guide](references/style-guide.md) — hai chế độ sáng/tối, màu, chữ, primitive chuyển động. Đọc trước khi dựng.
- [motion-and-sound](references/motion-and-sound.md) — hợp đồng IN/HOLD/OUT từng beat, đa dạng hình, screen thật, SFX. Đọc khi lập beat sheet.
- [qc-checklist](references/qc-checklist.md) — chạy trước mỗi lần gửi bản xem.
- [reference-analysis](references/reference-analysis.md) — phân tích 7 video mẫu (bằng chứng cho style; tham khảo khi cần).
- `references/library/` — chỉ mục thư viện nền (`BG_INDEX.csv`, ảnh `BG_CONTACT_*.jpg`) và SFX (`SFX_INDEX.csv`, 560 file Boom Casual UI) **nằm trên máy người dùng** ở `E:/TaiNguyen/...`.
- Sau khi cài HyperFrames: cú pháp chuẩn của đúng phiên bản ở `node_modules/hyperframes/dist/skills/hyperframes/SKILL.md` và `.../references/format.md`.

## Quy trình

### 1. Nhận việc
Brief, voice/kịch bản, screen recording, tỉ lệ (mặc định 1080×1920), mục tiêu, CTA, thương hiệu. Hỏi chỉ phần thiếu ảnh hưởng kết quả. File trên máy người dùng: công cụ liên kết máy tính (`get_device_info` → xin quyền đúng thư mục → `device_stage_files` chỉ file cần dùng); chưa liên kết thì xin gửi kèm. Probe từng file: thời lượng, fps, kích thước, cờ xoay, SAR/DAR, audio; VFR thì chuẩn hoá fps.

### 2. Chép lời và beat sheet
```bash
pip install --break-system-packages -q sherpa-onnx numpy
python3 <skill>/scripts/transcribe_vi.py voice.wav transcript.json     # mốc từng từ, model zipformer-vi tải từ GitHub
```
Chỉ có kịch bản: timing là dự kiến, ghi rõ; bản thu VO quyết định căn chỉnh cuối. Đối chiếu chính tả với kịch bản.
Chia câu theo thông tin/nhân quả; mỗi beat ghi đủ hợp đồng trong [motion-and-sound](references/motion-and-sound.md) vào `beats.json`. Mỗi câu chọn cách thể hiện:

| Ý nghĩa | Cách thể hiện |
|---|---|
| Thao tác phần mềm | Screen thật, giữ ngữ cảnh → zoom tới mục tiêu → thấy click → giữ phản hồi |
| So sánh | Hai thẻ cùng cỡ, nhãn rõ, cùng tiêu chí, đủ thời gian đọc |
| Khái niệm | Icon/hình đơn giản, mỗi lần một quan hệ |
| Số liệu | Số lớn + nhãn/đơn vị + nguồn (`edit-infographic`); không bịa |
| Kể chuyện | Talking head/b-roll liên hệ nhân quả với lời |
| Cần tập trung | Giảm chuyển động nền, giữ hình, bỏ SFX thừa |

Chuỗi thao tác chuẩn: **thấy ngữ cảnh → nhận ra mục tiêu → thấy click/chọn → thấy phản hồi → sang bước.** Bỏ thời gian chờ thật bằng cut có liên tục; không giả kết quả đã có.

### 3. Tài sản
- Screen recording thật của người dùng là ưu tiên số một. Trang web công khai có thể tự quay bằng Playwright. Không có thì dựng UI bằng HTML trong composition, ghi "giao diện mô phỏng" (starter có nhãn `#tag`).
- Nền: tra `library/BG_INDEX.csv` + contact sheet, lấy đúng file video (không phải WEBP preview) qua công cụ liên kết máy tính. Không có thì nền dựng bằng CSS như starter (lưới sáng / chấm tối).
- SFX: tra `library/SFX_INDEX.csv` theo `categories`/`description`, stage đúng file, tách take theo [motion-and-sound](references/motion-and-sound.md).
- Thiếu b-roll: tìm Pexels/Pixabay, ghi link + license; mạng chặn tải thì đưa link cụ thể cho người dùng tải.
- Mọi asset vào `assets/MANIFEST.csv`: id, beat, đường dẫn, nguồn, license, in/out, thật/mô phỏng.

### 4. Dựng bằng HyperFrames
```bash
cp -r <skill>/assets/starter ./film && cd film
npm install --save-exact -s hyperframes@0.8.201 gsap@3.15.0
```
Starter (đã render thử trên Claude, 11 s, "Check passed"):
- `compositions/hook-light.html` — hook nền sáng, keyword cam nghiêng, khung 0 đã có tiêu đề (thumbnail).
- `compositions/step-dark.html` — bước hướng dẫn nền tối: khung screen 16:9 rộng 940 px, camera `camTo(zoom, x, y)` đưa mục tiêu vào giữa và **tự kẹp không lộ mép video**, con trỏ, vòng sáng click, phụ đề trắng + từ khoá vàng, lùi camera để thấy phản hồi.
- `assets/screen.mp4` là giao diện mẫu — thay bằng screen thật; toạ độ mục tiêu tính theo nguồn × (940/chiều rộng nguồn).
Nhân bản `step-dark.html` cho từng bước (mỗi composition một ID riêng), thêm/bớt scene trong `index.html` theo beat sheet, thêm VO bằng `<audio id="vo" … data-start="0">`. Mỗi phần tử có IN/HOLD/OUT; `fromTo` có thời điểm tường minh; tween bắt đầu muộn mà đặt giá trị đầu khác trạng thái hiện tại thì thêm `immediateRender:false`. Font cục bộ khai báo @font-face **trong từng composition**.

Thứ tự dựng: rough cut theo ý và audio → crop/zoom/con trỏ → đồ hoạ → chữ → polish chuyển động → SFX/nhạc. Phụ đề karaoke nguyên văn (nếu cần) dùng `edit-caption-karaoke` làm lớp trong suốt rồi đặt `<video muted>` lên trên, hoặc ghép bằng ffmpeg sau.

### 5. Kiểm tra và render
```bash
cd /đường/dẫn/tuyệt/đối/film && export HYPERFRAMES_BROWSER_PATH=/usr/bin/google-chrome && npx hyperframes check .
cd /đường/dẫn/tuyệt/đối/film && export HYPERFRAMES_BROWSER_PATH=/usr/bin/google-chrome && npx hyperframes render . -o renders/film.mp4 --fps 30 --workers 1
```
**Biến môi trường phải đặt trong cùng lệnh** (mỗi lệnh shell mới không giữ `export`); thiếu nó render sẽ báo lỗi Chrome và **không ghi file mới** — luôn kiểm thời gian sửa đổi của file xuất. Render dài chạy bằng tác vụ nền. `check` phải "Check passed": sửa lỗi tương phản (cam nhạt trên nền sáng), `line_unread` (chữ giữ chưa đủ lâu), `first_frame_empty`. Overflow của camera zoom là có chủ đích: đánh dấu `data-layout-allow-overflow` trên wrapper camera.
Trích khung từ MP4 (đầu/giữa/cuối mỗi beat, sát mỗi click) và xem thật; chạy [qc-checklist](references/qc-checklist.md).

### 6. Bàn giao
MP4, thư mục `film/` (composition, assets, `package-lock.json`), `beats.json`, `assets/MANIFEST.csv`, ghi chú: phần nào là mô phỏng, SFX nào chưa nghe duyệt, kiểm tra nào chưa chạy. Phản hồi của người dùng: chỉ cập nhật quy tắc chung của skill khi phản hồi áp dụng rộng; đặc thù một shot giữ trong dự án. Ví dụ: "zoom chóng mặt" → giảm tần suất/biên độ và thêm giữ; "chữ che nút" → sửa bố cục; "âm dày" → đổi quy tắc chọn cue.
