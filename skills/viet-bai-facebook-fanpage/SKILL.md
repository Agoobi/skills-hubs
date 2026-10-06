---
name: viet-bai-facebook-fanpage
description: Viết bài fanpage, tạo draft trên Zernio để duyệt tay.
version: 0.1.1
author: Agoobi
license: MIT
metadata:
  hermes:
    category: coquifly
    tags: [facebook, fanpage, zernio, vietnamese]
---

# viet-bai-facebook-fanpage

Viết bài Facebook fanpage theo quy trình có nhiều "cổng" (gate) để user duyệt từng bước, hỗ trợ **nhiều page**, rồi đẩy bài lên **Zernio dưới dạng DRAFT** và gửi link để user tự bấm Publish.

## Quy tắc sắt (không bao giờ vi phạm)

1. **Agent KHÔNG publish.** Không dùng `publishNow`. Kết thúc mặc định là draft trong Zernio.
2. Lên lịch tự động (`schedule`) chỉ khi user nói rõ "duyệt, lên lịch giúp tôi" ở Gate 7; nếu không, chỉ ghi giờ dự kiến.
3. Mỗi Gate phải **dừng và chờ user trả lời**. Không gộp gate, không tự đoán thông tin thiếu.
4. Không bịa số liệu, khuyến mãi, cam kết, nguồn ảnh. Không in API key ra chat.

## Cài đặt (một lần)

Mọi lệnh chạy bằng `python -I scripts/fanpage.py <lệnh>` từ thư mục skill (chỉ cần Python 3, không cần cài thư viện).

1. Copy `settings.example.json` thành `settings.json` (file này bị `.gitignore`, không commit).
2. Điền `zernio.api_key` (dạng `sk_...`, tạo ở dashboard Zernio) — hoặc đặt biến môi trường `ZERNIO_API_KEY` (ưu tiên hơn file).
3. Kết nối các Facebook Page trong Zernio (mỗi Page chọn ở bước connect), rồi chạy `sync-accounts --write` để tự điền `account_id` các page vào `settings.json`.
4. Điền cho mỗi page: `brand_voice`, `audience`, `default_cta`, `hashtags`, `avoid`, `best_times`, `timezone`.

### Quản lý nhiều page

`settings.json > pages` là một map `alias -> cấu hình`. Mỗi alias = 1 fanpage = 1 `account_id` Zernio, có giọng văn/hashtag/giờ vàng riêng. Thêm page mới: kết nối trong Zernio → `sync-accounts --write` → chỉnh brand voice. `default_page` dùng khi user không nói page nào. Xem `references/settings-schema.md`.

## Quy trình (các Gate)

Bắt đầu: chạy `pages`. Nếu chưa có `settings.json` hoặc thiếu key → hướng dẫn user phần Cài đặt rồi dừng. Chạy `check` (chỉ đọc) để xem page nào `needsReconnect` / `canPost: false` và báo user trước khi viết.

**Gate 1 — Chọn page.** Liệt kê page (label + alias). Hỏi đăng page nào (có thể nhiều page: soạn riêng từng page theo giọng văn riêng). Nếu chỉ có 1 page, xác nhận nhanh.

**Gate 2 — Nội dung.** Hỏi gọn trong 1 lượt: chủ đề/thông điệp chính, mục tiêu (bán hàng, tương tác, thông báo, kể chuyện), sản phẩm/ưu đãi/số liệu thật, CTA, độ dài mong muốn, điều cần tránh. Thiếu dữ kiện thì hỏi lại, không bịa.

**Gate 3 — Ảnh/media.** Hỏi user chọn 1 trong 4:
- **A. User thả ảnh**: nhận đường dẫn file local hoặc URL.
- **B. Agent tìm ảnh**: `search-images "<từ khóa>" --source commons` (Wikimedia Commons) hoặc `--source openverse`. Trình 3-5 ứng viên kèm giấy phép + tác giả + link nguồn; user chọn; `download` về. Nếu CC-BY/CC-BY-SA thì thêm dòng credit vào bài/comment. Không dùng ảnh khi không rõ giấy phép. Commons phù hợp ảnh địa danh/sự kiện/khái niệm, kém cho ảnh sản phẩm thương mại → gợi ý user cung cấp ảnh thật.
- **C. Agent gen ảnh**: dùng công cụ tạo ảnh có sẵn trong môi trường (nếu có); viết prompt, user duyệt trước khi tạo. Nếu không có tool → nói rõ và đưa phương án A/B.
- **D. Không dùng ảnh.**
Yêu cầu user xác nhận ảnh cuối cùng.

**Gate 4 — Bản nháp.** Viết 1-2 phương án theo `brand_voice`, `audience`, `default_cta`, `hashtags`, `avoid` của page (xem `references/viet-bai.md`). Hiển thị nguyên văn. Hỏi: sửa gì? chọn phương án nào? Lặp đến khi user nói "ok".

**Gate 5 — Comment đầu tiên (first comment).** Hỏi có muốn comment đầu bài không (link, ghi chú giá, credit ảnh, hashtag đẩy xuống comment...). Soạn nếu cần, user duyệt. Comment được lưu vào draft (`platformSpecificData.firstComment`) và Zernio đăng nó khi user publish; vẫn đưa text comment trong tin bàn giao để user kiểm tra.

**Gate 6 — Lịch.** Hỏi thời điểm đăng: gợi ý từ `best_times` của page, múi giờ của page. Ghi lại giờ dự kiến. Mặc định: **chỉ tạo draft**, user tự lên lịch/publish trên Zernio.

**Gate 7 — Duyệt cuối.** Lưu nội dung vào file tạm, chạy `validate --page <alias> --content-file <file> --media <url>... --first-comment "..."` (dry-run của Zernio, không tạo post); báo lỗi/cảnh báo nếu có. In tóm tắt: page, nội dung đầy đủ, ảnh, first comment, giờ dự kiến, chế độ (draft). Hỏi: "Tạo draft trên Zernio nhé?" Chỉ chạy khi user đồng ý.

**Bàn giao.**

```
python -I scripts/fanpage.py draft --page <alias> --content-file <file.txt> --media <file hoặc url>... --first-comment "<text>" --intended-time "<giờ dự kiến>"
```

Lệnh tự upload ảnh local (`/media/presign`) và tạo post `isDraft: true` (theo docs Zernio, `isDraft` thắng `publishNow`/`scheduledFor`: bài chỉ được lưu, không bao giờ đăng). Có `Idempotency-Key` nên không tạo trùng khi retry. Gửi user: **link bài trên Zernio** (`post_url` trong kết quả, dạng `https://zernio.com/dashboard/posts-all?post=<post_id>`), trạng thái `draft`, giờ dự kiến, text first comment. Nhắc: "Bạn mở Zernio, kiểm tra và bấm Publish/Schedule bằng tay." Nếu user ở Gate 6-7 nói rõ "lên lịch giúp luôn" thì mới dùng `schedule --time ... --i-have-user-approval` (đúng timezone page) và nói rõ bài sẽ tự đăng lúc đó. Zernio đăng NGAY nếu giờ đã qua, nên script từ chối mọi giờ không cách hiện tại ít nhất 5 phút.

Kiểm tra lại: `status <post_id>`.

## Xử lý lỗi

- 401: key sai/hết hạn → nhờ user cập nhật key. 409: trùng nội dung trong 24h → hỏi user có muốn sửa nội dung.
- Page chưa có `account_id` → `sync-accounts --write`; page không xuất hiện → user cần kết nối lại trong Zernio.
- Tool/mạng lỗi: báo lỗi nguyên văn, không giả vờ đã tạo draft.

## Guardrails

- Không tự publish, không tự lên lịch khi chưa được user duyệt rõ ràng.
- Không bịa số liệu, nguồn, ưu đãi, đánh giá khách hàng, cam kết của doanh nghiệp.
- Không dùng ảnh không rõ bản quyền; ghi credit khi giấy phép yêu cầu.
- Che API key và `account_id` khi hiển thị cho người khác; không commit `settings.json`.
