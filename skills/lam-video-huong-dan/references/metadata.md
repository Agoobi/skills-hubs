# output/metadata.json

File này đi cùng video trong `output/`. Người dùng (hoặc một công cụ đăng bài) đọc nó để điền form đăng trên từng nền tảng, nên mỗi trường phải **dán được ngay**, không cần sửa.

Tạo khung: `python -I scripts/video.py metadata init --project <dự án>`.
Kiểm tra: `python -I scripts/video.py metadata check --project <dự án>`.

`init` chỉ tạo khối cho nền tảng có trong `platforms` của kênh và hợp định dạng: video ngắn có `tiktok`, `youtube-shorts`, `reels`; video dài có `youtube`; `facebook` có ở cả hai.

## Cấu trúc

```json
{
  "video": {
    "file": "web-ai-cong-tien-hai-lan.mp4",
    "name": "Web AI cộng tiền hai lần",
    "channel": "khang-dev",
    "channel_label": "Khang Dev",
    "handle": "",
    "format": "short",
    "language": "vi",
    "created": "2026-10-10",
    "width": 1080,
    "height": 1920,
    "duration": 41.2,
    "bytes": 9123456
  },
  "platforms": {
    "tiktok": {
      "caption": "Web dựng bằng AI có thể đang cộng tiền hai lần cho một lần chuyển khoản. Cách kiểm tra trong 30 giây.",
      "hashtags": ["#vibecode", "#sepay", "#laptrinhweb"],
      "cover_time": 1.2
    },
    "youtube-shorts": {
      "title": "Web AI cộng tiền hai lần? Kiểm tra ngay chỗ này",
      "description": "Webhook thanh toán bị gọi lại mà code không kiểm tra giao dịch đã xử lý.\n\nNhắn Zalo nếu web của bạn gặp đúng lỗi này.",
      "hashtags": ["#shorts", "#vibecode"],
      "visibility": "private",
      "made_for_kids": false
    },
    "youtube": {
      "title": "",
      "description": "",
      "tags": [],
      "chapters": [{ "time": "0:00", "title": "Mở đầu" }],
      "thumbnail_text": [],
      "category": "Science & Technology",
      "language": "vi",
      "visibility": "private",
      "made_for_kids": false,
      "pinned_comment": ""
    }
  },
  "sources": [{ "file": "assets/logos/sepay-site-1.svg", "source": "https://sepay.vn/...", "kind": "logo-site" }]
}
```

`video.width`, `height`, `duration`, `bytes` do `check` tự đo từ file mp4; không điền tay.

## Cách điền

**Tiêu đề (YouTube, Shorts)**
- Nói đúng lời hứa của hook. Không hứa thứ video không làm.
- Từ khoá người ta tìm đặt ở nửa đầu. Dưới 60 ký tự thì không bị cắt trên điện thoại; giới hạn cứng 100.
- Hai mẫu của Metics Media: "Hướng dẫn [công cụ] cho người mới (năm)" và "Cách [đạt kết quả] bằng [công cụ]".
- Không viết hoa toàn bộ, không dùng từ trong `avoid` của kênh.

**Mô tả YouTube (video dài)**
1. Hai dòng đầu: video giúp làm được gì. Đây là phần hiện trước nút "xem thêm".
2. Link liên quan (trang sản phẩm, tài liệu). Link affiliate phải ghi rõ là affiliate.
3. Mốc chương: `check` yêu cầu bắt đầu ở `0:00` và có ít nhất 3 mốc. `init` lấy sẵn từ các cảnh `chapter` và thời điểm thật trong `audio/manifest.json`; kiểm lại với video đã xuất, vì dựng có thể làm lệch vài giây.
4. Câu kêu gọi của kênh.

Khi dán mô tả lên YouTube, chèn danh sách chương thành các dòng `0:00 Tiêu đề`.

**Caption TikTok / Reels**
- 1–2 câu: câu đầu lặp lại hook, câu sau nói người xem nhận được gì.
- 3–5 hashtag: 1 thẻ chủ đề rộng, 2–3 thẻ ngách, tuỳ chọn 1 thẻ của kênh. Mỗi thẻ viết liền, bắt đầu bằng `#`.
- `cover_time`: giây trong video có khung hình rõ nhất làm ảnh bìa (thường là khung kết quả ở hook).

**Tags YouTube**: 5–10 cụm người xem sẽ gõ tìm, tổng không quá 500 ký tự.

**thumbnail_text**: 2–3 phương án chữ cho ảnh bìa, mỗi phương án tối đa 4 từ. Skill không tự tạo ảnh bìa.

**visibility**: luôn để `private`. Người dùng tự chuyển sang công khai khi đăng.

## Giới hạn mà `check` kiểm

| Nền tảng | Kiểm |
|---|---|
| `youtube` | tiêu đề ≤ 100 ký tự và không trống; mô tả ≤ 5000; tags ≤ 500 ký tự; chương bắt đầu 0:00, ≥ 3 mốc, đủ tiêu đề |
| `youtube-shorts` | tiêu đề ≤ 100 và không trống; mô tả ≤ 5000 |
| `tiktok`, `reels` | caption ≤ 2200 và không trống; ≤ 5 hashtag, đúng dạng `#the` |
| mọi nền tảng | không chứa cụm trong `avoid` của kênh; file mp4 có trong `output/` và đúng kích thước định dạng |

Các con số là mức an toàn; nền tảng có thể cho phép nhiều hơn.
