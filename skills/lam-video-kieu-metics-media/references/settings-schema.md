# settings.json

Nằm cạnh `SKILL.md`, bị `.gitignore`. Copy từ `settings.example.json`.

## OpenRouter (dùng chung cho mọi kênh)

| Khóa | Ý nghĩa |
|---|---|
| `openrouter.api_key` | Key `sk-or-v1-...`. Biến môi trường `OPENROUTER_API_KEY` ưu tiên hơn file. Không in key ra chat. |
| `openrouter.base_url` | Mặc định `https://openrouter.ai/api/v1`. |
| `openrouter.tts_model` | Model đọc. Mặc định `google/gemini-3.1-flash-tts-preview` (đọc tốt tiếng Việt, trả về PCM, script tự bọc thành `.wav`). Xem model khác: `python -I scripts/video.py voices`. |
| `openrouter.image_model` | Model vẽ ảnh bìa. Mặc định `google/gemini-3.1-flash-image` (nhận ảnh linh vật làm tham chiếu, viết được chữ tiếng Việt có dấu). |
| `openrouter.response_format` | `pcm` (mặc định) hoặc `mp3` nếu model hỗ trợ. |

## Kênh

`channels` là một map `alias -> cấu hình`. Mỗi alias là **một kênh**: một giọng, một cách xưng hô, một nhóm người xem, một câu kêu gọi. `default_channel` dùng khi người dùng không nói kênh nào.

| Khóa | Ý nghĩa |
|---|---|
| `label` | Tên hiển thị của kênh. |
| `platforms` | Nơi đăng: `tiktok`, `youtube-shorts`, `reels`, `youtube`, `facebook`. Dùng để nhắc vùng an toàn và độ dài. |
| `handle` | Tên kênh hiện ở thẻ tên và cuối video. |
| `language` | `vi` hoặc `en`. Ngôn ngữ lời đọc và chữ trên hình. |
| `default_format` | `short` hoặc `long`. Vẫn phải xác nhận lại ở Cổng 1. |
| `voice` | Tên giọng của model đọc. Với Gemini: giọng nam có `Charon` (rõ, điềm), `Puck` (trẻ, tươi), `Orus` (chắc); giọng nữ có `Kore`. Không sao chép được giọng của một người thật; chọn giọng có sẵn gần nhất rồi nghe thử. |
| `voice_style` | Một câu chỉ cách đọc, và là cách **chính** để chỉnh nhịp: thử nghiệm cho thấy câu "đọc nhanh, gọn, dứt khoát" rút ngắn lời đọc khoảng một phần tư, còn để trống thì giọng đọc khá chậm. Được ghép vào đầu văn bản gửi cho model dưới dạng "`<voice_style>`: `<lời đọc>`". Để trống nếu model đọc luôn cả câu này thành tiếng. |
| `speed` | Tốc độ đọc, 1.0 là giữ nguyên. Model đọc bỏ qua tham số tốc độ, nên script tự tăng/giảm tốc bằng ffmpeg sau khi tạo (giữ nguyên cao độ). Dùng 1.05–1.15 để nhanh hơn một chút; trên 1.2 bắt đầu nghe không tự nhiên. Muốn nhanh hơn nhiều thì sửa `voice_style` trước. |
| `tts_model` | Ghi đè model đọc cho riêng kênh này (không bắt buộc). |
| `persona` | Cách xưng hô và giọng văn. Lời đọc phải theo đúng. |
| `audience` | Người xem mục tiêu. Quyết định độ sâu kỹ thuật và ví dụ. |
| `topics` | Các mảng chủ đề của kênh, dùng để gợi ý và để từ chối chủ đề lạc kênh. |
| `cta` | Câu kêu gọi cuối video. |
| `accent` | Màu nhận diện cố định của kênh (`#RRGGBB`). Để trống thì lấy màu thương hiệu của chủ đề từng video. |
| `logo` | Đường dẫn file logo thật của kênh (tuyệt đối, hoặc tính từ thư mục skill). Để trống thì không hiện logo kênh. Lệnh `thumbnail` dùng file này làm ảnh tham chiếu linh vật, nên cần PNG, JPG hoặc WebP. |
| `image_model` | Ghi đè model vẽ ảnh bìa cho riêng kênh này (không bắt buộc). |
| `thumbnail_style` | Đoạn tả phong cách ảnh bìa riêng của kênh, bằng tiếng Anh (không bắt buộc). Để trống thì dùng phong cách giấy kẻ ô trong `thumbnail.md`. |
| `avoid` | Từ và cụm từ không dùng trong lời đọc và chữ trên hình. |
| `captions` | `true` để dựng phụ đề vào video. Video ngắn luôn có phụ đề dù đặt gì. |
| `music` | `true` nếu kênh dùng nhạc nền. |

## Thêm một kênh

1. Thêm một khối mới trong `channels` với alias viết thường, không dấu, nối bằng gạch ngang.
2. Điền ít nhất `label`, `language`, `voice`, `persona`, `cta`.
3. Chạy `python -I scripts/video.py check` để xem còn thiếu gì.
4. Nghe thử giọng: `python -I scripts/video.py tts --channel <alias> --text "Một câu thử" --out thu.wav`.

## API dùng

- `POST {base_url}/audio/speech` với `{model, input, voice, response_format[, speed]}`: trả về âm thanh. Với PCM, tần số lấy mẫu nằm trong header `Content-Type` (`rate=24000`).
- `POST {base_url}/chat/completions` với `modalities: ["image", "text"]` và `image_config.aspect_ratio`: trả về ảnh bìa dạng data URL (lệnh `thumbnail`).
- `GET {base_url}/key`: kiểm tra key và hạn mức (lệnh `check --online`).
- `GET {base_url}/models?output_modalities=speech`: danh sách model đọc (lệnh `voices`).
