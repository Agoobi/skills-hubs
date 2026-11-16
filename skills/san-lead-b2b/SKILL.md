---
name: san-lead-b2b
description: Săn lead B2B: quét dự án, mời thầu, tìm người quyết định.
version: 0.1.0
author: Agoobi
license: MIT
metadata:
  hermes:
    category: sales
    tags: [lead, b2b, apify, linkedin, dau-thau, du-an, vietnamese, san-lead]
---

# san-lead-b2b

Tìm **cơ hội bán thiết bị** cho doanh nghiệp B2B ở Việt Nam và **người ra quyết định** ở đúng công ty đó, rồi ghi vào
trang **Săn lead** của Open WebUI (sidebar → Săn lead). Sale xem, đổi trạng thái (Mới / Đang theo / Đã liên hệ / Bỏ
qua), ghi chú, xuất CSV ở đó.

Cách làm: **tìm công ty sắp mua trước, tìm người sau.** Script đọc tin từ Google News, các trang danh sách được theo dõi
(ĐTM của tỉnh, thông báo mời chào giá của doanh nghiệp), tìm Google qua Apify (mời chào giá, ĐTM, cấp phép, khởi công,
mở rộng, tuyển người cho nhà máy mới, trang đấu thầu), cho LLM của Hermes đọc từng tin, rồi tìm người trên LinkedIn
(Google X-ray và Apify) cho cơ hội điểm cao. Trang Săn lead kiểm tra lại mọi thứ agent gửi (ngành, vùng, link nguồn,
hạn chót, tin cũ), gộp trùng và chấm điểm 0–100.

Trang Săn lead là phần của [openwebui-custom](https://github.com/Agoobi/openwebui-custom). Key Apify, hồ sơ bên bán,
ngành, vùng, nguồn, trần chi phí đều đặt trên trang đó (Cài đặt); skill lấy về qua token trong
`<DATA_DIR>/cqf/lead/agent.json` (cùng máy). Không cần biến môi trường.

## Quy tắc sắt

1. **Agent không liên hệ ai.** Không gửi tin, email, kết nối LinkedIn, gọi điện. Chỉ tìm, ghi vào Săn lead, báo trong chat.
2. **Không bịa.** Tên người, số điện thoại, email, hạn chót chỉ lấy từ nguồn. Thiếu thì để trống. Thiết bị agent tự suy
   ra luôn đánh dấu "gợi ý" (`equipment_inferred`). Mỗi cơ hội phải có link gốc.
3. **Không đổi cài đặt, key hay trạng thái của sale.** Đó là việc của người dùng trên trang Săn lead (API tự chặn).
4. **Tôn trọng trần chi phí.** Script tự dừng gọi Apify khi chạm trần mỗi lần quét / mỗi tháng. Không tự nâng trần,
   không chạy `run` nhiều lần liền để "tìm thêm".
5. Không vượt tường lửa, captcha hay chặn IP của trang nào. Trang chặn máy chủ thì đọc qua Google (`site:`), hoặc bỏ qua.
6. Thông tin cá nhân: chỉ thông tin công việc công khai (chức danh, công ty, link LinkedIn, liên hệ doanh nghiệp).

## Lệnh

Chạy từ thư mục skill: `python3 -I scripts/lead.py <lệnh>` (chỉ cần Python 3).

| Lệnh | Làm gì |
| --- | --- |
| `status` | Key Apify, chi phí tháng, LLM, ngành, vùng, nguồn, lần quét gần nhất. Chạy đầu tiên. |
| `start --trigger chat` | Bắt đầu 1 lần quét **ở nền** (mất 3–10 phút, lâu hơn giới hạn 1 lệnh). In mã lần quét. |
| `wait <mã>` | Chờ tối đa 170 giây, in tiến độ; xong thì in báo cáo. Chưa xong thì chạy lại `wait <mã>`. |
| `report [--hours 26]` | Báo cáo cơ hội mới (bảng Markdown) + link trang Săn lead. |
| `top [--limit 10]` | Cơ hội điểm cao đang ở mục Mới, kèm id. |
| `people --opportunity <id>` | Tìm người ra quyết định cho 1 cơ hội (tốn Apify). |
| `check-sources` | Thử từng trang theo dõi: đọc được không, bao nhiêu link. |

## Quy trình

**User nói "quét lead", "tìm khách", "có dự án mới không"...**

1. `status`. Chưa có key Apify: nói user vào Open WebUI → **Săn lead** → **Cài đặt** → **Key Apify** (lấy ở
   console.apify.com → Settings → API & Integrations), vẫn quét được Google News và trang theo dõi. "Hàng bên bán" trống:
   nhắc user ghi để điểm và gợi ý tiếp cận sát hơn.
2. `start --trigger chat`, rồi `wait <mã>` lặp lại tới khi thấy "Xong lần quét". Báo user ngắn gọn trong lúc chờ.
3. **Dán nguyên bảng báo cáo** script in ra (giữ link). Thêm 2–3 câu: cơ hội nào đáng gọi trước và vì sao (dựa vào
   điểm, hạn chót, gợi ý tiếp cận). Không thêm thông tin ngoài bảng.
4. Lỗi "ví LLM của Hermes hết tiền (402)": báo user nạp ví (trang Ví & hoá đơn của nhà cung cấp LLM) rồi quét lại;
   tin chưa đọc sẽ được đọc ở lần sau.

**User hỏi về 1 cơ hội / muốn tìm người:** `top` lấy id → `people --opportunity <id>` → báo người tìm được (tên, chức
danh, link LinkedIn, gợi ý tiếp cận). Muốn xem đủ thì mở trang Săn lead.

**User muốn thêm nguồn / đổi ngành, vùng, trần chi phí:** hướng dẫn sửa trên trang Săn lead → Cài đặt (Trang theo dõi
thêm, Từ khoá thiết bị thêm, Ngành, Vùng, Giới hạn và chi phí). Agent không tự sửa.

## Quét tự động mỗi sáng (cài 1 lần)

```bash
cp scripts/cron_san_lead.py ~/.hermes/scripts/san-lead.py
hermes cron create "30 6 * * *" --name "San lead hang ngay" --script san-lead.py --no-agent --deliver coquifly
```

Cron chạy script không qua LLM của agent (chỉ LLM đọc tin), gửi bảng báo cáo vào kênh chính. Tiến độ chi tiết ở
`state/run-*.log`; mỗi lần quét cũng hiện ở Săn lead → **Lần quét** (số tin, cơ hội mới, chi phí).

## Chi phí (tham khảo, gói Apify Free $5/tháng)

- Google News, trang theo dõi: miễn phí.
- Tìm Google qua Apify: khoảng $0.0045 / truy vấn (18 truy vấn / lần ≈ $0.08), tìm bài gốc cho tin Google News được giữ
  và tìm người qua Google: thêm khoảng $0.0045 / lượt.
- LinkedIn qua Apify: $0.10 / 25 hồ sơ; lượt tìm theo chức danh chạy mỗi tuần 1 lần.
- LLM đọc tin: theo ví của Hermes (deepseek flash, tắt suy luận: vài cent / lần quét).

Chi tiết nguồn, cách chấm điểm và cách đọc tin: `references/nguon-va-cham-diem.md`.
