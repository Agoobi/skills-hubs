# Viết kịch bản: hook, cấu trúc, lời đọc tự nhiên

Đọc file này ở Cổng 3 (hook và dàn ý) và Cổng 4 (lời đọc).

## Hook

Hook là **khung hình đầu tiên + câu đầu tiên**. Hai thứ phải cùng nói một điều.

Ba dạng hook, luôn đề xuất cả ba cho người dùng chọn:

1. **Kết quả trước**: cho thấy thứ đã làm xong rồi mới nói cách làm.
   "Trang này mình dựng trong 20 phút. Đây là từng bước."
2. **Vấn đề đang xảy ra**: chỉ vào một lỗi người xem có thể đang mắc.
   "Web bạn dựng bằng AI có thể đang cộng tiền hai lần cho một lần chuyển khoản."
3. **Điều trái dự đoán**: một sự thật làm người xem phải xem tiếp để hiểu.
   "Phần khó nhất của một web dựng bằng AI không phải là dựng."

Quy tắc:

- Câu đầu **tối đa 12 từ** (ngắn) hoặc 20 từ (dài), có một con số hoặc một danh từ cụ thể.
- Không mở bằng lời chào, tên kênh, "trong video này", hay câu hỏi tu từ.
- Lời hứa phải được **giữ đúng** trong video. Nếu kết quả thật không tới mức đó thì hạ lời hứa, không thổi phồng.
- Hình của hook phải là tài sản thật đã có (kết quả, màn hình lỗi). Chưa có thì quay ở Cổng 5 trước khi chốt hook.

## Cấu trúc

**Video ngắn (25–60 giây)**

| Thời điểm | Nội dung |
|---|---|
| 0–3s | Hook: hình thật + câu hứa hoặc câu vấn đề |
| 3–8s | Vì sao đáng quan tâm, đúng 1 câu |
| 8–45s | 2–3 bước, mỗi bước 1 câu + 1 cảnh thao tác đã zoom |
| cuối | Kết quả sau khi làm + 1 câu kêu gọi của kênh |

Một video ngắn chỉ mang **một ý**. Nếu dàn ý có "và còn nữa", đó là hai video.

**Video dài (3–25 phút)**

| Đoạn | Nội dung |
|---|---|
| Hook | Kết quả thật + câu hứa (0–20s) |
| Chứng minh | Đi qua kết quả, tả đúng thứ đang thấy |
| Gỡ nghi ngờ | Nêu 1–2 điều người xem đang nghĩ ("tốn tiền không", "cần biết code không") và trả lời bằng số liệu thật |
| Lộ trình | "X bước", mỗi bước một cụm 2–5 từ; đây cũng là tên các chương |
| Các chương | Mỗi chương: việc cần làm → thao tác → kết quả nhìn thấy được |
| Kết | Tóm tắt 1 câu, kêu gọi của kênh |

Tên chương là **động từ + đối tượng** ("Kết nối SePay", "Chạy migration"), không phải danh từ chung ("Giới thiệu", "Cài đặt").

Giữ người xem qua đoạn dài:

- Trước một đoạn cài đặt khô, mở một vòng: "Xong bước này bạn sẽ thấy tiền vào ví tự động."
- Sau mỗi chương, cho thấy **một thứ đã chạy** trước khi sang chương sau.
- Nói trước những chỗ dễ sai: "Chỗ này nhiều người dán nhầm key."

## Lời đọc tự nhiên

Lời đọc là để **nghe**, không phải để đọc bằng mắt.

- Mỗi câu một ý, một hành động. Câu dài hơn 18 từ thì tách.
- Dùng từ người ta nói thật: "bấm", "dán", "kéo xuống", "ngay chỗ này". Tránh "tiến hành", "thực hiện thao tác", "như các bạn có thể thấy".
- Chỉ vào màn hình: "ở góc trên bên phải", "dòng thứ hai". Câu nào không chỉ được vào đâu thì cần một đồ hoạ riêng.
- Số đọc được thành tiếng: viết "hai mươi đô một tháng" trong lời đọc, hình hiện "$20/tháng".
- Thuật ngữ quen dùng giữ nguyên tiếng Anh (webhook, deploy, API key); lần đầu xuất hiện thêm nửa câu giải thích.
- Xưng hô theo `channels.<alias>.persona`. Không đổi xưng hô giữa video.
- Không dùng dấu ngoặc, gạch đầu dòng, ký hiệu trong lời đọc: máy đọc sẽ đọc sai hoặc ngắt kỳ.
- Tránh các cụm trong `channels.<alias>.avoid`.

**Kiểm tra bằng tai**: đọc to từng câu. Câu nào phải lấy hơi giữa chừng hoặc nghe như văn bản thì viết lại.

**Không bịa**: mọi bước, giá, tên nút, kết quả trong lời đọc phải có trong `research.md` của Cổng 2 kèm nguồn. Thiếu thì quay lại hỏi người dùng, không đoán.

## Định dạng `script.json`

```json
{
  "format": "short",
  "channel": "khang-dev",
  "language": "vi",
  "title": "Web AI cộng tiền hai lần",
  "scenes": [
    {
      "id": "s01-hook",
      "kind": "result",
      "vo": "Web này cộng tiền hai lần cho một lần chuyển khoản.",
      "visual": "Quay màn hình ví: số dư nhảy từ 100k lên 300k sau một giao dịch 100k",
      "on_screen": "+200.000đ ???",
      "asset": "captures/vi-nhay-so.mp4"
    }
  ]
}
```

`kind` là một trong: `result`, `explainer`, `chapter`, `screen`, `text`, `outro`. `vo` để trống cho thẻ chương không lời. `asset` trỏ tới file thật trong dự án; cảnh `explainer` và `text` có thể không cần.

Sau khi người dùng duyệt, file này là nguồn duy nhất cho lời đọc: `tts-script` đọc nó để tạo âm thanh và đo thời lượng.
