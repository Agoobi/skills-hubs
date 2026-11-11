# Motion recipes

Đây là thông số khởi điểm tái dựng, không phải keyframe đo từ project gốc. Kích thước theo 1920×1080; 0,4 s tương đương 12 frame ở 30 fps.

| Động tác | Cách dựng | Gợi ý |
|---|---|---|
| Giấy vào + settle | Wrapper x/y/rotation; shadow ở wrapper riêng | 0,45–0,75 s; góc đầu 15–35°, cuối ±2–4°; power3.out |
| Cutout xuất hiện | Dịch 30–90 px + opacity hoặc vào từ ngoài khung | 0,3–0,6 s; power2.out |
| Zoom bằng chứng | Scale/translate world wrapper, neo vùng đọc | scale 1→1,15–1,45 trong 0,6–1 s; power2.inOut |
| Drift trong hold | Chỉ world/background; HUD đứng yên nếu cần | scale 1→1,03–1,07 trong 3–6 s; none |
| Highlight | Một span/rect mỗi dòng; scaleX 0→1, origin trái | 0,18–0,35 s/dòng; stagger 0,08–0,16 s |
| Callout | Dot → SVG line → label; chung hệ tọa độ | 0,12 + 0,25–0,45 + 0,2–0,35 s |
| Route/ring | SVG path length + dashoffset; mask riêng cho đường đứt | 0,5–1,2 s; none/power1.inOut |
| Shot→map | Giữ chủ thể gần cùng vị trí qua cut rồi zoom ra | 0,4–0,8 s |
| Parallax | Nền 0,3×, giữa 0,65×, trước 1× lượng pan | pan 30–100 px; giả lập 2.5D |
| Chữ theo cụm | 1–4 từ/cụm, clip/opacity/translate; chừa dấu | 0,15–0,3 s/cụm |
| Wipe giấy | Giấy che full frame, đổi cảnh lúc bị che | 0,35–0,65 s tổng |

Hold 1–2,5 s cho nhãn ngắn chỉ là khởi điểm; tài liệu dài theo voice. Cảnh map biển giữ lâu hơn collage khoa học; không áp mọi shot thành hai giây.

Lớp: background → map/newsprint → texture nền → cutout → callout → backing nhãn → typography. Grain 2–6% opacity để bắt đầu. Shadow giấy offset 3–8 px, blur 6–16 px, opacity 15–25%; tránh bóng UI lớn.

Chỉ một chuyển động chủ đạo, có landing rõ để đọc. Nếu texture làm giảm đọc, giảm texture trước khi thêm outline chữ. Overshoot nhỏ chỉ cho giấy/vật thể nhẹ, không bật nảy bản đồ và chứng cứ.

