# Gợi ý viết bài website (chuẩn SEO cơ bản)

- **Một bài, một từ khóa chính.** Đưa từ khóa vào tiêu đề (≤ 60 ký tự), câu đầu tiên, 1-2 tiêu đề H2, slug và đoạn tóm tắt (`--excerpt`, 120-160 ký tự, dùng làm mô tả khi chia sẻ).
- **Tiêu đề bài là dòng `# ...` đầu file.** Trong nội dung chỉ dùng `##` (H2) và `###` (H3), không dùng `#` lần nữa.
- Mở bài 2-3 câu nói thẳng vấn đề của người đọc. Thân bài chia mục H2 rõ ràng, đoạn 2-4 câu, có danh sách khi liệt kê.
- Độ dài theo `length` của site (thường 800-1200 từ). Không độn chữ.
- Ảnh: 1 ảnh đại diện (1200×630 đẹp nhất khi chia sẻ Facebook/Zalo) + ảnh minh họa trong bài, luôn có alt mô tả nội dung ảnh. Tên file ảnh không dấu (script tự đổi).
- Liên kết: 1-3 link nội bộ tới bài/sản phẩm khác trên site (user cung cấp hoặc lấy từ sitemap), link ngoài chỉ tới nguồn uy tín.
- Kết bài: tóm tắt + CTA (`default_cta`).
- Số liệu, giá, khuyến mãi, chính sách, trích dẫn: **chỉ dùng thông tin user đưa**. Không có thì để `[CẦN XÁC NHẬN: ...]` trong bản nháp và hỏi user.
- Tránh: nhồi từ khóa, cam kết tuyệt đối, so sánh đích danh đối thủ, nội dung y tế/tài chính chưa kiểm chứng, từ trong `avoid`.
- Bài viết lại từ nguồn khác: viết lại bằng ý của mình, ghi nguồn; không chép nguyên văn.

## Định dạng file nội dung

Markdown, script tự chuyển sang HTML (hiện trong khối "Classic" của trình soạn thảo; user bấm "Chuyển thành khối" nếu muốn):

```
# Tiêu đề bài

Đoạn mở bài có **chữ đậm**, *nghiêng*, [link](https://...).

## Mục 1
- ý một
- ý hai

![Mô tả ảnh](anh/hinh-1.jpg)
```

Ảnh trong bài là file local (đường dẫn tính từ thư mục file .md) hoặc URL: script upload vào Media Library và thay link. Dòng bắt đầu bằng `<` được giữ nguyên là HTML (vd khung nhúng YouTube). Có thể đưa file `.html` thay cho `.md`.

## settings.json (mỗi site)

| Khóa | Ý nghĩa |
|---|---|
| `url` | Địa chỉ site, vd `https://shop.vn` (không có `/` cuối) |
| `username` | Tên đăng nhập WordPress của tài khoản tạo Application Password |
| `app_password` | Application Password (Users → Profile → Application Passwords). Hoặc env `WP_APP_PASSWORD_<ALIAS>` (vd `WP_APP_PASSWORD_SHOP`), env được ưu tiên |
| `timezone` | Múi giờ khi lên lịch, nên trùng Settings → General của site |
| `default_category` | Chuyên mục mặc định khi user không chọn (phải có sẵn) |
| `brand_voice`, `audience`, `default_cta`, `seo_keywords`, `avoid`, `length` | Giọng văn và quy ước viết của site |
