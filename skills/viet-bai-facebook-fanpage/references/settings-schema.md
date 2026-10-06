# settings.json

| Khóa | Ý nghĩa |
|---|---|
| `zernio.api_key` | Key `sk_...` từ Zernio. Biến môi trường `ZERNIO_API_KEY` ưu tiên hơn. |
| `zernio.base_url` | Mặc định `https://zernio.com/api/v1`. |
| `zernio.post_url_template` | Mẫu link mở bài trên Zernio, `{post_id}` được thay bằng ID post (mặc định `https://zernio.com/dashboard/posts-all?post={post_id}`). |
| `default_page` | Alias page dùng khi user không chỉ định. |
| `pages.<alias>.account_id` | ID tài khoản Facebook Page trong Zernio (lấy bằng `sync-accounts`). |
| `pages.<alias>.timezone` | Múi giờ IANA cho lịch. |
| `pages.<alias>.brand_voice` / `audience` / `default_cta` | Định hướng giọng văn riêng từng page. |
| `pages.<alias>.hashtags` / `avoid` | Hashtag mặc định / từ-cụm từ cấm. |
| `pages.<alias>.best_times` | Khung giờ gợi ý (HH:MM). |

Thêm page: kết nối trong Zernio → `python -I scripts/fanpage.py sync-accounts --write` → chỉnh các trường giọng văn.

API Zernio dùng: `GET /v1/accounts`, `GET /v1/accounts/health`, `GET /v1/usage-stats`, `POST /v1/media/presign` (+ PUT lên `uploadUrl`, dùng `publicUrl`), `POST /v1/tools/validate/post` (dry-run), `POST /v1/posts` (`isDraft: true` hoặc `scheduledFor` + `timezone`, header `Idempotency-Key`), `GET /v1/posts/{id}`.

Lưu ý từ docs: `isDraft: true` thắng `publishNow` và `scheduledFor`; `scheduledFor` ở quá khứ sẽ bị đăng ngay; chuỗi giờ không có `Z`/offset được hiểu theo `timezone`.
