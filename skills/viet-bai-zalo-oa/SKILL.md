---
name: viet-bai-zalo-oa
description: Viết bài Zalo OA, tạo bài ẩn để chủ OA duyệt và hiện.
version: 0.1.0
author: Agoobi
license: MIT
metadata:
  hermes:
    category: coquifly
    tags: [zalo, zalo-oa, bai-viet, vietnamese]
---

# viet-bai-zalo-oa

Viết bài (article) cho **Zalo Official Account** theo các "cổng" (gate) để user duyệt từng bước, hỗ trợ **nhiều OA**, rồi tạo bài qua Zalo OA API ở trạng thái **ẨN** và gửi link để chủ OA tự kiểm tra, bật hiển thị hoặc gửi broadcast.

## Quy tắc sắt

1. **Agent KHÔNG hiện bài, KHÔNG gửi broadcast, KHÔNG xóa bài.** Script luôn gửi `status: hide`, không có lệnh đăng/xóa.
2. Mỗi Gate phải **dừng và chờ user trả lời**. Không gộp gate, không đoán thông tin thiếu.
3. Không bịa số liệu, giá, khuyến mãi, thời hạn, đánh giá khách hàng.
4. Không in App Secret, access token, refresh token ra chat. Không commit `settings.json`.
5. Không sửa bài đang hiển thị (script từ chối).

## Cài đặt (một lần)

Mọi lệnh chạy bằng `python -I scripts/zalooa.py <lệnh>` từ thư mục skill (chỉ cần Python 3). Cần env `ZALO_APP_ID`, `ZALO_APP_SECRET` (app trên developers.zalo.me mà admin quản lý).

1. App Zalo: mục **Official Account** khai báo callback URL là một trang bất kỳ của mình (vd trang chủ website `https://shop.vn/`) và bật quyền **quản lý bài viết**.
2. Kết nối OA, chọn một trong hai cách:
   - **Có sẵn token** (admin lấy ở developers.zalo.me → Công cụ → API Explorer, loại *OA access token*): đặt env `ZALO_ACCESS_TOKEN`, `ZALO_REFRESH_TOKEN` rồi chạy `connect-import`. Script tự đọc `oa_id` và tên OA. Không dán token vào tham số dòng lệnh.
   - **OAuth**: `connect --redirect <callback URL>` → gửi link cho **chủ OA** (tài khoản Zalo có quyền admin OA) bấm Đồng ý. Zalo chuyển về callback URL kèm `?code=...&oa_id=...`; chủ OA copy nguyên URL trên thanh địa chỉ gửi lại → `connect-finish "<URL>"`. Link hết hạn sau 30 phút.
3. Copy `settings.example.json` thành `settings.json`, điền `oa_id` (bước 2 in ra), giọng văn, tác giả. Xem `references/viet-bai.md`.
   Muốn user gửi ảnh trên máy: điền `image_host` = một thư mục mà web server của shop phục vụ công khai qua https (`dir`) và URL tương ứng (`url`), vd Caddy `file_server` trên VPS chạy Hermes. Zalo chép ảnh sang máy chủ của Zalo ngay khi tạo bài, nên thư mục chỉ cần truy cập được lúc tạo/sửa bài. Không dùng dịch vụ lưu ảnh công khai của bên thứ ba.
4. `check --oa <alias>`: kiểm tra token, tên OA, quyền đọc bài viết.

`settings.json` **không** chứa token. Token lưu ở `~/.hermes/zalo/tokens.json` (`$ZALO_TOKEN_FILE`, quyền 600, có khóa file), tự làm mới trước khi hết hạn. Access token sống khoảng 24 giờ; refresh token **chỉ dùng được 1 lần** (mỗi lần làm mới Zalo trả cặp mới, cặp cũ chết), nên không dùng cùng refresh token ở nơi khác sau khi đã nạp vào skill. Refresh token hết hạn sau khoảng 3 tháng không dùng; khi đó kết nối lại (bước 2).

## Quy trình (các Gate)

Bắt đầu: `oas`. OA nào `ket_noi: CHUA` → làm phần Cài đặt rồi dừng.

**Gate 1 — Chọn OA.** Liệt kê OA (label + alias). Chỉ 1 OA thì xác nhận nhanh.

**Gate 2 — Nội dung.** Hỏi gọn trong 1 lượt: chủ đề, mục tiêu (ưu đãi, tin tức, hướng dẫn, chăm sóc khách), thông tin thật (sản phẩm, giá, ưu đãi, thời hạn, điều kiện), CTA, độ dài. Thiếu thì hỏi lại.

**Gate 3 — Ảnh.** Bài bắt buộc có **1 ảnh bìa**; ảnh trong bài tùy chọn. Hỏi user chọn cho từng loại:
- **A. User đưa URL https** trả thẳng file ảnh.
- **B. User đưa file trên máy** (jpg/png/webp/gif). Script tự chép vào `image_host` (thư mục web của shop, xem Cài đặt) rồi dùng URL đó. Chưa có `image_host` → upload lên website bằng skill `viet-bai-website-wordpress` (`upload`) lấy `url`, hoặc nhờ admin cấu hình `image_host`.
- **C. Agent tạo ảnh** bằng công cụ có sẵn trong môi trường (nếu có): viết prompt, user duyệt trước khi tạo, rồi dùng như B. Không có công cụ → nói rõ, quay về A/B.
- **D. Không có ảnh trong bài** (ảnh bìa vẫn bắt buộc).

Mỗi ảnh **≤ 1 MB** (lớn hơn: Zalo nhận lệnh nhưng lỗi khi xử lý). Ảnh trong bài: dòng riêng `![chú thích](URL hoặc file)` trong file nội dung. Một số host bị Zalo từ chối (đã gặp Wikimedia, Picsum); ảnh trên website của shop hoặc Unsplash thì nhận. Không dùng ảnh không rõ bản quyền. User xác nhận ảnh cuối cùng.

**Gate 4 — Bản nháp.** Viết **1-2 phương án** theo `references/viet-bai.md` và cấu hình OA (`brand_voice`, `audience`, `default_cta`, `avoid`, `length`); mỗi phương án kèm mô tả ngắn (≤ 300 ký tự, hiện ở danh sách bài và khi chia sẻ). Bài tạo qua API **chỉ có chữ thô**: không đậm, nghiêng, link bấm được; nhấn mạnh bằng cách tách đoạn, emoji, tiêu đề mục. Hiển thị nguyên văn, hỏi: chọn phương án nào? sửa gì? Lặp đến khi user nói "ok", rồi lưu bản chốt vào `drafts/<ten>.md` (dòng đầu `# Tiêu đề`, tối đa 150 ký tự).

**Gate 5 — Duyệt cuối.** Chạy `validate` (cùng tham số với `draft`; không gửi gì lên Zalo): kiểm độ dài, tải thử từng ảnh (có phải ảnh, ≤ 1 MB, có chuyển hướng không) và in `preview` đúng như bài sẽ hiện. Có `errors` → sửa rồi chạy lại; có `warnings` → báo user. Gửi user preview kèm: OA, tiêu đề, mô tả, tác giả, ảnh bìa, bình luận bật/tắt, trạng thái **ẨN**. Hỏi: "Tạo bài (ẩn) trên Zalo OA nhé?" Chỉ chạy `draft` khi user đồng ý.

**Bàn giao.**

```
python -I scripts/zalooa.py draft --oa <alias> --content-file drafts/<ten>.md --cover <URL https | file> \
  --description "<mô tả ngắn>" [--author "<tác giả>"] [--comment show|hide]
```

Script kiểm ảnh lại (lỗi thì dừng, chưa gửi gì), chép ảnh trên máy vào `image_host`, tạo bài (`article/create`), chờ Zalo xử lý xong (`POST article/verify`), rồi **đọc lại bài và chỉ báo thành công khi Zalo xác nhận `status: hide`**. Gửi user: tiêu đề, `id`, trạng thái ẩn, trang quản lý `https://oa.zalo.me` → Bài viết. Nhắc: "Bạn mở trang quản lý bài viết của OA, xem trước, rồi bật Hiển thị hoặc gửi bài cho người quan tâm."

## Sửa bài đã tạo

```
python -I scripts/zalooa.py update <id> --oa <alias> [--title ...] [--content-file ...] [--description ...] [--cover ...] [--author ...]
```

Chỉ bài tạo bằng skill này (script lưu bản đã gửi ở `drafts/<alias>-<id>.json` vì API sửa cần gửi lại đủ trường) và đang ẩn. Bài khác hoặc đang hiện → hướng dẫn user sửa trên oa.zalo.me. Hiển thị bản sửa cho user duyệt trước khi chạy.

Xem lại: `list`, `detail <id>`.

## Xử lý lỗi

- `-216` / `-124`: token sai, hết hạn → script tự làm mới 1 lần; vẫn lỗi thì chạy lại `connect`.
- `-230`: OA chưa cấp quyền cho app → `connect` lại, nhắc chủ OA bật quyền bài viết.
- `-201`: tham số sai (tiêu đề / mô tả quá dài, ảnh bìa không tải được hoặc host bị Zalo từ chối → thử URL ảnh khác).
- `-200 Upload media failed` lúc verify: ảnh > 1 MB hoặc Zalo không tải được ảnh. Chạy `validate`, thu nhỏ ảnh.
- Tạo xong mà chưa có `id` (Zalo xử lý chậm): chờ vài phút rồi `list`, không tạo lại để tránh trùng bài.
- Lỗi khác: báo nguyên văn, không nói đã tạo bài khi chưa có `id`.
