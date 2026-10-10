# Tài sản thật: logo và quay màn hình

Người dùng ghét logo tự vẽ và demo giả. Lý do chính đáng: một logo vẽ lại sai nét làm cả video trông rẻ tiền, và một màn hình dựng giả dạy người xem bấm vào nút không tồn tại. Vì vậy mọi logo và mọi màn hình sản phẩm trong video phải là **file lấy từ nguồn thật**, có ghi nguồn.

## Sổ nguồn

Mỗi tài sản có một dòng trong `<dự án>/assets/ledger.json`: file, nguồn (URL), loại, thời điểm lấy. Lệnh `logo` và `capture.cjs` tự ghi. Tài sản người dùng đưa thì ghi nguồn là "người dùng cung cấp". Trước khi xuất video, tài sản nào không có dòng trong sổ thì không được dùng.

## Logo

```
python -I scripts/video.py logo <tên-miền-hoặc-tên-thương-hiệu> --out <dự án>/assets/logos
```

Lệnh thử lần lượt và lưu **mọi ứng viên tìm được** kèm nguồn:

1. Thư viện logo SVG công khai (svgl) theo tên thương hiệu.
2. Bộ Simple Icons theo tên thương hiệu (một màu, hợp cho icon nhỏ).
3. Chính trang của thương hiệu: `apple-touch-icon`, icon khai báo trong `<head>`, logo trong `<header>`.

Sau đó **mở từng ứng viên ra xem** (đọc file ảnh) rồi chọn:

- Ưu tiên SVG hoặc PNG nền trong suốt, cạnh ngắn ít nhất 256px.
- Đúng phiên bản logo hiện tại của thương hiệu (so với trang chủ của họ).
- Không kéo giãn, không đổi màu, không cắt mất phần nào. Cần bản trắng cho nền tối thì tìm bản trắng chính thức, không tự tô lại.

Không tìm được logo đạt yêu cầu thì **dừng và hỏi người dùng** xin file. Không vẽ, không dùng chữ cái thay thế, không dùng icon tương tự.

## Quay màn hình thật

```
node scripts/capture.cjs --steps <dự án>/captures/<tên>.steps.json --out <dự án>/captures --format long
```

`capture.cjs` mở trình duyệt thật bằng Playwright, làm theo các bước, quay lại thành video và ghi `<tên>.log.json` (thời điểm từng bước, toạ độ con trỏ) để lúc dựng đặt zoom và viên thuốc tên miền cho đúng.

Thời điểm trong log tính từ lúc script chạy, sớm hơn video một chút. Thời điểm trong file video = `t - videoOffset` (trường `videoOffset` có sẵn trong log, sai số khoảng 0.2 giây). Trước khi đặt zoom, trích một khung hình ở mốc đó ra xem cho chắc.

File bước:

```json
{
  "name": "sepay-tao-webhook",
  "url": "https://my.sepay.vn/",
  "steps": [
    { "do": "wait", "ms": 1200 },
    { "do": "mark", "label": "trang-chu" },
    { "do": "move", "selector": "text=Webhooks" },
    { "do": "click", "selector": "text=Webhooks" },
    { "do": "scroll", "y": 600, "ms": 900 },
    { "do": "type", "selector": "input[name=url]", "text": "https://vi-du.vn/api/webhooks/sepay" },
    { "do": "shot", "name": "form-da-dien" }
  ]
}
```

Các lệnh: `goto`, `wait`, `move`, `click`, `type`, `scroll`, `scrollto` (cuộn mượt đưa một phần tử vào giữa khung), `key`, `mark` (đánh dấu mốc cho lúc dựng), `shot` (chụp ảnh tĩnh), `scene` / `end` (xem dưới). `--format short` quay khung dọc 1080×1920; nhiều trang web hiện bản mobile ở khung này, đúng thứ người xem điện thoại sẽ thấy.

### Quay khớp độ dài lời đọc

Cách cho hình và lời khớp nhau mà không phải cắt ghép bằng tay: **tạo lời đọc trước, rồi quay mỗi cảnh dài đúng bằng lời đọc của nó**.

```json
{ "do": "scene", "id": "s12-ask", "duration": 7.78 },
{ "do": "move", "selector": "main >> text=Is the beige silk bedding set" },
{ "do": "end" }
```

Các bước nằm giữa `scene` và `end` được chạy, phần thời gian còn thiếu được chờ cho đủ `duration`, rồi script cắt ra file `<id>.mp4` dài đúng chừng đó. `duration` của một cảnh = mốc bắt đầu của cảnh sau trừ mốc bắt đầu của cảnh này trong `audio/manifest.json`. Nhiều cảnh liền nhau trên cùng một trang đặt trong cùng một phiên quay để con trỏ và vị trí cuộn nối tiếp tự nhiên. Kết quả báo `overrun` nếu các bước chạy lâu hơn `duration`: khi đó bớt bước hoặc rút ngắn `ms`.

Vì vậy với cảnh quay màn hình, thứ tự thực tế là: duyệt lời đọc (Cổng 4) → tạo giọng (Cổng 6) → quay (Cổng 5). Logo và màu vẫn làm ở Cổng 5 như thường.

### Phóng to nội dung trang

Nhiều trang giới hạn bề rộng nội dung, nên quay ở 1920×1080 sẽ thừa lề hai bên. Thêm `"viewport": { "width": 1440, "height": 810 }` vào file bước: trang được dựng ở khung nhỏ hơn rồi video được phóng lên đúng kích thước xuất, chữ to hơn khoảng 1,33 lần và hơi mềm hơn một chút so với quay gốc. Toạ độ trong log là theo khung `viewport`; nhân với `scale` trong log để ra toạ độ trên video.

Chọn phần tử bằng `main >> text=...` thay vì `text=...` khi trang có menu ẩn chứa cùng dòng chữ, nếu không script sẽ chờ một phần tử không bao giờ hiện.

### Trước khi quay

- **Tự đi qua luồng một lần** (Cổng 2) để biết các bước thật. Không viết file bước từ trí nhớ.
- Quay ở độ phân giải của định dạng đã chốt; không phóng to video nhỏ.
- Dọn màn hình: đóng thông báo, banner cookie (chọn từ chối), tab thừa.

### Đăng nhập và dữ liệu riêng tư

- Script **không gõ vào ô mật khẩu** và sẽ dừng nếu gặp. Trang cần đăng nhập thì chạy:
  ```
  node scripts/capture.cjs --login --profile <thư mục hồ sơ> --url <trang>
  ```
  Trình duyệt mở ra, **người dùng tự đăng nhập**, đóng cửa sổ là xong. Các lần quay sau dùng lại `--profile` đó.
- Gặp CAPTCHA hoặc xác minh "không phải robot": dừng, báo người dùng. Không tìm cách vượt.
- Che dữ liệu thật trước khi quay: số dư, email, số điện thoại, API key, tên khách hàng. Dùng tài khoản thử nếu có. Dữ liệu của khách hàng của người dùng chỉ được quay khi họ nói rõ là được.
- Không quay thao tác có hậu quả thật (thanh toán, xoá, gửi tin) trừ khi người dùng yêu cầu và đang ở môi trường thử.

### Khi không quay được

Trang chặn trình duyệt tự động, cần thiết bị thật, hoặc cần tài khoản người dùng không muốn dùng: hỏi người dùng tự quay màn hình rồi đưa file. Ghi vào sổ nguồn là "người dùng cung cấp". **Không dựng lại màn hình bằng HTML để thay thế**; nếu thiếu hẳn một cảnh thì viết lại lời đọc để không cần cảnh đó.

## Ảnh và video minh hoạ khác

- Chỉ dùng khi lời đọc cần và không có màn hình thật nào hợp. Lấy qua `/media-use` từ nguồn có giấy phép rõ; ghi giấy phép vào sổ nguồn.
- Không dùng ảnh do AI tạo để giả làm ảnh chụp sản phẩm, con người, hay kết quả.

## Bảng xem lại cho người dùng (Cổng 5)

Sau khi gom đủ, gửi người dùng một danh sách ngắn: mỗi tài sản một dòng gồm tên file, nó dùng cho cảnh nào, và nguồn. Kèm ảnh chụp các khung chính của mỗi đoạn quay. Người dùng duyệt xong mới sang bước giọng đọc.
