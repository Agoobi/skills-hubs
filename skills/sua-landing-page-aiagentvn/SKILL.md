---
name: sua-landing-page-aiagentvn
description: Sửa landing page aiagentvn.com rồi deploy an toàn.
version: 0.1.0
author: Agoobi
license: MIT
metadata:
  hermes:
    category: coquifly
    tags: [landing-page, aiagentvn, wordpress, deploy, onepanel, vietnamese]
---

# sua-landing-page-aiagentvn

Sửa landing page của aiagentvn.com, gồm các trang trong `pages/landing` của theme `Agoobi/aiagentvn-theme` như `/video-ai/`, `/agent-facebook-ads/`, `/khoa-hoc/`… Sau đó deploy lên hosting qua OnePanel MCP.

Dùng khi admin nói "sửa trang …", "đổi chữ/giá/ảnh/nút trên landing", "thêm video/case vào trang", "deploy landing", "rollback landing", hoặc dán một link aiagentvn.com và muốn chỉnh trang đó.

Admin mô tả thay đổi bằng lời, bạn sửa code, cho xem trước, mở PR, rồi deploy đúng nhánh `main` lên hosting và kiểm tra trang thật. Công cụ đi kèm: `scripts/landing.py` (trong thư mục skill này).

## Cài một lần

1. Có `git`, `gh` (đăng nhập tài khoản có quyền repo `Agoobi/aiagentvn-theme`) và Python 3.9+.
2. Lấy skill: bật trong Coquifly, hoặc với Claude Code thì chép thư mục `skills/sua-landing-page-aiagentvn` của repo `Agoobi/skills-hubs` vào `~/.claude/skills/`.
3. Clone theme: `gh repo clone Agoobi/aiagentvn-theme` rồi làm việc trong thư mục đó.
4. Chủ site đưa riêng 2 giá trị, admin tự đặt làm **biến môi trường của máy** (không dán vào chat, không ghi vào file trong repo):
   - `ONEPANEL_MCP_URL`
   - `ONEPANEL_MCP_TOKEN`

   Thiếu 2 biến này thì vẫn sửa, xem trước và mở PR được, chỉ không deploy được. Khi đó hãy nhắc admin xin chủ site.

Trong mọi bước: không in, không lặp lại, không commit token hay URL hosting. Nếu admin dán token vào chat, nhắc họ đặt thành biến môi trường và đổi token sau.

## Quy trình

Gọi công cụ bằng `python <thư mục skill>/scripts/landing.py <lệnh>`, chạy trong thư mục repo theme. Trong các ví dụ dưới, `landing.py` là viết tắt của đường dẫn đó.

### 1. Lấy code mới nhất, tạo nhánh

```bash
git switch main && git pull
git switch -c landing/<tên-trang>-<việc-ngắn>
```

### 2. Tìm đúng file của trang

```bash
python landing.py find https://aiagentvn.com/video-ai/
```

Lệnh in ra `page key` và các file của trang:

- `pages/landing/<key>.html`: nội dung trang (HTML thuần, không có header/footer chung).
- `assets/landing/<key>.css`: CSS riêng của trang.
- `assets/landing/<key>.js`: JS riêng của trang (nếu có).
- `assets/landing/<key>.tw.css`: bản Tailwind **đã build sẵn**. Không sửa file này.

Trang chủ, blog, `/dich-vu/`, `/lien-he/` không phải landing page. Gặp các trang đó thì dừng lại và báo admin.

### 3. Sửa

Quy tắc bắt buộc:

- **Chỉ đổi đúng phần admin yêu cầu.** Giữ nguyên thiết kế, màu, font, bố cục và các đoạn chữ khác của trang. Admin đã chốt: landing page giữ giao diện gốc.
- **Chỉ sửa 3 loại file trên của đúng trang đó.** Không sửa `inc/`, `functions.php`, `site-page.php`, `assets/ds/` (header, footer, menu dùng chung), và không sửa trang khác. Nếu việc cần đụng tới các chỗ đó, dừng lại và báo admin để chủ site làm.
- **Không sửa `tools/src/*` và không chạy `tools/migrate.py`.** Đó là nguồn cũ. Chạy lại sẽ đè mất mọi bản sửa đã làm trong `pages/landing`.
- **CSS mới phải nằm trong `assets/landing/<key>.css`**, viết lồng dưới class của trang (`.pg-<key> …` hoặc class gốc của trang như `.vl …`). Trang dùng Tailwind (`.tw.css`) chỉ có sẵn những class đã build. Thêm class Tailwind mới vào HTML sẽ không có tác dụng, nên hãy viết CSS thường.
- **Đường dẫn tới ảnh** trong theme dùng `{{static}}`, nghĩa là `assets/root-static/`. Ví dụ: `{{static}}videolab/e/anh.webp`. Ảnh mới để dạng `.webp`, mỗi ảnh dưới khoảng 200 KB. Video thì dùng YouTube (Short hoặc Unlisted) rồi nhúng `https://www.youtube.com/embed/<id>`, không đưa file video vào repo.
- **Chữ tiếng Việt có dấu đầy đủ.** Giá viết dạng `1.500.000đ`.
- Trên điện thoại (rộng 375px) trang không được tràn ngang.
- Trang Video Lab (`templates`): danh sách case khách hàng nằm trong mảng `EDIT_CASES` ở `assets/landing/templates.js`. Mỗi video có dạng `['<tên-ảnh>', '<nhãn>', '<youtube-id>']`, ảnh thumbnail 360×640 đặt tại `assets/root-static/videolab/e/<tên-ảnh>.webp`.

### 4. Xem trước

```bash
python landing.py preview <key>
```

Lệnh lấy trang thật đang chạy, thay phần thân trang, CSS và JS bằng bản trên máy, rồi in ra đường dẫn một file `.html`. Mở file đó trong trình duyệt ở cả khổ máy tính và khổ điện thoại, chụp màn hình cho admin xem. **Chờ admin đồng ý rồi mới sang bước 5.**

### 5. Commit và mở PR

```bash
git add <đúng các file đã sửa>
git commit -m "<Trang>: <thay đổi gì>"
git push -u origin HEAD
gh pr create --base main --fill
```

Không `git add -A`. Gửi admin link PR. Chỉ merge khi admin bảo (`gh pr merge <số> --squash`).

### 6. Deploy (sau khi PR đã merge vào main)

`deploy` chỉ ship đúng nhánh `main` trên GitHub, không lấy file đang sửa dở trên máy.

```bash
git fetch origin && git switch --detach origin/main
python landing.py plan
```

`plan` chỉ đọc. Nó so từng file của `main` với file đang chạy trên hosting và liệt kê file nào sẽ được ghi. Đưa danh sách cho admin xem. Nếu có file nằm ngoài những gì PR đã sửa, dừng lại và hỏi admin. Thường đó là thay đổi của người khác chưa deploy.

Admin đồng ý thì chạy:

```bash
python landing.py deploy
```

Lệnh này làm lần lượt:

1. Sao lưu các file sắp bị thay vào `~/aiavn-backups/<mã>/` trên hosting.
2. Ghi file mới. Ảnh được gửi theo đường riêng vì API của hosting chỉ ghi được file chữ.
3. Lưu commit đang live.
4. Xoá cache.
5. Đọc lại từng file để kiểm tra.

Cuối cùng lệnh in ra **mã rollback**, bạn báo mã này cho admin.

Lần đầu tiên dùng, khi hosting chưa có mốc commit, lệnh báo cần `--base`. Hãy hỏi chủ site commit nào đang live rồi chạy `python landing.py deploy --base <commit>`.

### 7. Kiểm tra trang thật

Mở `https://aiagentvn.com/<slug>/` (thêm `?v=<số bất kỳ>` để bỏ qua cache):

- Thay đổi đã hiện ra.
- Console không có lỗi JS.
- Khổ điện thoại không vỡ bố cục.

Một số trang (như Video Lab) chỉ vẽ phần danh sách sau khi trang tải xong toàn bộ video, nên hãy chờ vài giây rồi mới kết luận.

### Khi cần quay lại

```bash
python landing.py rollback <mã>
```

Lệnh trả các file chữ về bản trước deploy và xoá cache. Ảnh không tự quay lại. Nếu cần quay cả ảnh, hãy revert PR trên GitHub rồi deploy lại.

## Báo cáo cho admin

Sau mỗi lần làm, báo bằng tiếng Việt, ngắn gọn:

- Đã đổi gì, trên trang nào (kèm link).
- Link PR.
- Đã deploy chưa, mã rollback.
- Đã kiểm tra những gì trên trang thật.
- Việc gì chưa làm được và vì sao.
