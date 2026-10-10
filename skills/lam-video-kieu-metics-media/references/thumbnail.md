# Ảnh bìa (thumbnail)

Đọc file này ở Cổng 9, sau khi video đã xuất. Ảnh bìa là **tranh minh hoạ**, không phải ảnh chụp sản phẩm: nó được model tạo ảnh vẽ ra qua OpenRouter, theo một phong cách cố định, với linh vật của kênh làm nhân vật chính.

## Phong cách

Rút ra từ ảnh mẫu chủ kênh chọn (tháng 10/2026): một khung dọc có tôm hùm đỏ gõ laptop ở nửa trên và cáo cam đeo kính chỉ vào bảng "QUY TRÌNH 2.0" ở nửa dưới.

| Thành phần | Trong ảnh mẫu | Quy tắc khi tạo |
|---|---|---|
| Nền | Giấy kẻ ô trắng, ô nhỏ màu xám nhạt, có nếp nhàu mềm khắp tờ | Luôn là tờ giấy kẻ ô nhàu nhẹ; không dùng nền màu trơn hay ảnh chụp |
| Viền | Hai dải nâu đất chạy dọc mép trái và mép phải | Giữ hai dải; đây là dấu nhận diện của loạt ảnh bìa |
| Nhân vật | Con vật hoạt hình tròn trịa, nét viền đậm, màu phẳng và tươi, bóng đổ rất nhẹ | Nhân vật chính là **linh vật của kênh** (file `logo` trong settings), vẽ lại theo nét sticker |
| Đạo cụ | Vật thật quen thuộc gắn với ý của video: bàn và laptop, bảng trắng có sơ đồ | Mỗi nhóm một đạo cụ nói lên ý chính; sơ đồ trên bảng tối đa 3–4 khối |
| Bố cục | Hai nhóm hình xếp chồng theo trục giữa, mỗi nhóm rộng khoảng nửa tờ, quanh mỗi nhóm là giấy trống | Video ngắn: hai nhóm trên và dưới. Video dài: nhóm chính bên trái hai phần ba, nhóm phụ bên phải |
| Chữ | Chỉ có một dòng trên bảng, chữ in hoa đậm, khổ hẹp | Chữ nằm **trên đạo cụ** (bảng, biển, màn hình), không nổi trên nền. Tối đa 4 từ |
| Khoảng trống | Trên và dưới còn nhiều giấy trống | Video ngắn chừa 12% trên và 22% dưới cho tên kênh và nút của nền tảng |

Thứ không lấy từ ảnh mẫu: các icon ứng dụng nhỏ cạnh laptop. Model không được vẽ logo hay icon của thương hiệu thật; cần logo thật thì ghép file thật vào sau.

## Cách làm

1. **Đề xuất ý.** Viết 2 phương án, mỗi phương án gồm: nhóm trên là gì, nhóm dưới là gì, chữ trên đạo cụ. Nhóm trên là **hiện tượng** (thứ người xem gặp), nhóm dưới là **linh vật đang chỉ ra hoặc phản ứng**. Chữ lấy từ `thumbnail_text` hoặc từ hook, tối đa 4 từ. Người dùng chọn một phương án.
2. **Tạo ảnh.**
   ```
   python -I scripts/video.py thumbnail --project <dự án> --variants 2 \
     --title "CỘNG TIỀN 2 LẦN?" \
     --scene "Upper group: ... Lower group: the panda mascot ..."
   ```
   `--scene` viết bằng tiếng Anh, tả vật và tư thế, không tả phong cách (phong cách đã có sẵn trong lệnh). `--title` giữ nguyên tiếng Việt có dấu. Linh vật lấy từ `channels.<alias>.logo`; kênh chưa có `logo` thì truyền `--ref <file>` hoặc hỏi người dùng xin ảnh linh vật.
3. **Tự xem từng ảnh** (đọc file ảnh) trước khi gửi người dùng:
   - Chữ đúng từng dấu. Sai một dấu là tạo lại; không sửa bằng cách tả thêm vào `--scene`.
   - Linh vật đúng loài, đúng màu, đúng phụ kiện so với logo.
   - Không có logo, icon ứng dụng, tên thương hiệu, hay chữ thừa.
   - Hai dải viền và nền giấy kẻ ô còn đủ; hai nhóm không chạm mép.
4. **Người dùng chọn.** Gửi các bản đạt. Bản được chọn lưu thành `output/thumbnail.png` (chạy lại với `--variants 1`, hoặc copy bản đã chọn). `metadata.json` ghi `video.thumbnail`.

Lệnh đưa ảnh về đúng kích thước định dạng (1080×1920 hoặc 1920×1080) và ghi vào `assets/ledger.json` một dòng `thumbnail-ai` kèm model và nguyên văn prompt.

## Giới hạn

- Ảnh bìa không được trông như ảnh chụp sản phẩm, người thật, hay kết quả thật. Quy tắc "không dựng giả màn hình" vẫn giữ: muốn có màn hình thật trên bìa thì dùng khung hình của video (`cover_time`).
- Không vẽ linh vật hay nhân vật của kênh khác.
- Mỗi ảnh tốn tiền OpenRouter. Tạo 2 bản mỗi lượt; chỉ tạo thêm khi cả hai đều hỏng.
- Kênh muốn phong cách khác thì đặt `channels.<alias>.thumbnail_style` (một đoạn tả nền, nét vẽ và màu bằng tiếng Anh); phần bố cục và các điều cấm vẫn do lệnh thêm vào.
