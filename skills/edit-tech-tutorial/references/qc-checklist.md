# QC — dùng cho mỗi bản xem trước

## Nội dung và hình
- [ ] Mỗi câu có hình đúng ý; không bịa số liệu, trạng thái UI hay kết quả AI.
- [ ] Hook cho thấy mục tiêu/bằng chứng; đoạn dạy có đủ ngữ cảnh → mục tiêu → thao tác → phản hồi.
- [ ] Nhịp theo bản thu, có giữ để đọc; không lặp một khuôn cho mọi câu.
- [ ] Thành phẩm được thấy rõ; CTA chỉ khi brief yêu cầu.
- [ ] Chế độ sáng/tối và nền giúp phân đoạn, không tranh với nội dung.

## Chuyển động và chữ
- [ ] Bản sửa giữ VO, nội dung, bảng màu, typography đã duyệt; đã so thời lượng/thứ tự VO với bản trước.
- [ ] Từng beat có IN/HOLD/OUT; OUT thật sự có trong render.
- [ ] Bảng chế độ/cơ chế đã rà toàn bài: icon, thẻ, đoạn nguồn không lặp để lấp chỗ.
- [ ] Intake xác định thiếu hình → đã bổ sung đúng chỗ, có manifest, xuất hiện trong render.
- [ ] Phần mềm được nhắc tới dùng screen thật, hoặc mô phỏng có ghi rõ; không chỉ là logo.
- [ ] Camera zoom không lộ mép video (đã kẹp), không giật/chóng mặt.
- [ ] Đầu/giữa/cuối chuyển cảnh: không lộ mép mask, crop hụt, chữ nhoè khi giữ.
- [ ] Chữ Việt đúng dấu/chính tả, font không thiếu glyph; phụ đề nguyên văn khớp VO.
- [ ] Đọc ở cỡ điện thoại; chữ không che mục tiêu, mặt, nút, phản hồi; trong safe zone.
- [ ] Không phải chữ nào cũng cùng một animation; thứ bậc và màu nhấn nhất quán.

## Âm thanh
- [ ] Mỗi ranh giới scene đã xét; mỗi cue có hành động và mốc landing cụ thể.
- [ ] Mỗi take giữ đủ onset/thân/decay; đuôi không bị cắt hoặc đè.
- [ ] Mật độ âm đúng brief; yêu cầu không lặp/mức gốc được tuân thủ (kiểm hash, gain).
- [ ] Click khớp click (cùng khung vòng sáng), whoosh khớp chuyển động; bỏ cue không lý do.
- [ ] VO rõ; không click/pop ở mép audio; đo loudness/true peak, không clipping.

## Kỹ thuật
- [ ] `npx hyperframes check .` → "Check passed" (cảnh báo còn lại có lý do ghi rõ).
- [ ] Nền đúng file video gốc (không phải WEBP preview); vòng lặp nền không chớp; alpha đã thử ghép thật.
- [ ] Không khung đen/thiếu media ngoài ý đồ.
- [ ] Probe file xuất: thời lượng, kích thước, fps, codec, audio stream đúng brief.
- [ ] Thư mục nguồn dựng lại được (composition, assets, lockfile), manifest có nguồn/quyền/in-out.
- [ ] Bàn giao ghi rõ đã kiểm gì và chưa kiểm gì.

## Chấm điểm bản thử (1–5)
(1) ngôn ngữ hình ảnh, (2) typography, (3) motion, (4) hình đúng nội dung, (5) SFX, (6) nhịp, (7) đa dạng có chủ đích, (8) dễ sửa lại. Mục chưa xem/nghe ghi NOT TESTED, không cho điểm giả. Ngưỡng ≥ 4 mỗi mục; lỗi sai nội dung, mất media, chữ không đọc được, VO không rõ thì phải sửa dù điểm tổng cao.
