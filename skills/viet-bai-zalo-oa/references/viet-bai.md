# Gợi ý viết bài Zalo OA

- Người đọc là **người đã quan tâm OA**, đọc trên điện thoại: câu ngắn, đoạn 1-3 câu, nhiều xuống dòng, danh sách gạch đầu dòng.
- **Tiêu đề** (≤ 150 ký tự, nên dưới 70 để không bị cắt): nói rõ lợi ích hoặc tin chính, có con số thật nếu có.
- **Mô tả** (≤ 300 ký tự, nên 1-2 câu): tóm tắt giá trị bài, hiện ở danh sách bài và khi chia sẻ.
- Ảnh bìa ngang, chữ trên ảnh ít và to. Ảnh trong bài: ảnh sản phẩm, bảng giá dạng ảnh chỉ khi user cung cấp.
- Mỗi bài một mục tiêu, một CTA (`default_cta`), thường là "nhắn tin OA" hoặc link website.
- Ưu đãi: ghi rõ mức giảm, thời hạn, điều kiện đúng như user cung cấp. Thiếu thì hỏi, không đoán.
- Tránh: cam kết tuyệt đối, so sánh đích danh đối thủ, nội dung y tế / tài chính chưa kiểm chứng, từ trong `avoid`.

## Định dạng file nội dung

Markdown, script chuyển sang khối của bài Zalo:

```
# Tiêu đề bài

Đoạn mở bài, có thể kèm [link](https://shop.vn/...).

## Mục nhỏ
- ý một
- ý hai

![Chú thích ảnh](https://shop.vn/wp-content/uploads/anh.jpg)
```

Bài tạo qua API, Zalo bỏ mọi thẻ HTML và đổi xuống dòng thành dấu cách (đã kiểm với OA thật), nên script gửi **chữ thô, mỗi đoạn một khối**:

- Mỗi đoạn, mỗi ý danh sách (`• ý một`, `1. bước một`), mỗi trích dẫn là một khối riêng → hiện thành dòng riêng.
- `##` thành dòng VIẾT HOA (không có tiêu đề hay chữ đậm).
- `**đậm**`, `*nghiêng*` mất định dạng, chỉ còn chữ; `[chữ](URL)` thành `chữ (URL)`, link không bấm được.
- Dòng chỉ có ảnh `![chú thích](URL https hoặc file)` thành khối ảnh riêng. File tính từ thư mục của file nội dung, cần `image_host`. Mỗi ảnh ≤ 1 MB.
- Cần chữ đậm, link bấm được: chủ OA sửa trên oa.zalo.me trước khi hiện bài.

## settings.json (mỗi OA)

| Khóa | Ý nghĩa |
|---|---|
| `oa_id` | ID của OA (lệnh `oas` sau khi kết nối) |
| `label` | Tên hiển thị trong danh sách |
| `author` | Tác giả mặc định (≤ 50 ký tự) |
| `comment` | `show` / `hide`: cho phép bình luận |
| `brand_voice`, `audience`, `default_cta`, `avoid`, `length` | Giọng văn và quy ước viết |
| `image_host` | (gốc settings hoặc từng OA) `{"dir", "url"}`: thư mục web công khai để đăng ảnh trên máy |

Biến môi trường: `ZALO_APP_ID`, `ZALO_APP_SECRET` (bắt buộc khi kết nối và làm mới token), `ZALO_TOKEN_FILE` (tùy chọn), `ZALO_ACCESS_TOKEN` + `ZALO_REFRESH_TOKEN` (chỉ cho `connect-import`).
