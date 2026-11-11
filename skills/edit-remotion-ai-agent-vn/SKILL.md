---
name: edit-remotion-ai-agent-vn
description: "Dựng video dọc 9:16 nền tối cho AI Agent VN từ kịch bản: voice VieNeu mã nguồn mở giọng Hải Đăng (MiniMax dự phòng), hook có giọng + SFX, phụ đề từ khoá, footage Pixabay + khối HyperFrames, nhạc nền, con trỏ bấm link, kiểm tra rồi giao file."
---

# Edit Remotion AI Agent VN

Quy trình dựng video giải thích ngắn (1–3 phút) cho kênh AI Agent VN (aiagentvn.com), nhắm chủ doanh nghiệp nhỏ Việt Nam, không rành kỹ thuật. Động cơ dựng là HyperFrames qua skill `lam-video-kieu-metics-media` (đọc skill đó cho cú pháp composition, check, snapshot, render). Skill này quy định phong cách, giọng, âm thanh, minh hoạ và các bước kiểm tra riêng của kênh. Mục tiêu: người dùng đưa kịch bản là ra video gần như tự động, hạn chế thao tác tay.

## Khi nào dùng
Người dùng đưa kịch bản hoặc chủ đề (thường nằm trong doc "Kịch bản 10 video ..." hoặc file "10 KB" trong project, tách theo "VIDEO 0N") và muốn ra file mp4 dọc, hoặc muốn dựng lại video cũ theo style mới.

## 1. Nguyên tắc nội dung
- Mỗi video đánh MỘT insight khách (nỗi đau bằng lời khách, không dùng từ kỹ thuật): sợ mất khách ngoài giờ, sợ AI nói sai, chatbot cũ làm thất vọng, không biết bắt đầu, việc lặp ngốn giờ, sợ bị dẫy mua khoá, lo dữ liệu khách, muốn ví dụ đúng ngành.
- Độ dài theo nội dung (1–3 phút), không ép một con số. Giọng TTS đọc nhanh (~18–21 ký tự/giây) nên video thường ngắn hơn mục tiêu trong kịch bản: nói rõ khi giao, không độn thời lượng. Cứ 25–30 giây có một câu giữ chân (số bất ngờ, câu hỏi, phản đối).
- Cấu trúc: hook → nỗi đau (cảnh đời thường) → vì sao → cách làm (màn hình giả) → kết quả trước/sau → câu kết → outro.
- Không bịa số liệu. Số liệu công cụ để [SỐ] và lấy từ trang gốc ngày dựng (mở bằng Chrome), kèm link. Thông tin về hãng lớn (Google, Microsoft, LinkedIn…) lấy từ kịch bản người dùng thì ghi dòng nguồn chung và báo "chưa kiểm chứng" khi giao. Ví dụ tự dựng gắn chip "Ví dụ minh hoạ"; giao diện dựng lại gắn "Mô phỏng". Không nói "miễn phí", "siêu dễ", "cam kết 100%" khi chưa kiểm.
- Ưu tiên dựng giả (chat, bảng, dashboard, con trỏ) và footage stock thay vì bắt người dùng chụp màn hình. Chỉ xin ảnh/quay thật khi video hứa "làm lại được".

## 2. Phong cách hình (nền tối, theo logo)
- Khung 1080×1920, 30 fps, font Inter Tight.
- Màu: nền #091833 → #060E22, quầng tím #6030D0 góc phải trên, quầng teal #40B090 góc trái dưới; chữ trắng; nhấn mint #3FD6A6; tím #8A6BFF (chữ trên tím #C4B5FF); sai/cảnh báo san hô #FF6B6B; vàng nhấn #FFB84C; thẻ #0F2144 viền #1E3A6B; chữ phụ #9FB0CC. Không dùng cam của kênh tham khảo.
- KHÔNG có số thứ tự cảnh (kiểu "01 / 14"). Chip "Ví dụ minh hoạ"/"Mô phỏng" góc phải trên khi cần.
- Thẻ tiêu đề mở đầu (khung hook, người dùng chụp làm thumbnail): GIỮ CỠ LỚN như bản gốc, KHÔNG thu nhỏ theo safe zone. Logo ngang (crop có alpha) rộng ~560 px, đỉnh y ≈ 300; tiêu đề nghiêng viết hoa 900, **118 px**, khối chữ bắt đầu y ≈ 540; 3–4 dòng ngắn (tự ngắt bằng <br>), 1–2 dòng cuối màu mint. **Giãn dòng `line-height: 1.22`** (không dùng 1.05) để dấu tiếng Việt của dòng dưới (Ầ, Ỏ, Ữ, Ặ…) không dính vào chân chữ dòng trên. Mỗi dòng ≤ ~16 ký tự để không tràn ngang (vẫn trong x 40–1040); dài hơn thì rút gọn chữ và báo người dùng. Watermark "@aiagentvn · aiagentvn.com" ở đáy.
- Phụ đề: 2–3 từ mỗi lần, MỘT dòng, nghiêng viết hoa 58 px, viền 9 px màu nền, từ khoá và chữ số tô mint; khung phụ đề rộng 800 px ở giữa (x 140–940, không lấn cột nút bên phải), đặt khoảng y=1215–1430. Nội dung cảnh giữ trên y≈1150. Số trong phụ đề hiện bằng chữ số (2025, 11h, 5) dù lời đọc viết bằng chữ.
- Cảnh đổi theo từng câu voice (4–11 giây); mỗi ý trong câu xuất hiện đúng lúc giọng đọc tới (neo hiệu ứng vào cụm từ trong lời). Hiệu ứng hay dùng: pop, trượt vào, gạch ngang ý sai rồi hiện ý đúng, danh sách hiện từng dòng theo lời, hai cột so sánh, số lớn ở giữa, prompt gõ chữ + con trỏ bấm Gửi, mũi tên có chấm sáng chạy.
- Cách đổi nhanh một composition sáng cũ sang tối: thay token màu trong theme.css, thêm khối CSS ghi đè (nền, thẻ, bong bóng chat, chip, nút), thay các mã hex sáng trong HTML/JS, rồi thêm thẻ tiêu đề và dời toàn bộ thời gian cảnh thêm một khoảng bằng độ trễ mở đầu.
- Đừng phóng to cả cảnh bằng transform: dễ đè phụ đề.

### 2.1 Cỡ chữ và safe zone (người dùng đã duyệt từ KB 06–07)
Theo skill `safe-zone-chu-9x16` (đọc khi dựng). Bảng cỡ chữ cụ thể của kênh này, khung 1080×1920:

| Thành phần | Cỡ |
|---|---|
| Phụ đề | 58 px, 1 dòng, 1–3 từ, viền 9 px |
| Tiêu đề mở đầu (.tl, khung hook/thumbnail) | **118 px**, line-height 1.22, 3–4 dòng — ngoại lệ, KHÔNG thu nhỏ |
| Tiêu đề trong cảnh (.h) | 40–50 px (cụm nhấn lớn tới ~75 px) |
| Chữ trong thẻ (.ct/.rule/.tag/.nm) | 32–38 px |
| Chữ phụ, nhãn (.mid/.lab) | 30–34 px |
| Số lớn (.big) | 110–150 px |
| Dòng nguồn, chip, watermark | 28 px (tối thiểu) |

- Cách làm nhanh khi dựng bằng generator: viết CSS/inline theo cỡ thiết kế cũ rồi chạy một lượt nhân mọi `font-size` với 0,72 (tối thiểu 28 px) cho các cảnh, TRỪ cảnh thẻ tiêu đề (`s_title`) và class `.tl`; sau đó ghi đè `.st{font-size:58px;-webkit-text-stroke:9px}`, `.sub{left:140px;right:140px;padding:0}` và `.tl{font-size:118px;line-height:1.22}`. Chỉ đổi cỡ chữ, không đổi màu, font, vị trí cảnh, chuyển động.
- Khung hook là ngoại lệ duy nhất về cỡ chữ (để làm thumbnail). Kiểm tra bằng snapshot ở ~1,2 s: chữ to, đọc rõ khi thu nhỏ thành ô thumbnail, dấu không dính dòng trên, không tràn ngang.
- Nội dung nằm trong vùng y 220–1500, chữ không vượt x 960 (cột nút bấm của app). Kiểm tra bằng snapshot: chữ không chạm mép, phụ đề không xuống 2 dòng.

## 3. Minh hoạ: footage, khối dựng sẵn, icon
Mỗi cảnh nên có ít nhất một thứ "thật" hoặc chuyển động có nghĩa, không chỉ thẻ chữ.

**a. Footage/ảnh Pixabay (cảnh đời thường).** API key: biến môi trường `PIXABAY_API_KEY`, hoặc file `pixabay.txt` người dùng gửi trong chat (đọc lúc chạy; KHÔNG in key, không ghi vào skill/bộ nhớ/file khác). Domain cần cho phép: `pixabay.com`, `cdn.pixabay.com`. Python urllib phải gửi User-Agent kiểu trình duyệt (thiếu sẽ bị 403). Mẫu helper:
```python
import json, urllib.request, urllib.parse
UA={'User-Agent':'Mozilla/5.0 (aiagentvn video builder)'}
def search(key,q,kind='photo',n=10,orientation='vertical'):
    base='https://pixabay.com/api/videos/' if kind=='video' else 'https://pixabay.com/api/'
    p=dict(key=key,q=q,per_page=max(3,n),safesearch='true',lang='en')
    if kind=='photo' and orientation: p['orientation']=orientation
    r=urllib.request.urlopen(urllib.request.Request(base+'?'+urllib.parse.urlencode(p),headers=UA),timeout=30)
    return json.load(r)['hits']   # video: hit['videos']['medium'|'small'|'large']['url']; ảnh: hit['largeImageURL']
def download(url,path):
    open(path,'wb').write(urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=120).read())
```
- Từ khoá tìm bằng tiếng Anh, cụ thể ("hands typing laptop", "phone notification hand", "small shop cashier"). Ưu tiên cảnh không lộ rõ mặt người nước ngoài (tay, màn hình, bàn làm việc, cửa hàng) cho hợp khán giả Việt; tránh ảnh gắn tag "ai generated" khi cần cảnh thật.
- Tải về `assets/` của dự án; video cắt đúng đoạn cần, crop 9:16 bằng object-fit:cover, phủ lớp tối (gradient #091833 ~55–70%) để chữ trên footage đọc được. Xem 1 khung hình trước khi dùng.
- Pexels hiện ngừng cấp API key mới; nếu cần ảnh Pexels thì tải qua Chrome về Downloads rồi stage.

**b. Khối dựng sẵn HyperFrames registry (~450 khối, có sẵn trong CLI, không cần cài):**
```bash
npx hyperframes catalog --query "<english>" --json   # tìm
npx hyperframes add <name> --json                      # cài vào compositions/
```
Khối hữu ích: chat-message, message-thread-reveal, ai-chat-reveal, typing-indicator, notification-stack, native-notification-pop, badge-pop, count-up, number-pop-in, comparison-split, before-after-wipe, marker-checklist-card, success-check, animated-bar-chart, decline-chart, data-chart, icon-swap, agent-cursor. Đổi biến màu/font của khối sang palette kênh; giữ nguyên prefix id của khối.

**c. Icon:** bộ icon miễn phí qua npm (lucide-static, @tabler/icons, @phosphor-icons/core) → nhúng SVG inline, tô màu palette. Emoji dạng ảnh (twemoji/noto) chỉ cho cảnh cảm xúc.

**d. Cảnh ẩn dụ trừu tượng:** có thể dùng skill `edit-collage-broll`.

## 4. Giọng đọc

### 4.0 Thứ tự ưu tiên
1. **VieNeu-TTS mã nguồn mở (chính), giọng "Hải Đăng"** (nam, miền Bắc, tự nhiên; người dùng đã duyệt). Chạy ngay trong workspace: miễn phí, không giới hạn lượt, không cần Chrome, tự động hoàn toàn. Áp dụng từ KB 06 trở đi.
2. **MiniMax qua Chrome (dự phòng)**: chỉ khi VieNeu không chạy được (không tải được model, lỗi liên tục, đọc sai không sửa được) hoặc người dùng yêu cầu.
3. VieNeu Cloud API (bản v4, trả phí sau 7 ngày dùng thử) chỉ dùng khi người dùng cấp key và yêu cầu.
- MỘT video chỉ dùng MỘT giọng, kể cả câu kết (xem 4.5). Nếu phải đổi nguồn giữa chừng thì tạo lại toàn bộ bằng nguồn mới, không ghép hai giọng; báo rõ khi giao.
- Khi giao video, ghi giọng đã dùng.

### 4.1 Viết lời đọc cho TTS
- Số bằng chữ (hai mươi sáu, mười hai khách, mười một giờ đêm); từ tiếng Anh đổi sang tiếng Việt khi được (objection → xử lý từ chối, CRM → phần mềm khách hàng, follow-up → nhắc lịch theo dõi, copy → chép, report → báo cáo, dashboard → bảng điều khiển, lead → khách tiềm năng, database → danh sách khách, Ads → quảng cáo, Sales → nhân viên kinh doanh); thay "AI Agent" trong thân bài bằng "trợ lý AI". Kịch bản chỉ có phần VISUAL không có lời thì thêm một câu dẫn ngắn và báo người dùng.
- Mỗi câu kịch bản = 1 file wav.

### 4.2 VieNeu-TTS mã nguồn mở (chính)
- Domain cần cho phép (đã bật): `huggingface.co`, `*.hf.co` (file model lớn chuyển hướng sang us.aws.cdn.hf.co), `cas-bridge.xethub.hf.co`, `cdn-lfs.huggingface.co`.
- Cài trong venv riêng (workspace dựng lại mỗi session nên cài lại mỗi lần, ~1–2 phút kể cả tải model):
```bash
python3 -m venv /tmp/w/tts
/tmp/w/tts/bin/pip install -q vieneu "onnxruntime==1.22.1"
```
  BẮT BUỘC ghim `onnxruntime==1.22.1`: bản 1.23+ báo lỗi "External data path escapes model directory" khi đọc model trong cache Hugging Face.
- Dùng (bản v3 Turbo, 48 kHz, ONNX trên CPU):
```python
from vieneu import Vieneu
v = Vieneu()                       # tải model lần đầu ~10–60 s
for k, text in lines:              # mỗi câu một file
    a = v.infer(text, voice="Hải Đăng")
    v.save(a, f"{P}/audio/{k}_src.wav")
# v.list_preset_voices() → 25 giọng mẫu (Minh Triết, Thái Sơn, Quốc Tuấn, Thùy Dung, Đức Trí, Adam...)
```
- Tốc độ trên workspace 2 CPU: ~1,1–1,5× thời gian thực (video 75 s ≈ 2 phút tạo giọng). Chạy bằng background task nếu nhiều câu. Hải Đăng đọc ~20–21 ký tự/giây.
- Thông báo "HTTP 429 / Rate limited" từ Hugging Face lúc tải là bình thường, thư viện tự thử lại.
- Kiểm tra mỗi file: thời lượng hợp lý so với số ký tự (~15–24 ký tự/giây), không im lặng, không cụt, không "nói thêm". Bất thường thì tạo lại đúng câu đó (miễn phí nên có thể tạo lại thoải mái, khác với MiniMax).
- Nhân bản giọng: nếu người dùng gửi đoạn ghi âm 3–8 giây của chính họ, có thể nhân bản (xem README VieNeu-TTS, mục voice cloning). Chỉ nhân bản giọng người dùng hoặc người đã đồng ý.
- Nguồn: github.com/pnnbao97/VieNeu-TTS (model pnnbao-ump/VieNeu-TTS-v3-Turbo).

### 4.3 MiniMax qua Chrome (dự phòng)
- speech-2.8-hd, voice "Professional Guide", Vietnamese tự nhận. Dùng Chrome của người dùng (Claude in Chrome).
- Quy trình mỗi câu (gom 2–3 câu vào một browser_batch; batch quá dài dễ timeout):
  1. navigate https://www.minimax.io/audio/text-to-speech, wait 3s
  2. click nút tẩy chữ (cạnh bộ đếm ký tự)
  3. javascript: focus `[contenteditable="true"]`, dispatch `ClipboardEvent('paste')` với DataTransfer chứa câu; trả về bộ đếm `N / 5,000` (phải bằng số ký tự). Viết JS dạng top-level (dùng `var`, `await` trực tiếp, biểu thức cuối là giá trị trả về) và `throw` khi bộ đếm sai để batch dừng trước khi bấm Generate (tránh dồn chữ, tốn credit).
  4. click Generate, wait 10s + 6–8s (wait tối đa 10s mỗi lệnh)
  5. click icon tải ở thanh player → chọn MP3
- Toạ độ phụ thuộc chiều cao cửa sổ và thay đổi sau lần tạo đầu (thanh player xuất hiện): chụp màn hình sau lần tạo đầu tiên để lấy lại vị trí tẩy/Generate/tải/MP3 (vd viewport 577 có player: tẩy 863,365; Generate 788,425; tải 1220,527; MP3 1120,450).
- Sau mỗi đợt: device_list_dir Downloads, đối chiếu dung lượng/thứ tự, stage file. Câu bị sót tải: mở tab History, hover dòng đó, bấm icon tải (KHÔNG bấm icon thùng rác) → MP3; không tạo lại để khỏi tốn credit. Tên file theo giờ tạo nên dùng để đối chiếu thứ tự với History.
- Credit ≈ 1/ký tự; báo số credit đã dùng và còn lại khi giao.
- Nếu trang MiniMax hiện "Sign In": có thể đang ở trình duyệt khác. Dùng list_connected_browsers; nếu nhiều trình duyệt thì hỏi người dùng (hoặc switch_browser) rồi tabs_context_mcp createIfEmpty. Không tự đăng nhập.

### 4.4 VieNeu Cloud API (tuỳ chọn)
- POST https://api.vieneu.io/api/v1/audio/speech, header `Authorization: Bearer <key>`, JSON: input, voice (id lấy từ GET https://api.vieneu.io/api/v1/voices?engine=v4, luôn lọc theo engine), response_format wav. Key từ biến môi trường `VIENEU_API_KEY` hoặc file `vieneu.txt` người dùng gửi; KHÔNG in/ghi key. Dùng thử 7 ngày, 50 lượt/ngày (hết → HTTP 429 TRIAL_API_DAILY_LIMIT đến 0h giờ VN), sau đó phải mua gói token.

### 4.5 Câu kết: giọng nào thì câu kết đó
- Câu kết luôn cùng giọng với thân bài; không ghép câu kết giọng khác vào video.
- **Hải Đăng (VieNeu, mặc định):** dùng bản A người dùng đã duyệt. Lời đưa vào TTS (viết phiên âm để đọc đúng "AI Agent" và tên miền):
  `Nhận tư vấn giải pháp Ây Ai Ây-giần, tại Ây Ai Ây-giần Vi En, chấm com.`
  Bản đã duyệt nằm ở Downloads của người dùng (`cau_ket_hai_dang.mp3`) hoặc bản lưu trong dự án trước đó: LUÔN dùng đúng file đã duyệt, KHÔNG tạo lại. VieNeu không cho kết quả giống hệt giữa các lần tạo (KB 09 tạo lại câu kết bị đọc lệch: "nhận" thành "nhạm", ngắt dài trước ".com"). Chỉ khi mất file đã duyệt mới tạo lại: tạo 3–5 bản đúng chuỗi trên, gửi người dùng nghe chọn trước khi ghép, rồi lưu bản được chọn vào Downloads. Không đưa nguyên chữ "AI Agent"/"aiagentvn.com" vào TTS: đọc sai.
- **MiniMax (dự phòng):** dùng file voice người dùng đã sửa (cfb10cc0-10281.MP3); nếu không có thì cắt từ cuối KB 05.mp4 (đoạn ~68,72 s → 72,67 s).
- **Giọng khác/giọng mới:** tạo vài bản phiên âm khác nhau (vd "Ây Ai Ây-giần", "ê ai ê dần", tách từng chữ bằng dấu chấm), gửi người dùng nghe chọn trước khi ghép; ghi lại bản được chọn vào mục này.
- Phụ đề câu kết vẫn hiển thị đúng chữ "AI AGENT TẠI AIAGENTVN.COM" (không hiện phiên âm).

## 5. Âm thanh
- Mỗi câu một wav: cắt lặng librosa (top_db 35, đệm 0,03 s), chuẩn hoá −14 LUFS (pyloudnorm), đỉnh ≤ 0,89; nén khoảng lặng trong câu ≥0,2 s xuống 0,12 s cho nhịp liền (người dùng không thích nghỉ lâu); ghép với khoảng hở 0,12 s; manifest start/duration từng câu. VieNeu ra 48 kHz: resample về sample rate của pipeline khi xử lý.
- MiniMax: không tạo lại voice để sửa nhịp hay lỗi lặp câu, cắt sửa trên file sẵn có (tiết kiệm credit). VieNeu mã nguồn mở: có thể tạo lại câu lỗi (trừ câu kết, xem 4.5).
- Phụ đề khớp theo khoảng lặng/dấu câu khi chưa có ASR; câu kết đo tay. Muốn khớp từng từ: `npx hyperframes transcribe` (model tải từ Hugging Face, domain đã bật).
- Nhạc nền nhẹ chạy suốt + SFX tổng hợp bằng code: whoosh đổi cảnh, pop thẻ/số, click khi bấm, tick từng dòng danh sách/khi gạch, ding ý đúng, thud ý sai/cảnh báo.
- HOOK: giọng vào từ 0,35 s, thẻ tiêu đề hiện cùng lúc (~1,75 s) rồi chuyển vào cảnh đầu; riser + impact (boom trầm + nổ giòn + lấp lánh) ở ~0,05–0,3 s. Không để mở đầu im lặng. Phụ đề chạy ngay trên thẻ tiêu đề.
- data-volume="1" cho voice và bed (0,8 làm tổng chỉ −16 LUFS). Đo sau render: khoảng −14 đến −15 LUFS; không tự tăng thêm nếu đã đạt.

## 6. Câu kết và con trỏ
Cảnh outro: logo, nút aiagentvn.com, con trỏ di chuyển và click (lún + vòng sóng + gợi ý "Mở aiagentvn.com"); thời điểm click khớp từ cuối của câu voice kết. Giữ cảnh outro thêm ~1,5 s sau khi câu kết dứt để dòng gợi ý đọc kịp.

## 7. Quy trình
1. Lấy kịch bản đúng video; xác định câu voice và chỗ cần footage/khối/icon. Thiếu dữ liệu cần người dùng thì nói rõ việc nào bắt buộc, việc nào tự dựng giả.
2. Tạo thư mục dự án + lines.py/script.json (id câu, lời đọc TTS); `metadata init` của skill nền.
3. Voice theo mục 4 (VieNeu mã nguồn mở giọng Hải Đăng; MiniMax khi VieNeu không chạy được) + câu kết cùng giọng theo 4.5 → xử lý âm thanh (mục 5).
4. Tìm/tải footage Pixabay + chọn khối registry/icon cho từng cảnh (mục 3).
5. Khi đổi style hoặc giọng: làm bản xem thử 6–10 giây gửi duyệt trước. Video cùng series đã duyệt style và giọng thì dựng full luôn.
6. Dựng composition: mỗi câu một scene; hiệu ứng neo vào cụm từ trong lời đọc; phụ đề; outro; bed + SFX; cỡ chữ và safe zone theo mục 2.1 (khung hook giữ 118 px).
7. `npx hyperframes check` (phải "Check passed"), `snapshot` nhiều mốc (hook, cuối mỗi cảnh, outro) và XEM contact sheet thật.
8. Render `-w 2 -f 30` (chạy nền), đo LUFS (ffmpeg ebur128), ffprobe thời lượng, xem vài khung hình từ mp4.
9. Cập nhật metadata (duration), gửi file bằng SendUserFile và lưu thêm bản "KB 0N.mp4" vào Downloads của người dùng khi máy đang kết nối; báo ngắn: nội dung, giọng đã dùng, điều chưa kiểm (cách đọc từ tiếng Anh, thông tin hãng chưa kiểm chứng, phụ đề theo cụm, ngắn hơn mục tiêu).

## 8. Lỗi hay gặp
- HYPERFRAMES_BROWSER_PATH trỏ chromium cài sẵn; dùng đường dẫn tuyệt đối (cwd bị reset mỗi lệnh); render bằng background task, không dùng `&`.
- Render báo "Chrome not found" (không tải được chrome-headless-shell): đặt `HYPERFRAMES_BROWSER_PATH=/usr/bin/google-chrome`.
- GSAP từ CDN có thể bị chặn lúc render (lỗi sub_timeline_script_failure, cảnh đứng im): copy `node_modules/gsap/dist/gsap.min.js` vào `assets/` và nạp bằng đường dẫn local.
- `<video>` có data-start không được nằm trong một scene có data-start (lỗi video_nested_in_timed_element): đặt video ở cấp gốc, có id, z-index dưới scene; cảnh dùng nền trong suốt.
- SFX chồng nhau trên cùng data-track-index bị cảnh báo: chia làn tự động (làn nào trống thì dùng).
- Trùng id giữa các phần tử trong cùng cảnh (vd tiêu đề 'b0' và dòng danh sách 'b0') làm phần tử biến mất: dùng prefix riêng cho danh sách.
- Class .card là position:absolute: phần tử con trong grid/flex phải thêm position:relative, nếu không sẽ chồng lên nhau (check báo content_overlap).
- Vạch gạch ngang đè chữ: thêm data-layout-allow-occlusion cho vạch; thẻ tiêu đề cần data-layout-allow-overlap.
- Chữ dưới 28 px bị cảnh báo khó đọc: dòng nguồn để 28 px.
- Inline opacity:0 cộng tween from → lỗi gsap_from_opacity_noop.
- Chuyển số phát âm → chữ số trong phụ đề: dừng cụm số khi chữ số nối chữ số ("quận bảy không").
- VieNeu: onnxruntime 1.23+ lỗi "External data path escapes model directory" → ghim 1.22.1. Cài pip vào venv riêng (cài thẳng vào hệ thống với --break-system-packages có thể bị chặn).
- Đừng chạy script vá kịch bản hai lần; ánh xạ cảnh theo id, không theo vị trí. Không dùng pkill -f.
- Logo vuông nền navy hiện thành hộp sáng trên nền tối: dùng bản crop ngang có alpha.
- Thẻ dài làm chữ xuống dòng giữa cụm [tên cửa hàng]: bọc cụm trong một div.
- Không giả mạo thương hiệu, không dựng giao diện bên thứ ba như thật.