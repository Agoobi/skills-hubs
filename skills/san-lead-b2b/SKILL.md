---
name: san-lead-b2b
description: Săn lead B2B (lệnh /tim-lead): quét dự án, mời thầu, tìm người quyết định.
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
5. Không vượt captcha, đăng nhập hay chống bot của trang nào. Cổng `.gov.vn` chặn máy chủ nước ngoài: đọc qua proxy Việt
   Nam nếu quản trị viên nhập ở Cài đặt (như người dùng ở Việt Nam), không có thì qua Google (`site:`), hoặc bỏ qua.
6. Thông tin cá nhân: chỉ thông tin công việc công khai (chức danh, công ty, link LinkedIn, liên hệ doanh nghiệp).
   SĐT / email lấy từ trang của chính công ty, trang tra cứu doanh nghiệp, hoặc thư mời chào giá; mỗi giá trị phải có
   trong trang nguồn (script kiểm lại). Không đoán email theo mẫu tên, không lấy số fax hay mã số thuế làm SĐT.
7. **Không xoá dữ liệu** (cơ hội, người liên hệ, lần quét) trừ khi user nói rõ "xoá" trong chính tin nhắn đó.
   "Chạy lại hết" là quét thêm, không phải xoá.

## Lệnh

Chạy từ thư mục skill: `python3 -I scripts/lead.py <lệnh>` (chỉ cần Python 3).

| Lệnh | Làm gì |
| --- | --- |
| `status` | Key Apify, chi phí tháng, LLM, ngành, vùng, nguồn, lần quét gần nhất. Chạy đầu tiên. |
| `start --trigger chat` | Bắt đầu 1 lần quét **ở nền** (3–10 phút, lâu hơn giới hạn 1 lệnh). In mã lần quét. |
| `start --full` | Quét đầy đủ: mọi nhóm truy vấn (~140 truy vấn Google, chia lô 40), đọc thêm link trang theo dõi, tìm liên hệ tối đa 25 cơ hội. ~$0.6–0.8 Apify. Chỉ khi user xin "quét lại hết / quét đầy đủ". |
| `wait <mã>` | Chờ tối đa 170 giây, in tiến độ; xong thì in báo cáo. Chưa xong ("chưa xong") thì chạy lại `wait <mã>`. |
| `report [--hours 26]` | Báo cáo cơ hội mới còn hạn / tin mới (bảng Markdown, cột Liên hệ) + link trang. |
| `top [--limit 10]` | Cơ hội điểm cao đang ở mục Mới (còn mới), kèm id. |
| `audit` | **Đối chiếu từng cơ hội với bài nguồn**: tên công ty, tỉnh, hạn chót, thiết bị "theo nguồn", giá trị, SĐT đầu mối; mời thầu quá hạn / tin cũ còn hiện; thiếu liên hệ. In OK / XEM / LỖI cho từng cơ hội. |
| `explain <url>` | Đọc **1 link** như lúc quét: giữ hay loại, vì sao, ngày đăng, hạn chót, thiết bị, đầu mối, và trang Săn lead có nhận không. Dùng khi user gửi link hỏi "sao không có". |
| `contacts [--limit 10] [--all]` | Tìm website, SĐT, email, mã số thuế, người đại diện, LinkedIn công ty cho cơ hội chưa có SĐT / email (`--all`: tìm lại ngay, bỏ mốc 3 ngày). `--opportunity <id>`: 1 cơ hội. ~$0.014–0.03 / công ty. |
| `people --opportunity <id>` | Tìm người ra quyết định cho 1 cơ hội (`all`: mọi cơ hội đủ điểm còn thiếu người). Tốn Apify. |
| `check-sources` | Thử từng trang theo dõi: đọc được không, bao nhiêu link, bao nhiêu link đáng đọc. |

## Quy trình (làm tới cùng, không bỏ dở)

**A. User gõ `/tim-lead`, hoặc "tìm lead", "quét lead", "tìm khách", "có dự án / mời thầu mới không"**

1. `status`. Không có key Apify: nói user vào Săn lead → Cài đặt → Key Apify (vẫn quét được trang theo dõi, Google
   News). "Hàng bên bán" trống: nhắc user ghi (điểm và thiết bị gợi ý dựa vào đó).
2. `start --trigger chat` → `wait <mã>` **lặp lại tới khi thấy "Xong lần quét"** (có thể 5–8 lần). Không dừng giữa
   chừng, không bảo user "chạy lại sau". Báo user 1 câu ngắn mỗi 2–3 lượt chờ.
3. `audit`. Có **LỖI** thì đọc dòng lỗi, mở link nguồn (`explain <url>` nếu cần) và báo user rõ: cơ hội nào, sai gì,
   nguồn ghi gì. **THIẾU** liên hệ: chạy `contacts --opportunity <id>` cho từng cơ hội điểm cao còn thiếu (tối đa 5),
   rồi `report` lại.
4. Dán **nguyên bảng báo cáo** (giữ link, cột Liên hệ). Thêm 2–3 câu: nên gọi ai trước và vì sao — **mời thầu còn hạn
   gần nhất trước**, rồi dự án mới điểm cao có SĐT. Không thêm thông tin ngoài bảng / nguồn.
5. Lần quét báo lỗi:
   - "ví LLM của Hermes hết tiền (402)": báo user nạp ví (Ví & hoá đơn của nhà cung cấp LLM); tin chưa đọc sẽ đọc ở lần sau.
   - "gói Apify miễn phí hết lượt" / "chạm trần tháng": báo user; nguồn miễn phí (trang theo dõi, Google News) vẫn chạy.
     Đổi key / nâng gói ở Săn lead → Cài đặt. Không tự nâng trần.
   - "0 cơ hội mới": bình thường (tin đã có thì gộp). Vẫn dán bảng các cơ hội còn mới trong 26 giờ.

**B. User hỏi "sao không có …", gửi 1 link, hoặc nói "rõ ràng có SĐT / có mời thầu"**

1. Gửi link: `explain <url>`. Trả lời theo kết quả: đã hết hạn (ghi ngày), tin cũ, ngoài ngành / vùng, không phải thiết
   bị, trang bị chặn (captcha / chặn IP)… Nếu là cơ hội đúng mà bị loại oan: nói rõ, ghi lại link và lý do để sửa skill.
2. "Sao không có SĐT / email" cho 1 cơ hội: `top` lấy id → `contacts --opportunity <id>`. Vẫn không có: giải thích nguồn
   nào đã thử (website công ty, trang tra cứu, đoạn trích Google theo mã số thuế) và vì sao (công ty mới, số bị che,
   trang tra cứu chặn bằng captcha — **không vượt**). Không bao giờ bịa hay đoán số.
3. "Thiết bị lấy ở đâu": dòng **"Hạng mục thiết bị (theo nguồn)"** là nguồn ghi; **"Thiết bị gợi ý (AI đoán, nguồn
   không ghi)"** là đoán từ loại nhà máy, chỉ lấy trong "Hàng bên bán". Nói rõ là đoán.
4. "Sao toàn tin tức, ít mời thầu": mời thầu thật đến từ đơn vị có phòng lab (trung tâm / viện kiểm nghiệm, trường, chi
   cục thú y) và vài doanh nghiệp đăng thư mời (Bidiphar, DHG, Domesco, Sochem); doanh nghiệp tư nhân thường hỏi giá trực
   tiếp nên chỉ thấy qua tin dự án. Gói nhà nước đầy đủ nằm trên muasamcong: cần API đấu thầu trả phí (DauThau.info).

**C. User hỏi về 1 cơ hội / muốn tìm người**: `top` lấy id → `people --opportunity <id>` → báo người tìm được (tên, chức
danh, link LinkedIn, gợi ý tiếp cận). "Đầu mối gián tiếp" là người ở đúng công ty nhưng không ra quyết định.

**D. User muốn thêm nguồn / đổi ngành, vùng, trần chi phí, proxy**: hướng dẫn sửa ở Săn lead → Cài đặt (Trang theo dõi
thêm, Từ khoá thiết bị thêm, Ngành, Vùng, Giới hạn và chi phí, Proxy Việt Nam). Agent không tự sửa.

**E. User nói "chạy lại hết / quét lại / kiểm tra lại"**: `start --full` → `wait` tới khi xong → `contacts --all` →
`people --opportunity all` → `audit` → báo cáo. **Không xoá cơ hội, người liên hệ hay dữ liệu nào** — chỉ xoá khi user
nói rõ "xoá" trong chính tin nhắn đó (sale có trạng thái, ghi chú trên đó).

### Kiểm tra trước khi báo (tự soát)

- Mỗi dòng báo cáo có link nguồn; mời thầu có hạn chót ≥ hôm nay; tin dự án trong "Bỏ tin cũ hơn" (mặc định 30 ngày).
- SĐT / email trong bảng là của **chính** doanh nghiệp (hoặc phòng mua sắm ghi trong thư mời), không phải của sở, ban
  xúc tiến, tòa soạn, trang tra cứu. SĐT nhãn "đăng ký kinh doanh" là số đăng ký thuế (có thể là kế toán / dịch vụ).
- Tỉnh theo tên mới sau 1/7/2025; tên xã giống tên tỉnh (xã Khánh An ở Cà Mau) không phải tỉnh đó.
- Có gì `audit` báo LỖI mà chưa giải thích được: nói thẳng với user, không giấu.

## Lệnh `/tim-lead` (cài 1 lần)

- **Open WebUI:** Workspace → Prompts có prompt lệnh `tim-lead` (mọi người dùng xem được). Gõ `/tim-lead`, Enter để
  chọn, Enter để gửi. Nội dung prompt (cùng câu với alias dưới) bảo agent làm Quy trình A tới cùng.
- **Telegram, Coquifly (gateway Hermes):** thêm alias vào `~/.hermes/config.yaml` rồi khởi động lại gateway:

```yaml
quick_commands:
  tim-lead:
    type: alias
    target: "/san-lead-b2b Tìm lead ngay. Dùng skill san-lead-b2b, làm đúng Quy trình A tới cùng: quét mới (scripts/lead.py start --trigger chat, rồi wait lặp lại tới khi xong), chạy audit, tìm liên hệ (contacts --opportunity) cho cơ hội điểm cao còn thiếu SĐT/email, rồi dán nguyên bảng báo cáo và 2-3 câu nên liên hệ ai trước và vì sao (mời thầu còn hạn gần nhất trước). Báo rõ mọi LỖI audit tìm thấy."
```

Cả hai đường đều cần ví LLM của Hermes còn tiền (agent và bước đọc tin đều gọi LLM).

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
