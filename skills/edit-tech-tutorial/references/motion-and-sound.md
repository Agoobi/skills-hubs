# Hợp đồng từng beat, đa dạng hình ảnh và âm thanh

## Giữ phần đã duyệt
Người dùng đã duyệt voice, nội dung, bảng màu, typography rồi yêu cầu nâng edit: giữ nguyên các phần đó, lưu phiên bản mới riêng. So thời lượng, thứ tự VO, nội dung phụ đề với bản trước; không viết lại lời hay đổi style vì đang thêm motion.

## Hợp đồng cho từng beat (`beats.json` hoặc bảng)
`VO in/out | ý nghĩa | chế độ (sáng/tối/talking head/kết quả) | nguồn thật hay mô phỏng | file + in/out | mới/tái dùng + lý do | chữ | IN: thuộc tính, thời lượng, easing | HOLD: hành động, thời gian đọc | OUT: thuộc tính, thời lượng, easing | bóng | SFX: file, mốc transient, gain, lý do — hoặc none | QC`

- **IN** 0,25–0,45 s, lệch 24–65 px, scale 94–100%, opacity 0→100%, ease out. Từ khoá chương có thể 88→103→100% trong ~0,4 s, dùng thưa.
- **HOLD** là lựa chọn cụ thể: đọc ổn định; pan đến đúng control; b-roll push/pull 2–5%; reveal từng mục theo lời; progress thể hiện thao tác. Khoảng nghỉ là cần thiết. Không rung chữ để né cảnh tĩnh. HyperFrames `check` cảnh báo `line_unread` khi chữ ở trên màn hình ít hơn ~0,5 s + 0,3 s/từ — sửa bằng cách giữ lâu hơn hoặc rút gọn chữ.
- **OUT** 0,18–0,30 s, lệch 24–45 px, opacity hoặc scale nhẹ, ease in/in-out. Cắt thẳng có chủ đích là hợp lệ khi nối hành động, nhưng ghi rõ. Thiếu OUT là beat chưa xong.
- Chữ, icon, thẻ, screenshot, b-roll đều có IN/HOLD/OUT. Kế hoạch ghi "ease" chưa chứng minh bản render có easing — xem khung thật.
- Canh điểm nhấn theo bản thu; reveal xong trước lúc cần đọc.

## Bóng và khả năng đọc
Chữ trên footage: bóng đen 20–35%, lệch 2–4 px, blur 5–9 px ở 1080×1920. Trên nền sáng giảm ~10–18%. Thẻ/màn hình dùng bóng mềm hơn chữ. Xem ở cỡ điện thoại; tránh viền/bóng dày làm mất nét tối giản.

## Đa dạng theo ý nghĩa
- Lập bảng chế độ/cơ chế chuyển động cho cả timeline trước khi polish. Xen footage thật, screen thật, typography và motion giải thích.
- Không dùng lại cùng asset hoặc cùng đoạn nguồn để lấp câu mới. Đếm theo **file nguồn**: đổi in-point của cùng clip stock vẫn là lặp. Cần lặp để đối chiếu/tiếp tục thao tác thì ghi lý do và đổi điểm nhìn.
- Tránh ba beat liên tiếp cùng bố cục/cơ chế nhấn. Logo/nhãn chương lặp để định hướng thì được.

## Nguồn bổ sung và phần mềm thật
- Intake luôn có một lượt xác định hình còn thiếu. Thiếu b-roll (người làm việc, review…): tìm Pexels/Pixabay bằng tìm kiếm web, xem clip, ghi trang asset, tác giả, license, file, in/out. Mạng của phiên Claude có thể chặn tải trực tiếp từ các trang này: khi đó đưa danh sách link cụ thể cho người dùng tải về và gửi lại, không dừng ở việc "đề xuất".
- Lời nhắc tới ChatGPT, Claude, Codex, phần mềm nào: ưu tiên **screen recording thật** của người dùng, đủ lớn để nhận ra giao diện. Trang web công khai: có thể tự quay bằng Playwright (Chromium có sẵn) — `page.video` hoặc chụp chuỗi ảnh — rồi dùng như screen recording. Ảnh sản phẩm chính thức ghi là minh hoạ. Chưa có screen phù hợp thì dựng UI bằng HTML trong composition và ghi rõ "giao diện mô phỏng". Không giả kết quả AI; không dùng một logo cho cả bước hướng dẫn.

## Âm thanh
- Thư viện SFX/nền của người dùng nằm trên máy họ (`E:/TaiNguyen/...`, xem `library/SFX_INDEX.csv`, `library/BG_INDEX.csv`). Lấy bằng công cụ liên kết máy tính: xin quyền đúng thư mục → `device_list_dir` → `device_stage_files` **chỉ các file sẽ dùng**. Chưa liên kết máy thì nói rõ và xin người dùng gửi file; không tự thay bằng âm khác mà không báo.
- Lập bảng ranh giới scene trước; mỗi điểm nối một âm chính với mốc landing rõ. Âm bên trong scene chỉ cho hành động/keyword có lý do. Click đặt đúng khung click (cùng mốc vòng sáng), whoosh vào chuyển động, âm xác nhận vào trạng thái hoàn thành. Giữ yên khi người xem cần đọc UI.
- File SFX của thư viện Boom là container nhiều take (5–144 s): tách một take trọn từ trước onset đến hết decay tự nhiên (tìm khoảng gần im lặng bằng `silencedetect`/numpy), không chặt cụt theo độ dài cố định, không fade gấp để che điểm cắt. Đuôi được chạy qua cut.
- Yêu cầu **không lặp SFX**: mỗi file nguồn (và mỗi take) chỉ dùng một lần; đổi pitch/tempo/tên file không tính là nguồn mới. Kiểm bằng hash.
- Yêu cầu **mức gốc / để nguyên**: giữ gain nguồn, không normalize hàng loạt, không duck tự động; chỉ chặn đỉnh gây vỡ ở bus trộn và ghi rõ.
- Trộn: âm trong HyperFrames dùng `<audio id=… data-start data-volume>`; hoặc trộn bằng ffmpeg (`adelay` + `amix=normalize=0` + `alimiter`) rồi ghép vào MP4. VO là mốc chính, nhạc/SFX không che phụ âm. Loudness tham khảo −16 đến −14 LUFS, true peak ≤ −1 dBTP (`ebur128=peak=true`). Chỉ ghi "đã nghe duyệt" khi thật sự nghe được; đo đạc thì ghi là đo đạc.
- Quyền dùng: thư viện Boom có EULA kèm theo nhưng chưa xác minh quyền của người dùng — nhắc khi bàn giao sản phẩm thương mại. Không coi myinstants là nguồn có quyền.

## Tỉ lệ hình
Probe kích thước encoded, cờ xoay, SAR/DAR. Clip dọc có thể encoded ngang kèm rotation 90°. Chuẩn hoá rotation và pixel vuông **trước** khi scale/crop. So cùng một khung nguồn → composition → MP4 để chắc người/vật không méo.

## Cổng trước bàn giao
Đối chiếu render với beat sheet: có OUT thật; không có cảnh đứng im ngoài kế hoạch; đủ thời gian đọc; có nhịp nghỉ; asset mới thật sự xuất hiện; screen đúng nguồn; không lặp bố cục liên tục. Xem đầu/giữa/cuối các chuyển cảnh và toàn bài.
