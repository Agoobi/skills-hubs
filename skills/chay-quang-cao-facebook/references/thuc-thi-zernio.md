# Thực thi qua Zernio

Cùng quy trình, cùng Gate, cùng quy tắc với đường BM (`thuc-thi-bm-api.md`, cùng thứ tự mục). Zernio gọi Marketing API thay mình, nhận tiền theo **đơn vị chính** (VND `70000` = 70.000₫, USD `50` = $50) và tự đổi sang đơn vị Meta cần.

Đối chiếu theo OpenAPI của Zernio (bản 1.366.0, 10/2026): `https://zernio.com/openapi.json`, tài liệu `https://docs.zernio.com`. Zernio đổi API thường xuyên; khi tham số bị từ chối, đọc lại spec thay vì đoán.

## 0. Ba điều khác BM phải nhớ

1. **`status` mặc định là `ACTIVE`.** Mọi lệnh tạo (`/ads/create`, `/ads/boost`, `/ads/messaging`) mà bỏ `status` sẽ **chạy luôn**. Luôn gửi `"status": "PAUSED"`. `PAUSED` chỉ giữ đối tượng **cao nhất** mà lệnh tạo ra (campaign mới bị tắt, ad set và ad bên dưới bật sẵn, một lần bật campaign là chạy). Muốn mọi cấp đều tắt (ví dụ giữ ad dự phòng), gửi thêm `campaignStatus`, `adSetStatus`, `adStatus` = `PAUSED`.
2. **`countries` mặc định là `["US"]`** khi không có địa lý nào khác. Luôn gửi `countries: ["VN"]` (hoặc `regions`/`cities`).
3. **Chỉ thấy tài khoản trong lựa chọn của kết nối.** Token BM có thể thấy nhiều tài khoản hơn. Báo cáo "đang chạy gì" phải nói rõ phạm vi; muốn đủ thì thêm tài khoản vào kết nối trong Zernio hoặc dùng đường BM để đọc.

## 1. Chuẩn bị kết nối

1. Tạo API key ở `https://zernio.com/dashboard/api-keys` (dạng `sk_` + 64 ký tự hex). Đặt vào env `ZERNIO_API_KEY`.
2. Kết nối Meta Ads (loại `metaads`, đăng nhập business) và chọn tài khoản quảng cáo, Page.
3. `check` → `accounts --write`. `401 / invalid_token` = key bị thu hồi, tạo key mới.
4. Dùng qua MCP (Hermes): `mcp_servers.zernio.url: https://mcp.zernio.com/mcp`, header `Authorization: Bearer <key>`. ~118 tool quảng cáo **không** nằm ở tầng trên cùng: gọi qua `call_tool(name="<tool>", arguments={...})`, tìm tool bằng `call_tool(name="search_tools", arguments={"query": "..."})`. Tham số tool là **snake_case**; REST là **camelCase**. Thiếu MCP thì gọi REST trực tiếp `https://zernio.com/api/v1` với `Authorization: Bearer <key>`.

## 2. Tìm tài khoản và tài sản

| Việc | REST | Tool MCP |
|---|---|---|
| Kết nối (lấy `accountId` loại `metaads`) | `GET /v1/accounts`, `GET /v1/accounts/health` | `accounts_list` |
| Tài khoản quảng cáo, tiền tệ, múi giờ, `minimumDailyBudget`, `billingStatus` | `GET /v1/ads/accounts?accountId=` | `ad_accounts_list_ad_accounts` |
| Campaign + ad set **live** (ngân sách thật lúc này) | `GET /v1/ads/accounts/live?accountId=&adAccountId=&status=ACTIVE` | |
| Cây campaign → ad set → ad (bản đồng bộ) | `GET /v1/ads/tree`, `GET /v1/ads/campaigns?includeEmpty=true` | `ad_campaigns_list_ad_campaigns` |
| Bài IG để boost / danh tính IG | `GET /v1/ads/instagram-posts`, `GET /v1/ads/instagram-accounts` | `ad_accounts_list_ads_instagram_posts` |

Bản đồng bộ cập nhật mỗi 15–60 phút; trước khi ghi ngân sách đọc bản **live**. Campaign chưa có ad thì không hiện trong `/ads/tree` (dùng `includeEmpty=true`).

## 3. Mô hình dữ liệu

Giống Meta. `status` (chuẩn hoá của Zernio), `platformCampaignStatus` (= `effective_status` của Meta), `configuredStatus` (công tắc), `reviewStatus` (duyệt). Ngân sách nằm đúng một cấp: `budgetLevel: "adset"` (ABO, mặc định) hoặc `"campaign"` (CBO).

## 4–6. Tạo campaign, ad set, ad

Trên Meta, Zernio tạo theo **cây**, không tạo ad set rỗng (`POST /v1/ads/ad-sets` chỉ dành cho Google):

| Cần | Cách |
|---|---|
| Campaign + ad set + ad trong một lệnh | `POST /v1/ads/create` |
| Campaign rỗng (để thêm ad set sau) | `POST /v1/ads/campaigns` (`goal`, ngân sách = CBO, bỏ trống = ABO, `status: PAUSED`) |
| Thêm ad set vào campaign có sẵn (test nhiều tệp) | `POST /v1/ads/create` với `existingCampaignId` (CBO thì bỏ `budgetAmount`) |
| Thêm ad vào ad set có sẵn (giữ learning) | `POST /v1/ads/create` với `adSetId` (kế thừa ngân sách, tệp, goal, lịch) |
| Nhiều ad trong một ad set (CBO 1-3-5, A1 + 2 dự phòng) | `POST /v1/ads/create` với `creatives: [...]` |
| Dùng lại creative | `existingCreativeId` |

**Trường chính của `POST /v1/ads/create`** (gửi kèm header `Idempotency-Key` để thử lại không tạo trùng):

`accountId`, `adAccountId`, `name`, `goal`, `budgetAmount` + `budgetType` (`daily`|`lifetime`), `budgetLevel`, `status: "PAUSED"`, `headline`, `body`, `imageUrl` **hoặc** `video` (`{url}` hoặc `{id}`), `linkUrl`, `callToAction`, `countries`, `regions`, `cities`, `ageMin`, `ageMax`, `gender`, `interests`, `behaviors`, `audienceId`, `rawTargeting`, `advantageAudience` (`0`|`1`), `placements` (bỏ trống = tự động), `pageId`, `instagramAccountId`, `startDate`, `endDate`, `optimizationGoal`, `billingEvent`, `promotedObject`, `leadGenFormId`, `attributionSpec`, `bodies`/`headlines`/`descriptions` (1–5 phương án chữ), `specialAdCategories`, `platformSpecificData.bidStrategy` / `bidAmount` / `roasAverageFloor`, `multiAdvertiser: "OPT_OUT"`, `aiDisclosure`.

**Bộ tham số theo nhánh:**

| Nhánh | Lệnh | Tham số |
|---|---|---|
| Traffic | `/ads/create` | `goal: traffic` (mặc định `LINK_CLICKS`; muốn LPV: `optimizationGoal: LANDING_PAGE_VIEWS`) |
| Tương tác bài (bài có sẵn) | `/ads/boost` | `goal: engagement` + **`metaObjective: "OUTCOME_ENGAGEMENT"`** → campaign `OUTCOME_ENGAGEMENT`, ad set `POST_ENGAGEMENT`. Không có `metaObjective` thì boost engagement ra `OUTCOME_AWARENESS` (tối ưu reach) |
| Tin nhắn | `/ads/messaging` | `destination: messenger` (hoặc `whatsapp`, `instagram_direct`) hay `destinations: [...]`; ad set `CONVERSATIONS`; `welcomeMessage`; dùng bài có sẵn bằng `platformPostId` |
| Lead form | `/ads/lead-forms` rồi `/ads/create` | Tạo form (nội dung trong `platformSpecificData`, cần `privacyPolicyUrl`) → `goal: lead_generation` + `leadGenFormId` |
| Chuyển đổi web | `/ads/create` | `goal: conversions` + `promotedObject: {pixelId, customEventType: "PURCHASE"}` (pixel thiếu event → `1885014`) |
| Lead qua pixel | `/ads/create` | `goal: lead_conversion` + `promotedObject` |

`goal` → objective: `engagement`→`OUTCOME_ENGAGEMENT`, `traffic`/`page_visits`→`OUTCOME_TRAFFIC`, `awareness`/`video_views`→`OUTCOME_AWARENESS`, `lead_generation`/`lead_conversion`→`OUTCOME_LEADS`, `conversions`/`catalog_sales`→`OUTCOME_SALES`.

**Boost bài có sẵn** (`POST /v1/ads/boost`): `postId` (Zernio) hoặc `platformPostId` (`<pageId>_<postId>` / IG media id), `goal`, `budgetAmount` + `budgetType`, `targeting` lồng (camelCase: `countries`, `ageMin`, `ageMax`, `gender`, `interests`, `placements.publisherPlatforms`), `destinationType`, `callToAction` + `linkUrl` (nút ngoài) hoặc `MESSAGE_PAGE`/`WHATSAPP_MESSAGE`/`INSTAGRAM_MESSAGE` (không kèm link), `adSetId` để gắn vào ad set có sẵn. Boost **không idempotent** qua MCP: không tự thử lại khi timeout, đọc lại trước.

**Tệp:** `rawTargeting` nhận nguyên spec Meta (snake_case) cho thứ trường phẳng không diễn đạt được: `flexible_spec` (một phần tử = OR, nhiều phần tử = AND), `excluded_custom_audiences`, `targeting_automation`. Advantage+ audience giống BM (`age_max` khoá 65). Tìm sở thích/địa lý: `GET /v1/ads/targeting/search?dimension=interest|behavior|geo&q=`. Ước lượng: `POST /v1/ads/targeting/reach-estimate`.

**Media:** ảnh từ base64 `POST /v1/ads/images` (dùng khi Zernio không tải được link fbcdn/link có chữ ký: `403 Failed to download image`); video `POST /v1/ads/videos` (`videoUrl` hoặc base64 ≤ ~4,5 MB; `async: true` rồi đợi `GET /v1/ads/videos/{id}`). Video MP4 H.264/AAC. Link ảnh phải là file tĩnh trực tiếp (link chuyển hướng → `3858258`).

## 7. Dry-run

`validateOnly: true` trên `/ads/create`, `/ads/campaigns`, `/ads/messaging`: Meta kiểm cả cây bằng `execution_options=validate_only`, không tạo gì. Không hỗ trợ: video upload mới, `creatives[]`, `adSetId`, carousel, dynamic creative. Đôi khi Meta không dry-run được ad set chuyển đổi trong campaign mới: nút đó trả "unverified", vẫn tạo được bình thường. **Boost không có dry-run**: tạo `PAUSED` rồi đọc lại. Xem trước giao diện: `POST /v1/ads/preview`, `GET /v1/ads/{adId}/preview`.

## 8. Đọc lại và bàn giao

- `GET /v1/ads/{adId}` (tool `ad_campaigns_get_ad`: chỉ nhận `ad_id`), `GET /v1/ads/campaigns/{id}?accountId=`, `GET /v1/ads/ad-sets/{id}?accountId=`.
- Kết quả duyệt (không bật lại ad): `GET /v1/ads/{adId}/review`.
- Link bàn giao: `https://zernio.com/dashboard/ads` kèm `platformCampaignId`, ID ad, `status`, `reviewStatus`. Có thể đưa thêm link Ads Manager như đường BM.

## 9. Sửa, bật/tắt, nhân bản

- Bật/tắt: `PUT /v1/ads/campaigns/{id}/status`, `PUT /v1/ads/ad-sets/{id}/status`, `PUT /v1/ads/{adId}/status` (giá trị thường `active`/`paused`), hàng loạt `POST /v1/ads/campaigns/bulk-status`. Chỉ khi người dùng duyệt.
- Ngân sách: ABO `PUT /v1/ads/ad-sets/{id}` (`platform`, `budget`); CBO `PUT /v1/ads/campaigns/{id}`. Vẫn chịu giới hạn 4 lần/giờ của Meta. Không đổi được `optimizationGoal`/`destinationType` của ad set đã tạo.
- Tệp ad set: `PUT /v1/ads/ad-sets/{id}` với `targeting` (chỉ khoá gửi lên thay đổi).
- Creative trên Meta không sửa được (trừ tên): tạo creative mới rồi thay.
- **Nhân bản (scale ngang):** `POST /v1/ads/campaigns/{id}/duplicate` (`platform: facebook`, `deepCopy: true`, `renameStrategy`, `renamePrefix`) hoặc `POST /v1/ads/ad-sets/{id}/duplicate` (`campaignId` đích, `statusOption: "PAUSED"`). Bản sao dùng `POST /{id}/copies` của Meta, giữ bài viết gốc nên giữ like/comment. Sau đó sửa tệp bản sao bằng `PUT /v1/ads/ad-sets/{id}`.
- Xoá: `DELETE /v1/ads/campaigns/{id}`, `/ad-sets/{id}`, `/v1/ads/{adId}` chỉ khi người dùng yêu cầu.
- Nhật ký thay đổi tài khoản: `GET /v1/ads/activity`.

## 10. Custom audience (tệp loại trừ, LAL)

`POST /v1/ads/audiences` (không idempotent, không tự thử lại):

- Xem video: `type: "meta_engagement"`, `engagementSource: "video"`, `sourceId: <video id>`, `retentionDays: 7` (sự kiện mặc định `video_watched`).
- Tương tác Page: `type: "meta_engagement"`, `engagementSource: "page"`, `sourceId: <page id>`, `retentionDays: 7`.
- Khách web: `type: "website"`, `pixelId`, `retentionDays` (≤180), `urlContains`.
- Lookalike: `type: "lookalike"`, `sourceAudienceId`, `country: "VN"`, `ratio: 0.01`.
- Danh sách khách: `type: "customer_list"` rồi `POST /v1/ads/audiences/{id}/users`.
- Zernio không có "tệp kết hợp": loại trừ **cả hai** tệp (`audienceExclude` trên `/ads/messaging`, hoặc `rawTargeting.excluded_custom_audiences` trên `/ads/create`) là tương đương.

## 11. Báo cáo

- `report` trong script dùng `GET /v1/ads/insights?accountId=&objectId=act_...&level=&fields=&datePreset=`: Zernio trả **nguyên dòng insights của Meta**, nên số khớp đường BM (đã đối chiếu từng dòng 10/2026) và cùng quy tắc khử trùng `action_type`.
- Theo ngày cả tài khoản: `GET /v1/ads/timeline`. Một campaign kèm breakdown tuổi/giới/vị trí: `GET /v1/ads/campaigns/{id}/analytics?breakdowns=age,gender`. Báo cáo lớn: `POST /v1/ads/insights/reports` rồi `GET /v1/ads/insights/reports/{id}`.

## 12. Page: comment quảng cáo, tin nhắn

- Comment trên ad: `GET /v1/ads/{adId}/comments`, trả lời `POST .../comments/{commentId}/reply`, ẩn `POST .../hide`.
- Đăng bài organic, hộp thư: dùng phần posts/inbox của Zernio qua skill `viet-bai-facebook-fanpage`. Không dùng Graph API trực tiếp khi người dùng đã chọn đường Zernio.

## 13. Rule tự động (phanh ngân sách)

`POST /v1/ads/rules`: kiểm campaign hoặc ad set theo lịch (`schedule.everyMinutes`: 60, 180, 360, 720, 1440), mọi điều kiện phải đúng, hành động `notify` và **tối đa một** trong `pause` / `activate` / `adjust_budget` (`direction`, `percent` ≤ 90 khi giảm, `limit` = sàn/trần ngân sách), `cooldownMinutes` ≥ chu kỳ.

- Điều kiện: `metric` ∈ `spend, impressions, clicks, conversions, ctr, cpc, cpm, cpa, roas`; `window` ∈ `today, yesterday, last_3d, last_7d, last_14d, last_30d`; `op` `> >= < <=`; `value` là **ngưỡng tuyệt đối**. CPA khi 0 chuyển đổi không bao giờ khớp.
- **Không** so được với baseline động ("CPA hôm nay > trung bình 3 ngày + 30%"). Quy đổi phanh trong `test-scale.md`: `cpa` (`last_3d`) `>` `CPA mục tiêu × 1,3` → `adjust_budget` giảm 30%, `limit` = sàn ngân sách, `cooldownMinutes: 2880`. Rule 0 kết quả: `spend` (`today`) `>=` hạn mức chi không kết quả **và** `conversions` (`today`) `<` 1 → `notify` (hoặc `pause` nếu người dùng duyệt).
- "conversions" của Zernio là sự kiện nào phụ thuộc tài khoản: chạy `POST /v1/ads/rules/{id}/preview` để xem rule khớp gì **trước khi** `enabled: true`.
- Rule là cấu hình chạy nền: chỉ tạo/bật khi người dùng duyệt rõ từng rule. Xem lịch sử: `GET /v1/ads/rules/{id}/runs`.

## 14. Giới hạn và lỗi

- Phí Zernio (10/2026): 500 ad **đang chạy** miễn phí, sau đó tính theo ad/tháng; ad tạm dừng không tính. Tiền quảng cáo trả thẳng cho Meta. Kiểm lại bảng giá khi tư vấn.
- `401` key sai/thu hồi. `403 ads_allowance_exceeded`: hết 500 ad miễn phí và chưa có thanh toán. `403 Ads add-on required`: gói cũ hoặc token Meta thiếu quyền ads → kết nối lại. `422 linked_account_required`: dùng `accountId` loại `metaads`/`facebook`, không dùng tài khoản Instagram-login. `409`: trùng nội dung trong 24 giờ. `429`: chờ `Retry-After`.
- Lỗi Meta trả nguyên mã subcode (bảng ở `thuc-thi-bm-api.md` mục 14), ví dụ `1359188` thiếu thanh toán, `3858258` không tải được ảnh, `2446433` CTA chỉ dùng cho link ngoài, `1885154` ad set thiếu đối tượng quảng bá.

## Đối chiếu nhanh BM ↔ Zernio

| Việc | BM (Graph API) | Zernio |
|---|---|---|
| Liệt kê tài khoản | `/me/adaccounts` + business owned/client | `/v1/ads/accounts` (chỉ tài khoản đã chọn) |
| Tạo campaign | `POST /act_{id}/campaigns` | `POST /v1/ads/campaigns` hoặc trong `/ads/create` |
| Thêm ad set vào campaign | `POST /act_{id}/adsets` | `/ads/create` + `existingCampaignId` |
| Thêm ad vào ad set | `POST /act_{id}/ads` | `/ads/create` + `adSetId` |
| Tương tác bài | ad set `POST_ENGAGEMENT` + `ON_POST` | `/ads/boost` + `metaObjective: OUTCOME_ENGAGEMENT` |
| Tin nhắn | ad set `CONVERSATIONS` + `destination_type` | `/ads/messaging` |
| Lead form | `/{page_id}/leadgen_forms` + `LEAD_GENERATION` | `/ads/lead-forms` + `goal: lead_generation` |
| Dry-run | `execution_options=["validate_only"]` (chưa xác minh hết) | `validateOnly: true` (trừ boost) |
| Nhân bản | `POST /{id}/copies` | `/ads/campaigns/{id}/duplicate`, `/ads/ad-sets/{id}/duplicate` |
| Tệp loại trừ | `customaudiences` ENGAGEMENT | `/ads/audiences` `meta_engagement` |
| Phanh ngân sách | Script `watch` + người dùng duyệt | `/ads/rules` (ngưỡng tuyệt đối) hoặc `watch` |
| Báo cáo | `/{id}/insights` | `/v1/ads/insights` (cùng dòng dữ liệu) |
| Tiền | Đơn vị nhỏ nhất của tiền tệ (VND = đồng) | Đơn vị chính |
| Mặc định khi quên `status` | Bắt buộc gửi | **ACTIVE (chạy luôn)** |
