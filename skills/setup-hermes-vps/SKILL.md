---
name: setup-hermes-vps
description: Cài Hermes lên VPS khách: Telegram (yên lặng), OpenRouter, Zernio, Open WebUI.
version: 0.2.0
author: Agoobi
license: MIT
metadata:
  hermes:
    category: coquifly
    tags: [hermes, vps, setup, telegram, openrouter, zernio, onboarding, vietnamese]
---

# setup-hermes-vps

Bàn giao một con bot Hermes cho khách trên VPS riêng của khách, chỉ bằng một lệnh: cài SSH key → cài Hermes Agent → model qua OpenRouter (chat + tạo ảnh) → bot Telegram chạy nền 24/7 chỉ cho đúng người dùng → bot chỉ gửi **một tin kết quả**, không nhắn từng bước khi đang think → cài skill từ hub (mặc định `chay-quang-cao-facebook` qua Zernio) → cài **Open WebUI** có HTTPS tại `https://<ip-gạch-ngang>.sslip.io` → kiểm tra thật rồi báo kết quả.

Dùng khi người dùng nói "setup hermes cho khách", "cài bot lên VPS", "bàn giao bot", đưa IP VPS + key, hoặc muốn thêm/bớt Telegram ID, đổi model, cập nhật skill trên một VPS đã cài.

## Quy tắc

1. **Bí mật không ra chat, không vào git.** Không in lại mật khẩu, key, token. Ghi vào file env của khách (`chmod 600`), script tự chuyển qua stdin của ssh.
2. **Telegram ID mặc định luôn có:** `6005640491`, `9227652557`. Script tự thêm, không bao giờ bỏ, kể cả khi người dùng chỉ đưa ID khách.
3. **Mỗi VPS một bot Telegram riêng.** Một token chạy ở hai nơi thì hai nơi giành tin nhắn của nhau. Nếu người dùng đưa token đã dùng cho khách khác thì cảnh báo trước.
4. **Chỉ báo "xong" khi script in `XONG`.** Lỗi thì báo nguyên văn dòng `LOI:` và cách sửa, không đoán.
5. Không đụng vào quảng cáo của khách: setup chỉ đọc (`check`, `accounts`), không tạo/bật camp.

## Đầu vào cần hỏi (gom một lượt)

| Biến | Bắt buộc | Ghi chú |
|---|---|---|
| `VPS_HOST` | có | IP VPS (Ubuntu 22.04/24.04, ≥2 GB RAM) |
| `VPS_USER` / `VPS_PORT` | không | mặc định `root` / `22` |
| `VPS_PASSWORD` | lần đầu | để cài SSH key; đã vào được bằng key thì bỏ trống |
| `OPENROUTER_API_KEY` | có | `sk-or-v1-...` |
| `TELEGRAM_BOT_TOKEN` | có | bot riêng cho khách này (tạo qua @BotFather) |
| `CUSTOMER_TELEGRAM_IDS` | không | ID của khách, cách nhau dấu phẩy. Khách lấy ID qua @userinfobot |
| `ZERNIO_API_KEY` | có nếu cài skill quảng cáo | `sk_...`, khách đã kết nối Meta Ads trong Zernio |
| `CHAT_MODEL` | không | mặc định `deepseek/deepseek-v4.1-flash` |
| `IMAGE_MODEL` | không | mặc định `google/gemini-3.1-flash-lite-image` (model ảnh rẻ nhất) |
| `SKILLS` | không | mặc định `chay-quang-cao-facebook`; id skill trong `manifest.json`, cách nhau dấu phẩy |
| `OPENWEBUI` | không | mặc định `1`: cài Open WebUI. `0` để bỏ qua |
| `OPENWEBUI_DOMAIN` | không | mặc định `<ip-gạch-ngang>.sslip.io` (vd `151-246-182-155.sslip.io`). Đặt tên miền riêng nếu đã trỏ DNS |
| `TELEGRAM_QUIET` | không | mặc định `1`: bot Telegram chỉ gửi 1 tin kết quả. `0` để về mặc định của Hermes |

## Cách chạy

Chạy từ thư mục skill này, trên máy của người vận hành (cần `ssh`, `curl`, `python3`; lần đầu với mật khẩu cần `sshpass`).

**Windows (Git Bash):** `sshpass` hay báo `ssh-copy-id that bai` dù mật khẩu đúng. Cài key bằng paramiko (`py -m pip install paramiko`) rồi chạy lại, script sẽ thấy "Da vao duoc bang key":
```
py scripts/install-key.py ~/khach/<ten-khach>.env
```
Clone repo bằng `git -c core.autocrlf=false` (repo đã có `.gitattributes` ép LF cho `*.sh`; script ssh cũng tự bỏ `
`).
Mật khẩu có ký tự `#`, `!`: đặt trong dấu nháy đơn trong file env, đúng nguyên văn (`#` đầu chuỗi là một phần mật khẩu, không phải ghi chú).

1. Tạo file env cho khách ngoài thư mục skill, ví dụ `~/khach/<ten-khach>.env`, từ `templates/khach.env.example`, điền giá trị người dùng đưa, `chmod 600`.
2. Kiểm tra trước (không cài gì, chỉ thử key, bot, model, SSH):
   ```
   bash scripts/setup.sh ~/khach/<ten-khach>.env --check-only
   ```
   Có `LOI:` → dừng, báo người dùng. OpenRouter có hạn mức thấp (ví dụ $1/ngày) → nhắc người dùng.
3. Cài thật (5–10 phút lần đầu, chạy lại an toàn):
   ```
   bash scripts/setup.sh ~/khach/<ten-khach>.env
   ```
4. Báo người dùng: tên bot `@...`, VPS, danh sách ID được dùng, tài khoản quảng cáo Zernio thấy được (tên, ID, trạng thái, có thẻ chưa), và việc khách phải làm: mở bot, bấm **Start**.
5. Báo link Open WebUI. Tài khoản admin do script tạo, lưu ở `~/.hermes/openwebui.env` trên VPS (`ssh <vps> 'cat ~/.hermes/openwebui.env'`), đăng ký mở cửa đã tắt. Không in mật khẩu admin ra chat, chỉ chỉ đường lấy.
6. Nhắc đổi mật khẩu root của VPS nếu mật khẩu đã gửi qua chat.

## Việc hay gặp sau này

- **Thêm/bớt Telegram ID, đổi model, đổi key, thêm skill:** sửa file env của khách rồi chạy lại bước 3. Script ghi đè giá trị cũ, giữ `settings.json` của skill.
- **Ai đã nhắn bot:** `ssh <vps> 'grep -h "inbound message: platform=telegram" ~/.hermes/logs/gateway.log* | tail -20; grep -h "Blocked unauthorized" ~/.hermes/logs/gateway.log* | tail'`. Người bị chặn trước khi được thêm phải nhắn lại.
- **Bot nhắn quá nhiều khi đang think:** đã tắt sẵn (`TELEGRAM_QUIET=1`: tắt tin giữa chừng, nhật ký tool, lý luận; tiến độ gom thành 1 bong bóng "⏳ Working" tự xoá khi xong; `SOUL.md` dặn nhắn một lần). Muốn xem lại: `ssh <vps> 'hermes config show | grep -A10 telegram'`. Muốn bật lại tin giữa chừng cho một VPS: `hermes config set display.platforms.telegram.interim_assistant_messages true` rồi `systemctl --user restart hermes-gateway`.
- **Open WebUI không mở / HTTPS lỗi:** `ssh <vps> 'docker logs --tail 30 open-webui; docker logs --tail 30 caddy'`. Cổng 80/443 phải mở ở firewall nhà cung cấp VPS (Let's Encrypt cần).
- **Bot không trả lời:** `ssh <vps> 'systemctl --user status hermes-gateway; tail -30 ~/.hermes/logs/gateway.log'`. Xem `references/xu-ly-loi.md`.

## Script làm gì (để giải thích khi được hỏi)

`scripts/setup.sh` (máy vận hành): kiểm key OpenRouter + hạn mức, `getMe` Telegram, model có trên OpenRouter → cài SSH key bằng `sshpass` → đẩy `scripts/remote.sh` kèm biến bí mật qua stdin ssh.

`scripts/remote.sh` (trên VPS): cài Hermes bằng installer chính thức (`--skip-setup`) → ghi `~/.hermes/.env` (OpenRouter, Telegram token, `TELEGRAM_ALLOWED_USERS`, `TELEGRAM_HOME_CHANNEL`, Zernio) → `hermes config set` model chat + `image_gen` OpenRouter → clone hub, chép skill vào `~/.hermes/skills/<category>/<id>` → skill quảng cáo: `execution: zernio`, `check`, `accounts --write`, đặt tài khoản mặc định nếu chỉ có một → dừng gateway tạm do `hermes chat` sinh ra, `hermes gateway install` (systemd user + linger), chờ log `telegram connected`.

`scripts/openwebui.sh` (trên VPS, chạy sau `remote.sh`): bật API server Hermes (`API_SERVER_ENABLED`, `API_SERVER_KEY` ngẫu nhiên, chỉ nghe `127.0.0.1:8642`) → cài Docker nếu chưa có → chạy `open-webui` (host network, chỉ nghe `127.0.0.1:3000`, tự tạo admin bằng `WEBUI_ADMIN_EMAIL/PASSWORD`, tắt đăng ký, `ENABLE_PERSISTENT_CONFIG=false` để env luôn thắng) → đăng nhập thử bằng admin → chạy `caddy` làm HTTPS tự động cho `<ip>.sslip.io` → chờ `https://<domain>/health` trả về 200.
