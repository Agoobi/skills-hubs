# settings.json

Copy từ `settings.example.json`. File này đã `.gitignore`, không commit. Biến môi trường ưu tiên hơn file.

| Khoá | Ý nghĩa |
|---|---|
| `execution` | `"bm"` (Graph API, token system user) hoặc `"zernio"`. Script nhận `--via` để ghi đè từng lần |
| `timezone` | Múi giờ IANA dự phòng khi không đọc được múi giờ tài khoản |
| `currency` | Tiền tệ mặc định để trình bày (VND) |
| `meta.access_token` | Token system user. Env `FACEBOOK_ACCESS_TOKEN` ưu tiên hơn |
| `meta.graph_version` | Phiên bản Graph API, mặc định `v21.0`. Env `META_GRAPH_VERSION` |
| `meta.business_id` | ID Business Manager, để liệt kê tài khoản owned/client và Page. Env `META_BUSINESS_ID` |
| `meta.default_ad_account` | Tài khoản dùng khi người dùng không chỉ định (`act_...`) |
| `meta.ad_accounts` | Danh sách tài khoản, `accounts --write` tự điền (`id`, `name`, `currency`, `timezone`, `zernio_account_id`) |
| `zernio.api_key` | Key `sk_...`. Env `ZERNIO_API_KEY` ưu tiên hơn |
| `zernio.base_url` | Mặc định `https://zernio.com/api/v1` |
| `pages.<alias>` | `page_id`, `label`. `accounts --write` thêm Page tìm thấy |
| `pixels.<alias>` | `pixel_id`, `domain`, các sự kiện đang dùng |
| `forbidden_landing_domains` | Domain không bao giờ đề xuất làm sản phẩm/đích |
| `test_scale.result_type` | Kết quả dùng để test/scale (Purchase, Lead, CompleteRegistration, conversation…) |
| `test_scale.target_cost_per_result` | CPA/CPL mục tiêu. Bắt buộc trước khi scale |
| `test_scale.max_daily_budget_total` | Trần tổng ngân sách ngày mọi camp. Bắt buộc trước khi scale |
| `test_scale.test_loss_limit` | Hạn mức lỗ cho đợt test. Bắt buộc trước khi test |
| `test_scale.spend_per_ad_reference` | Mức chi tham khảo mỗi ad/ngày khi ước số ad test (250.000) |
| `test_scale.no_result_spend_multiplier` | Chi ≥ hệ số × mục tiêu mà 0 kết quả → ứng viên tắt (1,5) |
| `test_scale.ctr_warn_pct` / `frequency_warn` | Ngưỡng cảnh báo CTR link (1%) và frequency (3) |
| `test_scale.baseline_days` / `deterioration_trigger_pct` / `budget_cut_pct` / `cooldown_hours` | Phanh ngân sách: 3 ngày, +30%, giảm 30%, 48 giờ |
| `test_scale.scale_step_pct` / `scale_step_max_pct` | Bước tăng ngân sách: 20%, tối đa 30% |
| `test_scale.exclusion_window_days` | Cửa sổ tệp loại trừ khi scale ngang (7) |
| `alerts.overspend_pct` | `watch`: chi hôm nay vượt ngân sách ngày bao nhiêu % thì báo (25) |
| `alerts.no_delivery_after_hour` | Sau giờ này camp ACTIVE mà 0 hiển thị thì báo (8) |
| `alerts.slow_after_hour` / `slow_spend_pct` | Sau giờ này chi dưới x% ngân sách thì báo tiêu chậm (20 giờ, 50%) |
| `alerts.min_spend_to_judge` | Chỉ xét ngưỡng hiệu quả khi đã chi từ mức này |
| `alerts.thresholds.<OBJECTIVE>` | Theo objective (`OUTCOME_SALES`, `OUTCOME_LEADS`, `OUTCOME_ENGAGEMENT`, `OUTCOME_TRAFFIC`, `default`): `max_cost_per_result`, `max_cpc`, `min_ctr_pct`. `null` = tắt |

Mọi ngưỡng là cấu hình của dự án, đặt từ KPI và kinh tế đơn hàng, không phải chuẩn của Meta.
