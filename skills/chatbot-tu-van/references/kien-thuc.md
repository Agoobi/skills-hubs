# Soạn kiến thức cho chatbot

Bot chỉ trả lời từ `knowledge/*.md`, và guard coi mọi con số trong đó là đúng. Vì vậy file kiến thức phải chép đúng từ file gốc của user; `kb.py verify` kiểm tra lại các con số bằng code.

## Từ file gốc đến kiến thức

```
file user gửi ──ingest──► nguon/<ten>.md ──agent soạn──► knowledge/<chu-de>.md ──user duyệt──► verify ──► bot dùng
```

- `nguon/` là bản gốc chuyển sang Markdown, không sửa tay. Muốn đổi thì user gửi file mới rồi `ingest` lại.
- Excel: ô %, ô ngày được đọc như Excel hiển thị (`10%`, `31/12/2026`); dòng tiêu đề phía trên bảng giữ thành dòng chữ, dòng đầy đủ đầu tiên là tên cột. Giá lưu dạng số trong Excel ra số trần (`1500000`), soạn thành `1.500.000đ` hay `1,5 triệu` đều qua `verify`. Vẫn đọc lại `nguon/` sau khi ingest: ô gộp, bảng nhiều tầng tiêu đề có thể lệch cột.
- Một file kiến thức có thể lấy từ nhiều nguồn; một nguồn có thể chia ra nhiều file kiến thức.

## Cách soạn một file kiến thức

```
# Bảng giá dịch vụ

<!-- nguon: bang-gia-2026.md, chinh-sach.md -->

## Gói A
- Giá: 1.500.000đ / tháng
- Đóng 12 tháng: giảm 10%
```

- Dòng 2 bắt buộc: liệt kê **đúng** các file trong `nguon/` đã dùng.
- Mỗi file một chủ đề khách hay hỏi; tên file không dấu, gạch ngang (`chinh-sach-doi-tra.md`).
- Viết lại cho dễ tìm: tiêu đề `##` theo từng sản phẩm / câu hỏi, gạch đầu dòng ngắn, ghi cả tên gọi khác khách hay dùng.
- Con số, giá, %, thời hạn, điều kiện: **chép nguyên văn** (đổi `1.500.000đ` thành `1,5 triệu` vẫn được, verify quy đổi).
- Không thêm thông tin ngoài nguồn, không suy ra giá, không làm tròn, không "thường thì".
- Nguồn mâu thuẫn (hai bảng giá khác nhau, bản cũ / bản mới) hoặc thiếu (có sản phẩm mà không có giá): **dừng và hỏi user**, ghi rõ chỗ nào.
- Bảng lớn (Excel nhiều dòng): giữ dạng từng dòng `Cột: giá trị` hoặc chia file theo nhóm, không tóm tắt mất dòng.

## Kiểm tra

- `verify` báo `so_lieu_khong_co_trong_nguon`: sửa theo nguồn (hoặc thêm đúng file nguồn vào dòng 2), không xóa số cho qua.
- Verify chỉ kiểm con số. Nội dung chữ (điều kiện, quy trình) thì user phải đọc và duyệt trước khi verify.
- `status` sau mỗi lần cập nhật: mọi file phải `ok`, không còn `nguon_chua_dung` trừ khi user nói bỏ qua.
