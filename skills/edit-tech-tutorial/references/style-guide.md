# Hệ hình ảnh và chuyển động

## Hai chế độ (chọn theo nội dung từng đoạn, không ép cả video một chế độ)

**Sáng — giới thiệu/giải thích (`hook-light`):** nền trắng hơi ấm hoặc xám nhạt, lưới nhỏ/đồ hoạ góc rất mờ; nội dung ở trung tâm; một ý chính và tối đa vài vật thể phụ. Thẻ/khung video bo góc, bóng nhẹ tách khỏi nền. Hình trên, nhãn giải thích dưới. Dùng cho hook, khái niệm, so sánh, sơ đồ. Chữ nhấn: đậm, **nghiêng**, màu cam.

**Tối — hướng dẫn (`step-dark`):** màn hình (screen recording) chiếm vùng trên/giữa; nền đen/charcoal có chấm hoặc hạt rất nhẹ; phụ đề tóm ý 1–2 dòng trắng, từ khoá vàng. Chừa khoảng trống có chủ đích cho chữ; không thu nhỏ screenshot chỉ để nhét nhiều thứ. Nền phải kém nổi hơn UI. Tutorial vẫn có thể dùng nền sáng khi đủ tương phản.

### Màu khởi điểm (cảm giác, không phải mã đo từ video mẫu)
| Vai trò | Sáng | Tối |
|---|---|---|
| Nền | #F7F7F4 | #111214 |
| Chữ | #202020 | #FAFAFA |
| Nhấn | cam #CF5F38 (đủ tương phản 3:1 trên nền sáng; #E7774F chỉ dùng cho mảng lớn/nút) | vàng #F4F34C |

Mỗi đoạn một màu nhấn chính. Video cho AI Agent VN có thể thay bằng preset `aiagentvn` (nền #091833→#060E22, nhấn #3FD6A6) khi người dùng muốn đồng bộ kênh; giữ cấu trúc hai chế độ.

## Typography
- Be Vietnam Pro (đã đóng gói trong starter, đủ dấu). Inter/Manrope chỉ khi có file font cục bộ và kiểm dấu.
- Cỡ trên 1080×1920 theo `safe-zone-chu-9x16`: hook/khung thumbnail được lớn (keyword 120–150 px, tối đa 3 dòng ngắn); phụ đề tóm ý 54–60 px; chữ trong thẻ 30–40 px; nhãn 28–34 px.
- Một cụm keyword lớn/đậm/nghiêng đi với phần dẫn nhỏ hơn. Tối đa 1–2 dòng ngắn, không đoạn văn. Chữ tóm ý được rút gọn; phụ đề nguyên văn phải đúng bản thu. Không tô vàng mọi từ. Chữ không đè lên nút đang hướng dẫn.
- Vùng an toàn: theo `safe-zone-chu-9x16` (x 60–960, y 220–1500).

## Primitive chuyển động (khởi điểm, chỉnh theo bản thu)
| Primitive | Khởi điểm | Dùng khi |
|---|---|---|
| Đổi vị trí mượt | 0,25–0,45 s, ease out, đi 24–60 px | Thẻ/chữ đổi trạng thái |
| Scale vào/ra | 0,20–0,35 s, 94→100% | Nhấn một kết quả/keyword |
| Overshoot | 0,30–0,50 s, 96→103→100% (`back.out`) | Một từ quan trọng; không dùng cho mọi chữ |
| Slide reveal | 0,25–0,40 s, lệch 30–70 px | Hàng task, thẻ mới |
| Mask wipe | 0,25–0,50 s | Highlight/gạch chân, mở vùng thông tin |
| Mở panel UI | 0,3–0,6 s, neo tại control | Giải thích panel; UI dựng lại phải ghi "mô phỏng" |
| Camera push-in | 0,6–1,2 s, ~100→110% | Tăng tập trung không đổi shot |
| Pan/zoom tới target | 0,3–0,7 s rồi giữ | Mở menu, chọn option, đọc output |
| Parallax | 1–3 s, lệch 5–15 px | Collage/b-roll có chiều sâu |
| Match movement | Nối cùng hướng/neo | Đổi trạng thái mà mắt không phải tìm lại |
| Vòng sáng click | Vòng ngắn tại điểm bấm, đúng khung click | Click có ý nghĩa; không có halo bám theo mọi chuyển động |
| Motion blur | Chỉ khi vận tốc lớn | Chuyển thẻ/zoom nhanh; chữ dừng phải sắc |

Kinetic type không có nghĩa phụ đề nhảy từng từ liên tục: chọn reveal từng từ cho danh sách/nhấn cụm; giữ yên cho hướng dẫn; đổi màu cho keyword; mask cho quan hệ. Không chuyển động tuyến tính máy móc.

## Nối shot và nền
- Cắt theo ý/click/phản hồi. Chuyển cảnh lớn chỉ khi đổi chương hoặc nối hình tương ứng. Giữ hướng chuyển động/neo khi đổi panel. Không dùng whoosh để hợp thức hoá cú cắt không liên quan.
- Không lấy avatar, profile, watermark, logo cá nhân từ video tham chiếu.
- Nền: chọn theo đoạn, không đổi mỗi câu. Nền sáng có lưới cho infographic/intro; nền tối ít chi tiết cho UI. Footage đã full khung không cần nền trang trí. Video ngang giữ tỉ lệ, đặt trong khung trên nền tối.
