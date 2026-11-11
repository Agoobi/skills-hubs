# Chay TREN VPS, do setup.sh day qua stdin cua ssh (bien bi mat da export phia tren).
# Chay lai nhieu lan van an toan: ghi de gia tri cu, khong nhan doi.
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
HUB_URL="https://github.com/Agoobi/skills-hubs"

if ! command -v hermes >/dev/null; then
  echo "  Cai Hermes Agent (vai phut)..."
  curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash -s -- --skip-setup >/tmp/hermes-install.log 2>&1 \
    || { tail -20 /tmp/hermes-install.log; echo "LOI: cai Hermes that bai"; exit 1; }
  export PATH="$HOME/.local/bin:$PATH"
fi
echo "  $(hermes --version | head -1)"

# --- .env: dat hoac thay tung khoa ---
ENV="$(hermes config env-path)"; touch "$ENV"; chmod 600 "$ENV"
setenv() {
  python3 - "$ENV" "$1" "$2" <<'PY'
import sys, re
path, key, val = sys.argv[1:]
lines = open(path).read().splitlines()
out, done = [], False
for l in lines:
    if re.match(rf"^{re.escape(key)}=", l):
        if not done: out.append(f"{key}={val}"); done = True
    else: out.append(l)
if not done: out.append(f"{key}={val}")
open(path, "w").write("\n".join(out) + "\n")
PY
}
setenv OPENROUTER_API_KEY "$OPENROUTER_API_KEY"
setenv TELEGRAM_BOT_TOKEN "$TELEGRAM_BOT_TOKEN"
setenv TELEGRAM_ALLOWED_USERS "$ALLOWED_IDS"
setenv TELEGRAM_HOME_CHANNEL "$HOME_CHANNEL"
[ -n "$ZERNIO_API_KEY" ] && setenv ZERNIO_API_KEY "$ZERNIO_API_KEY"

hermes config set model.provider openrouter >/dev/null
hermes config set model.default "$CHAT_MODEL" >/dev/null
hermes config set image_gen.provider openrouter >/dev/null
hermes config set image_gen.model "$IMAGE_MODEL" >/dev/null
echo "  Model chat: $CHAT_MODEL | Model anh: $IMAGE_MODEL"

# --- Telegram yen lang: khong nhan tung buoc/suy nghi, chi 1 tin ket qua ---
# Mac dinh Hermes gui "tin giua chung" + nhat ky tool nen khach thay bot nhan lien tuc khi dang think.
if [ "${TELEGRAM_QUIET:-1}" = "1" ]; then
  for kv in tool_progress=off interim_assistant_messages=false show_reasoning=false busy_ack_detail=false \
            suppress_warning_notifications=true cleanup_progress=true long_running_notifications=true; do
    hermes config set "display.platforms.telegram.${kv%%=*}" "${kv#*=}" >/dev/null
  done
  SOUL="$HOME/.hermes/SOUL.md"; touch "$SOUL"
  grep -q "MOC-IM-LANG" "$SOUL" || printf '\n\n<!-- MOC-IM-LANG -->\nTrên Telegram: làm xong rồi mới nhắn một lần. Không nhắn từng bước, không kể quá trình suy nghĩ, không báo "đang làm". Việc dài thì cứ làm, hệ thống tự hiện trạng thái chờ.\n' >>"$SOUL"
  echo "  Telegram: che do yen lang (1 tin ket qua, tien do gom 1 bong bong tu xoa)"
fi

# --- Skill tu hub ---
HUB="$HOME/.hermes/skills-hub-src"
if [ -d "$HUB/.git" ]; then git -C "$HUB" pull -q --ff-only; else git clone -q --depth 1 "$HUB_URL" "$HUB"; fi
for id in $(echo "$SKILLS" | tr ',' ' '); do
  src="$HUB/skills/$id"; [ -f "$src/SKILL.md" ] || { echo "  BO QUA: hub khong co skill $id"; continue; }
  cat="$(python3 -I -c 'import json,sys;m=json.load(open(sys.argv[1]));print(next((s["category"] for s in m["skills"] if s["id"]==sys.argv[2]),"hub"))' "$HUB/manifest.json" "$id")"
  dst="$HOME/.hermes/skills/$cat/$id"; mkdir -p "$dst"
  # Giu settings.json cu cua khach khi cap nhat skill
  tar -C "$src" --exclude=settings.json -cf - . | tar -C "$dst" -xf -
  [ -f "$dst/settings.example.json" ] && [ ! -f "$dst/settings.json" ] && cp "$dst/settings.example.json" "$dst/settings.json"
  [ -f "$dst/settings.json" ] && chmod 600 "$dst/settings.json"
  echo "  Skill: $id -> $dst"
done

# --- Rieng skill quang cao: dung Zernio, key doc tu env, tu dien tai khoan ---
ADS="$(ls -d "$HOME"/.hermes/skills/*/chay-quang-cao-facebook 2>/dev/null | head -1 || true)"
if [ -n "$ADS" ] && [ -n "$ZERNIO_API_KEY" ]; then
  python3 -I - "$ADS/settings.json" <<'PY'
import json, sys
p = sys.argv[1]; s = json.load(open(p))
s["execution"] = "zernio"
s.setdefault("zernio", {})["api_key"] = ""          # key nam trong ~/.hermes/.env
for k in ("access_token", "business_id"):
    if str(s.get("meta", {}).get(k, "")).startswith(("DAN_", "ID_")): s["meta"][k] = ""
json.dump(s, open(p, "w"), ensure_ascii=False, indent=2)
PY
  ( cd "$ADS" && python3 -I scripts/meta_ads.py check >/tmp/ads-check.json 2>&1 ) \
    || { cat /tmp/ads-check.json; echo "LOI: Zernio check that bai"; exit 1; }
  ( cd "$ADS" && python3 -I scripts/meta_ads.py accounts --write >/tmp/ads-acc.json 2>&1 ) || cat /tmp/ads-acc.json
  python3 -I - "$ADS/settings.json" /tmp/ads-acc.json <<'PY'
import json, sys
p, acc = sys.argv[1:]; s = json.load(open(p))
try: accs = json.load(open(acc)).get("ad_accounts", [])
except Exception: accs = []
m = s.setdefault("meta", {})
if len(accs) == 1: m["default_ad_account"] = accs[0]["id"]
elif str(m.get("default_ad_account", "")).startswith("act_ID"): m["default_ad_account"] = ""
json.dump(s, open(p, "w"), ensure_ascii=False, indent=2)
print(f"  Zernio: {len(accs)} tai khoan quang cao")
for a in accs:
    st = "ACTIVE" if a.get("account_status") == 1 else a.get("account_status")
    print(f"    - {a.get('name')} ({a['id']}) {a.get('currency')} {st}, the: {'co' if a.get('has_payment_method') else 'CHUA'}")
if len(accs) != 1: print("  -> Nhieu/khong co tai khoan: chua dat mac dinh, bot se hoi.")
PY
  rm -f /tmp/ads-check.json /tmp/ads-acc.json
fi

# --- Gateway Telegram chay nen bang systemd ---
# `hermes chat` tu bat mot gateway tam (--idle-exit); no giu lock va chan service. Dung no truoc.
pkill -f "gateway run --quiet --idle-exit" 2>/dev/null && sleep 3 || true
hermes gateway install >/tmp/gw-install.log 2>&1 || { tail -20 /tmp/gw-install.log; exit 1; }
pkill -f "gateway run --quiet --idle-exit" 2>/dev/null && sleep 3 || true
LOG="$HOME/.hermes/logs/gateway.log"; MARK=$(wc -l 2>/dev/null <"$LOG" || echo 0)
systemctl --user restart hermes-gateway
for _ in $(seq 1 30); do
  sleep 2
  tail -n +"$((MARK+1))" "$LOG" 2>/dev/null | grep -q "telegram connected" && break
done
systemctl --user is-active --quiet hermes-gateway || { systemctl --user status hermes-gateway --no-pager | head; echo "LOI: gateway khong chay"; exit 1; }
if tail -n +"$((MARK+1))" "$LOG" | grep -q "telegram connected"; then
  echo "  Gateway: chay nen (systemd, song sau reboot/logout), Telegram da ket noi"
else
  tail -n +"$((MARK+1))" "$LOG" | grep -iE "error|conflict|telegram" | tail -8
  echo "LOI: gateway chay nhung Telegram chua ket noi (token dang dung o noi khac?)"; exit 1
fi
if tail -n +"$((MARK+1))" "$LOG" | grep -qi "conflict"; then
  echo "CANH BAO: Telegram bao Conflict - bot nay dang chay o may khac. Moi VPS phai dung bot rieng."
fi
