#!/usr/bin/env python3
"""Cong cu CHI DOC cho skill chay-quang-cao-facebook. Chi dung thu vien chuan.

Lenh: check | accounts | report | watch
Hai duong thuc thi (settings.json > execution):
  bm     -> Graph / Marketing API bang system-user token (FACEBOOK_ACCESS_TOKEN)
  zernio -> Zernio REST (ZERNIO_API_KEY); insights tra nguyen dong cua Meta
KHONG co lenh tao/sua/bat quang cao: viec do lam theo cac Gate trong SKILL.md.
Ket qua in ra JSON de agent doc (watch --mode alert in van ban de gui thang).
"""
import argparse, json, os, sys, time, urllib.parse, urllib.request, urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
SETTINGS = SKILL / "settings.json"
UA = "agoobi-ads-skill/0.1 (https://github.com/Agoobi/skills-hubs)"
GRAPH = "https://graph.facebook.com"
ZERNIO = "https://zernio.com/api/v1"
# Ma loi gioi han tan suat: cho roi thu lai. Loi khac (du lieu sai, quyen, token) khong thu lai.
THROTTLE = {4, 17, 32, 613, 80000, 80001, 80002, 80003, 80004, 80005, 80006, 80008, 80009, 80014}
BACKOFF = [5, 20, 60, 180]
# Tien te khong co don vi phu: ngan sach Graph API tinh thang bang don vi chinh.
ZERO_DECIMAL = {"CLP", "COP", "CRC", "HUF", "ISK", "IDR", "JPY", "KRW", "PYG", "TWD", "VND"}
ACCOUNT_STATUS = {1: "ACTIVE", 2: "DISABLED", 3: "UNSETTLED (nợ chưa thanh toán)", 7: "PENDING_RISK_REVIEW",
                  8: "PENDING_SETTLEMENT", 9: "IN_GRACE_PERIOD", 100: "PENDING_CLOSURE", 101: "CLOSED"}
INSIGHT_FIELDS = ("campaign_id,campaign_name,adset_id,adset_name,ad_id,ad_name,objective,optimization_goal,spend,"
                  "impressions,reach,frequency,inline_link_clicks,actions,date_start,date_stop")
# Moi loai ket qua: cac action_type Meta tra ve cho CUNG mot su kien, theo thu tu uu tien.
# Chi lay MOT khoa; cong nhieu khoa = dem trung.
RESULT_KEYS = {
    "purchase": ["offsite_conversion.fb_pixel_purchase", "omni_purchase", "purchase", "onsite_web_purchase"],
    "complete_registration": ["offsite_conversion.fb_pixel_complete_registration", "omni_complete_registration",
                              "complete_registration"],
    "lead": ["offsite_conversion.fb_pixel_lead", "onsite_conversion.lead_grouped", "leadgen_grouped", "lead"],
    "messaging": ["onsite_conversion.messaging_conversation_started_7d"],
    "post_engagement": ["post_engagement"],
    "landing_page_view": ["landing_page_view", "omni_landing_page_view"],
    "link_click": ["link_click"],
}
# optimization_goal cua ad set noi ro ket qua; o cap campaign Meta co the tra "Unknown" -> doan theo objective.
AUTO_BY_GOAL = {
    "POST_ENGAGEMENT": ["post_engagement"],
    "REPLIES": ["messaging"],
    "CONVERSATIONS": ["messaging"],
    "LEAD_GENERATION": ["lead"],
    "QUALITY_LEAD": ["lead"],
    "LANDING_PAGE_VIEWS": ["landing_page_view"],
    "LINK_CLICKS": ["link_click"],
}
AUTO_BY_OBJECTIVE = {
    "OUTCOME_SALES": ["purchase", "complete_registration", "lead"],
    "OUTCOME_LEADS": ["lead", "complete_registration"],
    "OUTCOME_ENGAGEMENT": ["messaging", "post_engagement"],
    "OUTCOME_TRAFFIC": ["landing_page_view", "link_click"],
}

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def out(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def die(msg, code=1):
    out({"ok": False, "error": msg})
    sys.exit(code)


def load():
    if SETTINGS.exists():
        return json.loads(SETTINGS.read_text(encoding="utf-8"))
    return {}


def save(cfg):
    SETTINGS.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def ratio(a, b, mult=1.0):
    return round(a / b * mult, 2) if a is not None and b else None


class Api:
    """Goi HTTP GET co retry khi bi gioi han tan suat. Khong bao gio in token."""

    def __init__(self, cfg, mode):
        self.mode = mode
        if mode == "bm":
            m = cfg.get("meta", {})
            self.secret = os.environ.get("FACEBOOK_ACCESS_TOKEN") or m.get("access_token", "")
            self.version = os.environ.get("META_GRAPH_VERSION") or m.get("graph_version", "v21.0")
            if not self.secret or "DAN_TOKEN" in self.secret:
                die("Thieu token BM. Dat env FACEBOOK_ACCESS_TOKEN hoac settings.json > meta.access_token.")
        else:
            z = cfg.get("zernio", {})
            self.secret = os.environ.get("ZERNIO_API_KEY") or z.get("api_key", "")
            self.base = z.get("base_url", ZERNIO).rstrip("/")
            if not self.secret.startswith("sk_") or "DAN_KEY" in self.secret:
                die("Thieu API key Zernio (sk_...). Dat env ZERNIO_API_KEY hoac settings.json > zernio.api_key.")

    def clean(self, text):
        return str(text).replace(self.secret, "***")

    def url(self, path, params):
        params = {k: v for k, v in params.items() if v is not None}
        if self.mode == "bm":
            params["access_token"] = self.secret
            return f"{GRAPH}/{self.version}/{path.lstrip('/')}?" + urllib.parse.urlencode(params)
        return f"{self.base}/{path.lstrip('/')}?" + urllib.parse.urlencode(params)

    def get(self, path, soft=False, **params):
        return self.fetch(self.url(path, params), soft)

    def fetch(self, url, soft=False):
        headers = {"User-Agent": UA}
        if self.mode == "zernio":
            headers["Authorization"] = f"Bearer {self.secret}"
        for attempt in range(len(BACKOFF) + 1):
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=120) as r:
                    return json.loads(r.read() or b"{}")
            except urllib.error.HTTPError as e:
                body = e.read().decode(errors="replace")
                try:
                    err = json.loads(body)
                except ValueError:
                    err = {}
                wait = self.wait_for(e, err, attempt)
                if wait is not None and attempt < len(BACKOFF):
                    time.sleep(wait)
                    continue
                msg = self.clean(f"HTTP {e.code} {url.split('?')[0]}: {body[:500]}")
                if soft:
                    return {"_error": msg}
                die(msg)
            except urllib.error.URLError as e:
                if attempt < len(BACKOFF):
                    time.sleep(BACKOFF[attempt])
                    continue
                die(self.clean(f"Loi mang {url.split('?')[0]}: {e.reason}"))
        die("Het so lan thu lai.")

    def wait_for(self, e, err, attempt):
        """So giay can cho neu la loi gioi han tan suat, None neu khong nen thu lai."""
        if self.mode == "zernio":
            if e.code != 429:
                return None
            return num(e.headers.get("Retry-After")) or BACKOFF[min(attempt, len(BACKOFF) - 1)]
        code = (err.get("error") or {}).get("code")
        if code not in THROTTLE:
            return None
        try:
            usage = json.loads(e.headers.get("X-Business-Use-Case-Usage") or "{}")
            mins = max(b.get("estimated_time_to_regain_access", 0) for v in usage.values() for b in v)
            if mins:
                return min(mins * 60, 900)
        except (ValueError, TypeError):
            pass
        return BACKOFF[min(attempt, len(BACKOFF) - 1)]

    def pages(self, path, **params):
        """Doc het cac trang ket qua (BM: paging.next; Zernio: paging.after)."""
        rows, d = [], self.get(path, **params)
        while True:
            rows += d.get("data", [])
            paging = d.get("paging") or {}
            if self.mode == "bm" and paging.get("next"):
                d = self.fetch(paging["next"])
            elif self.mode == "zernio" and paging.get("after"):
                d = self.get(path, after=paging["after"], **params)
            else:
                return rows


def mode_of(cfg, args):
    m = getattr(args, "via", None) or cfg.get("execution", "bm")
    if m not in ("bm", "zernio"):
        die("execution phai la 'bm' hoac 'zernio'.")
    return m


def zernio_meta_accounts(api):
    accts = api.get("accounts").get("accounts", [])
    return [a for a in accts if a.get("platform") == "metaads"]


# ---------- check ----------
def cmd_check(cfg, args):
    mode = mode_of(cfg, args)
    api = Api(cfg, mode)
    if mode == "bm":
        dbg = api.get("debug_token", input_token=api.secret).get("data", {})
        perms = api.get("me/permissions", soft=True)
        granted = sorted(p["permission"] for p in perms.get("data", []) if p.get("status") == "granted")
        need = {"ads_management", "ads_read", "business_management"}
        out({"ok": bool(dbg.get("is_valid")), "via": "bm", "graph_version": api.version,
             "type": dbg.get("type"), "app_id": dbg.get("app_id"),
             "expires_at": dbg.get("expires_at"), "never_expires": dbg.get("expires_at") == 0,
             "scopes": dbg.get("scopes") or granted, "missing_core_scopes": sorted(need - set(dbg.get("scopes") or granted)),
             "permissions_error": perms.get("_error")})
        return
    health = api.get("accounts/health")
    metas = [a for a in health.get("accounts", []) if a.get("platform") == "metaads"]
    out({"ok": bool(metas), "via": "zernio", "summary": health.get("summary"),
         "meta_ads_connections": [{k: a.get(k) for k in ("accountId", "displayName", "status", "canFetch",
                                                         "needsReconnect")} for a in metas],
         "hint": None if metas else "Chua ket noi tai khoan Meta Ads (metaads) trong Zernio."})


# ---------- accounts ----------
def cmd_accounts(cfg, args):
    mode = mode_of(cfg, args)
    api = Api(cfg, mode)
    found, pages, notes = {}, {}, []
    if mode == "bm":
        fields = "id,name,account_status,currency,timezone_name,business{id,name},funding_source_details,min_daily_budget"
        biz = cfg.get("meta", {}).get("business_id") or os.environ.get("META_BUSINESS_ID")
        sources = [("me/adaccounts", "me")]
        if biz:
            sources += [(f"{biz}/owned_ad_accounts", "owned"), (f"{biz}/client_ad_accounts", "client")]
        else:
            notes.append("Chua co meta.business_id: chi doc duoc /me/adaccounts, co the thieu tai khoan.")
        for path, src in sources:
            d = api.get(path, soft=True, fields=fields, limit=200)
            if "_error" in d:
                notes.append(f"{path}: {d['_error']}")
            for a in d.get("data", []):
                row = found.setdefault(a["id"], {"id": a["id"], "name": a.get("name"), "currency": a.get("currency"),
                                                 "timezone": a.get("timezone_name"),
                                                 "account_status": a.get("account_status"),
                                                 "business": (a.get("business") or {}).get("name"),
                                                 "has_payment_method": bool(a.get("funding_source_details")),
                                                 "min_daily_budget": a.get("min_daily_budget"), "sources": []})
                row["sources"].append(src)
        for path in ([f"{biz}/owned_pages"] if biz else []) + ["me/accounts"]:
            d = api.get(path, soft=True, fields="id,name", limit=200)
            for p in d.get("data", []):
                pages[p["id"]] = p.get("name")
    else:
        for conn in zernio_meta_accounts(api):
            d = api.get("ads/accounts", soft=True, accountId=conn["_id"])
            if "_error" in d:
                notes.append(d["_error"])
            for a in d.get("accounts", []):
                found[a["id"]] = {"id": a["id"], "name": a.get("name"), "currency": a.get("currency"),
                                  "timezone": a.get("timezoneName"), "account_status": a.get("accountStatus"),
                                  "business": a.get("businessName"),
                                  "has_payment_method": a.get("billingStatus") == "ok",
                                  "min_daily_budget": a.get("minimumDailyBudget"), "selectable": a.get("selectable"),
                                  "zernio_account_id": conn["_id"], "sources": ["zernio"]}
        notes.append("Zernio chi thay tai khoan nam trong lua chon cua ket noi; token BM co the thay nhieu hon.")
    accounts = sorted(found.values(), key=lambda a: a["id"])
    if args.write:
        cfg.setdefault("meta", {})["ad_accounts"] = [{k: a.get(k) for k in ("id", "name", "currency", "timezone",
                                                                             "zernio_account_id") if a.get(k)}
                                                     for a in accounts]
        if pages:
            cfg.setdefault("pages", {})
            known = {p.get("page_id") for p in cfg["pages"].values()}
            for pid, name in pages.items():
                if pid not in known:
                    cfg["pages"][f"page-{pid[-4:]}"] = {"page_id": pid, "label": name}
        save(cfg)
    out({"ok": True, "via": mode, "ad_accounts": accounts, "pages": pages, "notes": notes, "written": bool(args.write)})


# ---------- report ----------
def pick_result(row, result, action):
    """Chon DUNG MOT action_type lam ket qua. Tra (khoa, gia tri, cac khoa trung bi bo qua)."""
    acts = {a["action_type"]: num(a.get("value")) for a in row.get("actions") or []}
    if action:
        return action, acts.get(action), []
    kinds = [result] if result else (AUTO_BY_GOAL.get(row.get("optimization_goal"))
                                     or AUTO_BY_OBJECTIVE.get(row.get("objective"), []))
    for kind in kinds:
        keys = [k for k in RESULT_KEYS[kind] if k in acts]
        if keys:
            dup = [k for k in keys[1:] if acts[k] == acts[keys[0]]]
            return keys[0], acts[keys[0]], dup
    return None, None, []


def insight_rows(api, cfg, account, level, preset, since, until, fields=INSIGHT_FIELDS):
    if api.mode == "bm":
        p = {"level": level, "fields": fields, "limit": 500}
        p.update({"time_range": json.dumps({"since": since, "until": until})} if since else {"date_preset": preset})
        return api.pages(f"{account}/insights", **p)
    conn = zernio_conn_for(api, cfg, account)
    p = {"accountId": conn, "objectId": account, "level": level, "fields": fields, "limit": 500}
    p.update({"fromDate": since, "toDate": until} if since else {"datePreset": preset})
    return api.pages("ads/insights", **p)


def zernio_conn_for(api, cfg, account):
    for a in cfg.get("meta", {}).get("ad_accounts", []):
        if a.get("id") == account and a.get("zernio_account_id"):
            return a["zernio_account_id"]
    conns = zernio_meta_accounts(api)
    if len(conns) == 1:
        return conns[0]["_id"]
    die("Khong biet ket noi Zernio nao chua tai khoan nay. Chay 'accounts --write' truoc.")


def summarize(row, result, action):
    spend, imp = num(row.get("spend")) or 0.0, num(row.get("impressions"))
    reach, clicks = num(row.get("reach")), num(row.get("inline_link_clicks"))
    key, val, dup = pick_result(row, result, action)
    return {"campaign": row.get("campaign_name"), "campaign_id": row.get("campaign_id"),
            "adset": row.get("adset_name"), "adset_id": row.get("adset_id"),
            "ad": row.get("ad_name"), "ad_id": row.get("ad_id"), "objective": row.get("objective"),
            "optimization_goal": row.get("optimization_goal"),
            "spend": spend, "impressions": imp, "reach": reach,
            "frequency": ratio(imp, reach), "cpm": ratio(spend, imp, 1000),
            "link_clicks": clicks, "link_ctr_pct": ratio(clicks, imp, 100), "link_cpc": ratio(spend, clicks),
            "result_key": key, "results": val, "cost_per_result": ratio(spend, val),
            "duplicate_keys_ignored": dup, "period": f"{row.get('date_start')}..{row.get('date_stop')}"}


def cmd_report(cfg, args):
    api = Api(cfg, mode_of(cfg, args))
    account = args.account or cfg.get("meta", {}).get("default_ad_account")
    if not account:
        die("Can --account act_<id> (hoac settings.json > meta.default_ad_account).")
    account = account if account.startswith("act_") else "act_" + account
    rows = insight_rows(api, cfg, account, args.level, args.preset, args.since, args.until)
    items = [summarize(r, args.result, args.action) for r in rows]
    for it in items:
        for k in ("adset", "adset_id", "ad", "ad_id"):
            if it[k] is None:
                it.pop(k)
    total_spend = round(sum(i["spend"] for i in items), 2)
    out({"ok": True, "via": api.mode, "account": account, "level": args.level,
         "period": items[0]["period"] if items else None, "rows": items,
         "total_spend_this_level": total_spend,
         "notes": ["Reach khong cong duoc giua cac dong.",
                   "cost_per_result = spend / ket qua cua MOT action_type; N/A (null) khi 0 ket qua.",
                   "Khong cong so lieu giua cac cap campaign/adset/ad."]})


# ---------- watch ----------
def local_now(tz_name, cfg):
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo(tz_name or cfg.get("timezone", "Asia/Ho_Chi_Minh")))
    except Exception:
        return datetime.now(timezone(timedelta(hours=cfg.get("utc_offset_hours", 7))))


def live_structure(api, cfg, account, currency):
    """Campaign + ad set dang chay, ngan sach ngay quy ve don vi tien chinh."""
    if api.mode == "bm":
        div = 1 if currency in ZERO_DECIMAL else 100
        flt = json.dumps([{"field": "effective_status", "operator": "IN", "value": ["ACTIVE"]}])
        camps = api.pages(f"{account}/campaigns", fields="id,name,objective,daily_budget", filtering=flt, limit=200)
        sets = api.pages(f"{account}/adsets", fields="id,campaign_id,daily_budget", filtering=flt, limit=500)
        cb = {c["id"]: (num(c.get("daily_budget")) or 0) / div for c in camps}
        sb = [(s["campaign_id"], (num(s.get("daily_budget")) or 0) / div) for s in sets]
    else:
        d = api.get("ads/accounts/live", accountId=zernio_conn_for(api, cfg, account), adAccountId=account,
                    status="ACTIVE")
        cb = {c["platformCampaignId"]: c.get("dailyBudget") or 0 for c in d.get("campaigns", [])
              if c.get("platformCampaignStatus") == "ACTIVE"}
        sb = [(s.get("platformCampaignId"), s.get("dailyBudget") or 0) for s in d.get("adSets", [])]
    budget = dict(cb)
    for cid, b in sb:
        if cid in budget and not cb.get(cid):
            budget[cid] = budget.get(cid, 0) + b
    return budget


def account_info(api, cfg, account):
    if api.mode == "bm":
        a = api.get(account, fields="name,currency,timezone_name,account_status,funding_source_details")
        return {"name": a.get("name"), "currency": a.get("currency"), "tz": a.get("timezone_name"),
                "status": a.get("account_status"), "payment": bool(a.get("funding_source_details"))}
    d = api.get("ads/accounts", accountId=zernio_conn_for(api, cfg, account), adAccountId=account)
    a = (d.get("accounts") or [{}])[0]
    return {"name": a.get("name"), "currency": a.get("currency"), "tz": a.get("timezoneName"),
            "status": a.get("accountStatus"), "payment": a.get("billingStatus") == "ok"}


def threshold_for(alerts, objective):
    t = alerts.get("thresholds", {})
    return t.get(objective) or t.get("default") or {}


def check_campaign(c, budget, now, alerts):
    issues, name = [], f"{c['campaign']} ({c['campaign_id']})"
    if budget and c["spend"] > budget * (1 + alerts.get("overspend_pct", 25) / 100):
        issues.append(f"Chi {c['spend']:,.0f} vượt ngân sách ngày {budget:,.0f} hơn {alerts.get('overspend_pct', 25)}%: {name}")
    if not c["impressions"] and now.hour >= alerts.get("no_delivery_after_hour", 8):
        issues.append(f"Đang ACTIVE nhưng 0 hiển thị hôm nay: {name}")
    elif budget and now.hour >= alerts.get("slow_after_hour", 20) and \
            c["spend"] < budget * alerts.get("slow_spend_pct", 50) / 100:
        issues.append(f"Tiêu chậm: mới {c['spend']:,.0f}/{budget:,.0f} lúc {now:%H:%M}: {name}")
    t = threshold_for(alerts, c["objective"])
    if c["spend"] >= alerts.get("min_spend_to_judge", 0):
        if t.get("max_cost_per_result") is not None:
            cpr = c["cost_per_result"]
            if cpr is None and c["spend"] >= t["max_cost_per_result"]:
                issues.append(f"Đã chi {c['spend']:,.0f} mà 0 kết quả ({c['result_key'] or 'chưa xác định'}): {name}")
            elif cpr is not None and cpr > t["max_cost_per_result"]:
                issues.append(f"Chi phí/kết quả {cpr:,.0f} > ngưỡng {t['max_cost_per_result']:,.0f} ({c['result_key']}): {name}")
        if t.get("max_cpc") is not None and c["link_cpc"] is not None and c["link_cpc"] > t["max_cpc"]:
            issues.append(f"CPC link {c['link_cpc']:,.0f} > ngưỡng {t['max_cpc']:,.0f}: {name}")
        if t.get("min_ctr_pct") is not None and c["link_ctr_pct"] is not None and c["link_ctr_pct"] < t["min_ctr_pct"]:
            issues.append(f"CTR link {c['link_ctr_pct']}% < ngưỡng {t['min_ctr_pct']}%: {name}")
    return issues


def cmd_watch(cfg, args):
    api = Api(cfg, mode_of(cfg, args))
    alerts = cfg.get("alerts", {})
    if args.account:
        accounts = [args.account if args.account.startswith("act_") else "act_" + args.account]
    else:
        accounts = [a["id"] for a in cfg.get("meta", {}).get("ad_accounts", [])]
    if not accounts:
        die("Chua co danh sach tai khoan. Chay 'accounts --write' truoc hoac truyen --account.")
    report, lines = [], []
    for account in accounts:
        info = account_info(api, cfg, account)
        now = local_now(info["tz"], cfg)
        acc_issues = []
        if info["status"] not in (1, None):
            state = ACCOUNT_STATUS.get(info["status"], info["status"])
            acc_issues.append(f"Tài khoản {info['name']} ({account}) không ACTIVE (trạng thái {state}).")
        budgets = live_structure(api, cfg, account, info["currency"])
        if not budgets:
            # Tai khoan khong co camp chay: chi ghi vao digest, khong ban canh bao.
            report.append({"account": account, "name": info["name"], "active_campaigns": 0, "issues": acc_issues})
            continue
        if not info["payment"]:
            acc_issues.append(f"Tài khoản {info['name']} ({account}) chưa có phương thức thanh toán nhưng có camp ACTIVE.")
        rows = [summarize(r, None, None) for r in insight_rows(api, cfg, account, "campaign", "today", None, None)]
        by_id = {r["campaign_id"]: r for r in rows}
        camps = []
        for cid, budget in budgets.items():
            c = by_id.get(cid) or {"campaign": cid, "campaign_id": cid, "objective": None, "spend": 0.0,
                                   "impressions": 0, "link_cpc": None, "link_ctr_pct": None,
                                   "cost_per_result": None, "result_key": None, "results": None}
            issues = check_campaign(c, budget, now, alerts)
            acc_issues += issues
            camps.append({"campaign": c["campaign"], "campaign_id": cid, "objective": c["objective"],
                          "daily_budget": budget, "spend_today": c["spend"], "results": c["results"],
                          "result_key": c["result_key"], "cost_per_result": c["cost_per_result"],
                          "link_ctr_pct": c["link_ctr_pct"], "link_cpc": c["link_cpc"]})
        lines += [f"[{info['name']}] {i}" for i in acc_issues]
        report.append({"account": account, "name": info["name"], "currency": info["currency"],
                       "local_time": now.strftime("%Y-%m-%d %H:%M"), "active_campaigns": len(camps),
                       "campaigns": camps, "issues": acc_issues})
    if args.mode == "alert":
        if lines:
            print("⚠️ Cảnh báo quảng cáo Meta\n" + "\n".join(f"• {l}" for l in lines))
        return
    out({"ok": True, "via": api.mode, "accounts": report, "issue_count": len(lines)})


def main():
    ap = argparse.ArgumentParser(description="Doc so lieu quang cao Meta (chi doc).")
    ap.add_argument("--via", choices=["bm", "zernio"], help="Ghi de settings.json > execution")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check", help="Kiem tra token/ket noi va quyen")
    p = sub.add_parser("accounts", help="Liet ke MOI tai khoan quang cao va Page")
    p.add_argument("--write", action="store_true", help="Ghi danh sach vao settings.json")
    p = sub.add_parser("report", help="Bao cao 1 cap, khu trung action_type")
    p.add_argument("--account")
    p.add_argument("--level", choices=["campaign", "adset", "ad"], default="campaign")
    p.add_argument("--preset", default="last_7d", help="today, yesterday, last_7d, last_30d, maximum, ...")
    p.add_argument("--since")
    p.add_argument("--until")
    p.add_argument("--result", choices=sorted(RESULT_KEYS), help="Loai ket qua; bo trong = tu chon theo objective")
    p.add_argument("--action", help="Chi dinh dung mot action_type lam ket qua")
    p = sub.add_parser("watch", help="Quet camp dang chay theo nguong settings.json > alerts")
    p.add_argument("--account")
    p.add_argument("--mode", choices=["alert", "digest"], default="digest")
    args = ap.parse_args()
    if args.cmd == "report" and bool(args.since) != bool(args.until):
        die("--since va --until phai di cung nhau.")
    cfg = load()
    {"check": cmd_check, "accounts": cmd_accounts, "report": cmd_report, "watch": cmd_watch}[args.cmd](cfg, args)


if __name__ == "__main__":
    main()
