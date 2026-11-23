#!/usr/bin/env bash
# Cai Hermes Agent len VPS cua khach: SSH key, OpenRouter, Telegram va/hoac Zalo ca nhan, Zernio, skill tu hub.
# Dung: bash scripts/setup.sh <khach.env> [--check-only]
# Bi mat chi di qua stdin cua ssh, khong nam tren dong lenh (ps) hay trong log.
set -euo pipefail

DEFAULT_TELEGRAM_IDS="6005640491,9227652557"
# SDT Zalo nguoi van hanh, luon duoc nhan bot. Dung SDT, KHONG dung uid: uid Zalo tuong doi theo tung
# nick (cung 1 nguoi, 2 nick phu thay 2 uid khac nhau); zalo.sh tra uid tu SDT qua chinh nick phu.
DEFAULT_ZALO_PHONES=""
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

die() { echo "LOI: $*" >&2; exit 1; }
step() { echo; echo "== $*"; }

[ $# -ge 1 ] || die "thieu file env. Dung: bash scripts/setup.sh <khach.env> [--check-only]"
ENV_FILE="$1"; CHECK_ONLY="${2:-}"
[ -f "$ENV_FILE" ] || die "khong thay $ENV_FILE"
chmod 600 "$ENV_FILE" 2>/dev/null || true
set -a; # shellcheck disable=SC1090
. "$ENV_FILE"; set +a

VPS_USER="${VPS_USER:-root}"; VPS_PORT="${VPS_PORT:-22}"
CHAT_MODEL="${CHAT_MODEL:-deepseek/deepseek-v4.1-flash}"
IMAGE_MODEL="${IMAGE_MODEL:-google/gemini-3.1-flash-lite-image}"
SKILLS="${SKILLS:-chay-quang-cao-facebook}"
OPENWEBUI="${OPENWEBUI:-1}"          # 1 = cai Open WebUI (HTTPS qua sslip.io); 0 = bo qua
TELEGRAM_QUIET="${TELEGRAM_QUIET:-1}" # 1 = bot Telegram chi gui 1 tin ket qua, khong nhan tung buoc
ZALO="${ZALO:-0}"                     # 1 = gan Zalo ca nhan (nick phu) qua hermes-zalo-plugin
REQ="VPS_HOST OPENROUTER_API_KEY"; [ "$ZALO" = "1" ] || REQ="$REQ TELEGRAM_BOT_TOKEN"
for v in $REQ; do
  [ -n "${!v:-}" ] || die "$v dang trong trong $ENV_FILE"
done
case ",$SKILLS," in *,chay-quang-cao-facebook,*) [ -n "${ZERNIO_API_KEY:-}" ] || die "SKILLS co chay-quang-cao-facebook nhung ZERNIO_API_KEY trong";; esac

# Gop ID mac dinh + ID khach, bo trung, chi giu so.
ALLOWED_IDS="$(echo "$DEFAULT_TELEGRAM_IDS,${CUSTOMER_TELEGRAM_IDS:-}" | tr -s ', ' '\n' | grep -E '^[0-9]+$' | awk '!s[$0]++' | paste -sd, -)"
normcsv() { echo "$1" | tr -s ', ' '\n' | grep -E '^[0-9]+$' | awk '!s[$0]++' | paste -sd, - || true; }
ZALO_PHONES="$(normcsv "$DEFAULT_ZALO_PHONES,${CUSTOMER_ZALO_PHONES:-}")"
ZALO_IDS="$(normcsv "${CUSTOMER_ZALO_IDS:-}")"   # uid chi dung cho DUNG nick phu nay (lay tu log cua VPS nay)

step "1/5 Kiem tra key truoc khi dong vao VPS"
OR_JSON="$(curl -fsS https://openrouter.ai/api/v1/key -H "Authorization: Bearer $OPENROUTER_API_KEY")" \
  || die "OpenRouter key sai hoac het han"
python3 -c 'import json,sys
d=json.loads(sys.argv[1])["data"]; lim=d.get("limit"); rem=d.get("limit_remaining"); per=d.get("limit_reset") or "tong"
print("  OpenRouter: OK, han muc", "khong gioi han" if lim is None else "$%s (%s), con $%s" % (lim, per, rem))' "$OR_JSON"
BOT_USERNAME=""
if [ -n "${TELEGRAM_BOT_TOKEN:-}" ]; then
  TG_JSON="$(curl -fsS "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getMe")" || die "Telegram bot token sai"
  BOT_USERNAME="$(python3 -c 'import json,sys;print(json.loads(sys.argv[1])["result"]["username"])' "$TG_JSON")"
  echo "  Telegram: OK, bot @$BOT_USERNAME"
  echo "  ID Telegram duoc dung bot: $ALLOWED_IDS"
else
  echo "  Telegram: bo qua (khong co token)"
fi
if [ "$ZALO" = "1" ]; then echo "  Zalo: SDT duoc nhan bot: ${ZALO_PHONES:-(chua co)} | uid: ${ZALO_IDS:-(chua co)} | nhom: ${ZALO_GROUP_MODE:-mention}"; fi
for m in "$CHAT_MODEL" "$IMAGE_MODEL"; do
  curl -fsS https://openrouter.ai/api/v1/models | python3 -c 'import json,sys
ids={m["id"] for m in json.load(sys.stdin)["data"]}; m=sys.argv[1]
print("  Model", m, "OK" if m in ids else "KHONG CO TREN OPENROUTER"); sys.exit(0 if m in ids else 1)' "$m" \
    || die "model $m khong ton tai tren OpenRouter"
done

step "2/5 SSH key"
SSH_OPTS=(-p "$VPS_PORT" -o StrictHostKeyChecking=accept-new -o ConnectTimeout=15)
TARGET="$VPS_USER@$VPS_HOST"
[ -f "$HOME/.ssh/id_ed25519.pub" ] || ssh-keygen -t ed25519 -N "" -f "$HOME/.ssh/id_ed25519" -q
if ssh "${SSH_OPTS[@]}" -o BatchMode=yes "$TARGET" true 2>/dev/null; then
  echo "  Da vao duoc bang key"
else
  [ -n "${VPS_PASSWORD:-}" ] || die "chua vao duoc bang key va VPS_PASSWORD trong"
  # Uu tien paramiko (on dinh tren moi he, nhat la Windows/Git Bash); khong co thi dung sshpass.
  PY_SSH=""
  for c in py python3 python; do
    command -v "$c" >/dev/null && "$c" -c 'import paramiko' 2>/dev/null && { PY_SSH="$c"; break; }
  done
  if [ -n "$PY_SSH" ]; then
    "$PY_SSH" "$HERE/install-key.py" "$ENV_FILE" >/dev/null || die "cai key bang paramiko that bai (sai mat khau, VPS chan dang nhap mat khau, hoac sai port)"
  elif command -v sshpass >/dev/null; then
    SSHPASS="$VPS_PASSWORD" sshpass -e ssh-copy-id -i "$HOME/.ssh/id_ed25519.pub" "${SSH_OPTS[@]}" "$TARGET" >/dev/null 2>&1       || die "ssh-copy-id that bai (sai mat khau, VPS chan dang nhap mat khau, hoac sshpass loi tren Windows -> cai paramiko: py -m pip install paramiko)"
  else
    die "can paramiko (py -m pip install paramiko) hoac sshpass (sudo apt install sshpass) de cai key bang mat khau"
  fi
  ssh "${SSH_OPTS[@]}" -o BatchMode=yes "$TARGET" true || die "da chep key nhung van khong vao duoc bang key"
  echo "  Da cai key, tu gio vao khong can mat khau"
fi
ssh "${SSH_OPTS[@]}" "$TARGET" '. /etc/os-release; echo "  VPS: $PRETTY_NAME, RAM $(free -h | awk "/Mem/{print \$2}"), dia trong $(df -h / | awk "NR==2{print \$4}")"'

[ "$CHECK_ONLY" = "--check-only" ] && { echo; echo "--check-only: dung o day, chua cai gi."; exit 0; }

q() { printf '%q' "$1"; }

# --- Zalo: QR TRUOC khi cai Hermes (bridge khong can Hermes) de nguoi dung quet trong luc cai ---
QR_WATCH_PID=""
if [ "$ZALO" = "1" ]; then
  step "Zalo ca nhan: cai bridge, ra QR (truoc khi cai Hermes)"
  zremote() {
    { echo "export ZALO_STAGE=$1 ZALO_IDS=$(q "$ZALO_IDS") ZALO_PHONES=$(q "$ZALO_PHONES") ZALO_GROUP_MODE=$(q "${ZALO_GROUP_MODE:-mention}") ZALO_PLUGIN_VERSION=$(q "${ZALO_PLUGIN_VERSION:-1.0.12}")"
      cat "$HERE/zalo.sh"; } | tr -d '\r' | ssh "${SSH_OPTS[@]}" "$TARGET" 'bash -s'
  }
  QR_OUT="${ENV_FILE%.env}-zalo-qr.png"
  # Canh QR: moi lan bridge lam moi QR thi tai ve va in "ZALO_QR: <file>" (agent gui file do cho nguoi dung).
  qr_watch() {
    local last="" st mt
    while :; do
      read -r _ st mt <<<"$(zremote status 2>/dev/null || echo "x err 0")"
      if [ "$st" = "logged_in" ]; then echo "ZALO_SCANNED: da quet QR, Zalo dang nhap xong ($(date +%T))"; return 0; fi
      if [ "${mt:-0}" != "0" ] && [ "$mt" != "$last" ]; then
        scp -q -P "$VPS_PORT" -o StrictHostKeyChecking=accept-new "$TARGET:.hermes-zalo/qr.png" "$QR_OUT" \
          && echo "ZALO_QR: $QR_OUT ($(date +%T)) <- gui file nay cho nguoi dung NGAY"
        last="$mt"
      fi
      sleep 3
    done
  }
  OUT="$(zremote prepare)" || { echo "$OUT"; die "chuan bi Zalo that bai"; }
  echo "$OUT" | grep -v '^ZALO_' || true
  if echo "$OUT" | grep -q ZALO_QR_READY; then
    echo "  QR song ~1-2 phut, bridge tu lam moi. Nguoi dung quet bang app Zalo cua NICK PHU (dang xuat Zalo Web/PC cua nick phu truoc)."
    qr_watch & QR_WATCH_PID=$!
    trap '[ -n "$QR_WATCH_PID" ] && kill "$QR_WATCH_PID" 2>/dev/null || true' EXIT
  else
    echo "  Zalo da dang nhap san, khong can quet"
  fi
fi

step "3-5/5 Cai Hermes, cau hinh, bat gateway (chay tren VPS)"
{
  echo "export OPENROUTER_API_KEY=$(q "$OPENROUTER_API_KEY")"
  echo "export TELEGRAM_BOT_TOKEN=$(q "${TELEGRAM_BOT_TOKEN:-}")"
  echo "export ZERNIO_API_KEY=$(q "${ZERNIO_API_KEY:-}")"
  echo "export ALLOWED_IDS=$(q "$ALLOWED_IDS")"
  echo "export HOME_CHANNEL=$(q "${ALLOWED_IDS%%,*}")"
  echo "export CHAT_MODEL=$(q "$CHAT_MODEL") IMAGE_MODEL=$(q "$IMAGE_MODEL") SKILLS=$(q "$SKILLS")"
  echo "export TELEGRAM_QUIET=$(q "$TELEGRAM_QUIET") VPS_HOST=$(q "$VPS_HOST") OPENWEBUI_DOMAIN=$(q "${OPENWEBUI_DOMAIN:-}")"
  cat "$HERE/remote.sh"
  if [ "$OPENWEBUI" = "1" ]; then echo; cat "$HERE/openwebui.sh"; fi
} | tr -d '\r' | ssh "${SSH_OPTS[@]}" "$TARGET" 'bash -s'

if [ "$ZALO" = "1" ]; then
  step "Zalo ca nhan: cho quet QR, noi gateway"
  if [ -n "$QR_WATCH_PID" ] && kill -0 "$QR_WATCH_PID" 2>/dev/null; then
    DEADLINE=$(( $(date +%s) + ${ZALO_QR_WAIT:-900} ))
    while kill -0 "$QR_WATCH_PID" 2>/dev/null; do
      [ "$(date +%s)" -lt "$DEADLINE" ] || die "het ${ZALO_QR_WAIT:-900}s chua quet QR. Chay lai setup de lay QR moi"
      sleep 2
    done
  fi
  QR_WATCH_PID=""
  zremote finish || die "noi gateway voi Zalo that bai"
  rm -f "$QR_OUT"
fi

echo
echo "XONG. VPS: $VPS_HOST"
if [ -n "$BOT_USERNAME" ]; then
  echo "Telegram: @$BOT_USERNAME | ID duoc dung: $ALLOWED_IDS"
  echo "Nhan khach mo t.me/$BOT_USERNAME va bam Start."
fi
if [ "$ZALO" = "1" ]; then echo "Zalo: them nguoi duoc nhan bot: bash scripts/zalo-allow.sh $ENV_FILE (xem ai vua nhan) roi bash scripts/zalo-allow.sh $ENV_FILE <uid>"; fi
if [ "$OPENWEBUI" = "1" ]; then
  OW_DOMAIN="${OPENWEBUI_DOMAIN:-$(echo "$VPS_HOST" | tr . -).sslip.io}"
  echo "Open WebUI: https://$OW_DOMAIN (tai khoan admin: ssh $TARGET 'cat ~/.hermes/openwebui.env')"
fi
