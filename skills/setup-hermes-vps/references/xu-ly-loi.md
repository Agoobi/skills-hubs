# Xử lý lỗi khi setup Hermes trên VPS

| Dấu hiệu | Nguyên nhân | Cách sửa |
|---|---|---|
| `OpenRouter key sai hoac het han` | Key gõ sai / bị thu hồi / hết hạn mức | Nhờ người dùng tạo key mới ở openrouter.ai/keys |
| `Telegram bot token sai` | Token sai hoặc đã `/revoke` | Lấy token mới từ @BotFather |
| `model ... khong ton tai` | OpenRouter đổi tên model | Xem `curl -s https://openrouter.ai/api/v1/models`, chọn id mới, sửa `CHAT_MODEL`/`IMAGE_MODEL` |
| `ssh-copy-id that bai` | Sai mật khẩu, VPS tắt đăng nhập mật khẩu, sai port | Kiểm tra lại với nhà cung cấp VPS; thử `VPS_PORT` |
| Gateway `activating (auto-restart)`, mã thoát `75` | Một gateway tạm (`gateway run --quiet --idle-exit`, do `hermes chat` sinh ra) đang giữ lock | `pkill -f "gateway run --quiet --idle-exit"; systemctl --user restart hermes-gateway`. Script đã tự làm việc này |
| Log có `Conflict` / bot lúc trả lời lúc không | Cùng token bot đang chạy ở máy khác | Mỗi VPS một bot. Dừng gateway ở máy kia hoặc dùng bot khác |
| `Blocked unauthorized user <id>` | ID chưa có trong `TELEGRAM_ALLOWED_USERS` | Thêm vào `CUSTOMER_TELEGRAM_IDS`, chạy lại setup, nhờ họ nhắn lại |
| Zernio `check` lỗi 401 | Key Zernio sai | Key mới ở Zernio |
| Zernio thấy 0 tài khoản quảng cáo | Khách chưa kết nối Meta Ads trong Zernio hoặc chưa chọn tài khoản | Hướng dẫn khách kết nối trong Zernio, chạy lại setup |
| Cảnh báo `cua-driver was not installed: libXi.so.6` khi cài | Công cụ điều khiển desktop, VPS không có màn hình | Bỏ qua, không ảnh hưởng bot Telegram |
| Ảnh tạo xong nhưng không gửi được | Model ảnh lỗi/hết hạn mức | `grep image_generate ~/.hermes/logs/agent.log | tail`; đổi `IMAGE_MODEL` |
| `bash: line N: set: pipefail: invalid option name` | File `.sh` bị đổi sang CRLF khi clone trên Windows | Clone lại với `git -c core.autocrlf=false` (repo đã có `.gitattributes`); setup.sh cũng tự bỏ `
` |
| `ssh-copy-id that bai` nhưng mật khẩu đúng (Git Bash/Windows) | `sshpass` trên Windows không ổn định | Cài paramiko (`py -m pip install paramiko`), chạy lại: setup.sh tự dùng paramiko. Hoặc `py scripts/install-key.py <khach.env>` |
| `can paramiko ... hoac sshpass` | Máy vận hành thiếu cả hai | `py -m pip install paramiko` (Windows) hoặc `pip install paramiko` / `apt install sshpass` |
| Bot nhắn nhiều tin liên tục khi đang think | Mặc định Hermes bật tin giữa chừng + nhật ký tool | `TELEGRAM_QUIET=1` (mặc định). Thủ công: `hermes config set display.platforms.telegram.interim_assistant_messages false` và `...tool_progress off`, restart gateway |
| `LOI: HTTPS chua len` | Cổng 80/443 chưa mở ở firewall nhà cung cấp VPS, hoặc DNS sslip.io chưa phân giải | Mở 80/443; `docker logs caddy`; thử lại sau 1–2 phút |
| `LOI: khong dang nhap duoc admin Open WebUI` | Volume `open-webui` có sẵn admin khác (cài lần trước) | `docker rm -f open-webui; docker volume rm open-webui` rồi chạy lại (mất lịch sử chat) |
| Open WebUI không thấy model `hermes-agent` | Khoá API server lệch | Chạy lại setup (script đồng bộ `API_SERVER_KEY` vào cả hai) |
| `git is required` / `LOI: cai Hermes that bai` trên AlmaLinux, Rocky, CentOS | VPS tối giản chưa có `git` | Từ bản 0.2.1 `remote.sh` tự cài `git`, `curl`, `python3` bằng `apt`/`dnf`/`yum`. Bản cũ: `ssh <vps> 'dnf install -y git curl tar xz'` rồi chạy lại |
| `LOI: cai goi can thiet that bai` | Mạng VPS không tới kho gói, hoặc `dnf`/`apt` đang bị khoá | `cat /tmp/prereq-install.log` trên VPS; đợi tiến trình cập nhật tự động xong rồi chạy lại |
| `Unauthorized user: <uid> on zalo` trong gateway.log | uid chưa có trong `ZALO_ALLOWED_USERS` (Hermes mặc định chặn người lạ) | Thêm uid vào `CUSTOMER_ZALO_IDS`, chạy lại; người đó nhắn lại |
| Zalo `health` có `sessionDead:true`, `code=1006` rồi `cookie login failed` | Zalo huỷ phiên: nick phụ mở Zalo Web/PC ở nơi khác, hoặc đăng nhập 2 lần liên tiếp | Đăng xuất Zalo Web/PC của nick phụ, chạy lại setup (`ZALO=1`) để lấy QR mới |
| Người dùng nói đã quét nhưng không vào, log toàn `QR expired; regenerating` | Quét trúng QR cũ, hoặc 2 tiến trình cùng ghi `qr.png` (`login.mjs` chạy chồng service) | `pkill -f "hermes-zalo-plugin/(install\|login).mjs"; systemctl --user restart com.hermes.zaloplugin`, gửi QR mới. Script từ 0.3.0 đã tự làm |
| `Zalo plugin is running but not logged in` khi gateway khởi động | Bridge chưa đăng nhập / đang chờ quét | Quét QR; gateway tự thử lại mỗi phút, hoặc `systemctl --user restart hermes-gateway` |
| Bot Zalo không trả lời, log chỉ có `Zalo inbound: uid=...`, không có `Unauthorized` | uid người nhắn chưa có trong `ZALO_ALLOWED_USERS`: plugin bỏ qua im lặng. Hay gặp nhất khi chép uid từ VPS khác (uid tương đối theo từng nick phụ) | `bash scripts/zalo-allow.sh <env>` để xem uid thật, rồi `bash scripts/zalo-allow.sh <env> <uid>`; người đó nhắn lại |
| Bot im trong nhóm Zalo | `ZALO_GROUP_MODE=mention` mà không @tag/reply, hoặc người tag chưa có trong danh sách | @tag đúng nick phụ; thêm uid người đó |
| (máy vận hành, Git Bash) tải file từ VPS báo không có file dù có | Git Bash đổi `/root/...` thành `C:/Program Files/Git/root/...` | Thêm `MSYS_NO_PATHCONV=1` trước lệnh, hoặc dùng đường dẫn tương đối (`.hermes-zalo/qr.png`) như setup.sh |
| `CANH BAO: khong tra duoc uid cho so ...` | Sai SĐT, người đó tắt tìm kiếm qua SĐT, hoặc Zalo giới hạn tra cứu | Nhờ họ nhắn nick phụ, lấy uid bằng `zalo-allow.sh` |
