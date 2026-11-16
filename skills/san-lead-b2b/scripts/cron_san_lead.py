#!/usr/bin/env python3
"""Cron cua Hermes (--no-agent): chay 1 lan quet San lead, in bao cao (Hermes gui nguyen van vao kenh).

Cai: cp scripts/cron_san_lead.py ~/.hermes/scripts/san-lead.py
     hermes cron create "30 6 * * *" --name "San lead hang ngay" --script san-lead.py --no-agent --deliver coquifly
Tien do chi tiet ghi o <skill>/state/run-*.log.
"""
import glob
import os
import subprocess
import sys

HOME = os.path.expanduser("~/.hermes/skills")
found = sorted(glob.glob(os.path.join(HOME, "*", "san-lead-b2b", "scripts", "lead.py")) +
               glob.glob(os.path.join(HOME, "san-lead-b2b", "scripts", "lead.py")))
if not found:
    print("San lead: khong thay skill san-lead-b2b trong ~/.hermes/skills.")
    sys.exit(0)
lead = found[0]
result = subprocess.run([sys.executable, "-I", lead, "run", "--trigger", "cron", "--quiet"],
                        cwd=os.path.dirname(os.path.dirname(lead)), capture_output=True, text=True, timeout=3300)
out = (result.stdout or "").strip()
if result.returncode != 0 and not out:
    out = "San lead: lan quet loi. " + (result.stderr or "").strip()[-600:]
print(out)
