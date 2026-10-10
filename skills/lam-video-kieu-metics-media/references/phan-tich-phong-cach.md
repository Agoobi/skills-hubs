# Phân tích phong cách Metics Media

Nguồn: xem trực tiếp khung hình của hai video trên kênh `@MeticsMedia` (tháng 10/2026), chụp ở nhiều mốc thời gian:

- **A**: "How to Build $10K Websites in Minutes (Claude AI)", 25:09, khoảng 600 nghìn lượt xem.
- **B**: "Hermes Agent - Full Tutorial & Setup Guide (For Beginners)", 34:23, khoảng 500 nghìn lượt xem.

Kênh không có Shorts. Phần "video ngắn" trong skill này là bản chuyển thể từ cùng ngôn ngữ hình ảnh, không phải bản sao của thứ họ đã làm.

File này mô tả **cái họ làm và vì sao nó giữ người xem**. Con số dùng khi dựng nằm ở `design-tokens.md` và `edit-tokens.md`.

## 1. Bộ khung của một video

| Đoạn | Thời lượng quan sát | Họ làm gì |
|---|---|---|
| Hook | 0:00 – 0:20 | Một câu hứa kết quả, hình là **kết quả thật** (video A: dựng nhanh 5 trang web đã làm xong, mỗi trang 2–3 giây). |
| Chứng minh | 0:20 – 0:55 | Đi qua từng kết quả, mỗi cái 5–8 giây, lời đọc tả đúng thứ đang thấy trên màn hình. |
| Gỡ nghi ngờ | 0:55 – 1:30 | Nêu thẳng điều người xem đang nghĩ ("trang đẹp thế này thường có cái giá") rồi trả lời bằng đồ hoạ: hoá đơn $4,500 / $2,800 / $3,200. |
| Cách làm trong 1 câu | 1:30 – 2:20 | "Bạn chỉ cần nói với Claude bạn muốn gì". Hình là sơ đồ giản lược của giao diện thật. |
| Trấn an + lộ trình | 2:20 – 2:47 | "Nghe có vẻ phức tạp thì đừng lo", rồi vào chương 1. |
| Thân bài | 2:47 – 24:40 | 10 chương, mỗi chương mở bằng một thẻ chương, bên trong là quay màn hình thật. |
| Kết | 24:40 – hết | Tóm tắt 1 câu bằng đồ hoạ, nhắc link, cảm ơn. Không kéo dài. |

Video B cùng khung: hook 0:00–0:30, giới thiệu sản phẩm đến 1:23, chương 1 bắt đầu, chương thao tác bắt đầu ở 2:13.

Điều đáng học: **phần mở đầu dài gần 3 phút nhưng không có giây nào là "xin chào các bạn"**. Mỗi 5–10 giây đổi một kiểu hình (kết quả thật → đồ hoạ → người nói → đồ hoạ).

## 2. Năm kiểu hình và vai trò của từng kiểu

1. **Kết quả thật** (quay màn hình sản phẩm đã xong). Dùng để mở đầu và để chứng minh. Luôn là thứ thật, không phải ảnh minh hoạ.
2. **Đồ hoạ giải thích**: nền sáng gần trắng có quầng màu của thương hiệu, thẻ trắng bo góc đổ bóng mềm. Bên trong là **giao diện giản lược**: thanh xám thay cho chữ, ô vuông thay cho ảnh, nhưng **logo là logo thật** (dấu sao Claude, chân dung Hermes). Dùng khi nói ý trừu tượng: giá, so sánh, quy trình.
3. **Thẻ chương**: nền tối theo màu thương hiệu, số chương khổng lồ mờ phía sau, dòng "Chapter 2 of 10", tiêu đề đậm. Video B đổi sang kiểu chữ đơn cách và hình tượng Hermes: hệ thống giữ nguyên, lớp áo đổi theo chủ đề.
4. **Quay màn hình thao tác**: trình duyệt thật, toàn màn hình, con trỏ được phóng to. Khi vào một trang mới có **viên thuốc trắng ở góc dưới trái** ghi logo thật + tên miền ("claude.ai"). Giữa đoạn thao tác thỉnh thoảng cắt sang một đồ hoạ ngắn để tóm tắt lựa chọn (ví dụ thẻ so sánh gói Pro $20 và Max $100).
5. **Người nói trước máy quay**: xuất hiện 1–3 giây ở đầu, rồi quay lại ở những câu chuyển ý. Skill này làm video **không lộ mặt**, nên vai trò đó chuyển cho đồ hoạ chữ lớn hoặc kết quả thật (xem `edit-tokens.md`, mục thay thế người nói).

## 3. Vì sao nó không chán

- **Hình luôn khớp lời**. Câu nói "một giọt rơi từ đầu trang" đi cùng đúng cảnh giọt rơi. Không có cảnh nền chung chung.
- **Đổi kiểu hình trước khi mắt quen**. Trong phần mở đầu không kiểu hình nào đứng quá 10 giây.
- **Nói điều người xem đang nghĩ**. "Nghe có vẻ phức tạp", "bạn không cần biết code", "làm theo luồng chứ đừng bám từng ảnh chụp" (video B, 1:15). Mỗi câu gỡ một lý do bỏ xem.
- **Con số cụ thể**: $10,000, $20/tháng, "Chapter 4 of 10". Người xem biết mình đang ở đâu và còn bao lâu.
- **Mở vòng rồi đóng vòng**: "setup mới chỉ là phần đầu của video này" (video B, 0:40) giữ người xem qua đoạn cài đặt.
- **Thẻ chương là chỗ nghỉ**. 2–3 giây, không lời hoặc một câu ngắn, cho người xem biết đã xong một việc.

## 4. Giọng và lời

- Câu ngắn, ngôi thứ nhất, thì hiện tại: "Go down and click add, and then click connect."
- Mỗi câu một hành động hoặc một ý. Không có câu mở bài kiểu "trong video hôm nay chúng ta sẽ cùng nhau tìm hiểu".
- Lời đọc chỉ vào thứ đang hiện: "ở góc dưới này", "ngay tại đây".
- Tốc độ vừa phải, có nghỉ ngắn ở thẻ chương.
- Phụ đề trong ảnh chụp là phụ đề tự động của YouTube, không phải chữ dựng sẵn trong video.

## 5. Thứ không nên bắt chước

- **Người dẫn và bối cảnh quay**: đó là nhận diện riêng của họ.
- **Logo, hình hoạ, nhạc của kênh họ**.
- **Lời thoại nguyên văn**. Học cấu trúc câu, viết lời của mình.
- **Phần mở đầu 3 phút** cho video ngắn: bản ngắn chỉ có 2–3 giây để giữ người xem.
