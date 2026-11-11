#!/usr/bin/env bash
# Cai Hermes Agent len VPS cua khach: SSH key, OpenRouter, Telegram, Zernio, skill tu hub.
# Dung: bash scripts/setup.sh <khach.env> [--check-only]
# Bi mat chi di qua stdin cua ssh, khong nam tren dong lenh (ps) hay trong log.
set -euo pipefail

DEFAULT_TELEGRAM_IDS="6005640491,9227652557"
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
for v in VPS_HOST OPENROUTER_API_KEY TELEGRAM_BOT_TOKEN; do
  [ -n "${!v:-}" ] || die "$v dang trong trong $ENV_FILE"
done
case ",$SKILLS," in *,chay-quang-cao-facebook,*) [ -n "${ZERNIO_API_KEY:-}" ] || die "SKILLS co chay-quang-cao-facebook nhung ZERNIO_API_KEY trong";; esac

# Gop ID mac dinh + ID khach, bo trung, chi giu so.
ALLOWED_IDS="$(echo "$DEFAULT_TELEGRAM_IDS,${CUSTOMER_TELEGRAM_IDS:-}" | tr -s ', ' '\n' | grep -E '^[0-9]+$' | awk '!s[$0]++' | paste -sd, -)"

step "1/5 Kiem tra key truoc khi dong vao VPS"
OR_JSON="$(curl -fsS https://openrouter.ai/api/v1/key -H "Authorization: Bearer $OPENROUTER_API_KEY")" \
  || die "OpenRouter key sai hoac het han"
python3 -c 'import json,sys
d=json.loads(sys.argv[1])["data"]; lim=d.get("limit"); rem=d.get("limit_remaining"); per=d.get("limit_reset") or "tong"
print("  OpenRouter: OK, han muc", "khong gioi han" if lim is None else "$%s (%s), con $%s" % (lim, per, rem))' "$OR_JSON"
TG_JSON="$(curl -fsS "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getMe")" || die "Telegram bot token sai"
BOT_USERNAME="$(python3 -c 'import json,sys;print(json.loads(sys.argv[1])["result"]["username"])' "$TG_JSON")"
echo "  Telegram: OK, bot @$BOT_USERNAME"
echo "  ID duoc dung bot: $ALLOWED_IDS"
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

step "3-5/5 Cai Hermes, cau hinh, bat gateway (chay tren VPS)"
q() { printf '%q' "$1"; }
{
  echo "export OPENROUTER_API_KEY=$(q "$OPENROUTER_API_KEY")"
  echo "export TELEGRAM_BOT_TOKEN=$(q "$TELEGRAM_BOT_TOKEN")"
  echo "export ZERNIO_API_KEY=$(q "${ZERNIO_API_KEY:-}")"
  echo "export ALLOWED_IDS=$(q "$ALLOWED_IDS")"
  echo "export HOME_CHANNEL=$(q "${ALLOWED_IDS%%,*}")"
  echo "export CHAT_MODEL=$(q "$CHAT_MODEL") IMAGE_MODEL=$(q "$IMAGE_MODEL") SKILLS=$(q "$SKILLS")"
  echo "export TELEGRAM_QUIET=$(q "$TELEGRAM_QUIET") VPS_HOST=$(q "$VPS_HOST") OPENWEBUI_DOMAIN=$(q "${OPENWEBUI_DOMAIN:-}")"
  cat "$HERE/remote.sh"
  [ "$OPENWEBUI" = "1" ] && { echo; cat "$HERE/openwebui.sh"; }
} | tr -d '\r' | ssh "${SSH_OPTS[@]}" "$TARGET" 'bash -s'

echo
echo "XONG. Bot: @$BOT_USERNAME | VPS: $VPS_HOST | ID duoc dung: $ALLOWED_IDS"
echo "Nhan khach mo t.me/$BOT_USERNAME va bam Start."
if [ "$OPENWEBUI" = "1" ]; then
  OW_DOMAIN="${OPENWEBUI_DOMAIN:-$(echo "$VPS_HOST" | tr . -).sslip.io}"
  echo "Open WebUI: https://$OW_DOMAIN (tai khoan admin: ssh $TARGET 'cat ~/.hermes/openwebui.env')"
fi
