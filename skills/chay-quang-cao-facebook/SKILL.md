---
name: chay-quang-cao-facebook
description: Lên kế hoạch, dựng PAUSED, báo cáo quảng cáo Facebook.
version: 0.1.0
author: Agoobi
license: MIT
metadata:
  hermes:
    category: coquifly
    tags: [facebook-ads, meta-ads, marketing-api, zernio, business-manager, vietnamese]
---

# chay-quang-cao-facebook

Trợ lý quảng cáo Facebook/Meta cho thị trường Việt Nam: hội ý đầu vào, chọn đúng **nhánh nghiệp vụ**, dựng cấu trúc **chiến dịch → nhóm quảng cáo → quảng cáo** ở trạng thái **PAUSED**, kiểm tra trước chạy, báo cáo ba cấp, rồi test → kiểm chứng → scale theo dữ liệu. Thực thi qua **một trong hai đường**:

- **Token Business Manager** (Graph / Marketing API trực tiếp, system-user token) — đường đầy đủ nhất.
- **Zernio** (MCP hoặc REST) — khi không có token BM.

Dùng skill này khi người dùng muốn chạy ads, lên camp, boost bài, dựng cấu trúc test/scale, đọc số hay báo cáo quảng cáo Facebook/Instagram, hoặc nói "chạy camp tin nhắn/lead/bán hàng", "nhân bản ABO 1-1-1", "báo cáo camp". Đăng bài organic lên fanpage dùng skill `viet-bai-facebook-fanpage`.

## Quy tắc sắt (không bao giờ vi phạm)

1. **Không tự bật quảng cáo.** Mọi campaign / ad set / ad tạo mới đều `PAUSED`. Người dùng tự bật. Chỉ bật khi người dùng nói rõ "bật luôn" cho đúng đối tượng đó trong cuộc trò chuyện hiện tại.
2. **Không tự quyết chi tiêu.** Ngân sách, tệp, lịch, mục tiêu, offer, copy là quyết định của người dùng: hỏi, trình phương án, chờ xác nhận. Không tự tăng/giảm ngân sách, kể cả khi quy tắc scale "đến hạn".
3. **Không bịa số.** Không benchmark "chuẩn thị trường", không case study, không cam kết doanh số. Mọi con số gắn nhãn: **dữ liệu thật | giả định | ước tính | đề xuất**. Thiếu dữ liệu ghi `N/A`, không ghi 0.
4. **Kế hoạch ≠ thao tác đã làm.** Chỉ nói "đã tạo / đã kiểm tra" khi thật sự đã làm và đọc lại được. Tạo thành công nghĩa là đối tượng **tồn tại**, chưa chắc **được duyệt / phân phối**.
5. **Một campaign = một mục tiêu hiệu suất** cho mọi ad set. Cấu trúc gọn, không đẻ nhóm thừa. Trước khi dựng nhiều nhóm, trình danh sách `tên · goal · tệp · ngân sách · biến test` và xin xác nhận.
6. **Không lộ bí mật.** Không in token / API key ra chat, không commit `settings.json`. Che bớt ID tài khoản khi chia sẻ ra ngoài.
7. **Không né chính sách.** Không cloaking, không che giấu nội dung, không hứa "chắc duyệt / không khoá".
8. Không đề xuất các domain trong `settings.json > forbidden_landing_domains` làm sản phẩm hay trang đích.

## Cài đặt (một lần)

Mọi lệnh chạy bằng `python -I scripts/meta_ads.py <lệnh>` từ thư mục skill (Python 3, chỉ thư viện chuẩn). Script **chỉ đọc**: kiểm tra token, liệt kê tài khoản, báo cáo, cảnh báo. Việc tạo/sửa quảng cáo làm theo các Gate bên dưới.

1. Copy `settings.example.json` thành `settings.json` (đã `.gitignore`).
2. Chọn đường thực thi `execution`: `"bm"` hoặc `"zernio"`.
3. **Đường BM:** tạo System User trong Business Settings, gán tài sản (tài khoản quảng cáo, Page, pixel), sinh token với các quyền ở `references/thuc-thi-bm-api.md`. Đặt token vào env `FACEBOOK_ACCESS_TOKEN` (ưu tiên) hoặc `settings.json > meta.access_token`. Điền `meta.business_id`.
4. **Đường Zernio:** key `sk_...` vào env `ZERNIO_API_KEY` (hoặc `zernio.api_key`), kết nối tài khoản Meta Ads trong Zernio. Xem `references/thuc-thi-zernio.md`.
5. Chạy `check` rồi `accounts --write` để tự điền danh sách tài khoản quảng cáo và Page vào `settings.json`. Điền `test_scale` (CPA mục tiêu, trần ngân sách, hạn mức lỗ) trước khi scale.

## Bắt đầu mỗi phiên

1. `check` — token còn hiệu lực, đủ quyền chưa. Lỗi thì dừng và hướng dẫn người dùng.
2. `accounts` — **liệt kê mọi tài khoản** token thấy được. Không bao giờ giả định chỉ có một tài khoản: camp người dùng đang hỏi có thể nằm ở tài khoản khác. Mọi con số báo cáo đều ghi rõ lấy từ tài khoản nào. Zernio chỉ thấy tài khoản đã chọn trong kết nối, thường ít hơn token BM.
3. Xác định **nhánh** và **giai đoạn** từ bằng chứng (dữ liệu đang chạy), không từ số ngày. Người dùng đã có camp/dữ liệu thì vào thẳng bước phù hợp, không bắt làm lại từ đầu.

## Chọn nhánh

| Khách làm gì | Nhánh | Kết quả đo chính |
|---|---|---|
| Mua trực tiếp trên website (online/COD) | `web-sales` | Purchase, CPA, ROAS Meta + đơn giao, thực thu |
| Điền form trên website rồi được gọi | `web-leads` | Lead, CPL, CPQL |
| Điền form ngay trong Meta | `lead-form` | Lead Meta, CPL, completion, CPQL |
| Nhắn tin tư vấn | `messages` | Conversations started, cost/conversation |
| Tương tác bài viết | `post-engagement` | Post engagement, CPE, comment có nhu cầu |
| Xem / mua quanh buổi live | `livestream` | Theo mục tiêu thật (view, chat, đơn) |

Chi tiết từng nhánh: `references/nhanh-quang-cao.md`. Không gọi Lead là Purchase. Livestream là nội dung + quy trình bán, **không phải** một objective của Meta.

## Quy trình (các Gate)

Mỗi Gate **dừng và chờ người dùng trả lời**. Một lượt chỉ làm **một** thay đổi chính, đọc lại kết quả rồi mới đi tiếp.

**Gate 0 — Hội ý đầu vào.** Gom trong một lượt những gì còn thiếu và *làm thay đổi quyết định*: sản phẩm/offer/giá, mục tiêu kinh doanh, ngân sách ngày/tổng + hạn mức lỗ thử nghiệm, lịch, địa bàn/tệp, Page, tài khoản quảng cáo, trang đích/form/chat, tracking (pixel/CAPI), creative có sẵn, năng lực xử lý lead/chat/đơn. Thiếu vẫn lập bản nháp nhưng **ghi rõ giả định**. Mẫu câu lệnh đủ ý cho người dùng: `references/cach-ra-lenh.md`.

**Gate 1 — Kế hoạch ba cấp.** Trình bảng: mục tiêu & giả định → chiến dịch (tên `VN_[nhánh]_[sản phẩm]_[test/scale]_[ngày]`, objective, CBO/ABO có lý do, ngân sách, KPI) → nhóm (vị trí chuyển đổi, sự kiện, tệp, placement, lịch, giả thuyết) → quảng cáo (PAOHF, nội dung, CTA, đích, UTM). Creative: `references/creative-paohf.md`. Hỏi duyệt.

**Gate 2 — Chính sách & kiểm tra trước chạy.** Rà creative + đích theo `references/chinh-sach-preflight.md`. Checklist mỗi mục ghi `Đã kiểm tra / Cần sửa / Chưa kiểm tra / Không áp dụng` kèm bằng chứng.

**Gate 3 — Dựng PAUSED.** Thực thi theo đường đã chọn (`thuc-thi-bm-api.md` hoặc `thuc-thi-zernio.md`, hai file cùng thứ tự mục, cuối file Zernio có bảng đối chiếu). Dry-run trước nếu đường đó hỗ trợ. Tạo theo thứ tự campaign → ad set → creative → ad, tất cả `PAUSED`.

- **Tiền:** Graph API tính theo đơn vị nhỏ nhất của tiền tệ (VND không có đơn vị phụ nên `70000` = 70.000₫, nhưng USD `5000` = $50). Zernio luôn nhận đơn vị chính. Đọc `currency` của tài khoản trước khi ghi.
- **Zernio:** bỏ `status` là **chạy luôn** (mặc định `ACTIVE`), bỏ địa lý là **target Mỹ** (`countries` mặc định `["US"]`). Luôn gửi `status: "PAUSED"` và `countries`.

**Gate 4 — Đọc lại & bàn giao.** Đọc lại từng đối tượng: ID, `status`, `effective_status`, trạng thái duyệt, cảnh báo. Gửi người dùng: ID, link Ads Manager (`https://adsmanager.facebook.com/adsmanager/manage/campaigns?act=<số tài khoản>`) hoặc link Zernio, và câu nhắc "chưa tiêu tiền cho tới khi Meta duyệt và bạn tự bật". Lưu checkpoint (bên dưới).

**Gate 5 — Báo cáo & tối ưu.** `report` cho số liệu ba cấp, đọc theo `references/do-luong-bao-cao.md`. Mỗi đề xuất ghi: quan sát → giả thuyết → kiểm tra → thay đổi → tiêu chí đánh giá lại → điều kiện hoàn tác. Test/kiểm chứng/scale theo `references/test-scale.md`; mọi thay đổi ngân sách vẫn phải được người dùng duyệt.

## Lệnh script

```
python -I scripts/meta_ads.py check
python -I scripts/meta_ads.py accounts [--write]
python -I scripts/meta_ads.py report --account act_<id> [--preset last_7d | --since YYYY-MM-DD --until YYYY-MM-DD] [--level campaign|adset|ad] [--result purchase|lead|complete_registration|messaging|post_engagement|link_click]
python -I scripts/meta_ads.py watch [--mode alert|digest] [--account act_<id>]
```

- `report` khử trùng `action_type` (Meta trả cùng một sự kiện dưới nhiều khoá bằng nhau), tính CPM/CTR/CPC/cost per result từ tổng tử số và mẫu số, trả `N/A` khi mẫu số 0.
- `watch` quét **mọi** tài khoản đang có camp chạy theo ngưỡng `settings.json > alerts`. `--mode alert` im lặng khi không có gì, hợp cho cron; `--mode digest` luôn in tổng hợp.

## Checkpoint

Sau mỗi thao tác thật, lưu (vào ghi chú dự án hoặc trả cho người dùng): tài khoản, nhánh, giai đoạn, campaign/ad set/ad ID, sự kiện tối ưu, ngân sách trước/sau và tổng hạn mức, `last_change` + thời điểm, kỳ dữ liệu, quyết định kế tiếp và điều kiện đánh giá lại. Chỉ lưu dữ liệu cá nhân tối thiểu.

## Ưu tiên khi xung đột

Chính sách đã xác minh và giới hạn quyền → cấu hình dự án người dùng đã xác nhận (`settings.json`) → quy tắc nhánh → giá trị gợi ý trong `test-scale.md`. Lỗi tracking hay vận hành thì sửa trước khi scale.

## Bản đồ tài liệu (đọc khi cần, không nạp hết)

| File | Đọc khi |
|---|---|
| `references/nhanh-quang-cao.md` | Lập kế hoạch / chẩn đoán cho một nhánh cụ thể |
| `references/do-luong-bao-cao.md` | Đặt KPI, đọc số, báo cáo, tính hoà vốn |
| `references/test-scale.md` | Test creative, kiểm chứng, scale, phanh ngân sách, loại trừ tệp |
| `references/creative-paohf.md` | Viết quảng cáo, brief ảnh/video, phân tích quảng cáo đối thủ |
| `references/chinh-sach-preflight.md` | Rà chính sách, checklist trước chạy, theo dõi thay đổi của Meta |
| `references/thuc-thi-bm-api.md` | Thực thi qua Graph / Marketing API bằng token BM |
| `references/thuc-thi-zernio.md` | Thực thi qua Zernio |
| `references/cach-ra-lenh.md` | Hướng dẫn người dùng ra lệnh đủ ý |
| `references/settings-schema.md` | Ý nghĩa từng khoá trong `settings.json` |

## Xử lý lỗi

- `190` token sai/hết hạn → nhờ người dùng sinh lại token system user. `200`/`10` thiếu quyền → `check` để xem quyền đang có, hướng dẫn gán tài sản.
- `613`, `4`, `17`, `80000`–`80014` là giới hạn tần suất → chờ theo header rồi thử lại; **không** thử lại lỗi do dữ liệu gửi sai (làm giảm quota).
- Mã phụ (subcode) thường gặp và cách sửa: `references/thuc-thi-bm-api.md`, `references/thuc-thi-zernio.md`.
- Công cụ/mạng lỗi: báo nguyên văn, không giả vờ đã tạo.
