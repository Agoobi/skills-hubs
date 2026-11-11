---
name: edit-talking-head-broll
description: Thêm b-roll motion graphic vào video talking head có sẵn (người nói trước máy, bài giảng, đọc quảng cáo): chép lời tiếng Việt có mốc từng từ, quyết định từng câu để nguyên người nói / chèn thẻ đè lên / phủ kín bằng cảnh minh hoạ, vẽ đồ hoạ bằng canvas theo đúng lời nói, xuất MP4 giữ tiếng gốc và lớp b-roll trong suốt. Chạy hoàn toàn trên Claude.
---

# Edit Talking Head B-roll

Dựa trên skill `talking-head-b-roll` của iart.ai (MIT, xem `LICENSE-iart.txt`), đã chỉnh cho kênh tiếng Việt chạy trên Claude: chép lời bằng sherpa-onnx (zipformer-vi), font Be Vietnam Pro cục bộ, bảng màu preset `aiagentvn`, khung dọc 9:16 theo `safe-zone-chu-9x16`.

**Dùng khi:** video người nói đã quay xong, lời và cách nói đã chốt, chỉ cần thêm hình cho đỡ nhàm. **Không cắt, không dời, không crop footage**: mọi thứ là một lớp vẽ đè lên.
**Không dùng khi:** cần cắt lỗi nói, làm mịn da, hook 3 nhịp → `edit-ads-talking-head-9x16`; cần style V06 đã duyệt → `edit-talking-head-v06` (có thể dùng skill này cho phần b-roll bên trong).

Làm một lượt, không hỏi những gì footage hoặc mặc định đã trả lời; khi giao thì liệt kê những gì đã tự chọn. `<skill>` dưới đây là thư mục chứa file này.

## 0. Chuẩn bị
```bash
mkdir -p work && cd work                       # thư mục chứa video
cp -r <skill>/fonts ./fonts                     # font phải nằm cạnh page.html
npm i -s playwright-core                        # một lần mỗi thư mục làm việc
pip install --break-system-packages -q sherpa-onnx numpy
```
Chromium/Chrome có sẵn trên Claude (`/usr/bin/google-chrome`); **không** chạy `playwright install`. Footage nằm trên máy người dùng thì lấy qua công cụ liên kết máy tính (`device_stage_files`) hoặc xin người dùng gửi kèm.

## 1. Chép lời
```bash
python3 <skill>/scripts/transcribe_vi.py talk.mp4      # → transcript.json + in từng câu kèm mốc
```
Lần đầu tự tải model zipformer-vi (~260 MB) từ GitHub releases của k2-fsa/sherpa-onnx (huggingface thường bị chặn). Định dạng `transcript.json` khớp với `render.mjs`: `{video, words:[{text,start,end}], lines:[{start,end,text}]}`.
Đọc hết lời trước khi quyết định. Zipformer có thể nghe sai tên riêng, tiếng Anh, con số: có kịch bản thì đối chiếu; số không khớp với phần còn lại thì **không đưa lên hình** và báo khi giao. Chữ trên màn hình viết đúng chính tả (có dấu, viết hoa tên riêng), không chép nguyên chữ thường của transcript.

## 2. Lên kế hoạch: ba cách xử lý
- **A. Người nói** — chỉ video. Dùng cho câu mở, ý kiến/câu chuyện cá nhân, cảm xúc, CTA, câu kết.
- **B. Overlay** — video vẫn thấy, một lớp chữ/số/icon/danh sách ngắn đè lên. Một ý một lúc, rời đi khi sang câu khác. Khung dọc: đặt thẻ **dưới vùng mặt**, giữa ngang, trong vùng x 60–960, y ≤ 1500.
- **C. Cover** — cảnh minh hoạ phủ kín, giọng vẫn chạy. Dùng cho số liệu, so sánh, quy trình, cách hoạt động, giao diện sản phẩm, thứ có ≥ 3 phần.

Chia lời theo câu/vế. Mỗi đoạn gán A/B/C kèm một câu lý do và nói rõ B/C hiện gì. Kiểm nhịp:
- Mở bằng A, kết bằng A. Không để A kéo dài quá ~8 giây.
- Mỗi đoạn C khoảng 3–8 giây; quay về người nói giữa hai đoạn C để không thành slideshow.
- Đổi cách xử lý ở ranh giới câu; ít mà rõ hơn đổi liên tục.

### Đồng bộ hình với lời (quyết định theo từng chi tiết)
| Kiểu | Dùng cho | Đồng hồ |
|---|---|---|
| Vào sớm ~6 khung | Khung, trục, thẻ, cấu trúc quy trình | `s.now` |
| Khớp đúng từ | Con số, %, giá, thứ hạng, giá trị cuối của biểu đồ | `s.audioNow >= wordStart` |
| Chờ lời tiết lộ | Câu chốt, phủ định, đáp án giấu | `s.audioNow`, chặn tại từ tiết lộ |

Ví dụ "doanh thu tăng 30%": khung biểu đồ vào sớm, cột chốt và số 30% đọc được đúng lúc nói "30%". Giữ `SCENES.from/to` theo giây gốc của transcript; template tự cộng `VISUAL_LEAD_FRAMES` (mặc định 6). Không dời anchor thêm lần nữa.

Chữ trên màn hình chỉ dùng lời người nói thật sự nói, hoặc số/tên từ tài liệu người dùng đưa. **Không bịa số liệu, khẳng định hay trích dẫn.** Phụ đề chạy đầy đủ không thuộc skill này (dùng `edit-caption-karaoke` khi được yêu cầu).

## 3. Dựng trang
`cp <skill>/templates/b-roll.html page.html`, rồi đặt:
- `VIDEO`, `W`×`H` (dọc: 1080×1920), `FPS`, `DURATION` theo số `transcribe_vi.py` in ra.
- `FACE`: hộp đầu người nói (kể cả tóc, chừa chút khoảng) theo tỉ lệ khung. Kiểm bằng `node <skill>/scripts/render.mjs page.html face --stills 2s,20s --face` rồi chỉnh tới khi ôm đầu ở mọi khung.
- `SCENES`: mỗi đoạn B/C một mục `{ from, to, kind: 'overlay'|'cover', draw }`, mốc lấy từ `transcript.json` (rơi vào khoảng nghỉ giữa hai từ). Hai cảnh liền nhau thì cho `to` của cảnh trước bằng `from` của cảnh sau, tránh chớp người nói 0,5 giây.
- Mỗi cảnh viết một hàm `draw(t, s)` riêng theo đúng câu đó. Hai hàm mẫu (`keyword`, `bigNumber`) chỉ là khung cấu trúc. `s.in`/`s.out` cho vào/ra; `s.now` là đồng hồ cấu trúc; `s.audioNow` cho dữ kiện khớp lời.

**Màu & chữ:** mặc định preset `aiagentvn` trong `LOOK` (nền thẻ #0F2144, chữ #F5F7FA, nhấn #3FD6A6, phụ #8A6BFF, cảnh báo #FF6B6B). Dự án có `palette.json` hoặc preset khách thì thay vào `LOOK`. Mỗi cảnh một màu nhấn; `warn` chỉ cho cảnh báo/phản bác. Font Be Vietnam Pro (đủ dấu); thêm font khác phải là file cục bộ trong `fonts/`, khai báo trong `FONTS`. Không dùng Google Fonts CDN.
**Cỡ chữ & vùng an toàn:** theo `safe-zone-chu-9x16` (chữ trong thẻ 30–40 px, số nhấn 110–160 px, tối thiểu 28 px; không vượt x 960, không xuống dưới y 1500).
**Motion có diễn tiến:** đồ hoạ chính đi qua trạng thái ban đầu → hành động → kết quả → ra; không chỉ scale/fade icon rồi đứng yên.

## 4. Kiểm tra
```bash
node <skill>/scripts/render.mjs page.html --check              # đối chiếu kế hoạch với transcript và pixel
node <skill>/scripts/render.mjs page.html film.jpg --sheet 1   # cả phim, 1 khung/giây, đè lên video
node <skill>/scripts/render.mjs page.html shot --stills 12s,20s
```
`--check` phải qua: cover che kín người nói khi đã vào, overlay không chạm `FACE`, anchor nằm giữa hai từ, không chữ nào ra ngoài khung hay chồng chữ khác. Cảnh báo về nhịp có thể giữ nếu có lý do (nói ra khi giao). Script không biết hình có nói đúng ý câu không, chữ có đọc được không: **xem contact sheet và still từng cảnh**, sửa rồi xem lại.

## 5. Render và giao
```bash
node <skill>/scripts/render.mjs page.html film.mp4     # phim hoàn chỉnh: video + b-roll + tiếng gốc
node <skill>/scripts/render.mjs page.html b-roll.mov   # chỉ lớp b-roll, alpha ProRes 4444 (Premiere/CapCut PC/Resolve)
node <skill>/scripts/render.mjs page.html b-roll.webm  # alpha VP9, nhẹ
```
Render dài thì chạy bằng tác vụ nền. Giao `film.mp4`, `page.html` (mở trên trình duyệt để xem kèm tiếng và tua), bảng kế hoạch (mốc, lời nói, cách xử lý, trên hình có gì), lớp alpha nếu người dùng dựng tiếp ở phần mềm khác (đặt track trên video, bắt đầu từ 0). Nêu những gì đã tự chọn và chữ nào ASR nghe chưa chắc.

## Ghi chú kỹ thuật
- `render.mjs` cần Node ≥ 18, `playwright-core`, ffmpeg; tự dùng Chrome có sẵn.
- Footage điện thoại xoay 90°: `transcribe_vi.py` đã đảo W/H theo cờ xoay; kiểm still đầu tiên.
- Nguồn VFR: chuẩn hoá về fps cố định trước (`ffmpeg -i in.mp4 -r 25 -c:a copy talk.mp4`).
