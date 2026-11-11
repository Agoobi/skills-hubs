# Chay TREN VPS (setup.sh day qua stdin ssh, noi tiep remote.sh). Chay lai an toan.
# Open WebUI -> API server cua Hermes (127.0.0.1:8642), co HTTPS qua Caddy tai <ip>.sslip.io.
# Bien vao: VPS_HOST (bat buoc), OPENWEBUI_DOMAIN (tuy chon, mac dinh <ip-gach-ngang>.sslip.io)
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
STATE="$HOME/.hermes/openwebui.env"          # mat khau admin + khoa, chmod 600
DOMAIN="${OPENWEBUI_DOMAIN:-$(echo "$VPS_HOST" | tr . -).sslip.io}"
PORT=3000
rand() { python3 -c 'import secrets;print(secrets.token_hex(int(__import__("sys").argv[1])))' "$1"; }

# --- 1. API server cua Hermes (chi nghe 127.0.0.1, co khoa) ---
ENVF="$(hermes config env-path)"
API_KEY="$(grep -E '^API_SERVER_KEY=' "$ENVF" 2>/dev/null | tail -1 | cut -d= -f2- || true)"
[ -n "$API_KEY" ] || API_KEY="$(rand 24)"
hermes config set API_SERVER_ENABLED true >/dev/null
hermes config set API_SERVER_KEY "$API_KEY" >/dev/null
systemctl --user restart hermes-gateway
for _ in $(seq 1 30); do
  curl -fsS http://127.0.0.1:8642/health >/dev/null 2>&1 && break; sleep 2
done
curl -fsS http://127.0.0.1:8642/health >/dev/null 2>&1 || { echo "LOI: API server Hermes khong len (cong 8642)"; exit 1; }
curl -fsS -H "Authorization: Bearer $API_KEY" http://127.0.0.1:8642/v1/models >/dev/null \
  || { echo "LOI: API server tu choi khoa"; exit 1; }
echo "  Hermes API server: OK (127.0.0.1:8642)"

# --- 2. Docker ---
if ! command -v docker >/dev/null; then
  echo "  Cai Docker (vai phut)..."
  curl -fsSL https://get.docker.com | sh >/tmp/docker-install.log 2>&1 \
    || { tail -20 /tmp/docker-install.log; echo "LOI: cai Docker that bai"; exit 1; }
fi
systemctl enable --now docker >/dev/null 2>&1 || true

# --- 3. Tai khoan admin + khoa phien (tao 1 lan, giu nguyen khi chay lai) ---
touch "$STATE"; chmod 600 "$STATE"
getst() { grep -E "^$1=" "$STATE" | tail -1 | cut -d= -f2- || true; }
ADMIN_EMAIL="$(getst ADMIN_EMAIL)";   [ -n "$ADMIN_EMAIL" ]  || ADMIN_EMAIL="admin@hermes.local"
ADMIN_PASS="$(getst ADMIN_PASSWORD)"; [ -n "$ADMIN_PASS" ]   || ADMIN_PASS="$(rand 12)"
SECRET="$(getst WEBUI_SECRET_KEY)";   [ -n "$SECRET" ]       || SECRET="$(rand 32)"
printf 'URL=https://%s\nADMIN_EMAIL=%s\nADMIN_PASSWORD=%s\nWEBUI_SECRET_KEY=%s\n' "$DOMAIN" "$ADMIN_EMAIL" "$ADMIN_PASS" "$SECRET" >"$STATE"

# --- 4. Open WebUI (host network, chi nghe 127.0.0.1; ENABLE_PERSISTENT_CONFIG=false: env luon thang DB) ---
docker pull -q ghcr.io/open-webui/open-webui:main >/dev/null
docker rm -f open-webui >/dev/null 2>&1 || true
docker run -d --name open-webui --restart always --network host \
  -e HOST=127.0.0.1 -e PORT="$PORT" \
  -e ENABLE_PERSISTENT_CONFIG=false \
  -e OPENAI_API_BASE_URL=http://127.0.0.1:8642/v1 -e OPENAI_API_KEY="$API_KEY" \
  -e ENABLE_OLLAMA_API=false -e ENABLE_SIGNUP=false \
  -e WEBUI_ADMIN_EMAIL="$ADMIN_EMAIL" -e WEBUI_ADMIN_PASSWORD="$ADMIN_PASS" -e WEBUI_ADMIN_NAME=Admin \
  -e WEBUI_SECRET_KEY="$SECRET" -e WEBUI_URL="https://$DOMAIN" \
  -v open-webui:/app/backend/data ghcr.io/open-webui/open-webui:main >/dev/null
echo "  Open WebUI: dang khoi dong (lan dau 1-2 phut)..."
for _ in $(seq 1 90); do
  curl -fsS "http://127.0.0.1:$PORT/health" >/dev/null 2>&1 && break; sleep 3
done
curl -fsS "http://127.0.0.1:$PORT/health" >/dev/null 2>&1 \
  || { docker logs --tail 20 open-webui; echo "LOI: Open WebUI khong len"; exit 1; }

# Dang nhap thu bang tai khoan admin -> chung minh tai khoan co that
curl -fsS "http://127.0.0.1:$PORT/api/v1/auths/signin" -H 'Content-Type: application/json' \
  -d "$(python3 -c 'import json,sys;print(json.dumps({"email":sys.argv[1],"password":sys.argv[2]}))' "$ADMIN_EMAIL" "$ADMIN_PASS")" >/dev/null \
  || { echo "LOI: khong dang nhap duoc admin Open WebUI (DB cu co admin khac? xoa volume: docker volume rm open-webui)"; exit 1; }

# --- 5. Caddy: HTTPS tu dong cho <ip>.sslip.io ---
mkdir -p "$HOME/.hermes/caddy"
cat >"$HOME/.hermes/caddy/Caddyfile" <<EOF
$DOMAIN {
	encode zstd gzip
	reverse_proxy 127.0.0.1:$PORT {
		flush_interval -1
	}
}
EOF
docker rm -f caddy >/dev/null 2>&1 || true
docker run -d --name caddy --restart always --network host \
  -v "$HOME/.hermes/caddy/Caddyfile:/etc/caddy/Caddyfile:ro" -v caddy_data:/data -v caddy_config:/config caddy:2 >/dev/null
for _ in $(seq 1 40); do
  curl -fsS -o /dev/null "https://$DOMAIN/health" 2>/dev/null && break; sleep 3
done
curl -fsS -o /dev/null "https://$DOMAIN/health" 2>/dev/null \
  || { docker logs --tail 15 caddy; echo "LOI: HTTPS chua len. Kiem tra cong 80/443 co mo o firewall nha cung cap VPS khong"; exit 1; }
echo "  Open WebUI: https://$DOMAIN (HTTPS OK). Tai khoan admin luu o ~/.hermes/openwebui.env tren VPS"
