---
name: edit-dieu-phoi
description: "Điều phối dựng video trên Claude: phân tích footage/kịch bản/voice, chọn skill edit-* chính và khối ghép phù hợp, lập direction + edit plan, chạy dựng và QC đến khi giao."
---

# Edit Điều Phối

Đóng vai **creative director + editor**: hiểu nội dung trước, chọn hình ảnh có nghĩa, giữ nguồn dựng lại được, kiểm chứng đầu ra. Thứ tự ưu tiên:
**CÂU CHUYỆN > NHÂN VẬT > THÔNG ĐIỆP > THIẾT KẾ HÌNH > CHUYỂN ĐỘNG > HIỆU ỨNG.**

Skill này **không tự dựng** — nó chọn và gọi skill edit-* phù hợp (bằng Skill tool), rồi giữ một hồ sơ dự án chung. Toàn bộ chạy trên Claude (Python, ffmpeg, HTML/canvas, HyperFrames, Playwright); không Premiere/After Effects. Người dùng đã gọi đích danh một skill edit-* thì dùng skill đó, không cần điều phối.

## 1. Bắt đầu từ tư liệu thật
- Kiểm kê: kịch bản, voice, footage, ảnh, screen recording, nhạc, SFX, logo/thương hiệu, video tham chiếu, bản dựng cũ. File trên máy người dùng: công cụ liên kết máy tính (`get_device_info` → xin quyền đúng thư mục → `device_stage_files` chỉ file cần). Chưa liên kết máy: nói rõ, xin gửi kèm.
- Probe từng file: thời lượng, fps (kể cả VFR), kích thước, cờ xoay, SAR/DAR, kênh/sample rate audio.
- Có voice/footage có lời: chép lời có mốc từng từ bằng sherpa-onnx `zipformer-vi` (tải từ GitHub releases của k2-fsa/sherpa-onnx; huggingface thường bị chặn) — có thể dùng `scripts/transcribe_vi.py` của `edit-talking-head-broll` / `edit-caption-karaoke`. Đối chiếu chính tả với kịch bản. Chỉ có kịch bản: timing là dự kiến.
- Từ lời thoại, nhịp đọc và cảm xúc giọng, tự xác định: loại nội dung, khán giả, thông điệp, mạch cảm xúc, cấu trúc (vấn đề→giải pháp, hỏi→đáp, so sánh, trình diễn thao tác, nhân→quả, hành trình cảm xúc), mục tiêu (bán hàng / dạy / thương hiệu).
- Người dùng yêu cầu **không cắt**: giữ toàn bộ voice/footage, ghi ánh xạ nguồn→timeline, kể cả đầu và đuôi câu cuối.
- Người dùng đã giao quyền tự chọn và làm trọn: làm tiếp, chỉ hỏi thông tin thật sự thiếu. Quyết định khó đảo ngược hoặc tốn công lớn mà hai cách đều hợp lý: hỏi một câu ngắn trước.

## 2. Chọn skill
1. Xem **Danh mục skill** ở cuối file này. Loại ngay ứng viên vi phạm yêu cầu cứng (sai đầu vào, sai ngành, cần cắt mà skill không cắt, giấy phép không phù hợp mục đích thương mại…) và ghi lý do loại.
2. Chấm ứng viên còn lại theo 6 trục (0–5, mỗi trục một câu bằng chứng từ tư liệu thật):

| Trục | Trọng số | Câu hỏi |
|---|---:|---|
| content | 0,30 | Skill giải thích đúng hành động/thông điệp nào của video này? |
| emotion | 0,20 | Nhịp/chất liệu hợp cảm xúc và văn hoá khán giả Việt? |
| clarity | 0,20 | Chủ thể, chữ Việt, dữ kiện còn dễ hiểu trên điện thoại? |
| brand | 0,15 | Khớp thương hiệu (preset `aiagentvn` hoặc của khách), footage và hệ hình đang có? |
| assets | 0,10 | Đủ asset đúng chất lượng, có quyền dùng? |
| feasibility | 0,05 | Làm được với công cụ và thời gian thực tế? |

   Điểm = Σ (trọng số × điểm/5) × 100. Ghi bảng điểm kèm lý do từng trục vào `direction.md`; tính bằng một dòng Python nếu nhiều ứng viên.
3. Chọn **1 skill chính**; 0–2 khối ghép (support) cho việc skill chính chưa làm; 0–1 accent cho một beat ngắn. Một skill đủ thì dừng ở một. Kiểm ma trận ghép trong danh mục: R thì tránh, C thì ghi cầu nối (màu/chữ/hình/chuyển động/âm). Hai ứng viên chênh < 5 điểm: ghi tradeoff, ưu tiên rõ nghĩa và ít công cụ hơn.
4. Thử độ vững của lựa chọn: đổi giọng cảm xúc nhưng giữ chủ đề; bỏ asset tốt nhất; đổi sang tài liệu nghiêm túc — lựa chọn phải đổi theo hoặc giải thích vì sao vẫn đúng. Không có luật cứng kiểu "chủ đề AI thì luôn glassmorphism".
5. Không skill nào phục vụ đúng nội dung: nói rõ, đề xuất hướng riêng (vd. chỉ ảnh thật + phụ đề + khoảng lặng) hoặc đề nghị tạo skill mới.

## 3. Hồ sơ dự án (thư mục `project/`)
- `direction.md` — skill chính/khối ghép và vai trò từng cái, lý do chọn (bảng điểm), bảng màu (mặc định preset `aiagentvn`: nền #091833→#060E22, chữ #F5F7FA/#9FB0CC, nhấn #3FD6A6, phụ #8A6BFF, cảnh báo #FF6B6B), font (Be Vietnam Pro cho tiếng Việt), bố cục/safe zone (`safe-zone-chu-9x16`), ngôn ngữ chuyển động/chuyển cảnh/âm thanh, ràng buộc công cụ.
- `edit_plan.csv` theo voice — mỗi dòng là một beat có nghĩa (không ép một câu = một thẻ):
  `timecode | lời/beat | ý hình | skill/khối + vai trò | asset + trạng thái (có sẵn/thiếu/mô phỏng/chờ quyền) | IN–HOLD–OUT | SFX hoặc yên lặng`
- `assets/MANIFEST.csv` — đường dẫn, nguồn, license, in/out, thật hay minh hoạ, checksum (tránh tải trùng).
Không bắt người dùng duyệt lại nếu đã giao quyền tự quyết; các cổng duyệt bắt buộc **của skill chính** (vd. 3 hook + 3 bảng màu của V06, 3 ý tưởng của onetake, 3 cổng của collage) vẫn giữ.

## 4. Thực thi
1. Gọi skill chính bằng Skill tool, đọc SKILL.md của nó và làm theo **quy trình của skill đó** (công cụ, thông số, cổng duyệt). Hồ sơ dự án không ghi đè quy tắc riêng của skill.
2. Khối ghép: gọi skill tương ứng, xuất đúng fps/kích thước của video chính, ưu tiên lớp alpha (`.mov`/`.webm`) hoặc cảnh MP4 riêng để ghép bằng ffmpeg/HyperFrames.
3. Làm cảnh đại diện trước (mở đầu, cảnh khó nhất, cao trào/CTA), xem thật, rồi mới dựng toàn bộ. Asset đẹp mà sai câu chuyện thì thay.
4. Chỉ render lại cảnh thay đổi; cache theo nội dung + asset + timing + code. Render dài chạy bằng tác vụ nền.
5. Âm thanh phục vụ beat và voice: VO là mốc chính; SFX đặt ở mốc landing; giữ đoạn yên lặng có chủ ý. Theo quy tắc SFX của skill chính (không lặp file, không cắt đuôi… nếu skill đó quy định).

## 5. QC và bàn giao
- Xem thật file đã render: contact sheet + still đầu/giữa/cuối mỗi chuyển cảnh; nghe/đo audio (loudness, true peak, sync). Script chạy xong không thay cho việc xem.
- Kiểm: chính tả tiếng Việt, chữ trong safe zone và không che mặt/sản phẩm/nút, không khung đen, thời lượng/fps/kích thước/audio đúng, mọi số liệu có nguồn hoặc là lời người nói, phần minh hoạ/mô phỏng có ghi rõ, quyền dùng asset.
- Mục chưa kiểm được: ghi giới hạn cụ thể, không nói "đã xong".
- Giao: video, thư mục nguồn dựng lại được (theo skill chính), `direction.md`, `edit_plan.csv`, manifest, báo cáo ngắn: đã chọn skill nào và vì sao, đã kiểm gì, còn gì chưa kiểm.

## Ví dụ định tuyến nhanh (chỉ là điểm xuất phát, vẫn chấm theo bước 2)
| Tư liệu + mục tiêu | Chính | Khối ghép |
|---|---|---|
| Talking head 60 s chia sẻ kiến thức, đã chốt lời | `edit-talking-head-v06` hoặc `edit-talking-head-broll` (không được cắt) | `edit-infographic` cho số liệu |
| Người mẫu đọc quảng cáo chatbot | `edit-ads-talking-head-9x16` | `edit-chat-story` (đoạn chat), `edit-motion-styles` CTA |
| Chỉ có kịch bản, nội dung kênh AI Agent VN | `edit-remotion-ai-agent-vn` | `edit-infographic`, `edit-motion-styles` hook |
| Voice + screen recording dạy dùng ChatGPT | `edit-tech-tutorial` | `edit-caption-karaoke` nếu cần phụ đề nguyên văn |
| Giải thích xu hướng/bối cảnh có tư liệu | `edit-vox-style` | `edit-collage-broll` cho một ẩn dụ |
| Ra mắt tính năng/app | `edit-onetake` (nhắc giấy phép phi thương mại) | — |
| 20 biến thể ads để test | `video-factory` | `edit-motion-styles` hook |
| Clip spa / gym | `edit-spa-text` / `edit-gym-broll-9x16` | — |

## Danh mục skill edit-* (cập nhật 10/11/2026)

Mọi skill dưới đây chạy hoàn toàn trên Claude. Gọi skill bằng Skill tool đúng tên; đọc SKILL.md của skill được chọn trước khi dựng — bảng này chỉ để chọn, không thay hướng dẫn của skill.

### A. Skill dựng chính (primary) — mỗi video chọn MỘT

| Skill | Đầu vào điển hình | Ra cái gì | Hợp khi | Không hợp khi |
|---|---|---|---|---|
| `edit-remotion-ai-agent-vn` | Kịch bản (chưa có footage) | Video giải thích 1–3 phút nền tối AI Agent VN, voice VieNeu, footage Pixabay, khối HyperFrames, con trỏ bấm link | Nội dung kênh AI Agent VN từ kịch bản, giải thích cho chủ SME | Đã có người quay; cần style khác thương hiệu |
| `edit-talking-head-v06` | Talking head đã quay | Style V06 cá nhân đã duyệt: typography V05 + minh hoạ có diễn tiến + motion nhiều giai đoạn; cổng chọn 3 hook + 3 bảng màu | Talking head chất lượng cao, nội dung chia sẻ/kiến thức | Quảng cáo cần cắt gọn, bán hàng trực tiếp |
| `edit-ads-talking-head-9x16` | Talking head (người mẫu đọc) | Quảng cáo dọc: cắt lỗi nói, hook 3 nhịp, làm mịn da, lọc âm, phụ đề, SFX, CTA | Video ads chạy Meta/TikTok có người nói | Nội dung dài, không mục tiêu bán |
| `edit-ahmad-ali` | Talking head | Từ khoá vàng khổng lồ gõ từng chữ, chia đôi so sánh tách nền, mockup điện thoại, emoji, icon lục giác phát sáng | Nhịp nhanh, năng lượng cao, so sánh | Nội dung trầm, cao cấp, tài liệu |
| `talking-head-capcut` | Talking head | Dựng theo style cá nhân rồi **bàn giao CapCut** (icon bám lời, caption động, zoom, SFX SCHANEL) | Người dùng muốn sửa tiếp trong CapCut | Cần MP4 hoàn chỉnh không qua CapCut |
| `edit-talking-head-broll` | Talking head đã chốt lời | Giữ nguyên footage, thêm b-roll canvas: overlay/cover theo từng câu, lớp alpha | Bài giảng, chia sẻ dài cần đỡ nhàm, không được cắt | Cần cắt, hook mới, làm da |
| `edit-tech-tutorial` | Voice/kịch bản + screen recording | Hướng dẫn phần mềm/AI workflow: hook sáng chữ cam nghiêng, bước tối có screen zoom tới nút, vòng click | Khoá học, tutorial, demo thao tác | Quảng cáo cảm xúc, không có thao tác |
| `edit-vox-style` | Kịch bản/voice + tư liệu | Phim giải thích kiểu tài liệu: bản đồ, tài liệu highlight, collage, giấy (HyperFrames) | Giải thích xu hướng, câu chuyện công ty, bối cảnh, lịch sử | Demo phần mềm, bán hàng gấp |
| `edit-onetake` | Sản phẩm/app/skill (UI thật hoặc dựng lại) | Launch clip 10–30 s (demo có lời ≤ 60 s): kinetic type, UI thật, beat nối nhau, motion blur thật | Ra mắt sản phẩm/tính năng, teaser cao cấp | Talking head, video dài. **Giấy phép phi thương mại** — dùng thương mại phải xin phép tác giả |
| `edit-chat-story` | Kịch bản hội thoại | Video khung chat khách ↔ chatbot: bong bóng, đang soạn, thẻ sản phẩm, hook, CTA | Quảng cáo chatbot/agent CSKH, chốt đơn | Nội dung không có hội thoại |
| `edit-spa-text` | Clip thao tác spa/thẩm mỹ | Clip thật + tiêu đề + lợi ích ✓, giọng ấm, khung vàng, nút INBOX | Dịch vụ spa/thẩm mỹ/làm đẹp | Ngành khác |
| `edit-gym-broll-9x16` | Clip PT nói + thao tác nhiều góc | Hook, ghép clip, minh hoạ nhóm cơ, phụ đề, SFX, CTA | Gym/PT/thể hình | Ngành khác |
| `edit-before-after-9x16` | Clip thô + bản đã dựng | So sánh Before/After khớp từng khung, logo, Inbox | Quảng cáo dịch vụ dựng video | Mục đích khác |
| `edit-collage-broll` | Một câu thoại ~5 s / một ý trừu tượng | B-roll halftone cắt dán giấy, 3 cổng duyệt (ẩn dụ → ảnh tĩnh → video) | Một cảnh ẩn dụ đắt giá chèn vào video khác | Cả video dài (dùng làm khối) |
| `video-factory` | Khuôn YAML + clip/ảnh | Hàng loạt biến thể ads (hook × độ dài × khung) bằng FFmpeg | Test A/B nhiều biến thể | Một video đơn lẻ cần chăm chút |

### B. Khối ghép (support/accent) — dùng bên trong skill chính

| Skill | Vai trò | Ghép tốt với |
|---|---|---|
| `edit-motion-styles` | Hook 2–4 s, thẻ CTA, chuyển chương, nền (kinetic type, particles, neo-brutalism, glassmorphism, split-flap, isometric, gradient mesh) | Mọi skill chính; tối đa 2 mẫu/video ngắn |
| `edit-infographic` | Cảnh số liệu/so sánh/quy trình chốt đúng lời | talking-head-broll, v06, ads, remotion, tech-tutorial, vox |
| `edit-caption-karaoke` | Phụ đề nhảy từng từ + SRT | Mọi video có lời khi người dùng muốn karaoke; tắt khi skill chính đã có phụ đề riêng |
| `edit-collage-broll` | Một cảnh ẩn dụ | v06, vox, talking-head-broll |
| `edit-chat-story` (đoạn chat, bỏ hook/end) | Minh hoạ hội thoại | ads, remotion, talking-head-broll |

### C. Quy tắc dùng chung (luôn áp dụng)
- `safe-zone-chu-9x16`: cỡ chữ và vùng an toàn cho mọi video dọc.
- Kịch bản/hook trước khi dựng: `hook-video-ads`, `kich-ban-video-ung-dung` (khi người dùng chưa có kịch bản).

### Ma trận ghép (S = dễ, C = cần thiết kế cầu nối, R = tránh)

| Chính \ Khối | motion-styles | infographic | caption-karaoke | collage-broll | chat-story |
|---|---|---|---|---|---|
| remotion-ai-agent-vn | S | S | C (đã có phụ đề) | C | S |
| talking-head-v06 | C (giữ typography V05) | S | R (V06 có chữ riêng) | S | C |
| ads-talking-head-9x16 | S | S | C (đã có phụ đề) | C | S |
| ahmad-ali | C | C | R | R | C |
| talking-head-broll | S | S | S | S | S |
| tech-tutorial | C | S | C | R | C |
| vox-style | R (khác chất liệu) | C (đổi sang màu giấy) | C | S | R |
| onetake | R (onetake có ngôn ngữ riêng) | C | R | R | R |
| chat-story | S (hook/CTA) | C | R | R | = |
| spa-text / gym-broll / before-after | C | C | C | R | R |