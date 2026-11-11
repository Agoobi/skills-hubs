---
name: edit-onetake
description: "Làm video motion ngắn giới thiệu sản phẩm/app/skill/tính năng (10–30 s, demo có lời đến ~60 s) kiểu launch clip cao cấp: kinetic type, UI thật hoặc dựng lại, beat nối nhau, motion blur thật, SFX chung một không gian — chạy trên Claude bằng HTML hàm theo thời gian + Playwright."
---

# Edit Onetake (bản Claude)

Chuyển từ repo `onetake` của Patrick (github.com/feitangyuan/onetake). Đây không phải trình dựng video hay máy tạo slideshow: một **composition** (một file HTML, `window.__seek(t)`), một **thư viện chuyển động** (`lib/motion.js`), **footage** quay từ sản phẩm thật, một **bảng âm thanh** chung một không gian, và một **oracle** chấm nhịp và tính nối trước khi người xem phải xem.

**Giấy phép:** PolyForm Noncommercial 1.0.0 — chỉ miễn phí cho mục đích **phi thương mại**. Dùng cho video quảng cáo/bán hàng của doanh nghiệp là mục đích thương mại: trước khi làm video thương mại, nhắc người dùng một câu rằng cần xin phép tác giả (giấy phép thương mại), và để người dùng quyết định. Không xoá dòng `Required Notice` khỏi file.

Dùng cho: video launch/teaser/giới thiệu app, trang, skill, tính năng; demo tính năng có lời (dựng lại UI thay vì quay màn hình); làm theo cảm giác của một clip tham chiếu; thêm vốn chuyển động (chuyển cảnh, nối beat); chẩn đoán vì sao video motion trông như PPT (đơn điệu, không nhịp, chuyển cảnh cứng).
Không dùng cho: video dài, talking head, dựng footage có sẵn bằng chuyển cảnh (dùng skill talking head/MKQ/V06). Người dùng nêu HyperFrames hoặc Remotion thì dùng cái họ nêu.

## Thiết lập trong phiên Claude

Skill này **đã đóng gói sẵn** `lib/`, `scripts/`, `templates/`, `references/`, `looks/` (font + preset màu), `gallery/` (sheet xem trước các move) và `cases/*/README.md` của repo gốc (commit 013a61a) — không cần mạng. Chép ra thư mục làm việc vì các script ghi file vào `cases/` và `gallery/`:

```bash
cd <thư mục làm việc>
[ -d onetake ] || cp -r <skill> onetake      # <skill> = thư mục chứa file SKILL.md này
cd onetake
```
Chỉ khi cần bản mới hơn hoặc video mẫu trong `cases/` (mp4, ~90 MB, không đóng gói): `git clone https://github.com/feitangyuan/onetake.git onetake-upstream` rồi đọc lại SKILL.md của repo.

- Chromium và Playwright có sẵn, dùng được ngay. **Không** chạy `playwright install` hay cài lại Playwright.
- Thư viện Python cần: numpy, scipy, Pillow, matplotlib, opencv-python; `fonttools` + `brotli` cho `look.py` (`pip install --break-system-packages fonttools brotli` nếu thiếu). Node có sẵn cho `node scripts/test_motion.js`.
- Máy làm việc thường chỉ có **2 nhân**: render chạy `--workers 1` hoặc `2`; bản nháp 1080p30 vài trăm khung mất vài phút. Báo ước tính trước khi render dài. **Không render 4K60 (`--final`)** trừ khi người dùng duyệt bản nháp và yêu cầu.
- Mạng chỉ mở PyPI, npm, GitHub. huggingface.co và các kho âm thanh (Kenney, UIowa, Voxengo, Mixkit) thường bị chặn:
  - Lời đọc (TTS Kokoro) không dùng được và không hỗ trợ tiếng Việt → dùng giọng thật của người dùng (họ gửi file) hoặc không lời.
  - Mốc từng từ: thay `faster-whisper` bằng sherpa-onnx (`zipformer-vi`, `whisper-turbo` từ GitHub releases `k2-fsa/sherpa-onnx`), rồi ghi `words.json` đúng định dạng `vo_tools.py` cần.
  - SFX thu sẵn: dùng thư viện SCHANEL trên máy người dùng (`D:\Làm với Khoa\SCHANEL`, lấy bằng công cụ liên kết máy tính: xin quyền thư mục → stage đúng file cần) kết hợp bảng âm tổng hợp `scripts/sfx_palette.py`.
- Khung dọc cho Reels/TikTok: đặt `html,body` 1080×1920 trong comp, `window.__meta={dur,fps,w:1080,h:1920}`, và truyền `--width 1080 --height 1920` cho `render.py`/`stills.py`.
- Font tiếng Việt: các font trong `looks/` (Inter, Archivo, Geist, Fraunces, Instrument…) phải được kiểm dấu bằng `python3 scripts/look.py check`; thiếu glyph thì thay bằng Be Vietnam Pro (tải từ GitHub `google/fonts`) và ghi lại.

Đọc tài liệu trong repo khi đến bước tương ứng: `references/reference-deconstruction.md`, `rhythm.md`, `motion-library.md`, `composition.md`, `sound.md`, `product-demo.md`, và README của các `cases/*/`.

## Quy trình — đúng thứ tự, không bỏ bước

### 1 · Đo clip tham chiếu trước khi làm gì (bắt buộc khi có tham chiếu)

```bash
python3 scripts/analyze_ref.py ref.mp4 --out ana/     # energy map, cắt cảnh, độ tĩnh, contact sheet, dòng motion
```

Ghi lại các con số phim phải khớp: bao nhiêu % thời gian đứng yên, số cú cắt cứng và chúng dồn cụm ở đâu, kích thước phần tử so với khoảng trống, t80 (snap hay S-curve), có nhòe chuyển động hay không. Phim motion-web từng làm sai hai lần vì không đo: tham chiếu đứng yên 34%, có 7 cú cắt cứng trong hai cụm, mọi phần tử nhỏ trên nền rộng.

### 2 · Ý tưởng — ba ý trung tâm trước khi viết beat sheet (bắt buộc)

Một ý tưởng là một câu về **hình ảnh**, không phải về sản phẩm. Viết ba ý khác nhau ở ý trung tâm, không phải ba câu chuyện kể bằng cùng các thẻ:
- **một phần tử biến hình xuyên suốt** (một chấm là con trỏ, tách thành danh sách, rỗng thành vòng loading, duỗi thành đường cong, đáp xuống thành dấu chấm chữ i của logo);
- **một cú máy xuyên qua tỉ lệ** (từ trong con trỏ kéo ra ô nhập, lao qua nút gửi vào công việc, ra qua phim đã xong);
- **chia đôi trước/sau** (bên trái là slideshow, bên phải là bản nối, đến khi bên phải phá sang trái);
- **phản ứng dây chuyền** (mỗi beat là cú va chạm khởi động beat sau);
- hoặc ẩn dụ vật lý, một bề mặt liên tục, hệ chữ…

Mỗi ý gồm: khung hook, thứ gì nối qua từng ranh giới, nó loại bỏ điều gì (không thẻ? không cắt?), và **look** — một preset trong `looks/` (`python3 scripts/look.py sheet` → `gallery/sheets/looks.png`: paper, dusk, tabletop, ultramarine, riso, ember), màu của chính sản phẩm (`look.py from-shot shots/*.png --out look.json`), hoặc look riêng cho phim này. Trình bày ba ý và **để người dùng chọn**. Câu chuyện của template (chữ kinetic → gõ prompt → checklist tick → kết quả → staccato → logo đen) chỉ là một ý, không bao giờ là mặc định.

### 3 · Storyboard theo nhịp và theo tính nối

Beat sheet: `t · beat · cái gì chuyển động · cái gì đứng yên · cái gì mang sang beat sau`.
- **Nhịp:** độ dài shot chênh nhau ≥ 4 lần (chữ 0,25 s cạnh khoảng giữ 2,5 s). Ít nhất một đoạn gần như im lặng cả hình lẫn âm. Một câu chuyện, không phải catalogue. Phần tử nhỏ, nền rộng.
- **Nối:** ở mỗi ranh giới, gọi tên thứ sống sót và di chuyển: bàn tay, chủ thể, một container biến thành cảnh sau (`morphRect`), sân khấu mở ra từ chủ thể (`iris`), máy đẩy vào một thẻ tới khi nó thành cảnh (`zoomThrough`), dàn vật gom lại thành lockup (`gather` → `seal`). Không có gì sống sót thì đó là đổi slide, dù nhịp tốt. Cắt trần chỉ dành cho cụm hit và end card.

### 4 · Footage từ sản phẩm thật — hoặc dựng lại UI từ ảnh chụp

```bash
python3 scripts/record_footage.py footage.json --out footage/
```

Trang thật được Playwright điều khiển theo thời gian thực, quay đúng kích thước sẽ hiện, có dấu magenta khi thao tác bắt đầu, lưu đường đi con trỏ để comp vẽ lại bàn tay — **người xem phải thấy nguyên nhân, không chỉ kết quả**. Lưu ý máy làm việc chỉ vào được trang công khai mà mạng cho phép; trang của người dùng sau đăng nhập thì xin ảnh chụp/bản quay.

**Hoặc dựng lại:** khi phim đi qua các tính năng (nhất là có lời hoặc nhiều ngôn ngữ), người dùng chỉ gửi ảnh chụp/bản quay tham khảo; UI được dựng lại bằng HTML trong khung pixel của tham chiếu, mọi chuỗi chữ nằm trong một bảng, mọi trạng thái do `set(state)` thuần viết ra, highlight đo từ DOM (`lib/ui_kit.js`). Ngôn ngữ thứ hai là `?lang=` trên cùng comp, lời đọc ánh xạ bằng `UIK.timeWarp`, kiểm pixel bằng `scripts/frame_diff.py`. Nội dung phải là output thật của sản phẩm. Chi tiết: `references/product-demo.md`.

### 5 · Composition — một file, hàm thuần theo thời gian, moves từ thư viện

```bash
mkdir -p cases/my-film && cp templates/comp.html lib/motion.js cases/my-film/
python3 scripts/probe.py cases/my-film/comp.html     # khi đã chạy hết: thứ gì nối mỗi ranh giới, đường cong mỗi move
```

Chọn move bằng cách xem `gallery/sheets/<move>.png`. Thư viện có 39 move: entrance, carry, tiếp xúc và mô phỏng, camera, nhóm fluid; mỗi move là hàm của thời gian. Không tự viết lại spring/ease bằng hằng số. Giữ hợp đồng và helper của template, nhưng viết beat của ý đã chọn ở bước 2. Mọi thứ là `f(t)`; mô phỏng tính trước một lần ở 240 Hz. Xem trước bằng `?play`, ghim khung bằng `?t=6.4&hud`.

**Look đi cùng comp:** `python3 scripts/look.py apply ember cases/my-film/comp.html` (hoặc `look.json`) ghi `look.js`: 8 màu thành biến CSS và `LOOK.color`, 3 font subset theo đúng ký tự comp dùng rồi nhúng. Chạy lại sau khi đổi chữ.

**Camera có người vận hành:** `OM.camera(t, keys)`; key chủ thể sớm ~0,1 s trên `sineInOut` để bám, key điểm đáp trước cú snap trên `expoInOut` để vụt tới, thêm "tay cầm" (hai sóng sine chậm, bằng 0 khi giữ) và `OM.shake` khi đáp. Vẽ `OM.lattice` mờ phía sau nếu nền trống. Khai báo `__meta.inFrame` cho những gì không được rời khung. Chi tiết: `references/composition.md` → *A camera*.

### 6 · Render — nháp 1080p30, chỉ 4K60 khi đã duyệt

```bash
python3 scripts/stills.py comp.html --times 0.7,2.4,3.8,6.2,9.9 --out stills.png      # xem trước khi render
python3 scripts/render.py comp.html --out draft.mp4 --sfx sfx.wav --workers 2         # 1920×1080 · 30 fps · shutter 180°
```

Shutter là motion blur thật: mỗi khung động được seek nhiều lần trong lúc màn trập mở rồi lấy trung bình trong không gian tuyến tính; khung đứng yên bỏ qua. Trang có `window.__motion(t0, t1)` được chụp đủ số mẫu để các bản sao cách nhau `--gap` px.

### 7 · Âm thanh — một bảng chất liệu trong một căn phòng, không mỗi sự kiện một tiếng bíp

```bash
python3 scripts/sfx_palette.py --demo demo.wav     # nhanh: bảng tổng hợp (air, wood, glass, sub, bubble) trong một reverb
```

Bản tốt hơn: `score.py` đọc `window.__events()` của comp (thời điểm, loại, pan, cường độ) và đặt âm thu sẵn (SCHANEL) xếp lớp với âm tổng hợp, chung convolution reverb, nhạc duck dưới các hit, master −16 LUFS, trần true-peak −3,5 đến −4 dBTP để bản AAC không vượt −3 dBFS. Ít sự kiện âm hơn số beat. Lần đầu motion-web gắn sine pop cho mọi sự kiện và bị chê rẻ tiền ngay. Nhạc mặc định phải miễn phí bản quyền và ghi nguồn/giấy phép; nhạc thương mại chỉ khi người dùng tự đưa và xác nhận. Chi tiết: `references/sound.md`.

### 8 · Kiểm trước khi đưa người dùng xem

```bash
python3 scripts/verify_promo.py draft.mp4 --comp comp.html --ref ref.mp4 --shots 0,1.6,3.0,4.8,7.0,9.6
```

Các chân kiểm: nhịp (độ dài shot đều, không có đoạn đứng yên, âm bị clip hoặc không bao giờ yên), **burst** (fail khi tham chiếu có cụm hit mà phim không có), **continuity** (fail khi các beat thay thế nhau, điểm nối < 0,5), **curves** (chuyển động > 80 px/khung mà không có shutter blur), **framing** (phần tử trong `__meta.inFrame` rời khung hoặc bị cắt). Xem thêm ảnh tĩnh ở các mốc quan trọng.

## Luật cứng (mỗi luật từng trả giá bằng một bản dựng)

- Không mặc định câu chuyện của template. Ba ý khác nhau ở ý trung tâm; người dùng chọn.
- Không mang look của phim trước sang phim sau. Công cụ (replica, lời đọc, time warp) dùng lại được, look thì không. Preset được chọn có tên ở vòng ý tưởng thì được; mặc định âm thầm thì không.
- Ngôn ngữ thứ hai không tách nhánh composition: `?lang=`, time warp, bản gốc kiểm giống từng pixel.
- Không cắt theo máy đếm nhịp. Shot dài bằng nhau đọc như slide dù từng shot đẹp.
- Không thay beat — nối beat. Có thứ trên màn hình sống qua mỗi ranh giới và chuyển động/scale sang beat sau. Trừ cụm hit cắt cứng và end card.
- Không trưng cả trang như thumbnail mong chuyển động đọc được. Hoặc toàn khung có bàn tay, hoặc một thành phần của trang chạy trong thẻ.
- Không để khung lúc nào cũng chuyển động. Khoảng nghỉ làm cụm hit có lực; tham chiếu đứng yên một phần ba thời gian.
- Phần tử nhỏ, nền rộng (~70% trống). Footage tràn khung là ngoại lệ (một lần giữ bình tĩnh).
- Nguyên nhân phải thấy được: bàn tay vẽ từ đường đi đã ghi, hoặc chủ thể của ý tưởng.
- Moves từ thư viện, đường cong chọn theo t80. Một smootherstep tự viết cho mọi thứ làm mọi move cùng một kiểu.
- Chuyển động nhanh cần shutter. > 80 px/khung không blur sẽ thành nhiều bản sao; CSS blur không phải cách sửa.
- Camera biết đuổi theo và không bao giờ mất chủ thể; với cú snap, key điểm đáp trước khi nó di chuyển.
- Nháp 1080p30. Không 4K60 trước khi duyệt.
- Không particle/confetti/bụi bùng. Cần điểm nhấn thì cho chữ đáp xuống với squash và wobble.
- Một bộ chất liệu âm, một căn phòng.
- Mọi thứ tất định: `__seek(t)` hai lần cho cùng khung; mô phỏng tính trước với seed cố định; không `Math.random()` trên đường render (`OM.rng(seed)`).

## Các file trong repo

| đường dẫn | là gì |
|---|---|
| `lib/motion.js` | thư viện move → `window.OM` |
| `lib/ui_kit.js` | → `window.UIK`: UI dựng lại trên mặt phẳng, glowRing, độ đọc, ngôn ngữ, timeWarp, subAt |
| `looks/looks.json`, `looks/fonts/` | 6 look khởi đầu và font OFL kèm giấy phép |
| `scripts/look.py` | list / sheet / check / from-shot / apply → `look.js` |
| `scripts/analyze_ref.py` | tham chiếu → energy map, cắt, độ tĩnh, contact sheet, dòng motion |
| `scripts/record_footage.py` | config → bản quay thời gian thực có dấu thao tác → khung 30 fps + đường đi |
| `scripts/probe.py` | comp → thứ gì trên màn hình mỗi khung → điểm nối mỗi ranh giới, đường cong mỗi move |
| `scripts/render.py` | comp → mp4, shutter blur, `--workers` |
| `scripts/stills.py` | comp → contact sheet các mốc |
| `scripts/vo_tools.py` | lời đọc (Kokoro/faster-whisper — trên Claude thay như mục Thiết lập) |
| `scripts/frame_diff.py` | so hai comp ở các mốc |
| `scripts/sfx_palette.py` | chất liệu âm, phòng, `Score` |
| `scripts/verify_promo.py` | oracle nghiệm thu |
| `templates/comp.html` | khung composition (phim motion-web) |
| `references/*.md` | phương pháp chi tiết |
| `cases/*/README.md` | beat sheet, con số, bản bị chê và vì sao |

## Bàn giao

- Bản nháp MP4 + contact sheet các mốc + kết quả `verify_promo.py`.
- Thư mục phim: `comp.html`, `look.js`, `motion.js`, `score.py`/`sfx.wav`, beat sheet. Đủ để sửa và render lại.
- Nói rõ: bản nháp hay bản cuối, đã nghe hay chỉ đo, và nhắc giấy phép phi thương mại nếu video dùng cho kinh doanh.