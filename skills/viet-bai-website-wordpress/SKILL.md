---
name: viet-bai-website-wordpress
description: Viết bài website WordPress, tạo draft để duyệt tay.
version: 0.1.0
author: Agoobi
license: MIT
metadata:
  hermes:
    category: coquifly
    tags: [wordpress, website, seo, vietnamese]
---

# viet-bai-website-wordpress

Viết bài cho website WordPress theo các "cổng" (gate) để user duyệt từng bước, hỗ trợ **nhiều site**, rồi tạo bài **Draft** qua REST API (đăng nhập bằng **Application Password**) và gửi link để user tự bấm Publish.

## Quy tắc sắt

1. **Agent KHÔNG publish.** Script không có lệnh đăng ngay. Kết thúc mặc định là Draft (hoặc "Chờ duyệt" nếu user muốn).
2. Lên lịch (`schedule`) chỉ khi user nói rõ "duyệt, lên lịch giúp tôi" kèm giờ ở Gate 6.
3. Mỗi Gate phải **dừng và chờ user trả lời**. Không gộp gate, không đoán thông tin thiếu.
4. Không bịa số liệu, giá, khuyến mãi, trích dẫn, đánh giá khách hàng. Không in Application Password ra chat.
5. Không sửa bài đã đăng / đã lên lịch (script từ chối). Không xóa bài, không tạo chuyên mục mới.

## Cài đặt (một lần)

Mọi lệnh chạy bằng `python -I scripts/wordpress.py <lệnh>` từ thư mục skill (chỉ cần Python 3).

1. Khách tạo Application Password: WordPress → Users → Profile → **Application Passwords** → đặt tên (vd `Hermes`) → Add → chép chuỗi 24 ký tự (chỉ hiện 1 lần). Tài khoản cần vai trò **Editor** hoặc **Administrator** (Author không tạo được thẻ mới; Contributor không upload ảnh được).
2. Copy `settings.example.json` thành `settings.json` (đã `.gitignore`). Điền `url`, `username`, `app_password` (hoặc env `WP_APP_PASSWORD_<ALIAS>`), giọng văn của site. Xem `references/viet-bai.md`.
3. Chạy `check` để kiểm tra kết nối, quyền, cách gọi REST (`/wp-json` hoặc `?rest_route=`), plugin SEO, múi giờ. Lỗi nào cũng có `hint`.

Nhiều site: `settings.json > sites` là map `alias → cấu hình`; `default_site` dùng khi user không nói site nào.

## Quy trình (các Gate)

Bắt đầu: `sites`. Chưa có `settings.json` hoặc site báo `THIEU` → hướng dẫn phần Cài đặt rồi dừng. Chạy `check --site <alias>` trước khi viết; `ok: false` thì báo user và dừng.

**Gate 1 — Chọn site.** Liệt kê site (label + alias). Chỉ 1 site thì xác nhận nhanh.

**Gate 2 — Nội dung.** Hỏi gọn trong 1 lượt: chủ đề, từ khóa chính, mục tiêu bài (bán hàng, hướng dẫn, tin tức), thông tin thật cần có (sản phẩm, giá, ưu đãi, thời hạn), link nội bộ muốn chèn, độ dài, điều cần tránh. Thiếu thì hỏi lại.

**Gate 3 — Dàn ý.** Đưa tiêu đề (1-2 phương án) + dàn ý H2/H3 + từ khóa phụ. User duyệt dàn ý trước khi viết đầy đủ.

**Gate 4 — Ảnh.** Hỏi user chọn: **A.** user gửi ảnh (file hoặc URL); **B.** dùng ảnh có sẵn trong Media Library (user đưa media id); **C.** tạo ảnh bằng công cụ có sẵn trong môi trường (nếu có, duyệt prompt trước); **D.** không ảnh. Cần 1 ảnh đại diện; ảnh trong bài tùy chọn. Không dùng ảnh không rõ bản quyền.

**Gate 5 — Bản nháp.** Viết bài theo `references/viet-bai.md` và cấu hình site, lưu file `drafts/<slug>.md` (dòng đầu `# Tiêu đề`). Hiển thị nguyên văn + đề xuất `slug`, `excerpt` (120-160 ký tự), chuyên mục (lấy từ `terms`, chỉ chọn mục có sẵn), thẻ. Lặp đến khi user nói "ok".

**Gate 6 — Duyệt cuối.** Tóm tắt: site, tiêu đề, slug, chuyên mục, thẻ, ảnh đại diện, excerpt, trạng thái (Draft / Chờ duyệt / lên lịch giờ X nếu user yêu cầu rõ). Hỏi: "Tạo bài Draft trên website nhé?" Chỉ chạy khi user đồng ý.

**Bàn giao.**

```
python -I scripts/wordpress.py draft --site <alias> --content-file drafts/<slug>.md --slug <slug> \
  --excerpt "<tóm tắt>" --categories "<chuyên mục>" --tags "<thẻ 1>" "<thẻ 2>" --featured <file|URL|media id> [--pending]
```

Script tự upload ảnh đại diện và ảnh trong bài vào Media Library (tên file không dấu, alt theo tiêu đề / mô tả ảnh), tạo thẻ chưa có, chuyển Markdown sang HTML. Gửi user: `edit_url` (mở trình soạn thảo), `preview_url` (xem trước khi đã đăng nhập), trạng thái. Nhắc: "Bạn mở link, kiểm tra và bấm Publish."

Chỉ khi user đã duyệt rõ giờ đăng: `schedule <id> --time "YYYY-MM-DD HH:MM" --i-have-user-approval` (giờ theo `timezone` của site). Script từ chối giờ đã qua hoặc còn dưới 5 phút, vì WordPress sẽ đăng ngay. Nói rõ bài sẽ **tự đăng** lúc đó.

Kiểm tra lại: `status <id>`.

## Sửa bài đã tạo

User muốn đổi gì sau khi đã có draft: **sửa tại chỗ, không tạo bài mới**:

```
python -I scripts/wordpress.py update <id> [--title ...] [--content-file ...] [--excerpt ...] [--slug ...] \
  [--categories ...] [--tags ...] [--featured <file|URL|id|''>]
```

Chỉ gửi phần thay đổi; `--tags` không kèm gì = bỏ hết thẻ; `--featured ''` = bỏ ảnh đại diện. Chỉ áp dụng bài Draft / Chờ duyệt; trạng thái giữ nguyên. Hiển thị bản sửa cho user duyệt trước khi chạy.

## SEO

`check` cho biết site có Yoast / Rank Math / AIOSEO không. Các plugin này **không cho ghi** tiêu đề SEO / meta description qua REST mặc định, nên script không ghi. Đưa user đoạn "Tiêu đề SEO" và "Mô tả SEO" đề xuất trong tin bàn giao để dán vào ô của plugin. `excerpt` vẫn được ghi (nhiều theme / plugin dùng làm mô tả khi chưa có meta).

## Xử lý lỗi

- 401: sai user/app password; host Apache CGI xóa header Authorization (thêm dòng `SetEnvIf` trong `hint` vào `.htaccess`); plugin bảo mật tắt Application Passwords. Application Passwords cần site chạy HTTPS.
- 403 `rest_cannot_*`: tài khoản thiếu quyền, nhờ khách nâng lên Editor.
- `not_json`: firewall / Cloudflare / plugin chặn REST API, nhờ khách cho phép IP máy chạy agent hoặc tắt chặn REST.
- Chuyên mục không có: script liệt kê chuyên mục có sẵn; hỏi user chọn hoặc tự tạo trên WordPress.
- Lỗi mạng / lỗi khác: báo nguyên văn, không nói đã tạo bài khi chưa có `id`.
