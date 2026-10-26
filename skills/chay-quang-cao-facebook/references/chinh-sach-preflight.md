# Chính sách, kiểm tra trước chạy, theo dõi thay đổi của Meta

## Rà chính sách (xuyên suốt, không chỉ trước khi bật)

**Khi nào:** ngay khi nhận sản phẩm nhạy cảm (sức khoẻ, giảm cân, thuốc, mỹ phẩm chức năng, tài chính, tín dụng, việc làm, nhà ở, chính trị, cờ bạc…); trước khi tạo ad; khi sửa nội dung/đích; khi bị từ chối hoặc hạn chế.

**Rà gì:** caption, chữ trong ảnh, lời thoại, phụ đề, hình/video, landing page, form và hành trình sau click. Đối chiếu: claim gây hiểu lầm, chữa bệnh, trước/sau phóng đại, **thuộc tính cá nhân** ("bạn đang bị…", nhắm tình trạng sức khoẻ/tài chính), sản phẩm hạn chế, quyền dùng tài sản. Danh mục đặc biệt (nhà ở, việc làm, tín dụng, chính trị) phải khai `special_ad_categories` và chịu giới hạn tệp.

**Phân biệt theo thông báo thật:** từ chối ad | hạn chế tài khoản / Page / business | sự cố bảo mật / thanh toán. Chưa có thông báo thì không đoán nguyên nhân. Lý do từ chối: `ad_review_feedback` (BM) hoặc `GET /v1/ads/{adId}/review` (Zernio).

**Đầu ra:** nội dung bị ảnh hưởng | điều khoản/URL | bằng chứng | rủi ro | cách sửa | trạng thái.

**Quy tắc:** không hứa duyệt / không khoá; không che giấu nội dung, không cloaking, không né hạn chế; danh sách từ cấm không đủ thay rà soát.

Nguồn: Tiêu chuẩn quảng cáo `https://transparency.meta.com/policies/ad-standards/` · Tiêu chuẩn cộng đồng `https://transparency.meta.com/policies/community-standards/` · Business Help Center `https://www.facebook.com/business/help/` · Newsroom `https://about.fb.com/news/`. Trang bị chặn / đòi đăng nhập / 429 → ghi "chưa xác minh" kèm ngày.

## Checklist trước khi bàn giao (Gate 2)

Mỗi dòng ghi **Đã kiểm tra / Cần sửa / Chưa kiểm tra / Không áp dụng** + bằng chứng. Chưa kiểm tra thì không đánh dấu đạt.

| Hạng mục | Kiểm |
|---|---|
| Chính sách | Sản phẩm, nội dung, đích (mục trên) |
| Tài khoản | ACTIVE, có phương thức thanh toán, đúng tài khoản có pixel nếu cần |
| Quyền | Token/kết nối có quyền với tài khoản, Page, pixel; app Live (đường BM) |
| Ngân sách | Đúng mức, đúng cấp (CBO **hoặc** ABO), đúng đơn vị tiền, trong hạn mức |
| Lịch / múi giờ | Khớp giờ trực, lịch live; múi giờ tài khoản |
| Địa lý | Đã đặt quốc gia/vùng (Zernio mặc định US nếu bỏ trống) |
| Đích | Web chạy trên điện thoại, đặt hàng / gửi form / mở chat được thật |
| Tracking | Sự kiện bắn đúng hành động, không trùng Pixel/CAPI, không có dữ liệu cá nhân trong URL/sự kiện |
| Offer | Giá, quà, ship, điều kiện khớp giữa quảng cáo và đích |
| Vận hành | Tồn kho, người xử lý lead/chat/đơn, SLA |
| Creative | Đúng sản phẩm, chữ đọc được, preview đúng placement |
| Trạng thái | Mọi đối tượng `PAUSED` (Zernio: đã gửi `status: PAUSED`) |

Không đánh dấu "đã xác minh tracking" chỉ vì điểm đối sánh sự kiện cao. Chỉ yêu cầu xác minh tên miền / thứ tự sự kiện khi tài khoản thật sự cần.

## Theo dõi thay đổi của Meta

- Kiểm nguồn chính thức theo lịch (gợi ý hằng tuần) và trước quyết định cần thông tin mới; so với **mốc cơ sở** đã lưu.
- Phân loại: chính sách bắt buộc | tính năng/cấu hình | phân phối đã công bố | giả thuyết cần test. Ghi ngày công bố / hiệu lực, phạm vi, phần skill bị ảnh hưởng.
- Không lấy ngày quét làm ngày thay đổi. Nguồn không truy cập được → "chưa xác minh", không kết luận "không có thay đổi".
- Chỉ báo thay đổi thật. **Không tự đổi ngân sách hay bật quảng cáo vì tin mới.** Cập nhật skill sau khi người dùng xác nhận.
- Nhận biết phiên bản API: lỗi `2635` = phiên bản Graph đã bị bỏ.
