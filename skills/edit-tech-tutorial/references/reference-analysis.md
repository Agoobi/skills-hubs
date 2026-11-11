# Phân tích reference — v1, 27/10/2026

## Phạm vi chứng cứ

Nguồn: `E:/trainskill/editviral/Download (17).mp4` đến `(24).mp4` và master prompt người dùng cung cấp. Đã probe toàn bộ 8 file, tính SHA-256 và xem contact sheet xuyên suốt mỗi 2 giây; xem thêm 8 frame/giây trong ba cửa sổ 18:02–04, 19:18–20, 24:11–13. Timestamps phân đoạn bên dưới là khoảng quan sát, sai số khoảng ±2 giây; không phải EDL hoặc transcript đã align. Các đoạn sample dày giúp nhận diện hình thái chuyển động, không xác định được easing curve/keyframe gốc.

Chưa nghe duyệt toàn bộ soundtrack, chưa có transcript và chưa đo nhịp theo âm tiết. Vì vậy không kết luận tên SFX, loại nhạc, loudness hay độ lệch SFX–motion từ ảnh. Các mapping âm thanh trong tài liệu SFX là đề xuất theo master prompt, chưa phải kết quả nhận diện soundtrack. Font gốc và mã màu gốc chưa được xác minh. Đây là phân tích hình ảnh lấy mẫu toàn thời lượng, không phải tuyên bố đã xem/nghe từng frame.

Tất cả video: 576×1024, 9:16, 30 fps, có audio. 22 và 23 giống SHA-256 hoàn toàn, không tính là hai bằng chứng độc lập. Metadata đầy đủ trong `REFERENCE_METADATA.json`.

| File | Thời lượng | Chủ đề quan sát |
|---|---:|---|
| 17 | 117.168s | Quy trình tạo video bản đồ |
| 18 | 98.333s | Tạo hoạt hình bài tập thể hình |
| 19 | 53.233s | Giải thích mô hình kênh YouTube, infographic thời gian |
| 20 | 108.902s | Tạo video lịch sử hoạt hình 3D |
| 21 | 60.667s | Tổng hợp kho skill/video bằng AI |
| 22 | 91.833s | Tạo video quiz trên giấy |
| 23 | 91.833s | Bản sao byte-for-byte của 22 |
| 24 | 64.273s | Demo quy trình AI edit video |

## 17 — Bản đồ

| Khoảng | Hình ảnh và hành vi quan sát | Bài học |
|---|---|---|
| 0–6s | Trang kênh → thumbnail → video dọc trong giao diện; chữ tên kênh ở dưới | Hook bằng ví dụ cụ thể trước giải thích |
| 6–10s | Hai card dọc bo góc: video mẫu / AI tạo; cam nhấn “Tự làm” | So sánh cùng kích thước để đọc nhanh |
| 10–18s | Avatar áo đỏ, heading rồi montage nhiều card bản đồ; chữ BĐS lớn | Chia hierarchy, hình đi cùng ý |
| 18–44s | Screen chat sáng trong vùng trên, nền đen hạt bên dưới; caption trắng, keyword vàng; nhiều lần đổi crop vào nội dung | Tutorial ưu tiên mục đang dùng hơn toàn màn hình |
| 44–60s | Flow nền tối, popup model/tỷ lệ; kết quả bản đồ; sao chép prompt | Giữ liên tục chuỗi đầu vào → tùy chọn → kết quả |
| 60–74s | Preview/timeline tạo video, kéo cuối để lấy frame, tạo tiếp các đoạn | Dùng trạng thái giao diện làm cầu nối |
| 74–80s | Voice tool rồi màn hình edit | Tóm tắt bước cuối, không cần chép mọi thao tác |
| 80–100s | Thành phẩm bản đồ toàn khung; digital pan/zoom; vùng màu, viền, leader line và nhãn lớn | Khi kết quả cần nhìn chi tiết, cho chiếm toàn khung |
| 100–112s | Trang bài học → CTA chữ vàng và avatar | CTA tách khỏi nội dung dạy |
| 112–117.168s | Profile/end card nền sáng rồi outro nền tối | Outro nền tảng không phải công thức nội dung |

Thiết kế: white grid/soft gray decoration ở mở đầu; phần dạy có tương phản mạnh, khoảng trống dưới dành caption. Kiểu chữ đậm nghiêng + một ít chữ script ở hook, sans đậm ở tutorial. Kỹ thuật riêng: bản đồ nhiều tầng và leader line, chỉ dùng khi cần giải thích không gian. Giá trị thu hút quan sát được là bằng chứng trước/sau và thành phẩm; chưa có dữ liệu retention để kết luận hiệu quả.

## 18 — Thể hình 3D

| Khoảng | Quan sát | Bài học |
|---|---|---|
| 0–4s | Card bài tập, chữ cam “Tập GYM”; sample 2–4s cho thấy thay montage rồi fade/scale hiện nhóm card mới | Nhóm hình thành một ý, không animate từng card liên tục |
| 4–8s | Phone mockup và social card tràn khung; icon link/affiliate, bàn tay chỉ | Vật chứa và icon giải thích kênh phân phối |
| 8–16s | Collage bắt tay/tiền → màn hình editor → typography lớn → nền tối AI | Đổi hình theo luận điểm, không đổi chỉ vì hết một giây |
| 16–32s | Avatar “Cách làm”; chat chủ đề, image/video prompt; caption tóm ý ở dưới | Hook có đồ họa mạnh, phần dạy tiết chế hơn |
| 32–48s | Flow chọn model, tạo ảnh người tập; chuyển chế độ video | Zoom đúng control đang giải thích |
| 48–62s | Copy prompt video → clip sinh ra → voice tool → CapCut | Cho thấy mối nối giữa công cụ, giữ caption ngắn |
| 62–84s | Video tập toàn khung, cơ được tô sáng cam, đổi góc cơ thể; subtitle nhỏ | Visual giải thích cơ chế, không chỉ trang trí |
| 84–96s | Trang học, CTA chữ vàng, avatar | Chốt sau khi xem kết quả |
| 96–98.333s | Profile card trên nền sáng | Kết gọn theo mục tiêu riêng |

Kỹ thuật riêng: highlight cơ thể và thay đổi góc nhìn 3D. Không diễn giải tuyên bố sức khỏe thành tư vấn hoặc tái dùng footage khi chưa có quyền. SFX/nhịp VO chưa nghe kiểm chứng; không suy từ icon rằng có tiếng click.

## 19 — Infographic và talking head

| Khoảng | Quan sát | Bài học |
|---|---|---|
| 0–4s | Trang kênh/biểu đồ số liệu trên nền trắng, mốc “7 năm” màu cam | Bằng chứng làm hook, giữ nguồn khi dùng số |
| 4–8s | Nhân vật faceless collage → người dẫn thật, caption giữa/dưới thân | Chuyển abstraction sang con người |
| 8–14s | Mục 01, collage tay/ảnh/kính lúp; laptop; ý nghĩa hiển thị từng cụm chữ | Một bố cục phục vụ một luận điểm |
| 14–18s | Mục 02, thumbnail và số lượt xem lớn, coin và con số tiền | Phân biệt dữ liệu minh họa với số được xác minh |
| 18–20s | Sample dày: circle đỏ phóng từ biểu tượng play, khối cũ mờ đi, số 03 và tiêu đề mới hiện | Một shape có thể nối hai trạng thái bằng scale + opacity |
| 20–26s | Bốn hàng task, icon và badge thời gian; từng hàng chuyển từ trạng thái thủ công sang AI, tổng từ 8 giờ sang 11 phút | Giữ vị trí các hàng, chỉ đổi trạng thái đang so sánh |
| 26–30s | Diagram quy trình 4 bước → talking head | Tóm quan hệ trước đổi visual mode |
| 30–46s | Trang kênh, danh sách video, trang khóa học; chữ FYF rất lớn | Giữ nhãn ngắn, không phủ toàn trang bằng caption |
| 46–52s | Người dẫn CTA, chữ cam/vàng | B-roll quay về khuôn mặt đúng câu chốt |
| 52–53.233s | Profile card | Đoạn kết riêng |

Khác các tutorial còn lại: ít đoạn screen dark kéo dài hơn; infographic có vai trò cấu trúc lập luận. Collage đen trắng tương phản cam/đỏ, khoảng trắng rộng. Đây là reference mạnh nhất cho numbers, hierarchy và sequential reveal. Không đưa các số thời gian/doanh thu thành mặc định cho nội dung mới.

## 20 — Lịch sử hoạt hình

| Khoảng | Quan sát | Bài học |
|---|---|---|
| 0–6s | Thumbnail, bảng thống kê kênh, crop cận số | Bắt đầu từ bằng chứng nhìn thấy |
| 6–14s | Montage frame hoạt hình, cam “Phim tài liệu”; cảnh tối/blur và avatar hướng dẫn | Từ kết quả sang lời hứa hướng dẫn |
| 14–28s | Flash sáng ở đoạn đổi sang chat; danh sách ý tưởng, script, prompt | Flash là điểm chuyển riêng, không mặc định mọi cut |
| 28–42s | Dreamina UI, model list, prompt và kết quả ảnh | Giữ control/nhãn dễ đọc khi phóng |
| 42–60s | Flow, input ảnh, mode video, preview timeline, tạo các cảnh tiếp | Lặp quy trình được tóm bằng kết quả thay vì lặp cả thao tác |
| 60–70s | Voice tool và CapCut | Gộp các bước phụ để giữ mạch |
| 70–90s | Thành phẩm hoạt hình ngang đặt trên nền tối; nhãn “Thành quả”; nhân vật, đồ vật và góc máy thay đổi | Giữ aspect của thành phẩm, không kéo giãn |
| 90–102s | Trang học/CTA/avatar | Chốt gắn với tài liệu |
| 102–108.902s | Profile/outro nền tảng | Có thể bỏ nếu mục tiêu đầu ra không cần |

Tutorial dùng screen + caption trắng/vàng; các tên công cụ có lúc accent tím. Kỹ thuật riêng: video ngang trong canvas dọc, cảnh kể chuyện nhiều góc. Không mặc định mọi kết quả phải full bleed.

## 21 — Kho skill

| Khoảng | Quan sát | Bài học |
|---|---|---|
| 0–6s | Title cam rất lớn, collage trang kho mẫu/GitHub; frame blur/flash | Hook typography có cả bằng chứng |
| 6–10s | Trang tài liệu và cặp video gốc/đã edit; label “Phụ đề” | Thể hiện kết quả thay vì chỉ mô tả tính năng |
| 10–18s | Website HyperFrames, timeline/preview trong trang; chữ cam tóm khả năng | Screen lớn ở trên, giải thích ngắn ở dưới |
| 18–28s | Lần lượt nhiều repo/README; highlight từng khả năng | Thay crop/vị trí theo phần đang nói, tránh screenshot tĩnh dài |
| 28–38s | Demo người dẫn, ghost-editor, card so sánh đỏ, ảnh cây | Đan demo, số liệu và ẩn dụ |
| 38–50s | Thư viện video, grid mẫu, preview modal | Cho xem độ đa dạng bằng montage trong vật chứa |
| 50–54s | Avatar và chữ “kho mã nguồn” | Kết luận bằng một ý |
| 54–60.667s | Profile/outro | Nhận diện thương hiệu riêng reference |

Khác biệt: nền sáng xuyên phần lớn video, không bắt buộc chuyển dark tutorial. Không coi nội dung trang repo trong clip là tài liệu sản phẩm cập nhật.

## 22 — Quiz trên giấy

| Khoảng | Quan sát | Bài học |
|---|---|---|
| 0–8s | Profile, grid video quiz, mở một ví dụ | Cho người xem biết định dạng đầu ra |
| 8–12s | Hai card “Video gốc” / “AI tạo”; tint/flash nhẹ | So sánh có nhãn rõ |
| 12–24s | Master prompt → chủ đề → số câu hỏi trên chat; screen lớn, caption vàng/trắng | Dùng caption để diễn giải mục tiêu, không chép đầy prompt |
| 24–34s | Script trả về, prompt image/video, copy vùng text | Crop giữ phần cần thao tác |
| 34–52s | Flow tạo ảnh rồi mode video, popup thông số | Bước trước tạo input cho bước sau |
| 52–60s | Kết quả trang giấy và preview timeline | Giữ continuity của tờ giấy |
| 60–66s | CapCut timeline | Tóm khâu hoàn thiện |
| 66–84s | Tờ quiz toàn khung, vòng đếm số giảm, tay bút đánh dấu từng đáp án | Timer dành thời gian cho hành động đọc/trả lời |
| 84–88s | Trang prompt rồi CTA “QUIZ” | CTA bám nội dung |
| 88–91.833s | Profile | End card |

Kỹ thuật riêng: countdown và nét viết. Không dùng timer cho nội dung không cần người xem chờ; phải kiểm tra độ đúng của chữ/đáp án khi tạo ảnh bằng AI.

## 23 — Bản sao của 22

Đã probe và băm toàn bộ file. SHA-256 cùng `c4ffe2bc1e2462bbcd82cf9045d84701df75a8016ed0103606346d0b8b556153`; độ dài, resolution và fps giống nhau. Vì mọi byte trùng, dùng nguyên phân tích timeline 22 cho 23. Không tăng trọng số motif của clip này khi tổng hợp quy tắc.

## 24 — AI edit video

| Khoảng | Quan sát | Bài học |
|---|---|---|
| 0–2s | Người dẫn thật, điện thoại trước ngực, chữ cam/trắng | Hook gắn vật thể và lời hứa |
| 2–6s | Preview dọc bo góc trên nền trắng, caption/khung nhấn trong preview | Cho thấy mẫu hiệu ứng trong context |
| 6–10s | Avatar cùng heading “Cách thiết lập…” | Reset thành mục hướng dẫn |
| 10–20s | Chat/UI → Codex → plugins → tìm và cài; crop vùng trên | Cho thấy thao tác thực tế |
| 11–13s chi tiết | Con trỏ mở menu trái, chuyển mục Codex; click ring rõ; crop thay đổi để giữ menu trong khung | Chọn target rồi giữ phản hồi, không zoom trôi liên tục |
| 20–32s | Upload clip và prompt, một số khung không có caption dưới | Không bắt buộc chữ luôn có mặt |
| 32–38s | Chat trả kết quả, video đính kèm | Cần phân biệt output thực với màn hình đang chờ |
| 38–46s | Hai card video gốc/ChatGPT edit; overlay giải thích tính năng | Đặt bản gốc và kết quả ngang hàng |
| 46–52s | Card logo công cụ trên grid, B-roll gõ bàn phím | Nối ý tổng hợp với hành động con người |
| 52–56s | CTA/avatar trên nền tối | Chốt rõ một hành động |
| 56–64.273s | Profile và outro TikTok Lite | Phần bao bì nền tảng |

## Quy tắc lặp và kỹ thuật điều kiện

Lặp ở nhiều reference độc lập: proof-first hook; nền sáng xám nhẹ; sans đậm/nghiêng; cam cho key phrase; card bo góc; screen capture lớn; crop/zoom mục tiêu; tutorial nền tối với keyword vàng; đưa thành phẩm sau quy trình. 21 là ngoại lệ quan trọng: nền sáng có thể giữ xuyên bài.

Chỉ dùng khi ý nghĩa yêu cầu: infographic hàng trạng thái (19), map leader line (17), anatomy highlight (18), countdown/handwriting (22), collage meme (18/19), before/after (17/22/24). Avatar đỏ, watermark HUANVN, profile và mã CTA là nhận diện riêng; học vai trò bố cục, không sao chép asset.

Nhịp quan sát từ ảnh: hook thay trạng thái nhanh hơn; hướng dẫn giữ UI lâu hơn, có những cụm 4–10s cùng một ứng dụng nhưng đổi crop/response. Không áp luật cut mỗi N giây. Chưa có căn cứ kết luận VO nhấn từ nào đúng frame nào; phải align lại theo source mới.
