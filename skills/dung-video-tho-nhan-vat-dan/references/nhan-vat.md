# Nhân vật dẫn

Nhân vật được ráp từ [Open Peeps](https://www.openpeeps.com/) (Pablo Stanley, CC0) qua gói npm `@opeepsfun/open-peeps` (MIT) lúc build, nên không tốn phí tạo video và không cần file hình trong repo.

## Ngoại hình

Trong `settings.json > presenter`, đọc một lần lúc `init` và lưu vào `project.json`. Đổi settings thì sửa cả `project.json` của dự án đang làm.

| Trường | Ý nghĩa | Ví dụ |
|---|---|---|
| `name` | Tên gọi trong kịch bản | `anh Que` |
| `hair` | Kiểu tóc, là tên file trong `build/head/` của gói | `ShortFour`, `Pomp`, `LongHair`, `Bun`, `Afro`, `Bald` |
| `skin`, `hairColor` | Màu da, màu tóc | `#F1C7A0`, `#2A2320` |
| `pants` | Màu quần khi đứng, màu nhận diện của nhân vật | `#FF5C7A` |
| `top` | Màu áo ở khung tròn góc màn hình | `#121826` |
| `beard`, `accessory` | Râu, kính, là tên file trong `build/beard/`, `build/accessory/` | `Glasses` |

Thân đứng dùng họ `ColorPants` nên áo luôn đen. Tư thế chỉ tay của Open Peeps không có bản đổi màu áo, giữ một họ thì mọi cảnh mặc giống nhau.

Giữ một nhân vật xuyên suốt kênh để người xem nhận ra.

## Tư thế

`presenter.pose` ở nhịp dừng và cảnh riêng: `explain` (mặc định), `point` (tự chọn khi có `point: true`), `think`, `calm`. `side`: `right` (mặc định) hoặc `left`. Video dọc thì nhân vật luôn đứng dưới video.

## Miệng

Có ba nét mặt: ngậm, mở, chớp mắt. `cut` đo độ to của giọng 15 lần mỗi giây, `build.mjs` đổi nét mặt theo đó và tự chớp mắt khoảng 3,4 giây một lần. Đây là nhép miệng kiểu hoạt hình đơn giản, không khớp từng âm tiết.

Cần khớp môi thật hoặc người ảo giống người thì phải dùng dịch vụ trả phí như HeyGen, nằm ngoài skill này.
