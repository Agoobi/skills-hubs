# Edit token

Các con số nhịp dựng. Cột "Dài" suy ra từ hai video đã phân tích (xem `phan-tich-phong-cach.md`); cột "Ngắn" là bản chuyển thể cho video dọc, vì kênh gốc không làm Shorts.

## Hai định dạng

| | **Ngắn** | **Dài** |
|---|---|---|
| Khung hình | 1080×1920, 30fps | 1920×1080, 30fps |
| Thời lượng | 25–60 giây | 3–25 phút |
| Số ý | đúng 1 mẹo hoặc 1 lỗi | 1 quy trình trọn vẹn, 4–10 chương |
| Hook | 0–3 giây | 0–20 giây |
| Mở đầu trước khi vào việc | tối đa 6 giây | 45 giây – 2 phút 45 |
| Thẻ chương | không dùng; dùng nhãn bước "1/3" ở góc | có, mỗi chương một thẻ |
| Phụ đề dựng sẵn | bắt buộc, 2–4 từ mỗi lần | không bắt buộc (YouTube tự tạo); nên có nếu đăng nơi khác |
| Kết | 1 câu kêu gọi, 2–3 giây | tóm tắt 1 câu + kêu gọi, 10–20 giây |

Khi người dùng không nói rõ, hỏi ở Cổng 1. Không tự chọn.

## Nhịp cắt

| Đoạn | Độ dài mỗi cảnh (Dài) | Độ dài mỗi cảnh (Ngắn) |
|---|---|---|
| Hook: dựng nhanh kết quả | 2–3 giây | 0.8–1.5 giây |
| Chứng minh từng kết quả | 5–8 giây | 2–3 giây |
| Đồ hoạ giải thích | 6–12 giây, bên trong có 2–4 lần phần tử xuất hiện | 2–4 giây |
| Thẻ chương | 2.5–3 giây | không dùng |
| Quay màn hình thao tác | theo lời đọc; cứ 8–15 giây phải có một thay đổi (zoom, con trỏ đi, viên thuốc, cắt sang đồ hoạ) | 3–6 giây, luôn zoom vào vùng thao tác |

**Giới hạn hình đứng yên**: Dài không quá 8 giây, Ngắn không quá 2.5 giây. Quá giới hạn thì thêm chuyển động có nghĩa (zoom vào chỗ đang nói), không thêm hiệu ứng trang trí.

## Chuyển động

| Token | Giá trị |
|---|---|
| Phần tử vào | trượt lên 24px + mờ dần, 0.45 giây, `power3.out` |
| Các phần tử trong một thẻ | lệch nhau 0.08–0.12 giây |
| Thẻ nổi lên | phóng từ 0.94 lên 1, 0.5 giây, `power3.out` |
| Số liệu trong hoá đơn | hiện từng dòng, cách nhau 0.35 giây, khớp lúc lời đọc nói con số |
| Viên thuốc tên miền | trượt từ trái vào 0.4 giây, đứng 2.5–3 giây, mờ đi 0.3 giây |
| Zoom vào vùng thao tác | từ 1 lên 1.35–1.6, 0.6 giây, `power2.inOut`; giữ; trả về 0.5 giây |
| Con trỏ | phóng to 1.8–2 lần so với mặc định; di chuyển mượt, không nhảy |
| Thẻ chương | số khổng lồ trôi lên 40px suốt thẻ; nhãn vào trước 0.15 giây; tiêu đề hiện từng từ, từ chưa tới để màu `--chapter-title-dim` |
| Chuyển cảnh | cắt thẳng là mặc định. Video B có một lần quét chéo bằng màu nhấn khi vào phần giới thiệu; dùng tối đa 1–2 lần mỗi video |

Không dùng: rung, nảy, xoay, chớp sáng, chuyển cảnh 3D. Phong cách này sạch và chậm vừa phải.

## Từ vựng chuyển động

Bảng trên cho con số. Bảng này cho **tên gọi**, để `storyboard.md` ghi được mỗi cảnh vào bằng kiểu nào thay vì cảnh nào cũng "trượt lên + mờ dần". Từ khoá mượn từ cách dựng explainer cắt dán (collage); chỉ mượn tên và nguyên tắc, còn biên độ đã hạ xuống cho hợp phong cách sạch ở trên. Bản máy đọc được: `assets/tokens.json > motion.entrances`.

| Từ khoá | Phần tử vào thế nào | Giá trị | Hợp với |
|---|---|---|---|
| `rise` | trượt lên + mờ dần (kiểu mặc định ở bảng trên) | 24px, 0.45 giây, `power3.out` | chữ, dòng trong thẻ |
| `grow` | phóng từ nhỏ lên, gốc ở tâm (chính là "thẻ nổi lên") | 0.94 → 1, 0.5 giây, `power3.out` | thẻ, khung trình duyệt |
| `punch` | vào hơi to rồi co về đúng cỡ, không nảy lại | 1.12 → 1, 0.28 giây, `power4.out` | con số, cụm chữ nhấn |
| `swipe` | trượt ngang từ mép vào | 80px, 0.4 giây, `power3.out` | viên thuốc tên miền, thẻ so sánh trái/phải |
| `drop` | rơi từ trên xuống rồi dừng hẳn, không nảy | −60px, 0.4 giây, `power2.in` rồi dừng | dấu gạch, con dấu, thẻ "sai" |
| `unfold` | mở ra theo một chiều bằng `clip-path` | 0.5 giây, `power2.inOut` | thẻ hoá đơn, danh sách, khối code |
| `peel` | lớp phủ bóc chéo đi, lộ thứ bên dưới | 0.55 giây, `power2.inOut` | lật đáp án, trước/sau |
| `draw` | nét vẽ chạy dần (`stroke-dashoffset`) | 0.5–0.8 giây, `power1.inOut` | mũi tên, đường nối, khoanh vùng |
| `count` | số chạy tới giá trị thật | 0.6–1.2 giây, `power2.out` | số dư, giá, phần trăm |
| `zoom-through` | cảnh cũ phóng qua khỏi khung, cảnh mới hiện ra | 1 → 1.8 + mờ, 0.35 giây | chuyển cảnh; tính chung hạn mức 1–2 lần với quét chéo |

Quy tắc dùng:

- **Hai cảnh liền nhau không vào cùng một kiểu.** Video từ 5 cảnh trở lên dùng ít nhất 3 kiểu. Chọn kiểu theo **động từ của câu lời đọc**: "bị trừ" thì `drop`, "mở ra xem" thì `unfold`, "hoá ra" thì `peel`, "tăng lên" thì `count`.
- **Phần tử phụ vào lần lượt, không vào cùng lúc.** Trong một thẻ vẫn lệch 0.08–0.12 giây. Giữa các khối riêng trong một cảnh (2–4 khối) thì mỗi khối vào đúng lúc lời đọc nhắc tới nó.
- **Một cảnh một cụm chữ nhấn** (`on_screen`): 2–5 từ, hiện đúng lúc lời đọc nói tới từ đó, không hiện từ đầu cảnh. Thời điểm ước lượng bằng `vị trí từ trong câu ÷ số từ × độ dài cảnh` (lấy từ `audio/manifest.json`), sau đó nghe lại và chỉnh. Đây không phải phụ đề; phụ đề của video ngắn vẫn giữ như mục dưới.
- **Chuyển động nền sau khi vào xong**: phần tử chính trôi 4–6px theo chiều dọc hoặc thở 1 → 1.015, chu kỳ 4–6 giây, `sine.inOut`. Mỗi phần tử một pha lệch nhau để không cùng nhịp. Không áp lên chữ đang đọc và video quay màn hình. Chuyển động nền **không tính** là thay đổi để qua giới hạn hình đứng yên; giới hạn đó vẫn cần chuyển động có nghĩa.
- Kiểu `flip`, `spiral`, `shatter`, `wobble`, `boing` của cách dựng cắt dán **không dùng** ở đây: chúng là xoay, nảy, rung.

## Thay thế cảnh người nói (video không lộ mặt)

Metics Media dùng người nói ở các câu chuyển ý. Skill này thay bằng:

| Câu của họ dùng người nói | Thay bằng |
|---|---|
| Câu hứa đầu video | Kết quả thật toàn màn hình + chữ lớn 3–6 từ |
| Câu gỡ nghi ngờ ("thường có cái giá") | Đồ hoạ giải thích: thẻ hoá đơn, thẻ so sánh |
| Câu chuyển chương ("việc tiếp theo là") | Thẻ chương, hoặc cắt thẳng vào màn hình mới kèm viên thuốc tên miền |
| Câu trấn an ("đừng lo") | Chữ lớn trên nền `--canvas`, tối đa 2 dòng |

Không tạo người ảo, không dùng ảnh người lấy trên mạng.

## Nhịp lời đọc

Bản dựng đầu tiên của skill bị người dùng nhận xét là **hơi chậm**. Nguyên nhân: giọng đọc mặc định chỉ khoảng 175 từ/phút, và mỗi cảnh có thêm khoảng lặng.

| Token | Giá trị |
|---|---|
| Tốc độ lời đọc tiếng Việt | 210–240 từ/phút (đo bằng `words_per_minute` mà `tts-script` in ra) |
| Cách đạt | `voice_style` yêu cầu đọc nhanh, gọn; nếu vẫn dưới 210 thì thêm `speed` 1.05–1.15 |
| Khoảng lặng giữa hai cảnh | 0.15–0.25 giây (dài), 0.1 giây (ngắn) |
| Thẻ chương | 1.8–2.2 giây |

Sau khi `tts-script` chạy xong, nếu `words_per_minute` dưới 210 thì chỉnh rồi tạo lại trước khi quay và dựng.

## Âm thanh

| Token | Giá trị |
|---|---|
| Lời đọc | −16 LUFS (dài), −14 LUFS (ngắn); đỉnh không quá −1 dBTP |
| Nhạc nền | thấp hơn lời đọc 18–22 dB; tắt hẳn hoặc hạ thêm trong đoạn thao tác dài |
| Khoảng lặng giữa hai cảnh lời đọc | 0.25–0.4 giây (dài), 0.1–0.2 giây (ngắn) |
| Thẻ chương | lời đọc nghỉ, nhạc nhô lên 3 dB |
| Hiệu ứng tiếng | không bắt buộc; thấp hơn lời đọc 12–16 dB; đặt đúng mốc phần tử vào, không dồn ở đầu cảnh |
| Tiếng theo kiểu vào | `rise`/`swipe`/`zoom-through`: whoosh nhỏ · `grow`/`punch`: pop · `drop`: thud · `unfold`/`peel`: tiếng giấy · `count`: tick hoặc coin · con trỏ bấm: click |
| Đa dạng tiếng | hai cảnh liền nhau không dùng cùng một tiếng; mỗi mốc tối đa một tiếng |

Nhạc và hiệu ứng tiếng phải có giấy phép rõ ràng; lấy qua `/media-use`. Không có nhạc phù hợp thì làm video không nhạc.

## Phụ đề dựng sẵn

- **Ngắn**: 2–4 từ mỗi lần, chữ đậm 64px trắng viền tối, đặt ở 62–70% chiều cao khung, từ đang đọc tô màu nhấn. Không che vùng thao tác.
- **Dài**: nếu có, 1–2 dòng, tối đa 42 ký tự mỗi dòng, nền mờ tối, đặt sát đáy trong lề an toàn.
- Thời điểm lấy từ lời đọc thật (`audio/manifest.json`), không ước lượng.

## Danh sách kiểm trước khi xuất

1. Khung hình đầu tiên đã là kết quả hoặc vấn đề, không phải logo hay lời chào.
2. Không cảnh nào vượt giới hạn hình đứng yên.
3. Mọi câu lời đọc có hình khớp nghĩa.
4. Mọi logo và ảnh màn hình có dòng nguồn trong `assets/ledger.json`.
5. Chữ không tràn lề an toàn; ở video ngắn không nằm dưới vùng nút của nền tảng.
6. Tổng thời lượng đúng định dạng đã chốt.
7. Hai cảnh liền nhau không vào cùng một kiểu; mỗi cảnh có tối đa một cụm chữ nhấn, hiện đúng lúc lời đọc nói tới.
