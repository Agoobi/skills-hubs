#!/usr/bin/env python3
"""Cham chatbot bang bo cau hoi: gui tung cau qua webchat (nhu khach that), kiem tra cau tra loi.

    python3 scripts/eval.py --profile shop-a                          # bo mac dinh templates/cau-hoi-mau.json
    python3 scripts/eval.py --profile shop-a --cases my-cases.json   # them cau hoi rieng cua shop

File cau hoi: [{"hoi": "...", "phai_co": ["1.500.000"], "khong_duoc_co": ["Hermes"], "loai": "tai_lieu"}]
- phai_co: moi chuoi phai xuat hien (khong phan biet hoa thuong, bo dau). Dung cho gia/chinh sach trong tai lieu.
- khong_duoc_co: khong chuoi nao duoc xuat hien. Dung cho cau ngoai tai lieu / tan cong.
Moi cau dung 1 khach moi (vid moi) de khong dinh ngu canh. Ket qua: JSON + ty le dat.
"""
import argparse, json, os, sys, time, unicodedata, urllib.request
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def fold(s):
    s = unicodedata.normalize("NFD", str(s).lower().replace("đ", "d"))
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def http(method, url, body=None, headers=None, timeout=40):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data, method=method, headers={"Content-Type": "application/json", **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read() or b"{}")


def ask(base, origin, question, i, wait):
    vid = f"eval{int(time.time())}x{i:03d}"
    h = {"Origin": origin}
    seq = http("POST", base + "/api/chat", {"vid": vid, "text": question}, h)["seq"]
    t0 = time.time()
    while time.time() - t0 < wait:
        r = http("GET", f"{base}/api/messages?vid={vid}&after={seq}&typing=1", headers=h)
        if r.get("messages"):
            time.sleep(1.5)  # gom phan tra loi bi tach nhieu tin
            more = http("GET", f"{base}/api/messages?vid={vid}&after={seq}&typing=0", headers=h, timeout=5)
            return "\n".join(m["text"] for m in (more.get("messages") or r["messages"]))
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--profile")
    ap.add_argument("--hermes-home")
    ap.add_argument("--cases", action="append", help="File JSON cau hoi (lap lai duoc). Mac dinh: templates/cau-hoi-mau.json")
    ap.add_argument("--wait", type=int, default=120, help="So giay toi da cho moi cau")
    a = ap.parse_args()
    if a.hermes_home:
        home = Path(a.hermes_home).expanduser()
    else:
        base_home = Path(os.environ.get("HERMES_HOME") or Path.home() / ".hermes").expanduser()
        home = base_home / "profiles" / a.profile if a.profile and a.profile != "default" else base_home
    s = json.loads((home / "chatbot" / "settings.json").read_text(encoding="utf-8"))
    wc = s.get("webchat") or {}
    base = f"http://{(wc.get('host') or '127.0.0.1').replace('0.0.0.0', '127.0.0.1')}:{wc.get('port') or 8650}"
    origin = (wc.get("allowed_origins") or [""])[0]

    cases = []
    for f in a.cases or [str(SKILL / "templates" / "cau-hoi-mau.json")]:
        cases += json.loads(Path(f).read_text(encoding="utf-8"))
    results = []
    for i, c in enumerate(cases):
        try:
            ans = ask(base, origin, c["hoi"], i, a.wait)
        except OSError as e:
            ans, err = None, str(e)
        else:
            err = None if ans is not None else "khong tra loi"
        fa = fold(ans or "")
        thieu = [x for x in c.get("phai_co", []) if fold(x) not in fa]
        sai = [x for x in c.get("khong_duoc_co", []) if fold(x) in fa]
        ok = ans is not None and not thieu and not sai
        results.append({"ok": ok, "loai": c.get("loai", ""), "hoi": c["hoi"], "tra_loi": ans, "loi": err,
                        "thieu": thieu, "khong_duoc_co": sai})
        print(("DAT " if ok else "TRUOT ") + c["hoi"][:70], file=sys.stderr)
    passed = sum(r["ok"] for r in results)
    print(json.dumps({"dat": passed, "tong": len(results), "ty_le": round(passed / max(1, len(results)), 3),
                      "truot": [r for r in results if not r["ok"]], "tat_ca": results}, ensure_ascii=False, indent=2))
    sys.exit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()
