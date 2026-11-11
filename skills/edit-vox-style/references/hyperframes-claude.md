# HyperFrames trên Claude — đã kiểm với CLI 0.8.201 (10/11/2026)

Tên sản phẩm là HyperFrames; "Hyperframe" trong yêu cầu là framework HTML-to-video này. Starter `assets/hyperframes-starter/` đã render thử thành công trên Claude (check passed, MP4 1280×720, 10 s).

## Hợp đồng runtime
- `index.html` có root composition ID, width, height, duration (giây), fps. Starter là 1280×720/30 để thử nhanh. Phim mới: 1920×1080/30 (ngang, YouTube) hoặc **1080×1920/30 (dọc, Reels/TikTok)** theo brief. Khung dọc phải áp `safe-zone-chu-9x16`.
- Root chứa scene host có class `clip`, `data-composition-src`, `data-start`, `data-duration`, track index. Thứ tự hiển thị dùng z-index.
- Mỗi scene bọc style/markup/script trong template; root id là `root`, composition ID trùng host.
- Mỗi composition đăng ký timeline paused vào `window.__timelines[ID]`, kể cả root. Timeline con dùng giờ local (cảnh bắt đầu ở 6 s trên phim thì tween đầu cảnh là 0 s). Không tự add timeline con vào cha.
- Animate trên con/wrapper; tránh tween display/visibility/autoAlpha của clip. Không đặt transform CSS và GSAP cùng một node.
- Asset dùng đường dẫn `assets/...` tính từ project root, cả trong sub-composition.
- Video/audio khai báo timing bằng data attributes; audio có id riêng. Không gọi play/currentTime trong GSAP. Animate video thì animate wrapper.
- SVG path: lấy `getTotalLength` khi DOM sẵn, đặt cả dasharray và dashoffset. Motion dùng `fromTo` với vị trí thời gian tường minh.
- Texture procedural: seed cố định rồi bake thành ảnh. Không dùng CSS filter trên video để giả grain.
- Font: **file cục bộ trong `assets/fonts/`** khai báo @font-face, đủ dấu tiếng Việt (Be Vietnam Pro, Inter, Noto Serif cho trích dẫn). Starter dùng Arial/hệ thống — thay bằng font cục bộ trước khi dựng thật. Chờ font tải trước khi đo chữ.

## Lệnh (chạy trong thư mục dự án)
```sh
cp -r <skill>/assets/hyperframes-starter ./film && cd film
npm install --save-exact hyperframes@0.8.201 gsap@3.15.0
export HYPERFRAMES_BROWSER_PATH=/usr/bin/google-chrome     # Chrome có sẵn; PHẢI đặt trong cùng lệnh với render (mỗi lệnh shell mới không giữ export), thiếu thì render lỗi và không ghi file mới
npx hyperframes lint .
npx hyperframes check .                                    # phải "Check passed"
npx hyperframes snapshot . --at 0,0.35,1.5,3.3,4.8,6.5,8,9.9
npx hyperframes render . -o renders/film.mp4 --fps 30 --workers 1
```
- Dùng đường dẫn tuyệt đối (thư mục làm việc của shell có thể bị đặt lại giữa các lệnh). Render dài chạy bằng tác vụ nền.
- Log báo "BeginFrame did not run … software gpu" là bình thường trên Claude: renderer chuyển sang screenshot capture, chậm hơn nhưng đúng. Cảnh nặng (nhiều blur/ảnh lớn) có thể chậm: giảm kích thước ảnh, bake texture.
- Xem `--help` của phiên bản đang cài trước khi dùng flag. Không nâng phiên bản giữa chừng.
- Exit code của wrapper chưa chứng minh render xong: đọc log, probe file, trích khung từ MP4 để xem.

## QA
Lint/check; font; asset; khung sát cut; khung cuối; cùng timestamp sau seek tiến/lùi phải giống nhau; render MP4 rồi xem ảnh trích từ MP4. Giữ cảnh cuối đủ thời gian đọc. Nhãn nguồn phải đọc được; không dùng `data-layout-ignore` để giấu chữ quá nhỏ.

## Mapping tái sử dụng
| Thành phần tham chiếu | Triển khai |
|---|---|
| Giấy xoay vào | PNG/SVG mask alpha + wrapper rotation/xy, bóng ở wrapper |
| Vật liệu giấy | texture raster cục bộ, opacity thấp; không phủ mạnh lên chữ |
| Cutout lịch sử | WebP/PNG alpha, bake grayscale nếu cần; halo giấy ở layer riêng |
| Highlight tài liệu | rect/span trên từng dòng, clip hoặc scaleX; giữ nội dung gốc |
| Bản đồ có camera | raster/SVG địa lý + world transform cha; nhãn cùng hệ toạ độ |
| Leader/ring/route | SVG stroke/mask, dashoffset theo timeline |
| Camera 2.5D | nhiều wrapper cùng thời gian, biên độ pan khác nhau |
| Sound cue | audio id riêng, `data-start` theo beat; runtime tự mix |

Nguồn: [GSAP contract](https://hyperframes.heygen.com/guides/gsap-animation) · [HyperFrames repo](https://github.com/heygen-com/hyperframes) · [Quickstart](https://hyperframes.heygen.com/quickstart)
