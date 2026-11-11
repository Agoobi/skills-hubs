#!/usr/bin/env python3
"""Cai SSH key cua may nay len VPS bang paramiko (thay sshpass khi chay tren Windows).
Dung: py scripts/install-key.py <khach.env>
Doc VPS_HOST/VPS_USER/VPS_PORT/VPS_PASSWORD tu file env; khong in mat khau."""
import os, re, sys
import paramiko

def load(path):
    env = {}
    for line in open(path, encoding="utf-8"):
        m = re.match(r"^([A-Z_]+)=(.*)$", line.rstrip("\n"))
        if m:
            v = m.group(2).strip()
            if len(v) >= 2 and v[0] == v[-1] and v[0] in "'\"":
                v = v[1:-1]
            env[m.group(1)] = v
    return env

env = load(sys.argv[1])
pub_path = os.path.expanduser("~/.ssh/id_ed25519.pub")
if not os.path.exists(pub_path):
    sys.exit("LOI: chua co ~/.ssh/id_ed25519.pub (ssh-keygen -t ed25519)")
pub = open(pub_path).read().strip()
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    c.connect(env["VPS_HOST"], int(env.get("VPS_PORT") or 22), env.get("VPS_USER") or "root",
              env["VPS_PASSWORD"], look_for_keys=False, allow_agent=False, timeout=20)
except Exception as e:
    sys.exit(f"LOI: khong vao duoc VPS bang mat khau ({type(e).__name__}: {e})")
cmd = (f"mkdir -p ~/.ssh && chmod 700 ~/.ssh && touch ~/.ssh/authorized_keys && "
       f"(grep -qF '{pub}' ~/.ssh/authorized_keys || echo '{pub}' >> ~/.ssh/authorized_keys) && "
       f"chmod 600 ~/.ssh/authorized_keys && echo da-cai-key")
print(c.exec_command(cmd)[1].read().decode().strip())
