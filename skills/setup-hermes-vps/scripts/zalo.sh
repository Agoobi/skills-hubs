# Chay TREN VPS, do setup.sh day qua stdin cua ssh (sau remote.sh). Zalo CA NHAN (nick phu) qua
# hermes-zalo-plugin (zca-js, API khong chinh thuc). Hai giai doan, chon bang ZALO_STAGE:
#   prepare : cai Node + plugin, ghi ZALO_* vao ~/.hermes/.env, bat dang nhap QR chay nen
#             -> in "ZALO_QR_READY" (QR o ~/.hermes-zalo/qr.png) hoac "ZALO_LOGGED_IN" (da dang nhap san)
#   status  : in 1 dong "ZALO_STATE <logged_in|waiting|dead> <mtime qr>" de setup.sh cho khach quet
#   finish  : bat bridge thanh service, restart gateway, cho log "Zalo: connected"
# Chay lai an toan: da dang nhap thi khong hien QR nua.
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH" XDG_RUNTIME_DIR="/run/user/$(id -u)"
ZDIR="$HOME/.hermes-zalo"; QR="$ZDIR/qr.png"; CRED="$ZDIR/credentials.json"
PLUGIN_VER="${ZALO_PLUGIN_VERSION:-1.0.12}"
health() { curl -fsS --max-time 3 http://127.0.0.1:8787/health 2>/dev/null || true; }

case "${ZALO_STAGE:-prepare}" in
prepare)
  if ! command -v node >/dev/null || [ "$(node -v | cut -c2- | cut -d. -f1)" -lt 20 ]; then
    echo "  Cai Node.js 22..."
    if command -v apt-get >/dev/null; then
      curl -fsSL https://deb.nodesource.com/setup_22.x | bash - >/tmp/node-install.log 2>&1 \
        && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq nodejs >>/tmp/node-install.log 2>&1
    else
      curl -fsSL https://rpm.nodesource.com/setup_22.x | bash - >/tmp/node-install.log 2>&1 \
        && { dnf install -y nodejs || yum install -y nodejs; } >>/tmp/node-install.log 2>&1
    fi || { tail -20 /tmp/node-install.log; echo "LOI: cai Node.js that bai"; exit 1; }
  fi
  echo "  Node $(node -v)"
  npm ls -g hermes-zalo-plugin 2>/dev/null | grep -q "@$PLUGIN_VER" \
    || npm i -g "hermes-zalo-plugin@$PLUGIN_VER" >/tmp/npm-zalo.log 2>&1 \
    || { tail -20 /tmp/npm-zalo.log; echo "LOI: cai hermes-zalo-plugin that bai"; exit 1; }
  echo "  hermes-zalo-plugin $PLUGIN_VER"

  ENV="$(hermes config env-path)"; touch "$ENV"; chmod 600 "$ENV"
  setenv() { grep -q "^$1=" "$ENV" && sed -i "s|^$1=.*|$1=$2|" "$ENV" || echo "$1=$2" >>"$ENV"; }
  setenv ZALO_PLUGIN_URL http://127.0.0.1:8787
  setenv ZALO_ALLOWED_USERS "$ZALO_IDS"            # bat buoc: rong = Hermes chan het (Unauthorized user)
  setenv ZALO_GROUP_MODE "${ZALO_GROUP_MODE:-mention}"
  setenv ZALO_LOG_IDS true                          # log "Zalo inbound: uid=..." de lay uid them vao danh sach
  for kv in tool_progress=off interim_assistant_messages=false show_reasoning=false busy_ack_detail=false \
            suppress_warning_notifications=true; do
    hermes config set "display.platforms.zalo.${kv%%=*}" "${kv#*=}" >/dev/null 2>&1 || true
  done
  SOUL="$HOME/.hermes/SOUL.md"; touch "$SOUL"
  grep -q "MOC-ZALO" "$SOUL" || printf '\n\n<!-- MOC-ZALO -->\nTrên Zalo: trả lời bằng tiếng Việt, ngắn gọn; làm xong rồi mới nhắn một lần, không kể từng bước.\n' >>"$SOUL"
  echo "  Zalo: duoc nhan = $ZALO_IDS | nhom = ${ZALO_GROUP_MODE:-mention}"
  loginctl enable-linger "$(id -un)" 2>/dev/null || true

  # KHONG dung `hermes-zalo-plugin setup` (login.mjs): no dang nhap 1 lan, thoat, roi service dang nhap
  # lan 2 -> 2 phien lien tiep, va neu chay chong voi service thi 2 tien trinh cung ghi qr.png (QR doi
  # giua chung, quet khong vao). Chi dung service: server.js tu ra QR, quet xong la bridge dang nhap luon.
  pkill -f "hermes-zalo-plugin/(install|login).mjs" 2>/dev/null || true
  U="$HOME/.config/systemd/user/com.hermes.zaloplugin.service"
  [ -f "$U" ] || (cd /tmp && hermes-zalo-plugin setup --service-only >/tmp/zalo-svc.log 2>&1) \
    || { tail -20 /tmp/zalo-svc.log; echo "LOI: khong cai duoc service bridge Zalo"; exit 1; }
  # Ghi log bridge ra file: biet ly do khi phien Zalo rot
  grep -q StandardOutput "$U" || sed -i "/^RestartSec=/a StandardOutput=append:$ZDIR/bridge.log\nStandardError=append:$ZDIR/bridge.log" "$U"
  systemctl --user daemon-reload
  if health | grep -q '"loggedIn":true'; then echo "ZALO_LOGGED_IN"; exit 0; fi
  # Chua dang nhap: restart de bridge thu cookie da luu; Zalo da huy thi no tu ra QR moi.
  rm -f "$QR"; systemctl --user restart com.hermes.zaloplugin
  for _ in $(seq 1 30); do
    sleep 2
    health | grep -q '"loggedIn":true' && { echo "ZALO_LOGGED_IN"; exit 0; }
    [ -s "$QR" ] && { echo "ZALO_QR_READY"; exit 0; }
  done
  tail -5 "$ZDIR/bridge.log" 2>/dev/null || true
  echo "LOI: khong tao duoc QR Zalo"; exit 1 ;;

status)
  H="$(health)"; M="$(stat -c %Y "$QR" 2>/dev/null || echo 0)"
  if echo "$H" | grep -q '"loggedIn":true'; then echo "ZALO_STATE logged_in $M"
  elif echo "$H" | grep -q '"sessionDead":true'; then echo "ZALO_STATE dead $M"
  else echo "ZALO_STATE waiting $M"; fi ;;

finish)
  chmod 600 "$CRED" 2>/dev/null || true
  for _ in $(seq 1 15); do health | grep -q '"loggedIn":true' && break; sleep 2; done
  health | grep -q '"loggedIn":true' || { health; echo; echo "LOI: bridge Zalo chua dang nhap (phien bi Zalo huy? chay lai setup de lay QR moi)"; exit 1; }
  LOG="$HOME/.hermes/logs/gateway.log"; MARK=$(wc -l 2>/dev/null <"$LOG" || echo 0)
  systemctl --user restart hermes-gateway
  for _ in $(seq 1 20); do sleep 2; tail -n +"$((MARK+1))" "$LOG" 2>/dev/null | grep -q "Zalo: connected" && break; done
  if tail -n +"$((MARK+1))" "$LOG" | grep -q "Zalo: connected"; then
    echo "  Zalo: gateway da noi bridge ($(health | python3 -c 'import json,sys;print("ownId", json.load(sys.stdin).get("ownId"))'))"
  else
    tail -n +"$((MARK+1))" "$LOG" | grep -i zalo | tail -5
    echo "LOI: gateway chua noi duoc Zalo"; exit 1
  fi
  grep -h "QR scanned by" "$ZDIR/bridge.log" 2>/dev/null | tail -1 | sed 's/^/  /' || true ;;
esac
