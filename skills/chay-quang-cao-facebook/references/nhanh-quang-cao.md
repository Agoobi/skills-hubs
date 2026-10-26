# Sáu nhánh quảng cáo

Sáu nhánh là **nghiệp vụ**, không phải sáu objective của Meta. Với mỗi nhánh ghi rõ: mục tiêu kinh doanh | objective Meta | vị trí chuyển đổi | mục tiêu hiệu suất | sự kiện đích | KPI chính | KPI kinh doanh cuối. Tham số API cụ thể: `thuc-thi-bm-api.md` / `thuc-thi-zernio.md`.

## Quy tắc chung mọi nhánh

- Tiếng Việt, ngân sách VND, xác nhận múi giờ tài khoản (mặc định `Asia/Ho_Chi_Minh`).
- Làm theo chiến dịch → nhóm → quảng cáo. Tách campaign khi khác mục tiêu, sự kiện đích, thị trường hoặc cách vận hành; không tách theo từng sở thích.
- CBO hay ABO phải có lý do; không nói CBO luôn tốt hơn. Ngân sách nhỏ thì cấu trúc gọn, không ép lạnh–ấm–nóng.
- Tệp: rộng trong địa bàn phục vụ, sở thích có giả thuyết, custom/lookalike khi đủ dữ liệu, remarketing khi đủ lượng và có mục đích. Ghi rõ đâu là ràng buộc, đâu là gợi ý Advantage+. Người dùng chỉ muốn Facebook thì không tự thêm Instagram.
- Test tệp thì giữ offer/creative tương đương; test creative thì giữ tệp/offer tương đương. Ghi nhiễu do phân phối không đều.
- Không đặt bid cap / cost cap tuỳ tiện khi thiếu dữ liệu.
- Rà chính sách cả creative và đích (`chinh-sach-preflight.md`). Không hứa duyệt / không khoá.
- Đầu ra theo thứ tự: mục tiêu & giả định → chiến dịch → nhóm → quảng cáo → checklist → báo cáo → hành động → dữ liệu bàn giao. Mỗi chẩn đoán trỏ về đúng chỗ cần sửa: offer, creative, thiết lập, tracking hay bán hàng.

## 01 — Bán hàng trực tiếp trên website (`web-sales`)

**Dùng khi** khách chọn và đặt mua trên web (online hoặc COD). Web chỉ thu thông tin để gọi chốt → `web-leads`.

**Đầu vào riêng:** sản phẩm/biến thể/tồn kho/địa bàn giao; offer, ship, quà; kinh tế đơn (giá vốn, chi phí biến đổi, hoàn/huỷ); pixel/dataset, CAPI, sự kiện Purchase, UTM, hệ thống đơn.

**Điều kiện trước khi chạy:** web chạy tốt trên điện thoại, đặt hàng được thật, giá/offer/ship khớp quảng cáo, Purchase bắn đúng một lần (khử trùng Pixel/CAPI bằng `event_id`), tồn kho và người xử lý đơn sẵn sàng. Với COD, Purchase = đơn đặt, **không phải tiền đã thu**.

**Campaign:** Sales, vị trí chuyển đổi website. Tên `VN_WEB-SALES_[sản phẩm]_[test/scale]_[ngày]`. KPI từ kinh tế đơn hàng (số đơn, CPA, đóng góp sau ads).
**Ad set:** dataset + Purchase đúng, địa bàn giao được, tệp có căn cứ.
**Ad:** dẫn đúng trang sản phẩm/mua; UTM không chứa thông tin cá nhân.

**Báo cáo:** campaign (spend, Purchase, CPA, ROAS Meta, + đơn giao, thực thu, đóng góp sau ads nếu đối soát được) · ad set (spend, impressions, reach, CPM, frequency, Purchase, CPA) · ad (CTR/CPC đúng loại, LPV, Purchase, CPA, gắn với Angle/Hook/Offer/Format). Funnel: hiển thị → click → LPV → mua → xác nhận → giao/thu tiền.

**Chẩn đoán:** CTR thấp → angle/hook/format/offer · click có, LPV thấp → tốc độ/tracking · LPV có, ít mua → offer/checkout/niềm tin/mobile · Purchase nhiều, đơn hợp lệ ít → sự kiện trùng/sai, đơn rác · CPA tốt nhưng giao thấp → COD/ship/xác nhận, sửa vận hành trước khi scale · frequency tăng + hiệu quả giảm → mỏi nội dung, làm mới.

## 02 — Lead trên website (`web-leads`)

**Dùng khi** khách điền form trên web rồi được tư vấn/telesale. Không gọi Lead là Purchase.

**Đầu vào riêng:** URL landing/form, định nghĩa lead hợp lệ/qualified, sự kiện Lead, CRM, chống trùng, kịch bản + SLA gọi lại.

**Campaign:** Leads với website. KPI: CPL hợp lệ, CPQL và kết quả cuối, không chỉ CPL.
**Ad set:** dataset + Lead đúng hành động (không bắn mỗi lần tải trang); lịch và ngân sách khớp sức nhận lead của đội.
**Ad:** nêu điều kiện/giá khi cần lọc khách; CTA đăng ký/nhận tư vấn khớp hành động thật; form có câu hỏi sàng lọc vừa đủ.

**Báo cáo:** spend, Lead Meta, CPL, lead hợp lệ, qualified, CPQL, chốt. Funnel: click → LPV → Lead → lead duy nhất → hợp lệ → liên hệ được → qualified → chốt → giao/thu tiền. Tỷ lệ liên hệ = lead liên hệ được / lead duy nhất cùng cohort.

**Chẩn đoán:** click→LPV yếu → trang/tracking · LPV→Lead yếu → offer/form/niềm tin · lead nhiều, liên hệ thấp → chất lượng thông tin/SLA · liên hệ tốt, chốt thấp → nhu cầu/offer/tư vấn.

## 03 — Lead form trong Meta (`lead-form`)

**Dùng khi** khách gửi form ngay trong Meta (Instant Form). Form trên landing → `web-leads`.

**Đầu vào riêng:** Page, form, URL chính sách quyền riêng tư, câu hỏi lọc, CRM, đội gọi, SLA, quyền đọc lead.

**Campaign:** Leads. Không mặc định form càng ngắn càng tốt: chọn loại form (nhiều lượng hay chất lượng cao) theo nhu cầu.
**Ad set:** Instant forms + Page; tối ưu leads (conversion leads chỉ khi có và CRM tích hợp).
**Ad / form:** giới thiệu, thông tin liên hệ tối thiểu, câu hỏi đủ dùng, quyền riêng tư, trang cảm ơn + bước tiếp. Không hỏi dữ liệu nhạy cảm không cần thiết. Submit thử, kiểm tra lead vào CRM.

**Báo cáo:** spend, lead Meta, CPL, lead duy nhất/hợp lệ/qualified, CPQL, completion = submit / form opens (chỉ khi có số opens). **CPL giảm mà CPQL tăng = chất lượng xấu đi**, không scale vì lead rẻ.

## 04 — Tương tác bài viết (`post-engagement`)

**Dùng khi** muốn phân phối bài, tạo thảo luận, social proof. Mục tiêu thật là chat/lead/đơn → chọn nhánh tương ứng. Engagement rẻ **không** chứng minh sức mua.

**Campaign:** Engagement, tối ưu post engagement. Chưa nối doanh thu thì không đặt CPA/CPL hoà vốn.
**Ad:** đúng post ID khi cần gom tương tác. Không comment giả, feedback giả, minigame vi phạm; kiểm chính sách khi có khuyến mãi.

**Báo cáo:** spend, post engagements, CPE, reach; cấp bài: reactions/comments/shares/saves, **comment có nhu cầu** và cảm xúc. Phân loại comment: nhu cầu / xã giao / tiêu cực / spam. Không gộp tương tác organic vào paid nếu không tách được; ghi giới hạn.

## 05 — Tin nhắn (`messages`)

**Dùng khi** khách nhắn để tư vấn/bán. Phân biệt tin nhắn, conversation và khách mới.

**Đầu vào riêng:** Page/app nhắn (Messenger, WhatsApp, IG Direct), giờ trực, lời chào/câu hỏi gợi ý, kịch bản tư vấn, định nghĩa chat qualified, CRM.

**Campaign:** thường Engagement với messaging apps; Leads/Sales chỉ khi tài khoản hỗ trợ và khớp nghiệp vụ. KPI: cost/conversation, cost/chat qualified, chốt.
**Ad set:** lịch chạy trong giờ có người trực; ngân sách không vượt sức trả lời.
**Ad:** CTA nhắn tin, lời chào và câu hỏi giúp khai thác nhu cầu; kịch bản hỏi nhu cầu → tư vấn → giải đáp → chốt → follow-up.

**Báo cáo:** conversations started đúng cột Meta, cost/conversation, chat qualified duy nhất, chốt/giao. Một click/tin nhắn không phải một khách mới.

**Chẩn đoán:** ít chat → offer/creative/tệp · chat rẻ, chất lượng thấp → thông điệp/câu lọc · qualified tốt, chốt kém → tốc độ phản hồi/tư vấn/giá · chốt cao, giao thấp → xác nhận/COD/ship.

## 06 — Livestream (`livestream`)

**Dùng khi** quảng cáo hỗ trợ kéo người xem, tương tác, chat và bán quanh buổi live. Livestream là **nội dung + quy trình bán**, không bịa objective "Livestream"; không nhầm với vị trí in-stream.

**Ba giai đoạn:** trước (mời, lịch hẹn) · trong (view/engagement/chat trên live/post ID) · sau (replay, remarketing, chốt; sửa chữ "đang live"). Ngân sách nhỏ thì không ép đủ ba campaign.

**Giới hạn công cụ:** không có API quảng bá live đang diễn ra; dùng nội dung mời hoặc boost replay theo post ID và ghi rõ điểm đến khác.

**Báo cáo ba nguồn:** Ads Manager (reach, view đúng định nghĩa, ThruPlay, chat) · Page/live (người xem duy nhất nếu có, **peak concurrent = số xem đồng thời cao nhất, không phải tổng người xem**, watch time) · CRM (comment nhu cầu, chat, chốt, thực thu). Quy gán bằng mã offer/UTM/CRM; không lấy toàn doanh thu live chia chi phí ads rồi gọi ROAS.

## Bàn giao dữ liệu sau mọi nhánh

Chuyển cho CRM/telesale/người bán: nguồn (campaign/ad/form/post), thời điểm, trạng thái, định nghĩa chất lượng; dữ liệu cá nhân ở mức tối thiểu. Đối soát thực thu và chi phí trước khi kết luận lợi nhuận.
