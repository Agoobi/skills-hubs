---
name: viet-bai-website-wordpress
description: Viết bài website WordPress, xem trước trong chat, lên lịch đăng qua Lịch đăng của Open WebUI.
version: 0.2.0
author: Agoobi
license: MIT
metadata:
  hermes:
    category: coquifly
    tags: [wordpress, website, seo, vietnamese, lich-dang]
---

# viet-bai-website-wordpress

Viết bài cho website WordPress theo các "cổng" (gate) để user duyệt từng bước, **xem trước ngay trong chat**, rồi
**lên lịch đăng** trong **Lịch đăng** của Open WebUI (sidebar → Lịch đăng). Đúng giờ, máy chủ gửi bài lên WordPress qua
REST API (Application Password). User xem lịch, kéo đổi giờ, đổi Đăng thật / Lưu nháp, huỷ lịch ngay trên trang đó.

Lịch đăng là phần của [openwebui-custom](https://github.com/Agoobi/openwebui-custom). Máy chưa có Lịch đăng
(`lich.py status` báo "Chưa có Lịch đăng") thì dùng cách cũ ở cuối file (tạo Draft).

## Quy tắc sắt

1. **Agent KHÔNG đăng ngay.** Kết thúc là **hẹn giờ** trong Lịch đăng, chỉ khi user đã xem preview và đồng ý giờ đăng
   trong chat (`schedule ... --i-have-user-approval`). Giờ hẹn phải sau lúc này ít nhất 2 phút.
2. **Không tạo bài nháp nếu user không yêu cầu.** Mặc định là chế độ theo Cài đặt của Lịch đăng (thường "Đăng thật":
   tới giờ bài hiện trên site). Chỉ dùng `--mode draft` ("Lưu nháp trên WordPress": tới giờ bài vào WordPress dạng
   nháp) khi user nói rõ muốn vậy.
3. Mỗi Gate phải **dừng và chờ user trả lời**. Không gộp gate, không đoán thông tin thiếu.
4. Không bịa số liệu, giá, khuyến mãi, trích dẫn, đánh giá khách hàng. Không in Application Password ra chat.
5. Chuyên mục **chỉ chọn trong danh sách có sẵn** của site (`lich.py categories`); thẻ chưa có sẽ được tạo. Không xoá bài.
6. Agent không thêm / sửa site WordPress, không đổi múi giờ, khung giờ, chế độ mặc định: đó là việc của user trong
   Lịch đăng → Cài đặt. Lịch đăng cũng tự chặn các việc này.
7. **Xem trước = dán nguyên văn `preview_markdown`** vào câu trả lời: giữ bảng thông tin, ảnh bìa, chữ đậm, ảnh trong
   bài, link "Mở trong Lịch đăng". Không tóm tắt, không viết lại, không bỏ phần nào; câu của agent đặt trước hoặc sau.

## Cài đặt (một lần)

Mọi lệnh chạy bằng `python -I scripts/<file>.py <lệnh>` từ thư mục skill (chỉ cần Python 3).

1. User mở Open WebUI → **Lịch đăng** → **Cài đặt** → **Kết nối WordPress**: nhập địa chỉ site, tên đăng nhập,
   Application Password (WordPress → Users → Profile → Application Passwords → đặt tên `Lịch đăng` → Add → chép chuỗi
   24 ký tự). Tài khoản cần vai trò **Editor** hoặc **Administrator**. Lịch đăng kiểm tra kết nối và mã hoá mật khẩu.
2. `settings.json` (copy từ `settings.example.json`) giữ **giọng văn** từng site: `brand_voice`, `audience`,
   `default_cta`, `seo_keywords`, `avoid`, `length`, `default_category`. Alias trong file này được nối với site trong
   Lịch đăng theo `url`. Xem `references/viet-bai.md`.
3. Chạy `python -I scripts/lich.py status`: agent làm cho ai, múi giờ, khung giờ đăng, site và tình trạng kết nối.
   Site báo lỗi kết nối (tường lửa hosting chặn IP máy chủ, sai mật khẩu...) thì báo user nguyên văn, nhắc họ sửa trong
   Lịch đăng → Cài đặt, và vẫn có thể viết bài; bài sẽ chờ tới khi site kết nối được.

## Quy trình (các Gate)

Bắt đầu: `lich.py status`. Không có site nào → hướng dẫn phần Cài đặt rồi dừng.

**Gate 1 — Chọn site.** Liệt kê site (`lich.py sites`). Chỉ 1 site thì xác nhận nhanh.

**Gate 2 — Nội dung.** Hỏi gọn trong 1 lượt: chủ đề, từ khóa chính, mục tiêu bài (bán hàng, hướng dẫn, tin tức),
thông tin thật cần có (sản phẩm, giá, ưu đãi, thời hạn), link nội bộ muốn chèn, độ dài, điều cần tránh. Thiếu thì hỏi lại.

**Gate 3 — Dàn ý.** Đưa tiêu đề (1-2 phương án) + dàn ý H2/H3 + từ khóa phụ. User duyệt dàn ý trước khi viết đầy đủ.

**Gate 4 — Ảnh.** Hỏi user chọn: **A.** user gửi ảnh (file hoặc URL); **B.** tạo ảnh bằng công cụ có sẵn trong môi
trường (nếu có, duyệt prompt trước); **C.** không ảnh. Cần 1 ảnh đại diện; ảnh trong bài tùy chọn. Không dùng ảnh
không rõ bản quyền.

**Gate 5 — Bản nháp trong chat.** Viết bài theo `references/viet-bai.md` và giọng văn của site, lưu `drafts/<slug>.md`
(dòng đầu `# Tiêu đề`). Lấy chuyên mục có sẵn bằng `lich.py categories --site <alias>`. Đưa bài vào Lịch đăng
(chưa hẹn giờ):

```
python -I scripts/lich.py save --site <alias> --content-file drafts/<slug>.md --slug <slug> \
  --excerpt "<tóm tắt 120-160 ký tự>" --categories "<chuyên mục có sẵn>" --tags "<thẻ 1>" "<thẻ 2>" \
  --featured <file|URL>
```

Script chuyển Markdown sang HTML, tải ảnh đại diện và ảnh trong bài vào Lịch đăng (tới giờ đăng mới lên site), rồi in
`preview_markdown`. **Dán nguyên `preview_markdown` vào câu trả lời** để user xem bài ngay trong chat (bảng thông tin,
ảnh bìa, toàn văn bài) kèm link mở trong Lịch đăng (`/#lich-dang/post=<id>`, xem như trên web). User muốn sửa:
sửa file, chạy lại `save --id <id> ...` (sửa tại chỗ, không tạo bài mới), dán preview mới. Lặp đến khi user nói "ok".

**Gate 6 — Chọn giờ đăng và duyệt cuối.** Lấy giờ trống: `lich.py slots` (theo khung giờ đăng user đặt). Hỏi trong
1 lượt: "Đăng lúc nào? (gợi ý: <2-3 giờ trống>) · Đăng thật hay lưu nháp trên WordPress?". Tóm tắt: site, tiêu đề,
giờ đăng (kèm thứ, ngày, múi giờ), chế độ. Chỉ khi user đồng ý rõ:

```
python -I scripts/lich.py schedule <id> --time "YYYY-MM-DD HH:MM" [--mode publish|draft] --i-have-user-approval
python -I scripts/lich.py schedule <id> --next --i-have-user-approval        # khung giờ trống kế tiếp
```

Giờ hiểu theo múi giờ trong Cài đặt của Lịch đăng. Báo lại user câu `bao_nguoi_dung` mà script trả về (giờ đăng, bài
sẽ tự đăng hay vào nháp, link đổi giờ / huỷ). Gửi SEO: đoạn "Tiêu đề SEO" và "Mô tả SEO" đề xuất để user dán vào ô của
plugin SEO (Yoast / Rank Math không cho ghi qua REST).

## Sau khi hẹn

- Xem / theo dõi: `lich.py get <id>` (trạng thái, lỗi, lịch sử), `lich.py list` (bài trong 30 ngày tới + chưa lên lịch).
- User đổi ý: đổi giờ → `schedule <id> --time ...` (vẫn cần đồng ý); huỷ → `unschedule <id>` (bài về Chưa lên lịch,
  không mất); đổi chế độ → `mode <id> --mode draft|publish`. Hoặc user tự làm trên trang Lịch đăng.
- Đã đăng thì không sửa qua Lịch đăng nữa; sửa trong WordPress (link `wp_edit_url`).
- Gửi không được (mạng, tường lửa): máy chủ tự thử lại sau 1, 2, 5, 10 phút, tới 3 giờ sau giờ hẹn, không tạo bài trùng.
  Sai mật khẩu / thiếu quyền / chuyên mục không có: báo Lỗi ngay. Báo user nguyên văn lỗi trong `get`.

## SEO

Plugin SEO (Yoast / Rank Math / AIOSEO) **không cho ghi** tiêu đề SEO / meta description qua REST mặc định. Đưa user
đoạn "Tiêu đề SEO" và "Mô tả SEO" đề xuất. `excerpt` vẫn được ghi (nhiều theme / plugin dùng làm mô tả khi chưa có meta).

## Xử lý lỗi (lỗi kết nối site hiện trong Lịch đăng → Cài đặt và trong `lich.py status`)

- Tường lửa hosting chặn IP máy chủ (503 / thử thách / hết thời gian chờ): nhờ khách cho IP máy chủ (Lịch đăng hiện IP
  này) vào danh sách cho phép của hosting. Bài hẹn vẫn chờ và tự thử lại.
- 401: sai user / app password, hoặc host xoá header Authorization (thêm `SetEnvIf Authorization "(.*)"
  HTTP_AUTHORIZATION=$1` vào `.htaccess`), hoặc plugin bảo mật tắt Application Passwords. Cần site chạy HTTPS.
- 403 `rest_cannot_*`: tài khoản thiếu quyền, nhờ khách nâng lên Editor.
- Chuyên mục không có: chọn lại trong `lich.py categories`.
- HTTP 500 `internal_server_error` **chỉ khi gán ảnh đại diện** (`featured_media`): lỗi phía site (theme/plugin hỏng
  hook `set_post_thumbnail`). Bỏ `--featured`, chèn ảnh ngay trong nội dung `![chú thích](file hoặc URL)`, báo user tự
  gán ảnh đại diện trong wp-admin sau khi sửa lỗi site.
- Lỗi khác: báo nguyên văn, không nói đã hẹn khi script chưa trả `ok: true`.

## Cách cũ: máy chưa có Lịch đăng

Chỉ khi `lich.py status` báo chưa có Lịch đăng. Site cấu hình trong `settings.json` (`url`, `username`, `app_password`
hoặc env `WP_APP_PASSWORD_<ALIAS>`), kiểm tra bằng `wordpress.py check --site <alias>`. Gate 5 hiển thị bài nguyên văn
trong chat; Gate 6 tạo bài Draft khi user đồng ý:

```
python -I scripts/wordpress.py draft --site <alias> --content-file drafts/<slug>.md --slug <slug> \
  --excerpt "<tóm tắt>" --categories "<chuyên mục>" --tags "<thẻ 1>" "<thẻ 2>" --featured <file|URL|media id> [--pending]
```

Lên lịch bằng WordPress chỉ khi user duyệt rõ giờ: `wordpress.py schedule <id> --time "YYYY-MM-DD HH:MM"
--i-have-user-approval` (giờ theo `timezone` của site; script từ chối giờ đã qua hoặc còn dưới 5 phút). Sửa bài:
`wordpress.py update <id> ...`. Upload media trả `307` rồi lần sau thành công: CDN/nginx của host chuyển hướng ở request
đầu; chạy lại `upload` (kiểm tra Media Library để tránh tạo trùng).
