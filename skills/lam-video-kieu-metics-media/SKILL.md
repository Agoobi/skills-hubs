---
name: lam-video-kieu-metics-media
description: Làm video hướng dẫn kiểu Metics Media, ngắn hoặc dài.
version: 0.4.0
author: Agoobi
license: MIT
metadata:
  hermes:
    category: coquifly
    tags: [video, tutorial, tiktok, youtube, hyperframes, vietnamese]
---

# lam-video-kieu-metics-media

Làm video hướng dẫn không lộ mặt theo ngôn ngữ hình ảnh của Metics Media: mở bằng kết quả thật, đồ hoạ giải thích sạch, thẻ chương, quay màn hình thật có zoom. Hỗ trợ **video ngắn** (dọc, 25–60 giây) và **video dài** (ngang, 3–25 phút), **nhiều kênh** với giọng và người xem riêng. Giọng đọc và ảnh bìa tạo qua OpenRouter. Dựng và xuất bằng HyperFrames.

Dùng skill này khi người dùng muốn làm video hướng dẫn, video mẹo, video "mổ lỗi", tutorial công cụ, hoặc nói "làm video kiểu Metics Media", "làm short/TikTok hướng dẫn", "làm video dài cho YouTube" cho một kênh đã cấu hình.

## Nguồn phong cách

Skill này **phỏng theo phong cách dựng của kênh YouTube Metics Media** (https://www.youtube.com/@MeticsMedia). Bố cục video, nhịp cắt, kiểu đồ hoạ giải thích, thẻ chương và cách quay màn hình được rút ra từ việc xem khung hình của hai video trên kênh đó vào tháng 10/2026:

- "How to Build $10K Websites in Minutes (Claude AI)"
- "Hermes Agent - Full Tutorial & Setup Guide (For Beginners)"

Chi tiết quan sát và số đo nằm trong `references/phan-tich-phong-cach.md`. Skill chỉ học **cách làm**; nó không dùng lại hình ảnh, logo, giọng, nhạc hay lời thoại của Metics Media, và không có liên kết hay bảo trợ nào từ kênh đó. Phần video ngắn là bản chuyển thể, vì kênh gốc không làm Shorts.

## Quy tắc không được phá

1. **Mỗi cổng dừng lại chờ người dùng duyệt.** Không gộp cổng, không tự đi tiếp. Người dùng muốn kiểm soát chất lượng ở từng bước; đi tiếp khi chưa duyệt là làm lại từ đầu.
2. **Không tự vẽ logo, không dựng giả màn hình sản phẩm.** Logo là file tải từ nguồn chính thức. Màn hình là ảnh hoặc video quay thật bằng trình duyệt. Thiếu thì hỏi người dùng, hoặc viết lại lời để không cần cảnh đó. Chi tiết: `references/tai-san-that.md`.
3. **Không bịa.** Bước thao tác, giá, tên nút, kết quả phải có trong `research.md` kèm nguồn.
4. **Không in API key ra chat.** Không gõ mật khẩu, không vượt CAPTCHA; người dùng tự đăng nhập.
5. **Không đăng video.** Skill kết thúc ở file mp4 và phần mô tả. Người dùng tự đăng.

## Cài đặt (một lần)

Lệnh Python chạy từ thư mục skill: `python -I scripts/video.py <lệnh>` (chỉ cần Python 3).

1. Copy `settings.example.json` thành `settings.json` (đã `.gitignore`). Điền `openrouter.api_key`, hoặc đặt biến `OPENROUTER_API_KEY`.
2. Khai báo kênh trong `channels` (xem dưới và `references/settings-schema.md`).
3. Máy cần có `node`, `ffmpeg`, `ffprobe`, và gói `playwright` (`npm i -D playwright && npx playwright install chromium` trong thư mục dự án video).
4. Chạy `python -I scripts/video.py check --online`. Sửa hết mục trong `problems` trước khi làm video.

### Nhiều kênh

`settings.json > channels` là map `alias -> cấu hình`, giống `pages` của skill viết bài fanpage. Mỗi alias là một kênh với giọng đọc (`voice`, `voice_style`), cách xưng hô (`persona`), người xem (`audience`), câu kêu gọi (`cta`), màu nhận diện (`accent`), từ cấm (`avoid`) và định dạng mặc định riêng. `default_channel` dùng khi người dùng không nói kênh nào. Thêm kênh: thêm một khối mới rồi chạy `check`.

## Quy trình (các cổng)

Bắt đầu mỗi video: chạy `channels` và `check`. Thiếu settings hoặc thiếu công cụ thì hướng dẫn phần Cài đặt rồi dừng.

**Cổng 1 — Kênh, định dạng, mục tiêu.**
Liệt kê kênh (label + alias). Hỏi gọn trong một lượt: kênh nào; **ngắn hay dài** (gợi ý `default_format` nhưng phải xác nhận); chủ đề; người xem cần làm được gì sau khi xem; link sản phẩm/trang liên quan; tài sản người dùng đã có (video quay sẵn, tài khoản thử). Chủ đề lạc khỏi `topics` của kênh thì nói rõ và hỏi lại. Sau khi chốt: `init "<tên video>" --channel <alias> --format short|long`. Lệnh tạo thư mục dự án `tmp/<kênh>/<tên-video-không-dấu>/` ngay trong thư mục skill và in ra đường dẫn; mọi file của video nằm trong đó (xem mục Thư mục video).

**Cổng 2 — Nghiên cứu trên sản phẩm thật.**
Mở trang thật bằng trình duyệt và tự đi qua luồng định hướng dẫn. Ghi `research.md` trong dự án: từng bước theo đúng thứ tự, tên nút đúng chữ trên màn hình, giá và giới hạn kèm URL nguồn, chỗ dễ sai, và ảnh chụp mỗi bước. Bước nào cần đăng nhập hoặc không tự kiểm chứng được thì ghi rõ "chưa kiểm chứng" và hỏi người dùng. Trình bày tóm tắt; người dùng xác nhận luồng đúng.

**Cổng 3 — Hook và dàn ý.**
Đọc `references/kich-ban.md`. Đề xuất **3 hook** (kết quả trước, vấn đề đang xảy ra, điều trái dự đoán), mỗi hook gồm câu đầu + mô tả khung hình đầu. Kèm dàn ý: video ngắn 2–3 bước; video dài danh sách chương dạng "động từ + đối tượng". Người dùng chọn hook và sửa dàn ý.

**Cổng 4 — Lời đọc.**
Viết `script.json` đầy đủ theo định dạng trong `references/kich-ban.md`: mỗi cảnh có `vo`, `visual`, `on_screen`, `asset`. Giọng theo `persona`, tránh `avoid`. Đọc to từng câu để kiểm tra. Báo số từ và thời lượng ước tính. Hiển thị nguyên văn lời đọc; lặp tới khi người dùng nói ổn. Từ đây không đổi lời mà không hỏi.

**Cổng 5 — Tài sản thật.**
Đọc `references/tai-san-that.md`. Với mỗi cảnh cần hình:
- Logo: `logo <thương hiệu hoặc tên miền> --out <dự án>/assets/logos`, mở từng ứng viên ra xem, chọn bản đúng.
- Màn hình: viết file bước từ `research.md`, quay bằng `node scripts/capture.cjs --steps ... --out <dự án>/captures --format <short|long>`. Để hình khớp lời, quay **sau khi đã có giọng đọc** và dùng `scene`/`end` với độ dài lấy từ `audio/manifest.json` (xem "Quay khớp độ dài lời đọc" trong tài liệu); tức là phần quay màn hình của cổng này làm sau Cổng 6. Xem lại từng đoạn: trích khung hình ra xem, quay lại nếu có banner, dữ liệu riêng tư, con trỏ giật, hoặc khung không phủ kín.
- Màu: lấy màu thương hiệu của chủ đề (hoặc `accent` của kênh), chạy `theme --accent "#..." --out <dự án>/assets/theme.css`.
Gửi người dùng bảng: file, dùng cho cảnh nào, nguồn. Kèm khung hình chính của mỗi đoạn quay. Tài sản không lấy được thì nêu ra và hỏi, không thay bằng đồ tự vẽ.

**Cổng 6 — Giọng đọc.**
Tạo mẫu câu hook bằng `tts --channel <alias> --text "..." --out <dự án>/audio/mau-1.wav`; nếu người dùng chưa chốt giọng thì làm 2 mẫu với hai `--voice` khác nhau. Người dùng nghe và chọn. Sau đó `tts-script --script <dự án>/script.json` tạo âm thanh cho mọi cảnh và ghi `audio/manifest.json` (thời lượng thật, mốc bắt đầu và kết thúc từng cảnh). Báo tổng thời lượng; lệch khỏi định dạng đã chốt thì đề xuất cắt hoặc thêm câu nào và quay lại Cổng 4.

**Cổng 7 — Bảng phân cảnh theo thời gian thật.**
Đọc `references/edit-tokens.md` và `references/design-tokens.md`. Lập `storyboard.md`: mỗi cảnh một dòng với mốc thời gian lấy từ `manifest.json`, kiểu hình, tài sản, chuyển động (kiểu vào lấy tên trong mục "Từ vựng chuyển động", hai cảnh liền nhau không trùng kiểu; zoom vào đâu theo `captures/*.log.json`; viên thuốc tên miền lúc nào), chữ trên hình và mốc cụm chữ nhấn hiện ra. Kiểm theo giới hạn hình đứng yên của định dạng. Người dùng duyệt bảng này trước khi dựng.

**Cổng 8 — Dựng bằng HyperFrames.**
Nạp skill `/hyperframes` rồi `/hyperframes-core` (hợp đồng dựng), `/general-video` (video dài) và `/hyperframes-cli`. Dựng đúng `storyboard.md`:
- Dùng các khối trong `assets/tokens.css` và `assets/blocks.html`, màu từ `theme.css`, font Inter Tight đặt trong `assets/fonts` có `@font-face`.
- Lời đọc là các file trong `audio/`, đặt đúng mốc `start` của manifest. Video quay màn hình là `<video>` thật, zoom bằng cách biến đổi lớp bọc bên trong.
- Video ngắn luôn có phụ đề dựng sẵn, bám theo lời đọc.
Chạy `npx hyperframes check` tới khi sạch lỗi. Chụp ảnh tĩnh ở giữa mỗi cảnh (`snapshot`) và **tự xem từng ảnh**: chữ tràn, logo vỡ, vùng an toàn. Mở bản xem trước cho người dùng; sửa theo góp ý.

**Cổng 9 — Kiểm cuối và xuất.**
Chạy danh sách kiểm ở cuối `references/edit-tokens.md` và báo kết quả từng mục. Người dùng đồng ý thì `npx hyperframes render`, xuất ra đúng đường dẫn `output` ghi trong `project.json` (`output/<tên-video>.mp4`). Xem lại file mp4: khung đầu, khung cuối, một khung giữa mỗi chương, và nghe đoạn đầu.

Sau đó tạo thông tin đăng: `metadata init --project <dự án>` sinh `output/metadata.json` với một khối cho mỗi nền tảng của kênh. Điền tiêu đề, mô tả, caption, hashtag theo `references/metadata.md` (TikTok cần mô tả dài, không chỉ một câu), rồi `metadata check --project <dự án>` tới khi không còn mục nào trong `problems`. Đưa người dùng xem nội dung đã điền.

Cuối cùng làm ảnh bìa: đọc `references/thumbnail.md`, đề xuất 2 ý (nhóm hình trên, nhóm hình dưới, chữ tối đa 4 từ) cho người dùng chọn, rồi chạy `thumbnail --project <dự án> --variants 2 --title "..." --scene "..."`. Tự mở từng ảnh ra kiểm chữ và linh vật trước khi gửi; bản người dùng chọn lưu thành `output/thumbnail.png`.

**Bàn giao.** Gửi: đường dẫn thư mục `output/`, file mp4, ảnh bìa `thumbnail.png`, thời lượng, kênh và định dạng; đường dẫn `output/metadata.json` và tóm tắt nội dung từng nền tảng (tiêu đề, caption, hashtag; video dài có mốc chương và ý chữ cho thumbnail). Nhắc người dùng tự xem lại và tự đăng.

## Thư mục video

```
<thư mục skill>/tmp/<kênh>/<tên-video>/
├── project.json          kênh, định dạng, kích thước, đường dẫn xuất
├── research.md           Cổng 2
├── script.json           Cổng 4
├── storyboard.md         Cổng 7
├── assets/               logos/, fonts/, theme.css, ledger.json (sổ nguồn)
├── captures/             video và ảnh quay màn hình, file bước, log
├── audio/                lời đọc từng cảnh + manifest.json
├── (file dựng HyperFrames)
└── output/
    ├── <tên-video>.mp4   video hoàn chỉnh
    ├── metadata.json     tiêu đề, mô tả, caption, hashtag, mốc chương cho từng nền tảng
    └── thumbnail.png     ảnh bìa tranh minh hoạ, đúng kích thước định dạng
```

`tmp/` bị `.gitignore`. Người dùng chỉ cần lấy thư mục `output/`.

## Sửa video đã làm

Đổi lời: sửa `script.json` rồi `tts-script` lại (cảnh không đổi được dùng lại, không tốn tiền), cập nhật mốc thời gian trong bản dựng. Đổi hình: thay tài sản, ghi sổ nguồn, chụp lại ảnh tĩnh của cảnh đó. Mọi thay đổi vẫn qua người dùng duyệt trước khi xuất lại.

## Tài liệu

| File | Đọc khi |
|---|---|
| `references/phan-tich-phong-cach.md` | Cần hiểu vì sao phong cách này giữ người xem; trước Cổng 3 lần đầu dùng skill |
| `references/kich-ban.md` | Cổng 3 và 4 |
| `references/tai-san-that.md` | Cổng 2 và 5 |
| `references/edit-tokens.md` | Cổng 7, 8, 9 |
| `references/design-tokens.md` | Cổng 5 (màu) và 8 |
| `references/metadata.md` | Cổng 9: điền `output/metadata.json` |
| `references/thumbnail.md` | Cổng 9: phong cách và cách tạo ảnh bìa |
| `references/settings-schema.md` | Cài đặt, thêm kênh |
| `assets/blocks.html` | Xem trước các khối giao diện |
