# Đo lường và báo cáo

## Quy ước dữ liệu

- Ghi kỳ (bắt đầu/kết thúc), ngày trích xuất, múi giờ, tiền tệ, thuế/phí ads đã gồm chưa, cửa sổ attribution, nguồn và độ trễ.
- **Ghi rõ tài khoản quảng cáo** của mọi con số. Token thường thấy nhiều tài khoản; trả lời "không có camp nào chạy" khi chưa quét hết là sai.
- Tách nguồn: Ads Manager, web analytics, CRM/telesale, giao vận. Không gộp nguồn rồi cộng trùng chuyển đổi.
- Khoá là `campaign_id / adset_id / ad_id / post_id`; tên chỉ để hiển thị.
- Khử trùng lead/chat/đơn; một khách có thể nhiều đơn, không đồng nhất khách và đơn.
- So cohort có thời gian theo dõi bằng nhau. Đơn COD chưa giao = **đang xử lý**. Tách huỷ trước gửi, giao thất bại, hoàn sau giao, hoàn tiền; công bố mẫu số mỗi tỷ lệ.
- **Không cộng reach** giữa các dòng. **Không lấy trung bình** CTR/CPA/ROAS giữa các dòng: tính lại từ tổng tử số và tổng mẫu số. **Không cộng** số liệu ở cả ba cấp.
- Thiếu cột hoặc mẫu số 0 → `N/A`, không ghi CPA = 0. Không trộn link clicks, outbound clicks, clicks (all).
- Không có số liệu thì xuất mẫu với `N/A`; không điền số minh hoạ như số thật.

## Bẫy đếm trùng `action_type`

Meta trả **cùng một sự kiện dưới nhiều khoá có giá trị bằng nhau**, ví dụ đăng ký: `offsite_conversion.fb_pixel_complete_registration`, `complete_registration`, `omni_complete_registration`, `offsite_complete_registration_add_meta_leads`… Cộng các khoá = nhân số lên nhiều lần.

- Chỉ lấy **một** khoá: ưu tiên `offsite_conversion.fb_pixel_<sự kiện>`, rồi `omni_<sự kiện>`. Lead form: `onsite_conversion.lead_grouped`. Tin nhắn: `onsite_conversion.messaging_conversation_started_7d`. Tương tác bài: `post_engagement`.
- `report` trong script tự chọn theo `optimization_goal` của ad set (cấp campaign Meta có thể trả "Unknown" → đoán theo objective), in `result_key` đã dùng và các khoá trùng đã bỏ. Chỉ định tay bằng `--result` hoặc `--action`.
- Kiểm chéo: tổng cấp ad ≈ cấp ad set ≈ cấp campaign. Cấp trên gấp đôi cấp dưới = đang cộng trùng.
- Số **tổng** (aggregate) và cộng chuỗi **theo ngày** (`time_increment=1`) lệch nhau 1–2 đơn vị tương tác là bình thường. Khi bảng, biểu đồ và bìa báo cáo cần khớp nhau, cộng chuỗi ngày cho spend/impressions/clicks/kết quả; riêng `reach` lấy từ aggregate vì không cộng dồn được.

## Công thức

| Chỉ số | Công thức |
|---|---|
| CPM | Spend / impressions × 1.000 |
| Frequency | Impressions / reach cùng phạm vi |
| Link CTR | Link clicks / impressions × 100% |
| Link CPC | Spend / link clicks |
| Cost/LPV | Spend / landing page views |
| CVR web | Lead hoặc Purchase / LPV × 100% (ghi sự kiện và nguồn) |
| CPL | Spend / lead Meta |
| CPL hợp lệ | Spend / lead hợp lệ duy nhất |
| CPQL | Spend / qualified lead duy nhất |
| Form completion | Submit / form opens cùng nguồn × 100% |
| Cost/conversation | Spend / conversations started |
| CPE | Spend / post engagements |
| CPA đặt/chốt/giao | Spend / số đơn ở trạng thái tương ứng (ghi rõ trạng thái) |
| Tỷ lệ chốt | Đơn chốt / lead duy nhất (nếu mỗi lead tối đa 1 đơn) |
| Tỷ lệ giao | Đơn giao thành công / đơn chốt cùng cohort |
| ROAS Meta | Giá trị Purchase Meta quy gán / spend |
| ROAS thực thu | Doanh thu thực thu quy gán (phương pháp công bố) / chi phí ads cùng phạm vi |
| MER | Tổng doanh thu / tổng chi marketing (không gọi là ROAS) |
| Đóng góp sau ads | Thực thu ròng − chi phí biến đổi thực tế − chi phí ads đầy đủ |

**Thực thu ròng** = tiền thu sau giảm giá/hoàn tiền (không trừ hoàn hai lần). **Chi phí biến đổi** = giá vốn, quà, đóng gói, ship đi/hoàn, phí thanh toán, vận hành biến đổi, kể cả đơn thất bại. Hàng hoàn nhập kho tính theo tổn thất thật, không mặc định mất toàn giá vốn. Chưa trừ chi phí cố định và thuế thì chỉ gọi **đóng góp sau ads**, không gọi lợi nhuận ròng.

## KPI từ kinh tế đơn hàng

- **CPL hoà vốn** = đóng góp kỳ vọng trước ads trên một lead (tổng thực thu ròng kỳ vọng của cohort − toàn bộ chi phí biến đổi kỳ vọng, chia số lead). **CPL mục tiêu** = CPL hoà vốn − đóng góp sau ads mong muốn trên lead.
- Trường hợp đơn giản (mỗi lead tối đa 1 đơn): `CPL hoà vốn ≈ q × d × M`, với `q` tỷ lệ chốt, `d` tỷ lệ giao, `M` đóng góp trước ads mỗi đơn giao **đã phân bổ** chi phí đơn huỷ/hoàn.
- **CPA giao hoà vốn** = đóng góp trước ads trên đơn giao (đã phân bổ chi phí thất bại). **ROAS hoà vốn** = 1 / tỷ lệ đóng góp trước ads, chỉ khi biên đã gồm mọi chi phí biến đổi.
- Tương tác / người xem phục vụ nhận biết: dùng KPI nội dung đã thống nhất; chưa nối doanh thu thì không đặt CPL hoà vốn.
- Không dùng CPL/CPA "chuẩn thị trường Việt Nam" khi không có dữ liệu tương đương và nguồn rõ.

Ví dụ kiểm logic (giả định): spend 2.500.000₫, CPL 110.000₫ → ~22,73 lead **kỳ vọng**; chốt 70%, giao 92% → ~15,91 đơn chốt, ~14,64 đơn giao; CPA giao kỳ vọng ~170.807₫. Chưa có biên đóng góp thì chưa kết luận lãi. Báo số thật dùng số nguyên từ CRM.

## Dữ liệu không có trong API (phải hỏi người dùng/CRM)

Kinh tế đơn hàng (giá vốn, quà, ship, hoàn/huỷ, phí thanh toán), kết quả kinh doanh cuối (chốt, giao, thực thu), chất lượng lead/chat (hợp lệ, liên hệ được, qualified, SLA), tồn kho, năng lực xử lý. Ghi nguồn và ngày trích xuất. Không suy diễn từ số Meta.

## Mẫu báo cáo ba cấp

**Chiến dịch**

| ID/tên | Mục tiêu/sự kiện | Ngân sách | Spend | Kết quả Meta | Cost/result | Kết quả kinh doanh | KPI mục tiêu | Quyết định |
|---|---|---:|---:|---:|---:|---|---|---|

**Nhóm quảng cáo**

| ID/tên | Tệp/placement/lịch | Delivery | Spend | CPM | Frequency | Kết quả/CPA | Chất lượng downstream | Hành động |
|---|---|---|---:|---:|---:|---|---|---|

**Quảng cáo**

| ID/post | Angle/Hook/Format/Offer | Spend | Kết quả/CPA | CTR/CPC đúng loại | Video | CPQL/CPA giao | Kết luận |
|---|---|---:|---|---|---|---|---|

**Funnel và việc tiếp theo:** số và tỷ lệ từng bước kèm mẫu số, nguồn, cohort, số đang xử lý. Kết luận dạng **quan sát → giả thuyết → kiểm tra cần làm → thay đổi → tiêu chí đánh giá lại**, ghi mức chắc chắn. Mẫu ít không phải thắng chắc; phân biệt biến động ngẫu nhiên, attribution trễ và lỗi tracking.

**Hành động:** ưu tiên | cấp tác động | bằng chứng | thay đổi | ngân sách ảnh hưởng | điều kiện đánh giá lại / hoàn tác.

## Chẩn đoán có điều kiện

- **CPM cao:** tệp, placement, cạnh tranh, chất lượng; không kết luận "thị trường" chỉ từ CPM.
- **CTR/CPC xấu:** angle, hook, format, offer, đúng loại click, độ khớp điểm đến.
- **Click tốt, LPV thấp:** tốc độ, lỗi trang, tracking.
- **LPV tốt, chuyển đổi thấp:** offer, form, checkout, niềm tin, mobile, đo lường.
- **Lead/chat rẻ, ít đơn:** chất lượng, trùng, SLA, kịch bản chốt, giá/ship, tồn kho.
- **Chốt cao, giao thấp:** xác nhận, địa bàn, vận chuyển, COD; không tăng ngân sách theo CPA Meta.
- **Frequency tăng, hiệu quả giảm:** mỏi nội dung hoặc bão hoà; frequency một mình không đủ để dừng.
- Kiểm lỗi và pacing sớm; đánh giá CPA khi đủ chi tiêu, kết quả và độ trễ. Không cứng "24 giờ", "3 ngày", "CTR 2%" cho mọi ngành. Ngân sách ngày của Meta là **trung bình linh hoạt** (có ngày chi vượt, ngày chi thiếu): đánh giá theo trung bình nhiều ngày.

## Cảnh báo tự động (`watch`)

`watch` quét **mọi tài khoản** trong `settings.json > meta.ad_accounts`, bỏ qua tài khoản không có camp chạy, và báo khi:

- Chi hôm nay vượt ngân sách ngày hơn `alerts.overspend_pct`.
- Camp ACTIVE mà 0 hiển thị sau `alerts.no_delivery_after_hour` (giờ tài khoản).
- Tiêu chậm sau `alerts.slow_after_hour` (dưới `slow_spend_pct`% ngân sách).
- Theo objective (`alerts.thresholds.<OBJECTIVE>`): chi phí/kết quả, CPC link, CTR link vượt ngưỡng; đã chi ≥ ngưỡng chi phí/kết quả mà 0 kết quả. Chỉ xét khi chi ≥ `min_spend_to_judge`.
- Tài khoản có camp chạy nhưng không ACTIVE hoặc chưa có phương thức thanh toán.

Ngưỡng là **cấu hình của dự án**, đặt từ KPI và kinh tế đơn hàng; ví dụ trong `settings.example.json` để `null` (tắt). Cron gợi ý: `watch --mode alert` vài giờ một lần (im lặng khi ổn) và `watch --mode digest` cuối ngày. Server chạy UTC thì đổi giờ khi đặt cron (VN = UTC+7).
