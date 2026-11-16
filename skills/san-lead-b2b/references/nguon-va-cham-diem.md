# Nguồn, cách đọc tin và chấm điểm

## Nguồn

| Nguồn | Cách lấy | Tiền | Ghi chú |
| --- | --- | --- | --- |
| Google News | RSS `news.google.com/rss/search`, 3 truy vấn × mỗi ngành (khởi công / cấp phép / mở rộng), `when:<n>d` | 0 | Chỉ có tiêu đề + tên báo. Tin được giữ thì script tìm **bài gốc** (`site:<báo> "<tiêu đề>"`) và đọc lại toàn văn. |
| Trang theo dõi | Đọc trang danh sách, lấy link mới có từ khoá phù hợp | 0 | Sẵn: ĐTM Cà Mau, Khánh Hòa; thông báo DHG Pharma, Bidiphar (bỏ ĐTM Đà Nẵng: trang đó là kho lưu trữ cũ). Thêm ở Cài đặt. |
| Google (Apify `apify~google-search-scraper`) | 18 truy vấn / lần, quay vòng nhóm thiết bị, ngành, tỉnh | ~$0.0045 / truy vấn | Thư mời chào giá theo nhóm thiết bị; khởi công / cấp phép / mở rộng / ĐTM theo ngành × tỉnh (tên cũ và mới); tuyển BQLDA nhà máy mới; `site:` trang đấu thầu (dauthau.asia, bidwinner.info), cổng ĐTM chặn IP nước ngoài, trang mời thầu doanh nghiệp. |
| LinkedIn X-ray | Google `site:linkedin.com/in "<công ty>" (Giám đốc OR Manager ...)` | ~$0.0045 / công ty | Người ở đúng công ty có cơ hội điểm cao. |
| LinkedIn (Apify `harvestapi~linkedin-profile-search`, không cookie) | Tìm theo tên công ty (cơ hội điểm cao nhất khi X-ray ít kết quả) và theo chức danh × ngành ở Việt Nam (mỗi tuần 1 lần) | $0.10 / 25 hồ sơ | Không dùng tài khoản LinkedIn của sale. |

**Không dùng:** cào trực tiếp muasamcong.mof.gov.vn (trang tìm kiếm cần token chống bot); vượt tường lửa của cổng tỉnh
chặn IP nước ngoài (Cần Thơ, Tây Ninh, Lâm Đồng... chặn máy chủ ở Singapore) — đọc qua Google `site:` thay vì vào thẳng.

Muasamcong không được Google lập chỉ mục tốt; gói thầu nhà nước lấy qua các trang tổng hợp (dauthau.asia, bidwinner.info)
và tin báo. Muốn đủ gói thầu nhà nước thì cần dịch vụ có API (DauThau.info bản trả phí) — chưa tích hợp.

## Tỉnh sau sáp nhập (1/7/2025)

Cơ hội xếp theo tỉnh mới; tên cũ trong nguồn giữ ở `province_old` và tìm được. Vùng mặc định (Đà Nẵng trở vào):
Đà Nẵng (+Quảng Nam), Quảng Ngãi (+Kon Tum), Gia Lai (+Bình Định), Đắk Lắk (+Phú Yên), Khánh Hòa (+Ninh Thuận),
Lâm Đồng (+Đắk Nông, Bình Thuận), TP. Hồ Chí Minh (+Bình Dương, Bà Rịa - Vũng Tàu), Đồng Nai (+Bình Phước),
Tây Ninh (+Long An), Đồng Tháp (+Tiền Giang), Vĩnh Long (+Bến Tre, Trà Vinh), Cần Thơ (+Sóc Trăng, Hậu Giang),
Cà Mau (+Bạc Liêu), An Giang (+Kiên Giang). Prompt đọc tin luôn kèm tên cũ, nếu không model loại nhầm (VD dự án ở
Bình Định bị coi là ngoài vùng).

## Đọc tin (LLM)

- Model: model của Hermes (Cài đặt → Model đọc tin để đổi). Gọi với `reasoning: {enabled: false}`: model suy luận trước
  thì ăn hết token và trả JSON cụt.
- Model dự phòng: `LEAD_LLM_MODELS="model1,model2"`. Model đang dùng hết tiền (402) hoặc hết lượt (429) thì tự
  chuyển sang model sau; hết cả danh sách thì dừng gọi LLM và Apify, tin chưa đọc để lần sau.
- Lô 6 tin, đọc lần lượt từng lô (`LEAD_LLM_WORKERS`, mặc định 1: cổng LLM giữ tiền theo từng request, ví ít tiền mà chạy song song thì bị 402). JSON lỗi hoặc hết token: chia đôi lô, đọc lại. Tin model bỏ sót: không đánh dấu đã đọc, lần
  sau đọc lại. Lỗi 402 (ví hết tiền): dừng mọi lượt gọi LLM còn lại, ghi rõ vào lần quét.
- Giữ khi: 1 doanh nghiệp / chủ đầu tư cụ thể ở Việt Nam, thuộc 7 ngành, và có tín hiệu mua: mời thầu / chào giá
  **thiết bị**; dự án nhà máy mới (cấp phép, ĐTM, động thổ, khởi công); mở rộng / nâng cấp; tín hiệu khác (tuyển BQLDA,
  phê duyệt ĐTM).
- Loại: quảng cáo nhà cung cấp; tin thị trường; nhà máy nước ngoài; mời thầu dịch vụ (du lịch, sự kiện, truyền thông,
  vé máy bay, thuê xe, phần mềm...); thiết bị y tế bệnh viện; ngành ngoài 7 ngành; đã khánh thành mà không có giai đoạn
  sau; trang "dự án đã thực hiện" của nhà thầu / đơn vị thiết kế; chuyển nhượng nhà máy; ngoài vùng.

## Trang Săn lead kiểm lại (agent không qua mặt được)

Không nhận cơ hội: thiếu tên doanh nghiệp cụ thể; ngành ngoài 7 ngành hoặc đang tắt; loại đang tắt; không có link
nguồn; tỉnh không nhận ra hoặc ngoài vùng; mời thầu thiếu tên gói hoặc đã hết hạn; hạn chót không đọc được; tin cũ hơn
"Bỏ tin cũ hơn (ngày)" (trừ mời thầu còn hạn). Người liên hệ: thiếu tên, chức danh, công ty, hoặc link không phải hồ sơ.

Gộp trùng: cùng công ty (tên đầy đủ / tên ngắn, VD "BAF" và "Công ty TNHH Chế biến Thực phẩm BAF Bình Định"), cùng
tỉnh, cùng nhóm (dự án / mời thầu; mời thầu thêm tên gói). Gộp thì thêm link nguồn, giữ trạng thái và ghi chú của sale.

## Điểm 0–100

| Phần | Điểm |
| --- | --- |
| Mời thầu còn hạn / mời thầu không rõ hạn | 35 / 26 |
| Dự án mới / mở rộng / tín hiệu khác | 30 / 25 / 15 |
| Ngành ưu tiên / ngành theo dõi | 15 / 8 |
| Trong vùng | 10 |
| Tin trong 14 ngày / 45 ngày / chưa rõ ngày | 15 / 8 / 4 |
| Thiết bị khớp "Hàng bên bán" (nguồn ghi / gợi ý) | 15 / 8 |
| Có người / đầu mối liên hệ | 10 |

Tìm người cho cơ hội từ "Chỉ tìm người cho cơ hội từ điểm" (mặc định 55), tối đa "Số người mỗi cơ hội" (mặc định 4).
