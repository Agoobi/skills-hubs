---
name: edit-vox-style
description: Dựng video giải thích kiểu phim tài liệu (Vox Style) bằng HyperFrames trên Claude — bản đồ, tài liệu được highlight, ảnh cắt collage, typography và chất liệu giấy, camera dẫn theo lời — cho video giải thích xu hướng, kinh doanh, công nghệ, lịch sử. Khung ngang hoặc dọc 9:16.
---

# Edit Vox Style

Bản chạy hoàn toàn trên Claude của skill `vox-style`: dựng bằng HyperFrames (HTML + GSAP → MP4), âm thanh trộn bằng HyperFrames/ffmpeg. Đã bỏ phần hoàn thiện âm thanh trong Premiere và xử lý lỗi Windows. Không thêm logo Vox hoặc tự nhận là tác phẩm của Vox.

Mục tiêu: người xem **hiểu lập luận qua bằng chứng thị giác**, không phải xem hiệu ứng.

## Chọn đúng phạm vi
- Dựng mới hoặc sửa hình: HyperFrames — đọc [hyperframes-claude](references/hyperframes-claude.md).
- Âm thanh (voice, nhạc, SFX, voice-only): đọc [audio-claude](references/audio-claude.md).
- Video talking head có sẵn cần chèn b-roll kiểu Vox: dùng skill này cho từng cảnh minh hoạ, ghép bằng `edit-talking-head-broll` hoặc `edit-talking-head-v06`.
Yêu cầu hiện tại của người dùng quyết định chế độ; không mặc định mọi phim có nhạc/SFX.

## Chọn ngôn ngữ hình ảnh
Đọc [phân tích tham chiếu](references/reference-analysis.md). Bốn nhánh:
- **Evidence / map:** nền trắng hoặc biển navy, tài liệu thật, chữ đen, highlight xanh, nét nối và nhãn địa lý. Hợp luật, chính sách, địa chính trị, dữ liệu.
- **Editorial collage:** nền vàng nhạt/chartreuse, ảnh cắt đen trắng, hình tròn xanh bạc hà, nhấn đỏ. Hợp lịch sử khoa học, câu chuyện công ty.
- **Archival scrapbook:** giấy kem cũ, báo/bản đồ mờ, mép rách, băng dính, ảnh trắng đen viền giấy, chữ condensed. Hợp lịch sử, thể thao.
- **Red technology documentary (bản đã duyệt):** đỏ chủ đạo, nền kem/trắng ngà, charcoal và ảnh đen trắng; tài liệu highlight, collage có chiều sâu, camera theo lời dẫn. Đọc [quy chuẩn đã duyệt](references/approved-red-documentary.md). Không tự thêm xanh/mint/chartreuse vào nhánh này. Mỗi khung ưu tiên một vật dụng nhỏ; không dùng callout trang trí đường gấp khúc + chấm tròn.

Chỉ nói "Vox Style" thì chọn nhánh theo chủ đề và nêu ngắn lý do. Với nội dung AI Agent VN (AI, kinh doanh, công nghệ), nhánh mặc định là **Red technology documentary**; khách muốn màu thương hiệu thì giữ cấu trúc nhánh, đổi màu nhấn.

## Từ lời thoại thành cảnh
1. Lấy kịch bản/voice, tỉ lệ khung, thời lượng, tài sản có sẵn. Chưa có voice thì dựng timing tạm và ghi rõ. Có voice thì chép lời có mốc từng từ bằng sherpa-onnx (`zipformer-vi`, tải từ GitHub releases của k2-fsa/sherpa-onnx; huggingface thường bị chặn) để đặt cue.
2. Mỗi beat ghi: timecode → ý cần hiểu → bằng chứng → động tác dẫn mắt → hold → nối cảnh. Bản đồ trả lời "ở đâu"; highlight đúng câu; zoom tới chi tiết có ý nghĩa.
3. Tách lớp nền, tư liệu, chủ thể, chú thích, texture. Một trọng tâm mỗi cảnh; nhãn xuất hiện tuần tự.
4. Giữ vật thể hoặc hướng chuyển động qua cut khi nội dung liên quan. Hard cut khi đổi ý; wipe giấy khi chuyển chương scrapbook.
5. Thiết kế trạng thái nghỉ trước, rồi thêm IN/hold/OUT. Đọc [motion recipes](references/motion-recipes.md) — thông số là đề xuất, không phải keyframe gốc.

## Chất liệu và sự chính xác
- Ảnh/tư liệu có nguồn; cutout PNG/WebP alpha giữ chi tiết cạnh. Không thay toàn bộ tư liệu bằng icon. Không tải ảnh người nổi tiếng từ web đưa vào phim.
- Giấy/grain tương phản thấp, chữ sắc. Mép rách và băng dính chủ yếu cho scrapbook.
- Màu nhấn có vai trò nhất quán: điểm địa lý, từ khoá, vùng đọc.
- Sans đậm cho nhãn, condensed cho ngày tháng scrapbook, serif khi là tư liệu/trích dẫn. Font cục bộ, đủ dấu tiếng Việt, được phép đóng gói.
- Tách dữ kiện, minh hoạ và suy luận. Tài liệu dựng lại để minh hoạ phải ghi "minh hoạ"; không tạo trích dẫn, văn bản luật hay bài báo giả trông như thật. Lưu nguồn từng asset trong `assets/SOURCES.txt` hoặc manifest.
- Khung dọc 9:16: chữ và chi tiết bằng chứng theo `safe-zone-chu-9x16`; tài liệu/bản đồ dùng camera crop dọc, không thu nhỏ cả trang ngang vào giữa khung.

## HyperFrames
Chép `assets/hyperframes-starter/` sang dự án mới (mẫu có giấy vào cảnh, zoom/highlight, route/callout — không phải phim hoàn chỉnh hay bản đồ thật). Không sửa starter trong skill.
Timeline hữu hạn, seek được tới mọi thời điểm; timeline GSAP paused đăng ký đúng composition ID. Không dùng timer, random mỗi lần render, animation theo đồng hồ thật hoặc callback tạo nội dung giữa timeline. Asset cục bộ, phiên bản thư viện cố định trong lockfile. Phim nhiều cảnh chia sub-composition.

## Kiểm tra và bàn giao
- `npx hyperframes check .` phải "Check passed"; snapshot đầu, giữa, cuối chuyển động, khung sát cut, khung cuối.
- Cùng một timestamp sau seek tiến/lùi phải cho cùng hình.
- Render MP4 rồi trích khung từ MP4 để xem: khung trống, mất font, crop, nét quá mảnh, giật cut. HTML mở được chưa chứng minh render được.
- Có voice: cue khớp từ khoá, nhạc/SFX không lấn lời.
- Bàn giao: MP4, thư mục nguồn HyperFrames (đã có lockfile), manifest nguồn asset; nêu đúng mức đã kiểm thử. Runtime lỗi thì báo phần chưa test, không đổi công cụ rồi vẫn gọi là HyperFrames.
