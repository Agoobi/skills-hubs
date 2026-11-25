#!/usr/bin/env bash
# Them nguoi duoc nhan bot Zalo tren mot VPS da cai (ZALO=1).
#   bash scripts/zalo-allow.sh <khach.env>               # liet ke ai vua nhan / @tag nick phu (ten, uid, da duoc nhan chua)
#   bash scripts/zalo-allow.sh <khach.env> <uid> [uid..]  # them uid roi restart gateway
# uid lay tu danh sach tren (uid tuong doi theo tung nick phu: chi dung uid cua CHINH VPS nay).
# Nguoi bi bo qua phai nhan lai sau khi duoc them (tin cu khong xu ly lai).
set -euo pipefail
die() { echo "LOI: $*" >&2; exit 1; }
[ $# -ge 1 ] || die "Dung: bash scripts/zalo-allow.sh <khach.env> [uid ...]"
ENV_FILE="$1"; shift
[ -f "$ENV_FILE" ] || die "khong thay $ENV_FILE"
set -a; # shellcheck disable=SC1090
. "$ENV_FILE"; set +a
TARGET="${VPS_USER:-root}@$VPS_HOST"
SSH_OPTS=(-p "${VPS_PORT:-22}" -o StrictHostKeyChecking=accept-new -o ConnectTimeout=15 -o BatchMode=yes)
ssh "${SSH_OPTS[@]}" "$TARGET" true 2>/dev/null || die "chua vao duoc VPS bang key. Chay setup.sh truoc"

NEW="$(echo "$*" | tr -s ', ' '\n' | grep -E '^[0-9]+$' | paste -sd, - || true)"
[ $# -eq 0 ] || [ -n "$NEW" ] || die "uid phai la so"
ssh "${SSH_OPTS[@]}" "$TARGET" "NEW='$NEW' bash -s" <<'EOF'
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"; XDG_RUNTIME_DIR="/run/user/$(id -u)"; export XDG_RUNTIME_DIR
ENV="$HOME/.hermes/.env"; LOG="$HOME/.hermes/logs/gateway.log"
CUR="$(grep '^ZALO_ALLOWED_USERS=' "$ENV" | cut -d= -f2- || true)"
if [ -z "$NEW" ]; then
  echo "Dang duoc nhan bot: ${CUR:-(chua ai)}"
  echo "Nguoi vua nhan nick phu (moi nhat cuoi):"
  grep -h "Zalo inbound" "$LOG"* 2>/dev/null | tail -300 | python3 -c '
import re, sys
cur = set(sys.argv[1].split(",")) if sys.argv[1] else set()
seen = {}
for l in sys.stdin:
    m = re.search(r"^(\S+ \S+).*uid=(\d+) name=(.*?) threadId=(\d+) type=(\w+)", l)
    if m: seen[m.group(2)] = (m.group(1)[:16], m.group(3).strip("\x27\""), m.group(5))
for uid, (t, name, typ) in list(seen.items())[-20:]:
    ok = "DA DUOC NHAN" if uid in cur else "chua"
    print(f"  {t}  uid={uid}  {name}  ({typ})  {ok}")
if not seen: print("  (chua co ai nhan. Nho nguoi do nhan 1 tin vao nick phu, hoac @tag nick phu trong nhom)")
' "$CUR"
  exit 0
fi
IDS="$(echo "$CUR,$NEW" | tr -s ', ' '\n' | grep -E '^[0-9]+$' | awk '!s[$0]++' | paste -sd, -)"
if grep -q '^ZALO_ALLOWED_USERS=' "$ENV"; then sed -i "s|^ZALO_ALLOWED_USERS=.*|ZALO_ALLOWED_USERS=$IDS|" "$ENV"; else echo "ZALO_ALLOWED_USERS=$IDS" >>"$ENV"; fi
MARK=$(wc -l <"$LOG" 2>/dev/null || echo 0)
systemctl --user restart hermes-gateway
for _ in $(seq 1 20); do sleep 2; tail -n +"$((MARK+1))" "$LOG" | grep -q "Zalo: connected" && break; done
tail -n +"$((MARK+1))" "$LOG" | grep -q "Zalo: connected" || { echo "LOI: gateway chua noi lai Zalo"; exit 1; }
echo "XONG. Duoc nhan bot: $IDS (nho nguoi moi them nhan lai 1 tin)"
EOF
