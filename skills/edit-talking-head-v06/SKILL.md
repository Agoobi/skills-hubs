---
name: edit-talking-head-v06
description: "Dựng talking head theo style V06 cá nhân đã duyệt (typography V05 + minh họa có diễn tiến + motion nhiều giai đoạn) hoàn toàn trên Claude bằng Python/ffmpeg/HTML, không dùng Premiere/After Effects. Cho chọn 3 hook và 3 bảng màu (preset aiagentvn) trước khi dựng."
---

# Edit Talking Head V06 — dựng trên Claude

Bản này chuyển skill `talking-head-premiere` sang làm hoàn toàn trên Claude: cắt, camera, đồ họa, trộn âm và xuất đều bằng Python, ffmpeg và trang HTML render qua Playwright. Không mở, không tạo và không bàn giao `.prproj`/`.aep`. Bàn giao là MP4 cuối và thư mục nguồn có thể dựng lại.

## Style được duyệt

**Typography V05 + sự phong phú minh họa của V02 + chất lượng motion/compositing V06.** Người dùng duyệt test 15 giây đầu, rồi duyệt bản V06 đầy đủ ngày 21/10/2026. Đây là style cá nhân, không phải công thức cho mọi video. Yêu cầu mới của người dùng luôn được ưu tiên.

- Giữ typography đã duyệt khi nâng cấp motion: font, weight, kích thước, bố cục, màu, timing, easing, shadow. Không quay lại typography V02.
- Nhân vật và lời nói dẫn câu chuyện. Chọn minh họa theo nghĩa từng câu. Không thêm số liệu, kết quả phần mềm hay khẳng định ngoài lời thoại.
- Graphic chính có **vào → tương tác/biến đổi → ra/chuyển cảnh** phù hợp. Không chỉ scale/fade icon rồi để đứng yên, nhưng cũng không bắt mọi graphic dùng đủ mọi kỹ thuật.
- Xen minh họa, tương tác, chiều sâu và khoảng nghỉ. Không lặp chuỗi subtitle → UI card → UI card. Không lấy số icon, số SFX hay tỉ lệ visual làm tiêu chí đạt.

### Nhận diện hình ảnh

- Chữ nhấn dùng **Anton**, chữ phụ dùng **Inter** (đã duyệt). Với tiếng Việt: kiểm tra dấu không bị cắt hay thiếu glyph; Anton thiếu dấu thì đổi chữ nhấn sang **Be Vietnam Pro Black/ExtraBold** và ghi vào bảng quyết định. Tải font từ GitHub `google/fonts` (`raw.githubusercontent.com/google/fonts/main/ofl/<tên>/...`). Inter có sẵn ở `/usr/share/fonts/opentype/inter/`.
- Màu lấy từ **bảng màu theo vai trò** (mục "Bảng màu và preset" ngay dưới). Mặc định là preset `aiagentvn`. Không viết mã màu cứng trong script đồ họa. Màu cảnh báo chỉ dành cho keyword quan trọng, nghiêm trọng hoặc phản bác, không làm màu trang trí.
- Typography có shadow để không phẳng, lõi chữ vẫn rõ. Hạn chế gạch/underline vô nghĩa. Đường nối, timeline, progress chỉ dùng khi có chức năng diễn giải.
- Không để graphic che mặt, biểu cảm, keyword hay cử chỉ quan trọng. Xác định vùng trống trên khung đã ghép, không chỉ trên lớp alpha.
- Nguồn đã duyệt là 720×1280/25 fps, zoom footage 100–112% là mức nhẹ đã dùng. Với nguồn khác, chọn mức theo độ nét. Camera đồ họa được phép di chuyển rõ hơn camera footage.
- Glow: dùng trên keyword, icon, stroke/chart và khoảnh khắc reveal. Giữ lõi rõ, halo mềm nhiều bán kính, tint theo accent, cường độ theo nhịp. Không phủ glow lên footage, da mặt hay mọi subtitle. Gọi đúng tên: đây là glow nhiều lớp tự dựng, không phải plugin Deep Glow.

### Bảng màu và preset

Màu chia làm hai lớp:
- **Lớp lõi (giữ theo thương hiệu):** nền, chữ chính, chữ phụ, màu cảnh báo, font.
- **Lớp bối cảnh (được đổi theo footage):** nhấn phụ, tông glow, độ đậm và viền thẻ, vệt sáng nền.

Vai trò dùng chung cho mọi preset: `bg_top`, `bg_bottom`, `bg_glow_1`, `bg_glow_2`, `text`, `text_muted`, `accent` (keyword, số lớn, tick, glow chính), `accent_2` (viền, nhãn, chấm trang trí), `on_accent_2`, `warn` (cảnh báo, phản bác, sai), `card_bg`, `card_border`, `font_display`, `font_body`.

**Preset `aiagentvn` (mặc định, theo logo AI Agent VN):**

| Vai trò | Giá trị |
|---|---|
| Nền | #091833 → #060E22 |
| Vệt sáng nền | tím #6030D0 (~35%) góc trên phải, xanh ngọc #40B090 (~18%) góc dưới trái |
| Chữ chính / chữ phụ | trắng ngà #F5F7FA / #9FB0CC |
| `accent` | xanh ngọc #3FD6A6 |
| `accent_2` / chữ trên nền tím | tím #8A6BFF / #C4B5FF |
| `warn` | san hô #FF6B6B |
| Thẻ | nền #0F2144, viền #1E3A6B |
| Font | Anton cho chữ nhấn (thiếu dấu thì Be Vietnam Pro Black), Inter cho chữ phụ |
| Logo | bản cắt ngang (biểu tượng + chữ AI AGENT), bỏ nền navy, dùng file gốc, không tự vẽ |

**Preset `v06-goc` (bản đã duyệt 21/10/2026, chỉ dùng khi người dùng gọi tên):** nền tối, chữ off-white, `accent` #72A6E8, `warn` đỏ, font Anton/Inter.

Người dùng có thể thêm preset mới (vd. cho khách hàng) theo đúng bảng vai trò trên. Người dùng nêu preset hoặc mã màu trong yêu cầu thì dùng luôn.

Quy tắc cho mọi bảng màu:
- Mỗi cảnh chỉ một màu nhấn chính. `warn` luôn mang nghĩa cảnh báo/phản bác.
- Chữ trên nền đạt tương phản ≥ 4,5:1; `accent` so với nền ≥ 3:1.
- `accent` cách xa tông da và màu áo người nói (khác biệt màu ΔE ≥ 20), để không bị chìm.
- Glow lấy màu `accent`, không phủ lên da mặt.
- Đổi font thì kiểm tra lại dấu tiếng Việt.

### Motion có diễn tiến

Graphic quan trọng cho thấy **trạng thái ban đầu → hành động → phản hồi/kết quả → kết thúc**. Easing, anticipation, overshoot, stagger và motion blur phục vụ hành động, không dùng một preset cho tất cả.

Ví dụ từ bản đã duyệt (điều chỉnh theo lời thoại mới, không chép):

| Ý nghĩa | Cách thể hiện |
|---|---|
| Không thể tiến xa | Marker đi trên đường, gặp rào và phản hồi |
| Kiến thức cần quyền tiếp cận | Sách nối với chìa khóa, sau đó tài liệu bị khóa/tường đóng quanh |
| Trả phí để học | Thẻ thao tác → tín hiệu đến khóa → khóa mở → luồng tới sách |
| Làm việc để lên bậc | Briefcase và marker đi qua các bậc trong phần trống của tài liệu |
| Tích lũy theo thời gian | Calendar nối với các lớp kiến thức tăng dần, không bịa số năm |
| AI hứa làm giàu rồi bị phản bác | Laptop → cursor/input → click → processing → kết quả → tiền có nguồn phát → thu về khi phản bác; không trình bày tiền như kết quả AI có thật |
| Cách làm việc thay đổi | Các node/route bên trong hai tài liệu chuyển cấu trúc |
| Nguyên tắc được kiểm chứng | Sách → shield/check → trạng thái kiểm chứng, kích hoạt lần lượt |
| Nguyên tắc qua thời gian | Timeline past/now/future gắn với chữ đã có; không thêm nhãn trùng hoặc số liệu giả |
| Học trong ngành | Mảnh thông tin truyền vào tài liệu → vùng chọn → insight, nội dung cũ còn đọc được |
| Sẵn sàng/khởi nghiệp | Progress hoàn tất → check, rồi minh họa đổi trạng thái business/idea/venture; kết thúc trả về người nói |

Giữ khoảng nghỉ: câu nói trực tiếp, phản bác mạnh hoặc kết luận không cần icon liên tục. Tỉ lệ 30/40/20/10 từng nêu chỉ để tham khảo.

### Quyết định cho từng câu (editorial)

- Phân tích từng luận điểm: giữ người nói tự nhiên, đổi cỡ cảnh, đổi bố cục, hay thay bằng minh họa. Mỗi đoạn có một mục đích thị giác riêng. Không thêm hiệu ứng chỉ để tăng số lượng.
- Hook: khuôn mặt + một typography/visual mạnh. Giải thích: infographic, callout, so sánh hoặc demo. Chuyển ý: đổi bố cục, cỡ cảnh hoặc cách minh họa. Luận điểm chính: graphic hoặc typography lớn, giảm thành phần phụ. Kết: giảm mật độ để thông điệp có trọng lượng.
- Camera theo độ quan trọng của câu, không zoom mỗi câu: push-in, pull-out, punch cut, bố cục lệch nhẹ, drift có chủ đích. Không để lộ viền trống ngoài footage, trừ khi là bố cục được thiết kế.
- Subtitle thường ổn định, dễ đọc. Keyword, con số, kết luận mới dùng pop, reveal theo từ, mask, overshoot hoặc replacement. Có thể đặt chữ sau người ở điểm chọn lọc, kiểm tra matte để chữ không đè lên da/mặt.
- Thay UI card bằng nhiều cách diễn giải: trim path, line graph, bar/progress, timeline, flowchart, so sánh mở, numbered steps, callout, minh họa toàn màn hình. Counter chỉ dùng số đã được nói hoặc đã xác minh. Không dựng đồ thị doanh thu giả.
- Icon morph chỉ khi hình tương thích và có ý nghĩa; crossfade không phải morph. Asset/B-roll có nguồn hợp lệ và liên quan trực tiếp; không làm giả interface hay hình bằng chứng.
- Depth chọn lọc: foreground/background, occlusion, parallax. Không biến cả video thành 3D. Kiểm tra contour qua nhiều khung.
- Hard cut chiếm phần lớn. Match cut, mask wipe, text-driven transition chỉ dùng khi nối được ý. Không dùng glitch, RGB split, shake hay zoom blur liên tục.
- Animation có anticipation/settle, enter/hold/exit hoặc cut kết thúc có chủ đích. Không dùng cùng easing cho mọi thứ, không cho mọi phần tử chuyển động cùng lúc. Motion blur dành cho chuyển động nhanh.

### Nhánh style tham chiếu (khi người dùng chọn nhánh khác V06)

Phân tích 10 video mẫu tại `E:\talking head` (20/10/2026, chỉ xem khung hình, chưa nghe):
- **A – Creator/marketing:** nền tối, chữ trắng đậm, keyword đỏ/xanh/vàng; thẻ số lượt xem, điện thoại, biểu đồ, notification; bố cục đổi theo tay chỉ/vật được nhắc.
- **B – Editorial sạch:** nền trắng, thẻ hình xếp lớp, chữ có phân cấp, serif italic chỉ làm điểm nhấn, nhấn đỏ trầm; tiêu đề lớn sau đầu tạo chiều sâu.
- **C – Storytelling kinh doanh:** tư liệu, quote đơn sắc, chữ xanh phát sáng, nhịp kể dài hơn.
Chọn một nhánh chính mỗi video. Mở bằng người nói và thông điệp cụ thể; đưa bằng chứng lên sớm nếu có. Tránh caption trên mặt và vùng giao diện Reels/TikTok ở cạnh phải và đáy.

## Quy trình trên Claude

Phiên chạy trên cloud. Footage, thư viện SFX/asset nằm trên máy người dùng: lấy bằng công cụ liên kết máy tính (`get_device_info` → xin quyền đúng thư mục cần → `device_list_dir` → `device_stage_files` chỉ các file sẽ dùng). Chưa liên kết máy thì nói rõ và xin người dùng gửi file kèm.

1. **Xác định đúng nguồn.** ffprobe: duration, fps, độ phân giải, cờ xoay, VFR, audio streams. VFR thì chuẩn hóa về fps cố định ngay từ đầu. Không mặc định file thiếu audio như lần cũ.
2. **Transcript có mốc từng từ.** Dùng sherpa-onnx (`zipformer-vi` cho mốc, `whisper-turbo` cho chính tả) từ GitHub releases của `k2-fsa/sherpa-onnx`; huggingface.co thường bị chặn. Ghi chữ hai mô hình nghe khác vào `uncertain`. Đặt cue theo nội dung, không theo đồng hồ.
3. **Cue sheet.** `cues.json`: mỗi câu/luận điểm → quyết định (người nói / camera / minh họa / typography lớn / nghỉ), graphic gì, diễn tiến 4 trạng thái, SFX nào. Tái sử dụng phần đã đạt; không dựng lại toàn bộ nếu chỉ sửa một đoạn.
**Cổng duyệt trước khi dựng: 3 hook + 3 bảng màu (bắt buộc dừng chờ chọn).**
Làm ngay sau khi có transcript và cue sheet, trước khi dựng đồ họa và render. Người dùng đã chỉ định sẵn hook hoặc màu trong yêu cầu thì bỏ qua phần đó.

*3 phương án hook* (2–4 giây đầu, mở bằng khuôn mặt + một typography/visual mạnh; không logo, không chào hỏi):
| Phương án | Cách làm |
|---|---|
| 1. Câu mở đầu gốc | Câu đầu của người nói + keyword/typography lớn hiện ngay khung đầu |
| 2. Câu mạnh nhất lên đầu | Câu có con số, kết quả hoặc câu hỏi gây tò mò từ giữa video đưa lên đầu, rồi về mạch gốc. Chỉ đề xuất khi không làm gãy nghĩa. |
| 3. Hook minh họa | Mở bằng một graphic có diễn tiến 1,5–2,5 giây, lời nói chạy bên dưới |
Mỗi phương án ghi: câu thoại + mốc, chữ trên màn hình, visual, lý do, rủi ro, và một ảnh tĩnh khung đầu (`hook_1.png`–`hook_3.png`, vẽ bằng preset `aiagentvn`). Mọi con số phải có trong lời nói hoặc nguồn đã xác minh. Câu hook phải bắt đầu đúng đầu từ; chép lời đoạn hook để kiểm.

*3 phương án màu:*
- Lấy mẫu màu từ footage: ~8 khung trải đều; dùng mốc khuôn mặt tách vùng da, áo (dưới cằm), phông nền; gom màu chủ đạo bằng k-means; đo nhiệt độ ánh sáng.
- **A. Đúng thương hiệu:** preset `aiagentvn` nguyên bản.
- **B. Hợp footage:** giữ lớp lõi; chọn `accent_2`, tông glow, độ đậm thẻ hài hoà với ánh sáng và phông (đèn ấm nghiêng ấm, đèn lạnh nghiêng lạnh). Nếu `accent` #3FD6A6 bị chìm vì áo/phông gần màu thì mới đổi `accent`, và ghi lý do.
- **C. Tương phản mạnh:** cho nội dung cần nổi, chạy quảng cáo; nền tối hơn, `accent` bão hoà và sáng hơn, thẻ đặc hơn.
- Mỗi phương án một ảnh tĩnh trên **cùng một khung** (có người nói, phụ đề, một graphic chính và một keyword), `palette_A.png`–`palette_C.png`, kèm bảng mã màu và số đo tương phản. Phương án nào không đạt quy tắc màu thì sửa trước khi gửi.

Gửi cả hook và màu trong một lần (dùng công cụ hỏi lựa chọn nếu có, phương án khuyên dùng đặt đầu, người dùng có thể ghép hoặc sửa mã màu), rồi **dừng**. Trong lúc chờ được làm: cắt, lọc âm, chọn SFX, viết code đồ họa đọc màu từ biến. Không render đồ họa hay bản test trước khi có lựa chọn. Chọn xong thì ghi `palette.json` (preset gốc + các vai trò đã đổi) và hook đã chọn vào `cues.json`.

4. **Cắt và lọc âm.** Cắt ấp úng, lặp, câu hỏng tại ranh giới từ (điểm năng lượng thấp nhất ±0,1 s, crossfade 8–12 ms). Sau khi cắt, chép lời lại chữ đầu/cuối mỗi đoạn (đệm 0,5 s im lặng) để chắc không mất chữ. 
   **Lọc âm** làm trên **toàn bộ file gốc, trước khi cắt**, để mốc thời gian không đổi. Chạy nền ngay sau bước 1, song song với chép lời:
   - **Khử vang** WPE (`nara_wpe`): STFT 1024/256, 24 taps, delay 2, 4 vòng lặp; chạy theo từng dải tần để đỡ tốn RAM.
   - **Khử ồn** GTCRN (`speech-enhancement-models/gtcrn_simple.onnx` từ GitHub releases của sherpa-onnx) chạy ở 16 kHz. Dùng kết quả làm mặt nạ thời gian–tần số áp lên tín hiệu 48 kHz để giữ dải cao; nội suy mặt nạ theo thời gian thật của từng khung STFT, không ghép theo số thứ tự khung (sẽ lệch dần). Trộn lại ~10% tín hiệu gốc để giọng không "méo nước".
   - **Lọc cắt thấp** 80 Hz.
   - **EQ:** -2 dB ở 250 Hz (bớt ù), +2,5 dB ở 3,5 kHz (rõ lời). Giọng đã sáng hoặc mỏng sẵn thì giảm mức tăng và ghi lý do.
   - **Nén nhẹ:** ngưỡng -22 dB, tỉ lệ 2,5.
   - **Cổng chặn nhẹ** cho khoảng lặng, không cắt cụt đuôi chữ.
   - **Chuẩn hoá** loudnorm hai lượt về -14 LUFS, TP -2 dBTP, để sau khi nén AAC đỉnh vẫn không quá -1 dBFS. Loudnorm không đạt mức tuyến tính thì cho qua bộ giới hạn đỉnh trước rồi mới loudnorm.

   **Đo và báo trước/sau** (ghi vào bảng quyết định):
   - ồn nền trong khoảng nghỉ: mục tiêu giảm ít nhất 15 dB;
   - độ vang: mức tiếng còn lại 60–150 ms sau mỗi chữ;
   - cân bằng tần số của giọng: không lệch quá 1–2 dB ngoài phần EQ cố ý.
   Chưa đạt thì chỉnh lại; khử ồn làm méo giọng thì tăng phần trộn gốc thay vì ép mạnh thêm.

   Chép lời lại bản đã lọc để chắc không mất chữ. Xuất `audio_compare.wav` dài ~10 giây (5 giây gốc → 5 giây đã lọc, cùng đoạn) để người dùng tự nghe. Nói rõ là đã đo số liệu, chưa phải đã nghe.
5. **Test ngắn khi đổi hướng.** Mốc đã thành công là test 15 giây đầu, đủ diễn tiến. Không ép mọi dự án phải test. Người dùng đã duyệt và cho làm full thì làm tới bàn giao, không hỏi lại từng cảnh.
6. **Dựng đồ họa** (thay After Effects):
   - Graphic có motion phức tạp: viết thành trang HTML mà mọi giá trị là hàm của thời gian (`window.__seek(t)`), render từng khung bằng Playwright (Chromium có sẵn, không chạy `playwright install`) ra PNG có alpha (`omit_background=True`). Có thể mượn đường cong và moves (spring, expoOut, back.out, camera…) từ thư viện của skill `edit-onetake` nếu đã có.
   - Graphic đơn giản (subtitle, thẻ, icon pop): vẽ bằng Pillow, cache sprite, chỉ vẽ lại khi đổi trạng thái.
   - Mọi màu đọc từ `palette.json`: trang HTML nạp thành biến CSS (`--accent`, `--warn`…), Pillow đọc cùng file. Muốn đổi màu sau này chỉ sửa `palette.json` rồi render lại lớp đồ họa, không dựng lại cắt/âm thanh.
   - Motion blur cho chuyển động nhanh: lấy trung bình 4–8 mẫu thời gian trong khung (shutter 180°) ở không gian tuyến tính.
   - Icon: Unicons (`github.com/Iconscout/unicons`, npm `@iconscout/unicons`) hoặc asset trong POWER PODCAST BUNDLE. Lưu nguồn/license cùng icon.
7. **Ghép.** Footage (zoom/reframe theo mốc khuôn mặt, làm mịn da nhẹ nếu cần) + lớp đồ họa alpha + subtitle → pipe khung thô vào ffmpeg (H.264, preset veryfast). Trên máy 2 nhân, ~4–7 khung/giây: báo ước tính trước khi render dài.
8. **Âm thanh.** Giọng, nhạc, SFX là 3 track riêng, ghép theo cùng số khung với hình (1 khung = 48000/fps mẫu). Trộn bằng numpy hoặc ffmpeg `amix` với `normalize=0`. Không dùng `-shortest` làm cụt đuôi SFX cuối.
9. **Kiểm tra trước khi báo xong.** Xem khung ghép ở lúc vào, trạng thái đầy đủ và lúc ra của từng graphic chính (nhất là chồng chữ, mép vùng vẽ, mặt/cử chỉ, motion blur). Giải mã toàn MP4, đo LUFS/đỉnh, chép lời lại bản đã trộn để chắc SFX không che lời. Nói đúng loại bằng chứng: xem khung, đo âm hay nghe thật là khác nhau. Chỉ đo số liệu thì không nói đã nghe.

## Asset và âm thanh

### Nguồn trên máy người dùng

Kiểm tra đường dẫn tồn tại trước khi dùng; khi đổi máy có thể ánh xạ thư viện khác.

| Nguồn | Vị trí | Cách dùng |
|---|---|---|
| SFX SCHANEL | `D:\Làm với Khoa\SCHANEL` | Thư viện SFX chính trên máy hiện tại. `New folder` là clip meme có giọng người: không tự dùng |
| BOOM Casual UI | `E:\TaiNguyen\SFX Meme\Boom_Library_Casual_UI_Construction_Kit_WAV` | Click, whoosh, shimmer, impact, card. Nhiều WAV chứa chuỗi take |
| POWER PODCAST BUNDLE | `E:\TaiNguyen\POWER PODCAST BUNDLE` | Được dùng toàn bộ asset (cả SFX) cho bản dựng của người dùng, không cần hỏi lại |
| Asset Index | `E:\TaiNguyen\POWER PODCAST BUNDLE\POWER_PODCAST_ASSET_INDEX.csv` + `.metadata.json` | Snapshot 3027 mục. Tìm trong index rồi xem ứng viên thật; không quét lại cả thư viện nếu index còn hợp lệ |
| Free Sfx Pack | `E:\TaiNguyen\Free Sfx Pack` | Whoosh, impact, bass, cloth, heartbeat, beep; chưa xác nhận chất âm bằng nghe |
| Video mẫu | `E:\talking head` | Học bố cục/nhịp/motion; không đưa mẫu vào video mới |
| Footage | `E:\talking head\rawvideo` | Chọn đúng file yêu cầu, không mặc định video 1p |
| Bản V06 chuẩn | `E:\talking head\edit-1p-v06\full\1P_TALKING_HEAD_V06_FINAL.mp4` (test: `...\test15\V06_FIRST_15_SECONDS_TEST.mp4`) | Nguồn style chính để đối chiếu. 20 camera clip, 41 SFX, 60,08 s là dữ kiện của video đó, không phải quota |
| Style documentary/collage | `E:\document\style-analysis\STYLE-GUIDE-VI.md` | Chỉ đọc khi người dùng yêu cầu style trong `E:\document` |

Ổ `E:` có thể không có trên máy hiện tại: kiểm tra bằng `device_list_dir`; không có thì dùng SCHANEL và tự tạo asset, ghi lại vào bảng quyết định.

### Chọn asset

- Thứ tự ưu tiên: asset đã dùng trong dự án → index/bundle → tự dựng bằng HTML/Pillow → nguồn ngoài nếu yêu cầu hiện tại cho phép. Xem/nghe ứng viên trước khi chốt; tên file không chứng minh nội dung. Preview Mister Horse không tự động là media dùng được; metadata alpha không chứng minh pixel trong suốt.
- Đã kiểm tra và dùng trong V06: `Money3.mov` (cụm tiền alpha), `NRG 03.mov` trong `EFFECTS/BLU GLOW` (vòng năng lượng cyan cho kết quả AI). `Blue Light 1.mov` là đèn báo động, đã loại khỏi cảnh AI. Không phải danh sách bắt buộc.
- Icon phải tham gia diễn giải: liên kết, được chọn, mở khóa, truyền dữ liệu, đổi trạng thái hoặc dẫn sang ý sau. Không dán badge mặc định cho mỗi câu.
- Được tạo thêm asset khi thư viện thiếu, nhưng phải bám ý đang nói và thống nhất style. Số liệu/chứng cứ phải từ nguồn thật.
- Không phân phối asset thương mại cùng skill.

### SFX

- SFX rõ, hợp hành động: click cho kích hoạt, swipe cho hướng chuyển, tick cho milestone/counter, impact cho luận điểm, rise trước reveal. Có thể layer impact ở bước ngoặt, không layer mọi hit.
- Đổi texture/take; không một âm cho mọi chuyển động, không xoay vòng 2–3 take cho cả phút. Kiểm tra cặp `source + sourceIn` để phát hiện cùng take đổi tên.
- Giữ trọn attack/body/tail; cho chồng track khi cần. Âm quá dài thì chọn âm ngắn hơn hoặc đổi thời điểm, không cắt/fade sớm để ép timing. Hình đã chuyển thì đuôi SFX vẫn chạy tiếp.
- WAV chứa nhiều biến thể: dùng silence detection để tìm ứng viên, chọn một biến thể hoàn chỉnh, không phát cả chuỗi.
- Cân từng âm theo voice. Không giảm đồng loạt 15–21 dB (V01 bị chê SFX quá nhỏ). Peak -12,5 đến -8,5 dBFS là điểm thử, không phải chuẩn. Đo từng file trước khi cân.
- Nhạc hợp tone, thấp hơn lời; có thể drop ngắn trước câu quan trọng. Không speed-ramp lời thoại. Giữ pause chiến lược, J/L-cut với minh họa khi hữu ích.
- Màu đồ họa theo `palette.json`. Footage: da tự nhiên, highlight có kiểm soát; không sharpen quá hay "AI face enhancement".

### Manifest SFX và audit

Một phần tử cho mỗi sự kiện:

```json
[{"path":"work/sfx/sfx_01.wav","start":1.12,"duration":1.77,"source":"D:/Làm với Khoa/SCHANEL/Swoosh_02.wav","sourceIn":0.0,"sourceOut":1.77,"gain":-3.0,"key":"impact"}]
```

`gain` là thay đổi khi xuất file, không phải mức tuyệt đối. Ghi script ở mục cuối ra `audit_sfx.py` rồi chạy `python3 audit_sfx.py manifest.json --video-duration <giây> --measure`: báo peak/RMS, take lặp, file thiếu, đuôi vượt thời lượng. Script chỉ đọc, không sửa audio, không thay thế việc nghe.

## Bài học từ các lỗi đã sửa

- **Hai tờ giấy:** tờ trước từng che đầu tiêu đề và dòng chữ của tờ sau. Sửa bằng khoảng hở thật, giảm độ nghiêng, bố cục hai cột, vào/ra phía ngoài. Chồng giấy chỉ ở vùng trống; đường nối không cắt ngang chữ. Kiểm tra cả lúc reveal và lúc rời cảnh.
- **Tiền/particle và mép vùng vẽ:** asset tiền từng bị bó trong ô hẹp, lộ mép cắt chữ nhật. Mở rộng cả canvas lẫn vùng animation; làm mềm mép nguồn nếu footage đã cắt vật thể. Không chỉ phóng asset trong khung cũ.
- **Motion cuối và bố cục dọc:** rocket từng bay chạm chữ VENTURE; giữ đường đi dưới vùng chữ, cho exit ngang. Giấy Industry Notes từng sát mép dưới; giảm kích thước nhẹ. Không mặc định tăng scale để có thêm motion.
- Không sao chép tọa độ, scale hay timecode của video 1p sang video mới. Xét bounds sau rotation/perspective và độ đọc trên điện thoại.
- **Phản hồi thật:** bản 27 bị chê quá tĩnh, đơn điệu → cần nhiều thay đổi thị giác và nhấn lời nói, tránh nhiều giây chỉ giữ khung đổi caption. 1p V01 có 41 shot/zoom và 50 SFX nhưng vẫn ít icon, âm nhỏ, lặp → không lấy số lượng làm tiêu chí. V02 thêm 32 Unicons ở 36 cue, 49 take cho 50 sự kiện, cân từng file.
- Không phân tích lại năm video mẫu, không quét lại toàn bộ bundle, không render lại phần đã đạt nếu không có lý do.

## Bàn giao

- MP4 cuối (1080×1920 hoặc theo nguồn/yêu cầu, H.264 + AAC 48 kHz).
- `audio_compare.wav` (nghe lọc âm trước/sau) và bảng số đo trước/sau: ồn nền, độ vang, cân bằng tần số, LUFS, đỉnh.
- 3 phương án hook và 3 phương án màu đã đề xuất (kèm ảnh), phương án người dùng chọn.
- Thư mục nguồn: `palette.json`, `cues.json`, `transcript.json`, `edit_plan.json`, `sfx-manifest.json`, các trang HTML/script đồ họa, `voice.wav`, `sfx.wav`, `music.wav` (nếu có). Đủ để dựng lại hoặc sửa từng cue mà không làm lại từ đầu.
- File lớn hơn ~30 MB không ghi thẳng về máy qua công cụ liên kết được: gửi qua khung chat (SendUserFile), hoặc ghi bản nén nhỏ hơn về máy.
- Nêu rõ: đồ họa đã render vào MP4, muốn sửa thì sửa nguồn HTML/script rồi xuất lại. Nói đúng phần đã/chưa kiểm được.

---

# Script audit_sfx.py

Khi cần audit SFX, ghi nguyên văn script dưới đây ra file `audit_sfx.py` rồi chạy. Script chỉ đọc, không sửa audio; cần ffmpeg và ffprobe cho `--measure`.

```python
"""Read-only SFX manifest audit; requires ffmpeg and ffprobe for --measure."""
import argparse
import array
from collections import defaultdict
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys


def measure(path):
    probe = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'a:0',
                            '-show_entries', 'stream=channels', '-of', 'json', str(path)],
                           capture_output=True, check=False)
    if probe.returncode:
        raise ValueError(probe.stderr.decode('utf-8', errors='replace'))
    streams = json.loads(probe.stdout).get('streams', [])
    if not streams:
        raise ValueError('No audio stream')
    channels = int(streams[0]['channels'])
    proc = subprocess.Popen(
        ['ffmpeg', '-v', 'error', '-i', str(path), '-map', '0:a:0', '-vn', '-f', 'f32le',
         '-acodec', 'pcm_f32le', '-ar', '48000', 'pipe:1'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    peak = power = count = 0
    while True:
        raw = proc.stdout.read(65536)
        if not raw:
            break
        values = array.array('f')
        values.frombytes(raw)
        if sys.byteorder != 'little':
            values.byteswap()
        if values:
            peak = max(peak, max(abs(x) for x in values))
            power += sum(x*x for x in values)
            count += len(values)
    error = proc.stderr.read().decode('utf-8', errors='replace')
    if proc.wait():
        raise ValueError(error.strip())
    db = lambda x: round(20*math.log10(x), 2) if x > 0 else None
    return {'peak_dbfs': db(peak), 'rms_dbfs': db(math.sqrt(power/count) if count else 0),
            'decoded_duration': round(count/(48000*channels), 6), 'clipping': peak >= 1.0}


def audit(events, base, duration=None, do_measure=False):
    takes = defaultdict(list)
    rows = []
    for i, event in enumerate(events):
        start, length = float(event['start']), float(event['duration'])
        if not all(math.isfinite(x) and x >= 0 for x in [start, length]):
            raise ValueError(f'Event {i+1}: start/duration must be finite and nonnegative')
        path = Path(event['path'])
        if not path.is_absolute():
            path = base/path
        source = str(event.get('source') or path).replace('\\', '/').casefold()
        key = (source, round(float(event.get('sourceIn', 0)), 5))
        takes[key].append(i+1)
        row = {'event': i+1, 'start': start, 'path': str(path), 'missing': not path.is_file()}
        if duration is not None and start+length > duration+0.001:
            row['tail_past_video_seconds'] = round(start+length-duration, 6)
        if do_measure and not row['missing']:
            try:
                row.update(measure(path))
                if start+row['decoded_duration'] > (duration if duration is not None else math.inf)+0.001:
                    row['decoded_tail_past_video'] = True
            except ValueError as exc:
                row['decode_error'] = str(exc)
        rows.append(row)
    repeats = [{'source': src, 'sourceIn': point, 'events': ids}
               for (src, point), ids in takes.items() if len(ids) > 1]
    return {'events': len(events), 'unique_takes': len(takes), 'repeated_takes': repeats,
            'missing_files': sum(r['missing'] for r in rows), 'files': rows,
            'note': 'Read-only measurements; not a listening review. Low RMS can include silence/tails.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--video-duration', type=float)
    parser.add_argument('--measure', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.measure and not all(shutil.which(x) for x in ['ffmpeg', 'ffprobe']):
        parser.error('ffmpeg and ffprobe are required for --measure')
    if args.video_duration is not None and (not math.isfinite(args.video_duration) or args.video_duration < 0):
        parser.error('--video-duration must be finite and nonnegative')
    try:
        events = json.loads(args.manifest.read_text(encoding='utf-8-sig'))
        if not isinstance(events, list):
            raise ValueError('Manifest must be a JSON list')
        result = audit(events, args.manifest.resolve().parent, args.video_duration, args.measure)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(output, encoding='utf-8')
        print(json.dumps({k: result[k] for k in ['events', 'unique_takes', 'missing_files', 'repeated_takes']}, ensure_ascii=False))
    else:
        print(output)
    return 2 if any(r['missing'] or r.get('decode_error') for r in result['files']) else 0


if __name__ == '__main__':
    raise SystemExit(main())
```