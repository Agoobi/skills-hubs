# plan.json: bản dựng

`plan.json` là nguồn duy nhất của video. `cut` và `build.mjs` đọc từ đây. Mọi vùng `rect` là `[x, y, rộng, cao]` tính bằng **phần trăm** khung video thô. Mọi `at`, `hold` là giây tính từ đầu nhịp trong video thành phẩm.

```json
{
  "captions": true,
  "music": { "file": "assets/nhac.mp3", "volume": 0.08 },
  "blur": [{ "rect": [1, 14, 16, 60], "from": 0, "to": 30 }],
  "labels": { "pause": "Tạm dừng", "fast": "Tua nhanh", "sample": "Dữ liệu ví dụ" },
  "beats": []
}
```

- `blur`: làm mờ trực tiếp vào hình. `from`, `to` là giây trong video thô; bỏ cả hai thì mờ suốt video.
- `music`: không bắt buộc. Tự lặp cho đủ độ dài.
- `labels.sample`: nhãn cố định ở góc video. Dùng khi hình là dữ liệu mẫu, không phải khách thật.
- `beats`: chạy lần lượt từ đầu tới cuối. `id` viết thường, không dấu.

## Bốn loại nhịp

### `play`: chạy một đoạn video thô

```json
{ "id": "mo-man", "src": [3, 12], "vo": "Lời đọc đè lên đoạn này.", "fx": [] }
```

- Có `vo`: tốc độ tự khớp với lời, từ x0.8 đến x6. Lời dài hơn hình thì giữ khung cuối. Đặt `speed` để ép tốc độ.
- Không `vo`: giữ tiếng gốc.
- `keepAudio: true` kèm `vo`: tiếng gốc nhỏ lại dưới giọng đọc.
- Giữ tiếng gốc mà muốn phụ đề: ghi nguyên văn vào `say`.
- `presenter: { "mode": "corner", "side": "right" }`: nhân vật tròn ở góc, miệng nói theo giọng.

### `pause`: dừng hình để nhân vật giải thích

```json
{
  "id": "dung-1", "type": "pause", "at": 12,
  "vo": "Khoan đã, chỗ này là danh sách việc agent đang làm.",
  "presenter": { "side": "right" },
  "fx": [{ "kind": "highlight", "rect": [22, 52, 52, 16], "label": "Danh sách việc", "on": "danh sách việc", "point": true }]
}
```

Video đứng ở giây `at`, thu nhỏ sang một bên, nhân vật đi vào nói, xong rút ra và video chạy tiếp. Đặt `at` đúng bằng điểm cuối của nhịp `play` trước để không bị giật hình. Nhân vật không bao giờ che video. Thời lượng tự tính theo lời.

### `cutaway`: cảnh riêng không có video

```json
{ "id": "tom-tat", "type": "cutaway", "title": "Ba việc cần nhớ", "points": ["Quay quy trình thật", "Đánh dấu chỗ lặp lại"], "image": "assets/overlays/so-do.png", "vo": "..." }
```

Dùng cho hook, tóm tắt, so sánh trước/sau, kêu gọi cuối video. `points` hiện dần theo lời; thêm `{ "text": "...", "on": "cụm từ" }` để khớp đúng chữ. `presenter: false` để bỏ nhân vật. `note`: dòng phụ, ví dụ ghi rõ số giả định.

Ba khối đồ hoạ dùng được trong cảnh riêng:

| Trường | Dạng | Dùng cho |
|---|---|---|
| `flow` | `["Đọc tin", "Mở bảng giá"]` | Sơ đồ quy trình, các ô hiện dần theo lời. Thêm `focus: { "nodes": [1], "on": "một khâu" }` để hiện cả sơ đồ rồi làm nổi các ô chọn. |
| `big` | `[{ "text": "4 phút", "on": "bốn phút" }]` | Phép tính chữ lớn, phần tử cuối là kết quả. |
| `compare` | `{ "before": { "title", "items", "on" }, "after": { ... } }` | Hai thẻ trước/sau. |

### `chapter`: thẻ chương

```json
{ "id": "phan-1", "type": "chapter", "kicker": "PHẦN 1", "title": "Xem agent làm việc", "hold": 1.6 }
```

## Hiệu ứng trong `fx`

Dùng ở `play` và `pause`. Thời điểm bắt đầu theo `at` (giây) hoặc `on` (một cụm từ có trong lời đọc). `on` ước lượng theo vị trí chữ trong câu, nên lệch khoảng nửa giây; cần chính xác thì dùng `at`.

| `kind` | Trường | Ghi chú |
|---|---|---|
| `zoom` | `rect`, `hold` | Máy quay tiến vào vùng, tự lùi sau `hold` giây. Tối đa x2.6. Hai zoom liên tiếp phải có `hold` để không chồng nhau. |
| `highlight` | `rect`, `label`, `hold`, `point` | Khung màu, tối phần còn lại. `label` tối đa 4 chữ. `point: true` vẽ đường từ tay nhân vật tới khung, chỉ ở nhịp dừng và không dùng cùng `zoom`. |
| `image` | `file`, `w`, `pos`, `caption`, `hold` | Ảnh minh hoạ. `w` là % chiều rộng khung hình. `pos`: `center`, `left`, `right`, `top`, `bottom`, `top-left`, `top-right`, `bottom-left`, `bottom-right`. Ở nhịp dừng, vị trí tính trong khung video đã thu nhỏ. |

## Khi nào dùng cái gì

- **Cắt thẳng**: khoảng chờ tải, gõ nhầm, rê chuột vô nghĩa, đoạn đứng yên trong `still_spans`. Mặc định là cắt.
- **Tua nhanh**: khi quá trình chờ cũng là một phần câu chuyện, ví dụ agent đang chạy. Giữ đoạn dưới 8 giây sau khi tua.
- **Dừng hình**: khi người xem cần hiểu một khái niệm mà màn hình không tự nói lên, trước một bước dễ sai, hoặc ngay sau một kết quả đáng chú ý. Mỗi lần dừng dưới 15 giây, cách nhau ít nhất 30 giây. Nhiều hơn là video bị đứt nhịp.
- **Zoom**: mỗi khi người xem cần đọc chữ, nhìn thấy nút được bấm, hoặc video dọc. Giữ ít nhất 1,5 giây để kịp đọc.
- **Khung chỉ**: khi màn hình có nhiều thứ và lời nói đến một chỗ. Dùng trước khi nghĩ tới mũi tên hay chữ.
- **Ảnh minh hoạ**: khi lời nhắc tới thứ không có trên màn hình, như sơ đồ, biểu đồ, kết quả, ảnh chụp bằng chứng. Mỗi ảnh chỉ nói một ý.
- **Cảnh riêng**: mở đầu, tóm tắt, kêu gọi. Không dùng giữa một thao tác đang diễn ra.

## Viết lời

- Câu ngắn, xưng hô theo kênh. Người xem không rành kỹ thuật thì đổi thuật ngữ thành lời thường.
- Nói điều hình không tự nói lên, không đọc lại chữ trên màn hình.
- Số viết bằng chữ khi giọng AI đọc sai, ví dụ "hai mươi phần trăm".
- Nhịp đầu nói ngay kết quả hoặc vấn đề của người xem. Giới thiệu bản thân để sau.
- Lời ước lượng khoảng 4 âm tiết mỗi giây.
