# Design token

Màu đo trực tiếp từ khung hình video (lấy trung bình vùng 7×7 điểm ảnh, nên có sai số nén vài đơn vị). Bản máy đọc được: `assets/tokens.json`. CSS dùng ngay: `assets/tokens.css`.

## Nguyên tắc: một hệ thống, màu nhấn đổi theo chủ đề

Metics Media không có một bảng màu cố định. Họ có **một bộ khung** và thay **màu nhấn** bằng màu thật của sản phẩm đang hướng dẫn:

| Video | Sản phẩm | Màu nhấn | Nền đồ hoạ | Thẻ chương |
|---|---|---|---|---|
| A | Claude | cam san hô `#E77B58` | kem `#FAF9F5` + quầng hồng cam | nâu đen `#1A110C` + quầng cam cháy |
| B | Hermes Agent | xanh dương đậm (khoảng `#1A1AE0`, ước lượng bằng mắt) | trắng + quầng tím nhạt | xanh navy + hình tượng chấm bi + chữ đơn cách |

Vì vậy **không chép cứng bảng màu cam**. Lấy màu nhấn từ thương hiệu thật của chủ đề (logo hoặc trang chủ của sản phẩm), rồi sinh phần còn lại:

```
python -I scripts/video.py theme --accent "#E77B58" --out <dự án>/assets/theme.css
```

Nếu kênh muốn nhận diện riêng không đổi theo chủ đề, đặt `channels.<alias>.accent` trong settings và dùng màu đó.

## Màu (giá trị gốc của video A, màu nhấn cam san hô)

| Token | Giá trị | Dùng cho |
|---|---|---|
| `--canvas` | `#FAF9F5` | Nền đồ hoạ giải thích |
| `--canvas-glow` | `#F4D2C6` | Quầng màu ở mép phải/dưới, loang bằng radial-gradient |
| `--card` | `#FDFCF8` | Thẻ nổi |
| `--card-tile` | `#EFE8E0` | Ô giữ chỗ bên trong thẻ (thay cho ảnh/chữ) |
| `--ink` | `#1C1917` | Chữ chính trên nền sáng |
| `--ink-soft` | `#6A6360` | Chữ phụ, icon nét |
| `--accent` | `#E77B58` | Viên thuốc số liệu, thanh tiến độ, nút |
| `--accent-soft` | `#E69F87` | Viền mềm quanh phần tử màu nhấn |
| `--chapter-bg` | `#1A110C` | Nền thẻ chương |
| `--chapter-glow` | `#A5553A` | Quầng sáng ở giữa đáy thẻ chương |
| `--chapter-numeral` | `#2A1A13` | Số chương khổng lồ, chỉ sáng hơn nền một chút |
| `--chapter-label` | `#B28C7F` | Dòng "Chapter 1 of 10" |
| `--chapter-title` | `#FEFCFB` | Tiêu đề chương |
| `--chapter-title-dim` | `#705042` | Từ cuối của tiêu đề khi đang hiện dần |
| `--screen-bg` | `#141414` | Nền quay màn hình ở chế độ tối |

Chữ trên `--accent` luôn là trắng. Không đặt chữ `--ink-soft` lên `--card-tile` (tương phản thấp).

## Chữ

Kiểu chữ của họ là sans hình học đậm, khoảng cách chữ khít. Dùng **Inter Tight** (giấy phép OFL, có đủ dấu tiếng Việt). HyperFrames cần file font nằm trong dự án và khai báo `@font-face`, không tải từ mạng lúc render.

| Vai trò | Cỡ ở khung 1920×1080 | Độ đậm | Khoảng cách chữ |
|---|---|---|---|
| Tiêu đề chương | 96px | 800 | -0.04em |
| Nhãn chương | 34px | 500 | -0.01em |
| Số chương khổng lồ | 900px | 800 | -0.06em |
| Tiêu đề thẻ ("Receipt") | 44px | 700 | -0.03em |
| Số liệu trong thẻ | 34px | 600 | -0.02em |
| Viên thuốc số liệu ("$10,000") | 40px | 700 | -0.02em |
| Viên thuốc tên miền | 34px | 700 | -0.02em |
| Phụ đề (video dài) | 40px | 500 | 0 |

Video ngắn 1080×1920: nhân mọi cỡ chữ với 1.25, riêng phụ đề 64px đậm 800.

## Hình khối

| Token | Giá trị |
|---|---|
| Bo góc thẻ | 24px |
| Bo góc ô bên trong thẻ | 12px |
| Viên thuốc | bo tròn hoàn toàn |
| Bo góc khung trình duyệt | 18px |
| Bóng thẻ | `0 2px 4px rgba(28,25,23,.04), 0 24px 60px -24px rgba(28,25,23,.22)` |
| Bóng khung trình duyệt | `0 40px 90px -40px rgba(28,25,23,.35)` |
| Lề an toàn (video dài) | 96px mỗi cạnh |
| Lề an toàn (video ngắn) | trên 220px, dưới 420px, hai bên 72px |

## Các khối dựng sẵn

Xem `assets/blocks.html` (mở bằng trình duyệt là thấy cả bộ). Mỗi khối là HTML + CSS thuần, đổi màu qua biến CSS:

- `canvas`: nền sáng có quầng màu.
- `chapter-card`: thẻ chương.
- `url-pill`: viên thuốc logo + tên miền ở góc dưới trái.
- `stat-pill`: viên thuốc số liệu.
- `browser-frame`: khung trình duyệt bọc ảnh/video thật.
- `receipt-card`, `compare-cards`: thẻ hoá đơn và thẻ so sánh gói.
- `logo-tile`: ô vuông trắng bo góc chứa **logo thật**.
- `lower-third`: thẻ tên kênh.

## Logo và giao diện trong đồ hoạ

- **Logo luôn là file thật** tải từ nguồn chính thức (xem `tai-san-that.md`). Không vẽ lại, không dùng icon "na ná".
- **Giao diện giản lược được phép** cho ý trừu tượng (thanh xám, ô vuông), vì chính Metics Media làm vậy. Nhưng khi lời đọc nói về một màn hình cụ thể thì phải dùng **ảnh hoặc video quay thật** đặt trong `browser-frame`.
- Icon nét (bút, mã, quả cầu, giỏ hàng) lấy từ một bộ icon mã nguồn mở có sẵn như Lucide; không tự vẽ.
