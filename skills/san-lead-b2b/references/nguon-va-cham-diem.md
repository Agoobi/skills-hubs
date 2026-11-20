# Nguồn, cách đọc tin và chấm điểm

## Nguồn

| Nguồn | Cách lấy | Tiền | Ghi chú |
| --- | --- | --- | --- |
| Google News (hạn chế) | RSS `news.google.com/rss/search`: 2 truy vấn mời chào giá thiết bị + 1 truy vấn dự án nhà máy mỗi ngành, `when:<n>d` | 0 | Chỉ có tiêu đề + tên báo. Tin được giữ thì script tìm **bài gốc** (`site:<báo> "<tiêu đề>"`) và đọc lại toàn văn. Không đọc trang báo địa phương. |
| Trang theo dõi | Đọc trang danh sách (HTML, RSS), lấy link mới có từ khoá phù hợp; trang mới thêm: lần đầu chỉ đọc 10 link đầu (30 với Báo Đấu thầu) | 0 | ~33 trang: Báo Đấu thầu (thông báo mời thầu, lọc đơn vị thuộc 7 ngành / viện / trường / trung tâm kiểm nghiệm, bỏ bệnh viện, điện, cảng...); BQL KCN / KKT và Xúc tiến đầu tư (Đà Nẵng, Chu Lai, Dung Quất, Gia Lai, Đắk Lắk, Vân Phong, Đồng Nai, Cà Mau, An Giang); mời thầu DHG, Bidiphar, Domesco, Navico; tin Minh Phú, Vĩnh Hoàn, Việt Úc, Masan, GreenFeed; VASEP, Cục Chăn nuôi và Thú y; ĐTM Cà Mau, Khánh Hòa. Thêm ở Cài đặt. `check-sources` để thử. |
| Google (Apify `apify~google-search-scraper`) | 18 truy vấn / lần, 2/3 là mời thầu / chào giá, quay vòng 8 nhóm thiết bị, ngành, tỉnh | ~$0.0045 / truy vấn | Thư mời chào giá / chào giá cạnh tranh / chào hàng cạnh tranh theo nhóm thiết bị; `site:` muasamcong, dauthau.asia, bidwinner.info, baodauthau.vn, thongtindauthau; khởi công / cấp phép / mở rộng / ĐTM theo ngành × tỉnh; `site:` cổng BQL KCN chặn IP nước ngoài hoặc chạy JavaScript (HEPZA, DSEZA, CEPIZA Cần Thơ, Tây Ninh, Đồng Tháp, Vĩnh Long, Lâm Đồng, IPA Khánh Hòa, IPC Quảng Ngãi, Cục Quản lý Dược); tuyển dụng chỉ huy trưởng / ban QLDA nhà máy mới (jobsgo, careerviet, vietnamworks, 123job, topcv, joboko); trang mời thầu doanh nghiệp. |
| Liên hệ doanh nghiệp | 4 truy vấn Google / công ty (`"<tên>" liên hệ điện thoại email`, `"<tên riêng>" mã số thuế`, `"<nguyên tên>"`, `site:linkedin.com/company "<tên>"`); đọc cả trang nhắc đúng tên công ty (thông báo của sở / ban xúc tiến, trang danh sách doanh nghiệp) và theo link sang trang chi tiết, đọc trang chủ + trang liên hệ của công ty và trang tra cứu doanh nghiệp, LLM chỉ ra giá trị nào của đúng công ty, script kiểm giá trị có trong trang | ~$0.014 / công ty | Website, SĐT (nhãn: tổng đài, mua hàng... ; số từ trang tra cứu ghi "đăng ký kinh doanh"), email, địa chỉ, MST, người đại diện, LinkedIn công ty, fanpage. Mỗi lần quét tối đa 10 cơ hội chưa có SĐT / email (điểm cao trước), tìm lại sau 14 ngày. |
| LinkedIn X-ray | Google `site:linkedin.com/in "<công ty>"` (cả có và không có chức danh) + tên đầu mối trong nguồn | ~$0.0045 / truy vấn | Cơ hội từ "Chỉ tìm người từ điểm", cả cơ hội cũ còn thiếu người; mỗi cơ hội tìm lại sau 30 ngày. |
| LinkedIn (Apify `harvestapi~linkedin-profile-search`, không cookie) | Lọc đúng công ty (`currentCompanies` = trang LinkedIn công ty tìm được) + chức danh ra quyết định; không có trang công ty thì tìm theo tên. Tối đa 2 lượt / lần quét. Thêm: theo chức danh × ngành ở Việt Nam (mỗi tuần 1 lần) | $0.10 / 25 hồ sơ | Không dùng tài khoản LinkedIn của sale. Gói Apify miễn phí có giới hạn lượt chạy actor này ("free user run limit reached"): script báo 1 lần trong lần quét và ngừng gọi; người liên hệ khi đó chỉ còn từ Google X-ray. Muốn tìm tiếp trên LinkedIn: nâng gói Apify. |

**Proxy Việt Nam (tuỳ chọn):** nhập ở Săn lead → Cài đặt → Proxy Việt Nam (host:port:user:pass; được kiểm tra, mã hoá,
không hiện lại). Có proxy thì trang `.gov.vn` đi qua proxy trước (BQL KCN Cần Thơ, Tây Ninh, Đồng Tháp, Vĩnh Long, Lâm Đồng,
IPA Khánh Hòa, IPC Quảng Ngãi, Gia Lai, Cục Quản lý Dược chặn máy chủ ở nước ngoài), lỗi thì thử đường thẳng; trang khác lỗi
thì thử lại qua proxy. Dự phòng: env `LEAD_PROXY` hoặc file `state/proxy` (chmod 600). Không có proxy: các cổng đó chỉ đọc
qua Google `site:`.

**Không dùng:** cào trực tiếp muasamcong.mof.gov.vn (trang tìm kiếm cần token chống bot — proxy không thay đổi điều này,
không vượt); captcha, đăng nhập, chống bot của bất kỳ trang nào.

Muasamcong không có dữ liệu mở / RSS / API công khai (kiểm 18/11/2026; QĐ 1090/QĐ-BTC chỉ kết nối cơ quan nhà nước) và
Google lập chỉ mục kém; gói thầu nhà nước lấy qua Báo Đấu thầu (trang theo dõi), các trang tổng hợp (`site:` dauthau.asia,
bidwinner.info, thongtindauthau) và thư mời trên web doanh nghiệp. Không mua API đấu thầu trả phí
(chủ dự án đã quyết 20/11/2026): agent không đề xuất cách này.

## Mời thầu / chào giá: lấy ở đâu

Nơi mua thiết bị, vật tư, sửa chữa phòng thí nghiệm nhiều nhất là **đơn vị công có phòng lab**: trung tâm / viện kiểm nghiệm, trường đại học, viện nghiên cứu, chi cục thú y, trung tâm chất lượng nông lâm thủy sản, Quatest. Họ đăng "thông báo mời chào giá / chào hàng cạnh tranh" ngay trên web của mình (có hạn nộp, danh mục, email nhận báo giá).

- Trang theo dõi loại `lab_buyer` (đọc trực tiếp mỗi lần quét): TT Kiểm nghiệm TP.HCM, Viện Kiểm nghiệm thuốc TP.HCM, ĐH Y Dược TP.HCM, TT Kiểm nghiệm Đà Nẵng. Thêm đơn vị khác ở Cài đặt → Trang theo dõi thêm.
- 8 truy vấn Google cố định mỗi lần quét (`LAB_BUYER_QUERIES`): trung tâm / viện kiểm nghiệm, chi cục thú y, viện / trường + thiết bị thí nghiệm, HPLC / sắc ký / quang phổ / tủ an toàn sinh học, Quatest / chất lượng nông lâm thủy sản, hóa chất / vật tư thí nghiệm, doanh nghiệp 7 ngành.
- Bộ lọc trước LLM giữ mọi tin có từ mời thầu / chào giá + thiết bị / thí nghiệm / hiệu chuẩn / bảo dưỡng (tiêu đề thư mời thường không ghi ngành); bỏ trang danh bạ nhà cung cấp, kết quả lựa chọn nhà thầu, Facebook, và gói tư vấn, quy hoạch, xây lắp, giao thông.
- dauthau.asia chặn máy chủ đọc trang chi tiết: chỉ có tiêu đề + đoạn trích; không có hạn / ngày thì bị loại (đúng luật tin mới). Bệnh viện (thiết bị khám chữa bệnh) không lấy.

Liên hệ của gói thầu: phòng mua sắm / email nhận báo giá ghi trong thư mời (đầu mối), cộng tổng đài / email của đơn vị (bước tìm liên hệ).

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
"Bỏ tin cũ hơn (ngày)" (mặc định 30, trừ mời thầu còn hạn); mời thầu không ghi hạn mà không rõ ngày đăng hoặc đăng quá
14 ngày (tháng trong link file, VD /2025-09/, cũng tính là ngày đăng); bài mới nhưng sự kiện chính (`event_date`: khởi
công, cấp GCN, phê duyệt ĐTM...) đã xảy ra quá "Bỏ tin cũ hơn". LLM cũng loại báo cáo tài chính, bài tổng hợp / phỏng vấn
chỉ nhắc lại việc cũ. Người liên hệ: thiếu tên, chức danh, công ty, link không phải hồ sơ; người đang tìm việc, thực tập,
cựu nhân viên, lao động phổ thông.

Cơ hội đã lưu mà thành cũ (mời thầu quá hạn, tin quá ngưỡng) không bị xoá: trang Săn lead ẩn mặc định (bộ lọc "Còn hạn,
tin mới"), báo cáo, tìm liên hệ và tìm người chỉ xét cơ hội còn mới.

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
