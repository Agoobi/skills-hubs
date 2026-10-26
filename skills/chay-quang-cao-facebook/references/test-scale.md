# Test → Kiểm chứng → Scale

Đây là **SOP thực chiến có thể sửa**, không phải chính sách hay cam kết của Meta. Các con số (30%, 48 giờ, 3 ngày, frequency 3, 30/70…) là cấu hình gợi ý, nằm trong `settings.json > test_scale`. Cấu hình dự án người dùng đã xác nhận luôn thắng giá trị gợi ý ở đây.

## Điều kiện bắt buộc trước khi tăng tiền

- `result_type` (Purchase, Lead web, Lead form, conversation…) với định nghĩa và nguồn. Không dùng CPA đơn thay cho CPL/chat.
- `target_cost_per_result`, trần ngân sách ngày/tổng (`max_daily_budget_total`), hạn mức lỗ thử nghiệm (`test_loss_limit`), độ trễ dữ liệu, công suất vận hành.
- Thiếu một trong các mục trên: chỉ lập phương án, **không tăng ngân sách**; vẫn phân tích phần độc lập.
- Mỗi lượt **một** thay đổi chính, ghi checkpoint, đọc lại kết quả. Không chạy hết lịch 20 ngày trong một lượt. Mọi thay đổi ngân sách cần người dùng duyệt.

## Giai đoạn 0 — Chuẩn bị Angle (trước khi quay)

Một Angle có 3 phần:
1. **Đang bị gì:** nỗi đau / mong muốn của khách.
2. **Tại sao chưa hết:** vì sao cách cũ thất bại.
3. **Mình làm sao:** cơ chế + kết quả nhìn thấy được.

Mỗi Angle làm ~3 video khác người nói / khác 3 giây đầu. Kho ý tưởng 10–15 concept theo vấn đề, trình diễn giải pháp, bằng chứng thật; không tạo feedback giả. Viết creative: `creative-paohf.md`.

Chuẩn bị thêm: chính sách, quyền và thanh toán, tracking (hành động thật, `event_id` khử trùng Pixel/CAPI, value/currency), giá/ship/quà, CRM, giờ trực, tồn kho. Form Meta/chat không cần pixel web nếu không dùng web.

## Giai đoạn 1 — TEST: tìm 2–3 mẫu thắng

**Cấu trúc mặc định CBO 1-3-5:** 1 campaign CBO, 3 ad set (Broad / Lookalike 1% người mua / Sở thích), mỗi ad set 5 video. Ngân sách ~1,5–2 triệu/ngày cả campaign (~100k/video/ngày). Chạy ~3 ngày.

**Ngân sách nhỏ:** ước số ad tách riêng = `floor(ngân sách test/ngày ÷ spend_per_ad_reference)` (mặc định 250.000₫): 500k → 2 ad, 1 triệu → 4, 2 triệu → 8. Dưới 1 thì kéo dài thời gian thay vì giả định đủ tín hiệu. Có thể dùng ABO gọn thay CBO 1-3-5.

**Đọc kết quả (sau khi đủ độ trễ):**
- Mẫu đã tiêu ≥ `no_result_spend_multiplier` × mục tiêu (mặc định 1,5) mà 0 kết quả, hoặc CPA > 150% mục tiêu → ứng viên tắt. Kiểm tracking, phân phối và hạn mức trước khi quyết.
- CTR link < `ctr_warn_pct` (1%) chỉ là **cảnh báo**; không tắt mẫu đang có lãi chỉ vì CTR.
- Mẫu ít được tiêu = **chưa đủ dữ liệu**, không phải thua. Ngân sách không chia đều giữa các ad.
- Chọn 1–2 ứng viên theo chi phí **và** chất lượng downstream; chưa gọi là thắng chắc.

## Giai đoạn 2 — VERIFY: kiểm chứng ứng viên

Gợi ý **WIN 1-3-1**: 1 campaign, 3 ad set, mỗi ad set 1 ứng viên (rộng / rộng + gợi ý sở thích / rộng + gợi ý khách web 30 ngày). Quan sát 3–4 ngày, đủ độ trễ. CBO phân phối không đều: ad set ít chi chưa chắc thua. Ngân sách nhỏ thì kiểm chứng ngay trong cấu trúc gọn.

Chỉ sang SCALE khi: đủ dữ liệu, kết quả lặp lại, cost/result đạt mục tiêu, cohort kinh doanh đạt chất lượng. Thiếu CRM thì chỉ kết luận hiệu quả quảng cáo, chưa xác nhận đủ điều kiện scale theo lợi nhuận.

## Giai đoạn 3 — SCALE DỌC: ABO 1-1-1

- 1 campaign **ABO**, 1 ad set Broad, **1 video thắng đang bật** + 2 video dự phòng cùng Angle **đang tắt** (gọi nội bộ "1 bật – 2 tắt").
- Tăng ngân sách **`scale_step_pct` (20%), tối đa `scale_step_max_pct` (30%) mỗi lần, không nhân đôi**. Ví dụ 5 → 6,5 → 8,5 triệu… Giữa hai lần tăng chờ ≥ `cooldown_hours` (48 giờ) + độ trễ.
- Ghi ngân sách trước/sau, tổng tiền mọi camp đang chạy và hạn mức. Không tự tăng theo ngày.

## Giai đoạn 4 — Test định dạng (ảnh vs video), không bỏ chung

- Ad set A (ABO, ~500k): chỉ 3 video cùng Angle. Ad set B (ABO, ~500k): chỉ 3 ảnh (ví dụ Before/After) cùng Angle. So sánh ~3 ngày.
- Đây là **so sánh vận hành**, không phải A/B kiểm soát (Broad giống nhau không bảo đảm cùng người xem). Muốn so chuẩn dùng A/B Test / Experiments khi có.
- 500k / 3 mẫu ≈ 167k/mẫu, thấp hơn mức tham khảo: cân nhắc ít mẫu hơn hoặc chạy lâu hơn.
- Khi cả hai cùng thắng mới gộp vào **Flexible** (tối đa 10 biến thể ở cấp ad, kiểm giới hạn thực tế trong tài khoản).

## Giai đoạn 5 — SCALE NGANG: nhân bản ABO 1-1-1

Mục tiêu: tăng tổng chi mà không làm chết con gốc.

| Bản | Tệp | Creative |
|---|---|---|
| Scale 1 (gốc) | Broad | Video thắng |
| Scale 2 | Lookalike 1% | Video thắng, **dùng bài viết có sẵn** |
| Scale 3 | Broad **+ loại trừ** | Video thắng, dùng bài viết có sẵn |

**Quy tắc nhân bản:**
- Chỉ nhân khi ad set gốc **đã ra khỏi Learning**. Mỗi ngày tối đa 2–3 ad set mới.
- Luôn **dùng bài viết có sẵn** (`object_story_id`) để giữ like/comment.
- Nhân bản để scale **luôn là ABO 1-1-1, không chuyển sang CBO**: ABO khoá ngân sách từng ad set nên các bản không giành tiền nhau; CBO dồn tiền vào ad set tốt nhất, các bản còn lại đói.
- Nhân bản không tự tăng tổng tiền; kiểm phân mảnh, trùng tệp, tổng ngân sách. Bản mới phải được kiểm chứng lại.

**Tệp loại trừ cho Scale 3+** (tạo trước rồi mới loại trừ được):
1. Tệp `DA XEM - Video WIN - 7 ngay`: người xem ≥3 giây video thắng, 7 ngày.
2. Tệp `TUONG TAC - Page - 7 ngay`: người tương tác Page, 7 ngày.
3. Ad set Scale 3 → **loại trừ cả hai tệp** (tương đương tệp kết hợp "đã xem HOẶC tương tác").
4. Chỉ loại trừ **`exclusion_window_days` (7) ngày**, không 30/180: tránh chồng tệp mà vẫn cho tệp cũ xem lại sau 7 ngày.
5. Mỗi lần thêm Scale 4, 5… tạo lại tệp loại trừ gồm khán giả của các bản trước.

Cách gọi API: `thuc-thi-bm-api.md` mục 9–10, `thuc-thi-zernio.md` mục 9–10.

## Giai đoạn 6 — Gom CBO WIN: giữ doanh thu nền

Khi đã có ≥3 video thắng khác nhau từ các bản ABO 1-1-1: một campaign **CBO WIN** (mỗi ad set một video thắng) chạy khoảng **30%** tổng ngân sách để giữ doanh thu nền; **70%** cho các ABO 1-1-1 scale. Tỷ lệ 30/70 là gợi ý, không ép với tài khoản nhỏ.

## Ba phanh

### 1. Phanh ngân sách — chẩn đoán trước, giảm một lần

- `baseline_cost` = tổng chi `baseline_days` (3) ngày hoàn chỉnh / tổng kết quả 3 ngày (không lấy trung bình ba CPA ngày). Mẫu số 0 → N/A, dùng hạn mức chi không kết quả.
- CPA trong ngày chỉ là **cảnh báo**; không so vài giờ đầu ngày với cả ngày trước.
- Khi CPA (dữ liệu đủ) vượt `baseline × (1 + deterioration_trigger_pct)` (30%) **và** vượt mục tiêu: kiểm tracking, trang đích, tồn kho, chất lượng CRM, thay đổi gần nhất. Vẫn đạt mục tiêu và đóng góp tốt → theo dõi, không giảm máy móc.
- Nếu vẫn xấu: **giảm `budget_cut_pct` (30%), không tắt**: `B_sau = B_trước × 0,7`, không dưới sàn. Ghi `last_change`, rồi **cooldown 48 giờ**: không giảm thêm mỗi lần rule chạy.
- Sau ~3 ngày trưởng thành vẫn yếu: giữ / thay mẫu / giảm tiếp / dừng theo **nguyên nhân** (lỗi ở web/offer/bán hàng thì sửa đúng chỗ).
- Dừng ngay phần bị ảnh hưởng nếu vượt hạn mức lỗ, đích lỗi, hết hàng.
- Không nói tạm dừng là xoá dữ liệu, bật lại đắt gấp đôi, hay giảm 30% chắc chắn không học lại.

### 2. Phanh creative — một mẫu bật, kho dự phòng

- Khi video chính có frequency > `frequency_warn` (3) **và** CPA đắt 2 ngày liên tiếp (đủ dữ liệu) → tắt video chính, bật **một** video dự phòng. Frequency một mình chỉ là cảnh báo; xem cùng CTR, CPM, CVR, cost/result, downstream.
- Thay có kiểm soát: ghi ad cũ, ad mới, kế hoạch hoàn tác; đọc lại `effective_status`. Không tự bật cả hai dự phòng.
- Thêm/bật ad có thể làm học lại; không hứa giữ nguyên learning.
- Bổ sung 1–2 mẫu mới mỗi đợt (biến thể cùng Angle + Angle mới ở kho test).

### 3. Phanh doanh thu — quản trị danh mục

- Ví dụ: scale 7 triệu, nền 3 triệu. Giảm scale 30% giải phóng 2,1 triệu; tăng nền 30% chỉ dùng 0,9 triệu → tổng mới 8,8 triệu. Dồn cả 2,1 triệu vào nền = tăng nền 70%, phải đánh giá riêng.
- Khi một ABO đắt 1–2 ngày: giảm ABO đó 30% và cân nhắc tăng CBO WIN trong giới hạn bước tăng. Không bảo đảm doanh thu giữ nguyên.
- Chỉ khôi phục scale khi dữ liệu đủ, chi phí và chất lượng đạt điều kiện, còn hạn mức.

## Quy tắc tự động

Chỉ cài khi người dùng duyệt rõ từng rule; rule là cấu hình chạy nền.

1. **Cảnh báo:** cost/result vượt mục tiêu và baseline × 1,3, dữ liệu đủ, ngoài cooldown. Chưa đủ dữ liệu → cảnh báo kiểm tra, không kết luận thua.
2. **Giảm một lần:** đủ điều kiện cảnh báo, đã kiểm tracking/kinh doanh, ngân sách trên sàn, chưa giảm trong cooldown → giảm 30%, lưu trạng thái chống chạy lặp, đọc lại ngân sách.
3. **Ưu tiên cao hơn:** tổng chi / hạn mức lỗ; 0 kết quả dùng hạn mức chi không kết quả (không lọt qua điều kiện CPA N/A).

Rule gốc của Meta và rule Zernio chỉ so **ngưỡng tuyệt đối**: quy đổi baseline thành số (ví dụ CPA 3 ngày > CPA mục tiêu × 1,3). Zernio: `thuc-thi-zernio.md` mục 13. Muốn baseline động thật thì dùng `watch` + người dùng duyệt từng lần giảm. Không tự chuyển tiền sang camp thắng, không tự bật lại. Kiểm tra rule khác để tránh giảm kép.

## Flexible và quảng cáo tách riêng

- `separate_ads`: mỗi ad một mẫu, đọc được chi/kết quả từng mẫu để chọn ứng viên scale. Không phải A/B kiểm soát.
- `flexible_bundle`: một ad nhiều tài sản (kiểm giới hạn thực tế, thường 10), hệ thống tự chọn tổ hợp. Một bundle 10 tài sản **không** phải 10 phép test; không chia CPA bundle cho số tài sản. Muốn đưa một tài sản sang ABO 1-1-1 thì kiểm chứng lại trong ad riêng.
- Format trong PAOHF (POV, demo, review…) khác chế độ Flexible.

## Duy trì

Giữ mẫu tốt, thêm biến thể thay vì sửa trực tiếp (sửa làm mất phép so sánh); ngoại lệ là lỗi/chính sách. Đợi 2–3 ngày + độ trễ trước khi so mẫu mới/cũ; không tắt mẫu cũ đang đóng góp tốt.

## Hồ sơ quyết định

giai đoạn | nhánh | kỳ/múi giờ/attribution | dữ liệu đủ/chưa | bằng chứng ba cấp | chất lượng cohort | hành động | ngân sách trước/sau/tổng | hạn mức | điều kiện đánh giá lại / hoàn tác | quyền thực thi | kết quả đọc lại.

## Nguồn (kiểm tra lại khi dùng)

- Learning phase và chỉnh sửa lớn: https://www.facebook.com/business/help/316478108955072
- A/B test: https://www.facebook.com/business/help/1738164643098669 · https://www.facebook.com/business/help/290009911394576
- Flexible ad format: https://www.facebook.com/business/help/835561738423867

Các trang Meta thường đòi đăng nhập; trang không đọc được thì ghi "chưa xác minh".
