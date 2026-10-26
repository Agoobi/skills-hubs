# Thực thi qua Graph / Marketing API (token Business Manager)

Đường đầy đủ nhất: đọc mọi tài khoản token được gán, tạo đủ campaign / ad set / creative / ad, đăng và quản lý bài Page, đọc tin nhắn. Bản tương đương qua Zernio: `thuc-thi-zernio.md` (cùng thứ tự mục để đối chiếu).

Mọi ví dụ dùng `V=v21.0` (đã chạy thật 10/2026). Meta ra phiên bản mới định kỳ; lỗi `2635` = phiên bản đã bị bỏ → tăng `meta.graph_version`.

## 1. Chuẩn bị token

1. Business Settings → Users → **System users** → tạo system user (vai trò Admin hoặc Employee).
2. **Assign assets**: tài khoản quảng cáo (Manage campaigns), Page (Create ads + Create content + Messages nếu cần), pixel/dataset.
3. App (Meta for Developers) ở chế độ **Live**. App ở Development Mode chỉ tạo được campaign/ad set; tạo creative/ad sẽ lỗi `1885183`.
4. Generate token, chọn quyền: `ads_management`, `ads_read`, `business_management`, `read_insights`; thêm `pages_show_list`, `pages_read_engagement`, `pages_manage_ads` để chạy quảng cáo có Page; `pages_manage_posts`, `pages_manage_engagement`, `pages_read_user_content` để đăng bài / xử lý comment; `pages_messaging` để đọc và trả lời tin nhắn.
5. Token system user **không hết hạn** (`expires_at = 0`). Đặt vào env `FACEBOOK_ACCESS_TOKEN`, chạy `check`.

Không dùng token người dùng (hết hạn 1–60 ngày) cho việc chạy định kỳ.

## 2. Tìm tài khoản và tài sản

- `accounts` trong script gộp `GET /me/adaccounts` + `GET /{business_id}/owned_ad_accounts` + `GET /{business_id}/client_ad_accounts`. Tài khoản **client** (BM khác chia sẻ) chỉ hiện ở `/me/adaccounts` hoặc `client_ad_accounts`, nên không được bỏ nguồn nào.
- Page: `GET /{business_id}/owned_pages`, `GET /me/accounts`. Pixel: `GET /{business_id}/adspixels`, `GET /act_{id}/adspixels`.
- Tài khoản không có pixel thì **không** chạy được mục tiêu chuyển đổi website: chọn tài khoản có pixel hoặc gắn pixel trước.
- ID cũ trong ghi chú có thể sai/hết hạn: luôn đọc lại live trước khi dùng.

## 3. Mô hình dữ liệu

`Ad account → Campaign (objective) → Ad set (ngân sách nếu ABO, tệp, lịch, tối ưu) → Ad (creative)`. Creative tái sử dụng được. `status` = công tắc đã đặt; `effective_status` = trạng thái phân phối thật (ví dụ `CAMPAIGN_PAUSED`, `WITH_ISSUES`).

**Đơn vị tiền:** trường ngân sách của Graph API tính theo **đơn vị nhỏ nhất** của tiền tệ. VND, JPY, KRW, IDR, TWD… không có đơn vị phụ nên `70000` = 70.000₫; USD thì `5000` = $50. Đọc `currency` của tài khoản trước khi ghi ngân sách. Số liệu `spend` trong insights luôn là đơn vị chính.

## 4. Tạo campaign

`POST /act_{id}/campaigns` (form fields, `--data-urlencode` cho JSON):

| Trường | Ghi chú |
|---|---|
| `name`, `objective`, `status=PAUSED` | Objective mới: `OUTCOME_AWARENESS`, `OUTCOME_TRAFFIC`, `OUTCOME_ENGAGEMENT`, `OUTCOME_LEADS`, `OUTCOME_SALES`, `OUTCOME_APP_PROMOTION` |
| `special_ad_categories=[]` | Bắt buộc, kể cả khi không thuộc danh mục đặc biệt |
| `is_adset_budget_sharing_enabled=0` | Bắt buộc khi **không** đặt ngân sách campaign (ABO); thiếu → subcode `4834011` |
| `daily_budget` / `lifetime_budget` + `bid_strategy` | Chỉ khi CBO. Ngân sách chỉ ở **một** cấp |

## 5. Tạo ad set

`POST /act_{id}/adsets`: `name`, `campaign_id`, `optimization_goal`, `billing_event`, `bid_strategy` (thiếu → `2490487`), `targeting`, `status=PAUSED`, ngân sách nếu ABO, `start_time`/`end_time` (ISO có offset, ví dụ `2026-11-01T08:00:00+0700`).

`targeting` **bắt buộc** có `targeting_automation.advantage_audience` = `0` hoặc `1` (thiếu → `1870227`):

```json
{"geo_locations":{"countries":["VN"]},"age_min":25,"age_max":45,"targeting_automation":{"advantage_audience":0}}
```

**Bộ tham số theo nhánh** (Traffic, Tương tác bài, Chuyển đổi web đã tạo thật thành công 10/2026; Tin nhắn và Lead form theo tài liệu Meta, kiểm bằng dry-run hoặc tạo `PAUSED` rồi đọc lại):

| Nhánh | Campaign objective | Ad set | Bắt buộc thêm |
|---|---|---|---|
| Traffic | `OUTCOME_TRAFFIC` | `optimization_goal=LINK_CLICKS` hoặc `LANDING_PAGE_VIEWS`, `billing_event=IMPRESSIONS` | Creative có link ngoài |
| Tương tác bài | `OUTCOME_ENGAGEMENT` | `optimization_goal=POST_ENGAGEMENT`, `billing_event=IMPRESSIONS` | **`destination_type=ON_POST`** + `promoted_object={"page_id":...}`. Thiếu `ON_POST` → `2490408` |
| Tin nhắn | `OUTCOME_ENGAGEMENT` | `optimization_goal=CONVERSATIONS`, `destination_type=MESSENGER` (hoặc `WHATSAPP`, `INSTAGRAM_DIRECT`) | `promoted_object.page_id` |
| Lead form | `OUTCOME_LEADS` | `optimization_goal=LEAD_GENERATION`, `destination_type=ON_AD` | `promoted_object.page_id`; creative gắn `lead_gen_form_id` |
| Chuyển đổi web | `OUTCOME_SALES` (hoặc `OUTCOME_LEADS`) | `optimization_goal=OFFSITE_CONVERSIONS`, `destination_type=WEBSITE` | `promoted_object={"pixel_id":...,"custom_event_type":"PURCHASE"}` |

`custom_event_type` hợp lệ cho web: `PURCHASE`, `INITIATED_CHECKOUT`, `ADD_TO_CART`, `ADD_PAYMENT_INFO`, `COMPLETE_REGISTRATION`, `LEAD`, `SUBSCRIBE`, `CONTENT_VIEW`, `START_TRIAL`, `DONATE`.

**Tệp:**
- **OR (khớp bất kỳ):** đặt mọi sở thích/hành vi trong **một** phần tử: `flexible_spec=[{"interests":[...],"behaviors":[...]}]`.
- **AND (thu hẹp):** nhiều phần tử trong `flexible_spec` → "and must also match".
- Luôn kiểm bằng `GET /{adset_id}/targetingsentencelines`: trả đúng câu Ads Manager hiển thị ("People who match…" vs "And must also match…").
- Advantage+ audience (`advantage_audience=1`): `age_max` bị khoá 65 (`1870189`), `age_min` chỉ 18–25. Muốn gợi ý tuổi hẹp hơn: thêm `targeting.age_range=[23,46]`.
- Loại trừ: `excluded_custom_audiences=[{"id":...}]`. Tìm sở thích: `GET /search?type=adinterest&q=<từ khoá>`.

**Customer lifecycle (chỉ ad set `OUTCOME_SALES`)**: trường `ad_set_goal`. `{"type":0}` = thu hút chuyển đổi từ mọi đối tượng; `2` = loại khách hiện tại (cần `existing_customers_exclusions`); `1` = loại khách hiện tại và đã tương tác.

Ngân sách ad set tối thiểu thực tế thường **cao hơn** `min_daily_budget` của tài khoản (lỗi `1885272` khi thấp quá).

## 6. Creative và ad

- Ảnh: `POST /act_{id}/adimages` (`-F filename=@anh.jpg`) → `image_hash`.
- Video: `POST https://graph-video.facebook.com/{V}/act_{id}/advideos` (`-F source=@video.mp4`) → `video_id`; đợi `GET /{video_id}?fields=status` báo `ready`. Chuyển HEVC sang H.264 trước (`ffmpeg -i in.mov -c:v libx264 -pix_fmt yuv420p -c:a aac out.mp4`).
- Creative video **bắt buộc thumbnail** (`image_hash` hoặc `image_url` trong `video_data`), thiếu → `1443226`. Lấy khung hình: `ffmpeg -ss 2 -i v.mp4 -frames:v 1 thumb.jpg`.
- Creative mới: `POST /act_{id}/adcreatives` với `object_story_spec`:
  - Link: `{"page_id":PG,"link_data":{"link":URL,"message":...,"name":tiêu đề,"image_hash":...,"call_to_action":{"type":"LEARN_MORE"}}}`
  - Video: `{"page_id":PG,"video_data":{"video_id":...,"image_hash":...,"message":...,"title":...,"call_to_action":{"type":"SIGN_UP","value":{"link":URL}}}}`
- Dùng **bài có sẵn** (giữ like/comment, cần khi nhân bản để scale): `object_story_id=<pageId>_<postId>`. Bài phải thuộc đúng Page của ad (`3858759`), và phải boost được (`2446187`).
- UTM: `url_tags=utm_source=facebook&utm_medium=paid&utm_campaign={{campaign.name}}`.
- Ad: `POST /act_{id}/ads` với `adset_id`, `creative={"creative_id":...}`, `status=PAUSED`. Đọc lý do bị từ chối: `GET /{ad_id}?fields=ad_review_feedback,effective_status`.

## 7. Dry-run

Marketing API nhận `execution_options=["validate_only"]` trên POST tạo đối tượng: kiểm tra không tạo. Chưa xác minh trên mọi loại đối tượng; nếu lỗi tham số thì bỏ, tạo `PAUSED` rồi đọc lại.

## 8. Đọc lại và bàn giao

- `GET /{id}?fields=name,status,effective_status,daily_budget,optimization_goal,promoted_object,issues_info`
- `GET /{adset_id}/targetingsentencelines` cho tệp.
- Link: `https://adsmanager.facebook.com/adsmanager/manage/campaigns?act=<số tài khoản không có act_>`.

## 9. Sửa, bật/tắt, nhân bản

- Sửa: `POST /{id}` với trường thay đổi. Bật/tắt: `status=ACTIVE|PAUSED` (chỉ khi người dùng duyệt). Tắt campaign thì con hiện `CAMPAIGN_PAUSED`; bật lại campaign không tự bật con đã tắt riêng.
- Ngân sách ad set: tối đa **4 lần/giờ** mỗi ad set (`613`/`1487632`). Giới hạn chi tài khoản: 10 lần/ngày.
- Nhân bản: `POST /{campaign_id}/copies` hoặc `POST /{adset_id}/copies` với `deep_copy=true`, `status_option=PAUSED`, `rename_options`. Để giữ social proof, ad trong bản sao vẫn trỏ `object_story_id` cũ.
- Xoá: `DELETE /{id}` (xoá campaign kéo theo con). Ưu tiên `ARCHIVED`/`PAUSED`, xoá chỉ khi người dùng yêu cầu.

## 10. Custom audience (tệp loại trừ, LAL)

- Xem video: `POST /act_{id}/customaudiences` với `subtype=ENGAGEMENT`, `rule` kiểu video (`event: video_watched` = xem ≥3 giây; `video_view_10s`, `video_completed`…), `retention_seconds=604800` (7 ngày).
- Tương tác Page: `subtype=ENGAGEMENT`, nguồn Page, `event: page_engaged`.
- Lookalike: `subtype=LOOKALIKE`, `origin_audience_id`, `lookalike_spec={"country":"VN","ratio":0.01}`.
- "Gộp" hai tệp để loại trừ: không cần tạo tệp kết hợp, đưa **cả hai** vào `excluded_custom_audiences` (loại trừ nhiều tệp = loại trừ hợp của chúng).

## 11. Báo cáo

`GET /{act|campaign|adset|ad}/insights` với `level`, `date_preset` hoặc `time_range={"since","until"}`, `time_increment=1` (theo ngày), `breakdowns` (`age`, `gender`, `region`, `publisher_platform`, `platform_position`…), `fields` (`spend,impressions,reach,frequency,inline_link_clicks,actions,cost_per_action_type,optimization_goal`). Dùng `report` trong script; đọc số theo `do-luong-bao-cao.md`. Báo cáo lớn: job bất đồng bộ `POST /{id}/insights` → đợi `async_status=Job Completed` → `GET /{report_run_id}/insights`. Lưu số liệu hằng ngày: đối tượng đã xoá mất lịch sử.

## 12. Page: đăng bài, comment, tin nhắn

Dùng **Page token**: `GET /{page_id}?fields=access_token` (token system user đọc bài Page sẽ lỗi `2069032`/`#210`).

- Bài đã đăng: `GET /{page_id}/published_posts?fields=id,message,created_time,permalink_url`; bài hẹn: `/scheduled_posts`.
- Đăng: `POST /{page_id}/feed` (`message`, `link`) hoặc `/photos` (`url`/`source` + `message`). Hẹn giờ: `published=false` + `scheduled_publish_time=<unix>` (10 phút – 75 ngày). Đăng bài organic là việc của skill `viet-bai-facebook-fanpage`; chỉ dùng ở đây khi cần bài làm creative và người dùng đã duyệt nội dung.
- Comment: `GET /{post_id}/comments?fields=id,message,from,is_hidden`; trả lời `POST /{comment_id}/comments`; ẩn spam `POST /{comment_id}` với `is_hidden=true`. `from` thường null qua API, nên lọc theo nội dung để tránh trả lời trùng.
- Tin nhắn (cần `pages_messaging`): `GET /{page_id}/conversations?fields=id,updated_time,snippet`, `GET /{conversation_id}?fields=messages{message,from,created_time}`, gửi `POST /{page_id}/messages` với `recipient.id` = PSID, chỉ trong cửa sổ 24 giờ. Kiểm tra quyền bằng `check` trước khi nói "thiếu quyền".

## 13. Giới hạn tần suất

Token system user chịu giới hạn **Business Use Case (BUC)**, cửa sổ trượt (không theo ngày):

| Nhóm | Cửa sổ | Hạn mức |
|---|---|---|
| Ads Management (tạo/sửa) | 1 giờ, mỗi tài khoản | Standard `300 + 40×ads đang chạy`; Advanced `100000 + 40×…` |
| Ads Insights | 1 giờ | Standard `600 + 400×ads đang chạy − 0.001×lỗi người dùng` |
| Custom Audience | 1 giờ | `5000 + 40×tệp` |
| Pages, LeadGen, Messenger | 24 giờ | theo tương tác |

- Header: `X-Business-Use-Case-Usage` (`call_count`, `total_cputime`, `total_time`, `estimated_time_to_regain_access` tính bằng **phút**), `X-Ad-Account-Usage`, `X-FB-Ads-Insights-Throttle`. Lấy **max** của ba chỉ số; không có header = không có tín hiệu, không phải an toàn.
- Lỗi throttle: `4`, `17`, `613`, `80000`–`80014` (`80004` khi tạo/sửa nhiều). Chờ theo header rồi backoff. **Lỗi do dữ liệu sai không thử lại** (làm giảm quota). App ở Development Mode chỉ có quota cơ bản.

## 14. Mã lỗi thường gặp

| Mã / subcode | Nghĩa → cách sửa |
|---|---|
| `190` | Token sai/hết hạn → sinh lại token system user |
| `200`, `10` | Thiếu quyền → `check`, gán tài sản cho system user |
| `100 / 4834011` | Thiếu `is_adset_budget_sharing_enabled` khi tạo campaign ABO |
| `100 / 2490487` | Ad set thiếu `bid_strategy` |
| `100 / 1870227` | Thiếu `targeting_automation.advantage_audience` |
| `100 / 1870189` | Advantage+ audience: `age_max` phải là 65 |
| `100 / 2490408` | Mục tiêu hiệu suất không hợp objective (POST_ENGAGEMENT thiếu `ON_POST`) |
| `100 / 1885272` | Ngân sách ad set quá thấp |
| `100 / 1885183` | App đang Development Mode, không tạo được creative |
| `100 / 1487202` | System user chưa có quyền Page để chạy ads |
| `100 / 1443226` | Creative video thiếu thumbnail |
| `100 / 3858759` | Bài không thuộc Page của ad |
| `100 / 2446187` | Bài không boost được |
| `100 / 1815520` | Creative không có link ngoài hợp lệ cho mục tiêu click |
| `100 / 1870252`, `1870258`, `1870261` | `ad_set_goal`: tài khoản chưa bật / thiếu `type` / danh mục đặc biệt chỉ cho BROAD |
| `100 / 1359188` | Tài khoản chưa có phương thức thanh toán hợp lệ |
| `2635` | Phiên bản API đã bị bỏ → tăng `graph_version` |
