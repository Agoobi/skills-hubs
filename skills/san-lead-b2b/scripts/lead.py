#!/usr/bin/env python3
"""San lead B2B cho Hermes: quet tin hieu mua thiet bi, doc tin bang LLM, tim nguoi ra quyet dinh, ghi vao trang
"San lead" cua Open WebUI (openwebui-custom, /api/v1/cqf/lead).

Chi can Python 3 (thu vien chuan). Key Apify, cai dat va LLM lay tu Open WebUI qua token trong
<DATA_DIR cua Open WebUI>/cqf/lead/agent.json (cung may). Dia chi API: env LEAD_API, mac dinh
http://127.0.0.1:8080/api/v1/cqf/lead.

    lead.py status                     key, cai dat, chi phi thang, lan quet gan nhat
    lead.py start [--trigger chat]     chay 1 lan quet o nen, in run id (lan quet dai hon gioi han lenh cua agent)
    lead.py wait <run_id>              cho toi 170 giay, in tien do; xong thi in bao cao
    lead.py run [--trigger chat]       chay 1 lan quet ngay trong lenh nay (in tien do + bao cao)
    lead.py report [--hours 26]        bao cao co hoi / nguoi moi tim thay
    lead.py top [--limit 10]           co hoi diem cao dang o trang thai Moi
    lead.py people --opportunity <id>  tim nguoi ra quyet dinh cho 1 co hoi
    lead.py check-sources              thu tung trang theo doi (doc duoc khong, bao nhieu link)
"""

import argparse
import concurrent.futures
import datetime as dt
import html
import json
import os
import re
import signal
import ssl
import subprocess
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
STATE = os.environ.get("LEAD_STATE_DIR") or os.path.join(SKILL, "state")
API = os.environ.get("LEAD_API", "http://127.0.0.1:8080/api/v1/cqf/lead")
AGENT_FILES = [os.environ.get("LEAD_AGENT_FILE", ""), "/opt/open-webui/data/cqf/lead/agent.json",
               "/app/backend/data/cqf/lead/agent.json"]
APIFY = "https://api.apify.com/v2"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
VN = dt.timezone(dt.timedelta(hours=7))

ACTOR_GOOGLE = "apify~google-search-scraper"
ACTOR_LINKEDIN = "harvestapi~linkedin-profile-search"
PRICE_GOOGLE_PAGE = 0.0045  # tren goi Free; goi tra phi re hon
PRICE_LINKEDIN_PAGE = 0.10  # 1 trang 25 ho so rut gon
LLM_BATCH = 6
LLM_WORKERS = 3
FETCH_WORKERS = 8
TEXT_CHARS = 1800

# ---------------------------------------------------------------- tu khoa (folded: khong dau, chu thuong)

INDUSTRY_TERMS = {
    "thuy_san": ["thủy sản", "thuỷ sản", "chế biến tôm", "cá tra", "hải sản", "tôm đông lạnh", "surimi", "cá ngừ"],
    "bot_ca": ["bột cá", "dầu cá", "mỡ cá", "collagen", "gelatin", "phụ phẩm thủy sản"],
    "duoc": ["dược phẩm", "nhà máy dược", "thuốc tiêm", "dịch truyền", "vắc xin", "vaccine", "sinh phẩm", "GMP"],
    "thu_y": ["thuốc thú y", "thú y", "chế phẩm sinh học"],
    "fnb": ["thực phẩm", "đồ uống", "nước giải khát", "sữa", "dầu ăn", "bia", "bánh kẹo"],
    "my_pham": ["mỹ phẩm", "hóa mỹ phẩm", "chất tẩy rửa"],
    "cam_hoa_chat": ["thức ăn chăn nuôi", "thức ăn thủy sản", "premix", "nhà máy cám", "hóa chất", "dung môi", "sơn"],
}
SIGNAL_TERMS = ["khởi công", "động thổ", "khánh thành", "xây dựng nhà máy", "nhà máy mới", "cấp phép đầu tư",
                "chứng nhận đăng ký đầu tư", "chủ trương đầu tư", "mở rộng", "nâng công suất", "dây chuyền mới",
                "đầu tư dây chuyền", "tác động môi trường", "ĐTM", "chào giá", "báo giá", "mời thầu", "chào thầu",
                "gói thầu", "mua sắm", "cung cấp lắp đặt", "trưởng ban quản lý dự án", "chỉ huy trưởng", "dự án"]
EQUIPMENT_TERMS = ["máy", "thiết bị", "dây chuyền", "hệ thống", "phòng thí nghiệm", "phòng lab", "kiểm nghiệm",
                   "hầm đông", "băng chuyền", "IQF", "lò hơi", "nồi hấp", "kính hiển vi", "ELISA", "sắc ký", "HPLC",
                   "quang phổ", "tủ", "cân", "đo", "phân tích"]
EQUIPMENT_GROUPS = [
    ["máy đóng gói", "máy chiết rót", "máy dán nhãn", "máy kiểm tra độ kín", "máy dò kim loại"],
    ["thiết bị phòng thí nghiệm", "thiết bị kiểm nghiệm", "máy ELISA", "máy phân tích đạm", "nồi hấp tiệt trùng"],
    ["dây chuyền fillet", "hầm đông", "băng chuyền IQF", "tủ cấp đông", "máy phân cỡ tôm"],
    ["máy sấy bột cá", "máy ly tâm", "dây chuyền bột cá", "máy ép dầu cá"],
    ["máy sắc ký", "máy quang phổ", "tủ an toàn sinh học", "kính hiển vi", "máy đo độ hòa tan"],
]
INDUSTRY_QUERY = {
    "thuy_san": '"thủy sản" OR "chế biến tôm" OR "cá tra"',
    "bot_ca": '"bột cá" OR "dầu cá" OR "phụ phẩm thủy sản"',
    "duoc": '"dược phẩm" OR "nhà máy dược" OR "vắc xin"',
    "thu_y": '"thuốc thú y" OR "chế phẩm sinh học"',
    "fnb": '"thực phẩm" OR "đồ uống" OR "sữa"',
    "my_pham": '"mỹ phẩm" OR "hóa mỹ phẩm"',
    "cam_hoa_chat": '"thức ăn chăn nuôi" OR "thức ăn thủy sản" OR "hóa chất"',
}
NOISE_HOSTS = ("youtube.com", "tiktok.com", "wikipedia.org", "shopee.vn", "lazada.vn", "tiki.vn", "alibaba.com",
               "amazon.", "pinterest.", "instagram.com", "x.com", "twitter.com")

# Trang danh sach duoc theo doi san (da kiem tra doc duoc tu may chu 151.246.182.77 ngay 16/11/2026).
# Cai dat > Trang theo doi them de bo sung. kind: dtm (danh sach DTM), tender (thong bao moi thau cua 1 doanh nghiep).
WATCH_DEFAULT = [
    {"url": "https://www.camau.gov.vn/danh-gia-tac-dong-moi-truong-child", "label": "ĐTM tỉnh Cà Mau", "kind": "dtm"},
    {"url": "https://snnmt.khanhhoa.gov.vn/danh-sach-tin/categoryid/quyet-dinh-phe-duyet-dtm?BCMenu=BCM_9066",
     "label": "ĐTM tỉnh Khánh Hòa", "kind": "dtm"},
    {"url": "https://danang.gov.vn/ttdt/csdl/dtm-du-an", "label": "ĐTM TP Đà Nẵng", "kind": "dtm"},
    {"url": "https://dhgpharma.com.vn/vi/thong-bao", "label": "Thông báo DHG Pharma", "kind": "tender",
     "company": "Công ty Cổ phần Dược Hậu Giang", "industry": "duoc", "province": "Cần Thơ"},
    {"url": "https://bidiphar.com/category/thong-tin-moi-thau/", "label": "Mời thầu Bidiphar", "kind": "tender",
     "company": "Công ty Cổ phần Dược - Trang thiết bị Y tế Bình Định (Bidiphar)", "industry": "duoc", "province": "Gia Lai"},
]
# Cong chan IP nuoc ngoai (may chu o Singapore khong mo duoc) hoac chi co file: doc qua Google (site:), khong vuot chan.
SITE_GROUPS_DTM = [
    ["sonnmt.cantho.gov.vn", "snnmt.tayninh.gov.vn", "snnmt.angiang.gov.vn"],
    ["lamdong.gov.vn", "snnmt.dongnai.gov.vn", "vinhlong.gov.vn"],
    ["dongthap.gov.vn", "hepza.hochiminhcity.gov.vn", "sonnmt.hochiminhcity.gov.vn"],
    ["snnmt.daklak.gov.vn", "snnmt.gialai.gov.vn", "chulaikkt.danang.gov.vn", "thamvan.mae.gov.vn"],
]
SITE_GROUPS_TENDER = [
    ["domesco.com", "navicorp.com.vn", "imexpharm.com", "pymepharco.com"],
    ["vinhhoan.com", "minhphu.com", "fimexvn.com", "idiseafood.com"],
    ["vienkiemnghiem.gov.vn", "nifc.gov.vn", "vinamilk.com.vn", "greenfeed.com.vn"],
]

# ---------------------------------------------------------------- tien ich


def fold(text):
    text = unicodedata.normalize("NFD", str(text or "")).replace("đ", "d").replace("Đ", "D")
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn").lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", text)).strip()


def has_any(folded, terms):
    padded = f" {folded} "
    return any(f" {fold(t)} " in padded for t in terms)


def today():
    return dt.datetime.now(VN).date()


def die(message, code=1):
    print(f"LOI: {message}", file=sys.stderr)
    sys.exit(code)


LOG_FILE = []


def log(message):
    stamp = dt.datetime.now(VN).strftime("%H:%M:%S")
    line = f"[{stamp}] {message}"
    if LOG_FILE:
        with open(LOG_FILE[0], "a", encoding="utf-8") as f:
            f.write(line + "\n")
    else:
        print(line, flush=True)


def _ssl_context(lenient=False):
    ctx = ssl.create_default_context()
    if lenient:  # nhieu cong .gov.vn dung chung chi / khoa DH cu
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        try:
            ctx.set_ciphers("DEFAULT@SECLEVEL=0")
        except ssl.SSLError:
            pass
    return ctx


def http_json(method, url, body=None, headers=None, timeout=60):
    data = json.dumps(body, ensure_ascii=False).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Content-Type": "application/json", "User-Agent": "san-lead-b2b/1.0", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            raw = res.read().decode("utf-8", "replace")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", "replace")[:600]
        try:
            detail = json.loads(detail).get("detail") or json.loads(detail).get("error", {}).get("message") or detail
        except (ValueError, AttributeError):
            pass
        raise RuntimeError(f"{method} {url.split('?')[0]} -> {error.code}: {detail}") from None


def fetch_text(url, timeout=18, limit=1_600_000):
    """(html, final_url) of a page; '' on failure. Lenient TLS for .gov.vn."""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "vi,en;q=0.8"})
    for lenient in (False, True):
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=_ssl_context(lenient)) as res:
                ctype = res.headers.get("Content-Type", "")
                if "html" not in ctype and "xml" not in ctype and ctype:
                    return "", res.geturl()
                raw = res.read(limit)
                charset = (res.headers.get_content_charset() or "utf-8").split(",")[0].strip()
                try:
                    return raw.decode(charset, "replace"), res.geturl()
                except LookupError:  # bang ma la ("utf-8,gbk", "none"...)
                    return raw.decode("utf-8", "replace"), res.geturl()
        except ssl.SSLError:
            continue
        except urllib.error.URLError as error:
            if isinstance(getattr(error, "reason", None), ssl.SSLError) and not lenient:
                continue
            return "", url
        except (TimeoutError, OSError, ValueError):
            return "", url
    return "", url


def strip_html(raw):
    raw = re.sub(r"(?is)<(script|style|noscript|svg|header|footer|nav|form|iframe)\b.*?</\1>", " ", raw)
    raw = re.sub(r"(?is)<br\s*/?>|</p>|</div>|</li>|</h\d>", "\n", raw)
    text = html.unescape(re.sub(r"(?s)<[^>]+>", " ", raw))
    lines = [re.sub(r"[ \t ]+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if len(line) > 1)


def main_text(raw):
    """Article text: <p> paragraphs first (skips menus), else the whole page text."""
    paras = [strip_html(p) for p in re.findall(r"(?is)<p\b[^>]*>(.*?)</p>", raw)]
    paras = [p for p in paras if len(p) >= 40]
    text = "\n".join(paras) if sum(len(p) for p in paras) >= 300 else strip_html(raw)
    return text[:TEXT_CHARS * 3]


DATE_PATTERNS = [
    r'article:published_time"\s+content="(\d{4}-\d{2}-\d{2})',
    r'"datePublished"\s*:\s*"(\d{4}-\d{2}-\d{2})',
    r'itemprop="datePublished"[^>]*content="(\d{4}-\d{2}-\d{2})',
    r'pubdate[^>]*content="(\d{4}-\d{2}-\d{2})',
]


def page_date(raw):
    for pattern in DATE_PATTERNS:
        m = re.search(pattern, raw)
        if m:
            return m.group(1)
    m = re.search(r"\b(\d{1,2})/(\d{1,2})/(20\d{2})\b", strip_html(raw[:200000])[:4000])
    if m:
        d, mo, y = map(int, m.groups())
        try:
            day = dt.date(y, mo, d)
            if day <= today():
                return day.isoformat()
        except ValueError:
            pass
    return ""


def url_norm(url):
    parts = urllib.parse.urlsplit(url)
    query = [(k, v) for k, v in urllib.parse.parse_qsl(parts.query) if not k.lower().startswith(("utm_", "fbclid", "gclid"))]
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, parts.path, urllib.parse.urlencode(query), ""))


# ---------------------------------------------------------------- Open WebUI (San lead)


def agent_token():
    for path in AGENT_FILES:
        if path and os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as f:
                    return json.load(f)["token"]
            except (OSError, ValueError, KeyError):
                continue
    die("Chua co San lead tren may nay (khong thay cqf/lead/agent.json). Cai openwebui-custom ban co San lead "
        "(sidebar Open WebUI > San lead) roi chay lai.")


def owui(method, path, body=None, timeout=60):
    return http_json(method, API + path, body, {"X-Lead-Agent-Token": agent_token()}, timeout)


# ---------------------------------------------------------------- Apify


class Budget:
    """Tien Apify cua 1 lan quet: dung truoc khi vuot tran lan quet / tran thang."""

    def __init__(self, cfg):
        s = cfg["settings"]
        self.key = cfg.get("apify_key") or ""
        self.per_run = float(s.get("max_usd_per_run") or 0)
        self.per_month = float(s.get("max_usd_per_month") or 0)
        self.spent = 0.0
        self.month_used = None
        self.stopped = ""

    def month(self):
        if self.month_used is None and self.key:
            try:
                data = http_json("GET", f"{APIFY}/users/me/limits", headers={"Authorization": f"Bearer {self.key}"}, timeout=25)
                self.month_used = float((data.get("data", {}).get("current") or {}).get("monthlyUsageUsd") or 0)
            except RuntimeError:
                self.month_used = 0.0
        return self.month_used or 0.0

    def allow(self, estimate, what):
        if _wallet_empty:
            self.stopped = "ví LLM hết tiền nên không gọi Apify (không đọc được kết quả)"
            return False
        if not self.key:
            self.stopped = "chưa có key Apify"
            return False
        if self.spent + estimate > self.per_run:
            self.stopped = f"chạm trần mỗi lần quét (${self.per_run:.2f}) trước khi {what}"
            return False
        if self.month() + self.spent + estimate > self.per_month:
            self.stopped = f"chạm trần tháng (${self.per_month:.2f}, Apify đã dùng ${self.month():.2f}) trước khi {what}"
            return False
        return True


def apify_run(budget, actor, payload, estimate, what, wait=280):
    """Chay 1 actor, cho xong, tra (items, cost). Khong du ngan sach -> ([], 0)."""
    if not budget.allow(estimate, what):
        log(f"Bỏ qua {what}: {budget.stopped}")
        return [], 0.0
    headers = {"Authorization": f"Bearer {budget.key}"}
    cap = max(0.5, round(estimate * 2, 2))  # Apify khong nhan tran duoi $0.50
    run = http_json("POST", f"{APIFY}/acts/{actor}/runs?waitForFinish=60&maxTotalChargeUsd={cap}", payload, headers, 90)["data"]
    started = time.time()
    while run.get("status") in ("READY", "RUNNING") and time.time() - started < wait:
        run = http_json("GET", f"{APIFY}/actor-runs/{run['id']}?waitForFinish=60", headers=headers, timeout=90)["data"]
    if run.get("status") in ("READY", "RUNNING"):
        http_json("POST", f"{APIFY}/actor-runs/{run['id']}/abort", {}, headers, 30)
        log(f"{what}: quá {wait} giây, đã dừng")
    items = http_json("GET", f"{APIFY}/datasets/{run['defaultDatasetId']}/items?clean=true&format=json", headers=headers, timeout=90)
    time.sleep(2)  # chi phi cap nhat sau khi run xong
    final = http_json("GET", f"{APIFY}/actor-runs/{run['id']}", headers=headers, timeout=30)["data"]
    cost = float(final.get("usageTotalUsd") or 0)
    budget.spent += cost
    if final.get("status") not in ("SUCCEEDED",):
        log(f"{what}: Apify trạng thái {final.get('status')} ({final.get('statusMessage') or ''})")
    return items if isinstance(items, list) else [], cost


def google_search(budget, queries, after):
    if not queries:
        return []
    payload = {"queries": "\n".join(queries), "countryCode": "vn", "languageCode": "vi", "maxPagesPerQuery": 1,
               "resultsPerPage": 10, "afterDate": after}
    items, cost = apify_run(budget, ACTOR_GOOGLE, payload, len(queries) * PRICE_GOOGLE_PAGE, f"{len(queries)} truy vấn Google")
    out = []
    for page in items:
        term = (page.get("searchQuery") or {}).get("term", "")
        term = re.sub(r"\s+(after|before):\S+", "", term).strip()  # Apify gan them after:<ngay> vao truy van
        for r in page.get("organicResults") or []:
            out.append({"query": term, "title": r.get("title") or "", "url": r.get("url") or "",
                        "snippet": r.get("description") or "", "date": (r.get("date") or "")[:10]})
    log(f"Google: {len(queries)} truy vấn, {len(out)} kết quả, ${cost:.3f}")
    return out


# ---------------------------------------------------------------- LLM


class WalletEmpty(RuntimeError):
    """Vi LLM het tien (402): dung moi lan goi LLM con lai trong lan quet."""


_wallet_empty = []


class Truncated(RuntimeError):
    """Model het token giua chung: chia lo nho hon roi doc lai."""


_REASONING_OFF = {"reasoning": {"enabled": False}}  # model suy nghi truoc thi an het token, tra JSON cut cut
_reasoning_param_ok = [os.environ.get("LEAD_LLM_REASONING") != "1"]


def llm_chat(llm, system, user, max_tokens=3500):
    if llm.get("error"):
        raise RuntimeError(f"LLM: {llm['error']}")
    if _wallet_empty:
        raise WalletEmpty(_wallet_empty[0])
    last = None
    for attempt in range(3):
        body = {"model": llm["model"], "temperature": 0, "max_tokens": max_tokens,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                **(_REASONING_OFF if _reasoning_param_ok[0] else {})}
        try:
            data = http_json("POST", llm["base_url"].rstrip("/") + "/chat/completions", body,
                             {"Authorization": f"Bearer {llm['api_key']}"}, timeout=180)
            choice = data["choices"][0]
            if choice.get("finish_reason") == "length":
                raise Truncated("model hết token giữa chừng")
            return choice["message"].get("content") or ""
        except Truncated:
            raise
        except RuntimeError as error:
            if "-> 402" in str(error):
                message = "ví LLM của Hermes hết tiền (402): nạp thêm rồi quét lại"
                _wallet_empty.append(message)
                raise WalletEmpty(message) from None
            if "reasoning" in str(error).lower() and _reasoning_param_ok[0]:
                _reasoning_param_ok[0] = False  # nha cung cap khong nhan tham so reasoning: goi lai khong co no
                continue
            last = error
        except (KeyError, IndexError, TimeoutError, OSError) as error:
            last = error
        time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"LLM không trả lời: {last}")


def _save_fail(prompt, error):
    try:
        os.makedirs(STATE, exist_ok=True)
        with open(os.path.join(STATE, "llm-fail.log"), "a", encoding="utf-8") as f:
            f.write(f"\n===== {dt.datetime.now(VN).isoformat()} {error}\n{prompt[:3000]}\n")
    except OSError:
        pass


def parse_json(text):
    text = re.sub(r"(?s)<think>.*?</think>", "", text or "").strip()
    fence = re.search(r"(?s)```(?:json)?\s*(.*?)```", text)
    if fence:
        text = fence.group(1)
    start = min([i for i in (text.find("["), text.find("{")) if i >= 0], default=-1)
    if start < 0:
        raise ValueError("không thấy JSON")
    decoder = json.JSONDecoder()
    value, _ = decoder.raw_decode(text[start:])
    return value


EXTRACT_SYSTEM = """Bạn là chuyên viên săn lead B2B cho một công ty bán thiết bị công nghiệp và phòng thí nghiệm ở Việt Nam.
Bạn đọc từng tin (tiêu đề, đoạn trích, nội dung trang) và quyết định tin đó có phải CƠ HỘI BÁN THIẾT BỊ hay không.

Chỉ giữ (keep=true) khi tin nói về MỘT doanh nghiệp / chủ đầu tư / đơn vị cụ thể tại VIỆT NAM, thuộc 7 ngành:
  duoc = Dược phẩm & sinh phẩm y tế (cả viện / trung tâm kiểm nghiệm thuốc)
  thu_y = Thuốc thú y & chế phẩm sinh học
  thuy_san = Chế biến & xuất khẩu thủy hải sản
  bot_ca = Bột cá, mỡ cá, dầu cá, collagen / gelatin, phụ phẩm thủy sản
  fnb = Thực phẩm, đồ uống, sữa (cả trung tâm kiểm nghiệm thực phẩm)
  my_pham = Mỹ phẩm, hóa mỹ phẩm, chất tẩy rửa
  cam_hoa_chat = Thức ăn chăn nuôi / thủy sản, premix, hóa chất, dung môi, sơn keo
VÀ tin cho thấy họ sắp hoặc đang mua thiết bị, theo một trong 4 loại (kind):
  moi_thau = mời thầu / thư mời chào giá / yêu cầu báo giá cho MÁY MÓC, THIẾT BỊ, DÂY CHUYỀN, THIẾT BỊ PHÒNG THÍ NGHIỆM
  du_an_moi = dự án nhà máy mới: được cấp phép / chấp thuận đầu tư, đang lập ĐTM, động thổ, khởi công, đang xây
  mo_rong = nhà máy đang chạy mở rộng, nâng công suất, thêm dây chuyền, cải tạo, tự động hóa
  tin_hieu = tín hiệu khác: tuyển trưởng ban QLDA / chỉ huy trưởng / kỹ sư cơ điện cho nhà máy mới, phê duyệt ĐTM...

LOẠI (keep=false) khi: quảng cáo của nhà cung cấp thiết bị; tin thị trường, giá cả, xuất khẩu chung chung; nhà máy ở
nước ngoài; mời thầu dịch vụ (du lịch, sự kiện, truyền thông, vé máy bay, thuê xe, phần mềm, bảo hiểm, xây lắp thuần,
văn phòng phẩm, quà tặng) hay mua xe, máy tính văn phòng; thiết bị y tế cho bệnh viện; ngành ngoài 7 ngành (điện, xi
măng, may mặc, cảng, đường giao thông, bất động sản...); nhà máy đã khánh thành mà không nói giai đoạn tiếp theo; tin
không nêu được tên doanh nghiệp / chủ đầu tư; trang danh sách, trang tìm việc chung, trang giới thiệu dịch vụ;
trang "dự án đã thực hiện" / "công trình tiêu biểu" của nhà thầu, nhà cung cấp, đơn vị thiết kế (việc đã xong, không
phải nhu cầu mới); tin chuyển nhượng, mua bán nhà máy; mời thầu đã có kết quả / đã đóng.

Quy tắc điền:
- company: tên đầy đủ nhất có trong nguồn (VD "Công ty Cổ phần Dược Hậu Giang"). Nguồn không có tên doanh nghiệp /
  chủ đầu tư thì company = "" (vẫn được giữ nếu là tin Google News chỉ có tiêu đề: hệ thống sẽ đọc bài gốc). Không bịa.
- title: tên gói thầu / tên dự án như nguồn. moi_thau bắt buộc có.
- summary: 1-2 câu tiếng Việt, chỉ sự thật trong nguồn (quy mô, vốn, công suất nếu có).
- province: tỉnh/thành viết như nguồn (tên cũ hay mới đều được). Không rõ thì "". location: KCN/CCN/xã/huyện nếu có.
- equipment: thiết bị nguồn NÊU RÕ (equipment_inferred=false). Nếu nguồn không nêu, suy ra 3-5 hạng mục thiết bị điển
  hình loại nhà máy đó cần, ưu tiên hàng bên bán có, và đặt equipment_inferred=true. Mỗi hạng mục là MỘT thiết bị, tối
  đa 6 từ (VD "Tủ an toàn sinh học", "Máy phân tích NIR"), không gộp nhiều thiết bị, không mở ngoặc liệt kê.
- deadline: hạn nộp hồ sơ / báo giá YYYY-MM-DD, chỉ khi nguồn ghi. progress: tiến độ CHÉP ĐÚNG mốc thời gian trong
  nguồn ("được cấp phép 9/2026, khởi công quý 1/2027"); không tự suy ra năm hay ngày nguồn không ghi. value: chỉ số
  tiền (vốn đầu tư / giá gói, VD "1.250 tỷ đồng"); không có số tiền thì "".
- contact: {name, phone, email} chỉ khi nguồn ghi (đầu mối của đơn vị). Không bịa.
- published: ngày đăng tin YYYY-MM-DD nếu biết, không thì "".
- plant_status: dang_chay | du_an_moi | chua_ro.
- industry và kind BẮT BUỘC có khi keep=true (dùng đúng mã ở trên). equipment là JSON array các chuỗi.
- Tỉnh nằm NGOÀI vùng theo dõi (danh sách trong tin nhắn) thì keep=false, reason "ngoài vùng".
- sales_note: 1-3 câu cho sale: nên gặp ai (phòng/chức danh), chào thiết bị gì của bên bán, vì sao lúc này. Không bịa số liệu.
Trả về ĐÚNG MỘT JSON array, mỗi phần tử: {"i": số thứ tự tin, "keep": true/false, "reason": "lý do ngắn",
"opportunity": {...các trường trên..., "industry": "<mã ngành>", "kind": "<mã loại>"}} (opportunity chỉ khi keep=true).
Không viết gì ngoài JSON."""


def extract_batch(llm, seller, batch, region=""):
    lines = []
    for n, c in enumerate(batch):
        lines.append(f"### Tin {n}\nNguồn: {c['url']}\nLoại nguồn: {c['origin']}" + (f" ({c['hint']})" if c.get("hint") else "")
                     + f"\nNgày (nếu biết): {c.get('date') or 'không rõ'}\nTiêu đề: {c['title']}\n"
                     + (f"Đoạn trích: {c['snippet']}\n" if c.get("snippet") else "")
                     + (f"Nội dung trang:\n{c['text'][:TEXT_CHARS]}\n" if c.get("text") else ""))
    user = (f"Bên bán: {seller.get('company') or '(chưa ghi tên)'}\nHàng bên bán có: {seller.get('products') or '(chưa ghi)'}\n"
            f"Không cần tìm: {seller.get('avoid') or '(không)'}\nVùng theo dõi: {region}\n"
            f"Hôm nay: {today().isoformat()}\n\n" + "\n".join(lines))
    try:
        value = parse_json(llm_chat(llm, EXTRACT_SYSTEM, user))
    except WalletEmpty:
        raise
    except (ValueError, Truncated) as error:
        if len(batch) > 1:  # chia doi, doc lai tung nua
            half = len(batch) // 2
            left = extract_batch(llm, seller, batch[:half], region)
            right = extract_batch(llm, seller, batch[half:], region)
            return {**left, **{k + half: v for k, v in right.items()}}
        _save_fail(user, error)
        return {}
    if isinstance(value, dict):
        value = value.get("items") or value.get("results") or [value]
    out = {}
    for item in value:
        if isinstance(item, dict) and isinstance(item.get("i"), int) and 0 <= item["i"] < len(batch):
            out[item["i"]] = item
    return out


PEOPLE_SYSTEM = """Bạn lọc hồ sơ LinkedIn cho sale B2B bán thiết bị công nghiệp / phòng thí nghiệm ở Việt Nam.
Với mỗi hồ sơ, giữ (keep=true) chỉ khi: người đó HIỆN làm ở công ty mục tiêu (hoặc một công ty Việt Nam thuộc 7 ngành:
dược, thú y, thủy sản, bột cá, thực phẩm-đồ uống, mỹ phẩm, cám-hóa chất) VÀ có vai trò ra quyết định / ảnh hưởng mua
thiết bị: giám đốc nhà máy, giám đốc / trưởng phòng kỹ thuật, dự án, bảo trì, cơ điện, sản xuất, QA/QC, R&D, mua hàng,
chuỗi cung ứng, ban giám đốc. Loại: nhân viên bán hàng / marketing, người của công ty bán thiết bị hay tư vấn, headhunter,
sinh viên, người ở nước ngoài, hồ sơ không rõ công ty.
Điền: name (đúng như hồ sơ), title (chức danh hiện tại), company (công ty hiện tại), role_group (ky_thuat | san_xuat_qa |
mua_sam | khac), industry (duoc | thu_y | thuy_san | bot_ca | fnb | my_pham | cam_hoa_chat | ""), location,
sales_note (1-2 câu: vì sao người này đáng gặp, chào thiết bị gì; dựa trên cơ hội nếu có, không bịa).
Trả về ĐÚNG MỘT JSON array: [{"i": số, "keep": true/false, "reason": "...", "person": {...}}]. Không viết gì ngoài JSON."""


def classify_people(llm, seller, profiles, context):
    out = []
    for start in range(0, len(profiles), 8):
        chunk = profiles[start:start + 8]
        lines = [f"### Hồ sơ {n}\n" + json.dumps(p, ensure_ascii=False) for n, p in enumerate(chunk)]
        user = (f"Hàng bên bán có: {seller.get('products') or '(chưa ghi)'}\n{context}\n\n" + "\n".join(lines))
        try:
            value = parse_json(llm_chat(llm, PEOPLE_SYSTEM, user))
        except WalletEmpty as error:
            log(f"Lọc hồ sơ dừng: {error}")
            break
        except (ValueError, RuntimeError) as error:
            if len(chunk) > 1:
                half = len(chunk) // 2
                out += classify_people(llm, seller, chunk[:half], context) + classify_people(llm, seller, chunk[half:], context)
            else:
                log(f"Lọc hồ sơ lỗi: {error}")
            continue
        for item in value if isinstance(value, list) else []:
            if isinstance(item, dict) and item.get("keep") and isinstance(item.get("i"), int) and 0 <= item["i"] < len(chunk):
                person = dict(item.get("person") or {})
                src = chunk[item["i"]]
                person["linkedin_url"] = src.get("linkedin_url") or person.get("linkedin_url", "")
                person["source"] = src.get("source", "")
                out.append(person)
    return out


INDUSTRY_KEYS = list(INDUSTRY_TERMS)
KIND_KEYS = ["moi_thau", "du_an_moi", "mo_rong", "tin_hieu"]


def normalise(o, candidate):
    """Sua kieu du lieu model hay viet sai: equipment la chuoi, thieu nganh (lay tu trang theo doi), contact rong."""
    o = dict(o)
    equipment = o.get("equipment") or []
    if isinstance(equipment, str):
        equipment = re.split(r"[;,\n]+", equipment)
    o["equipment"] = [str(e).strip() for e in equipment if isinstance(e, (str, int)) and len(str(e).strip()) >= 3][:12]
    o["equipment_inferred"] = bool(o.get("equipment_inferred")) if o["equipment"] else False
    hint = candidate.get("hint") or ""
    if o.get("industry") not in INDUSTRY_KEYS:
        m = re.search(r"industry=(\w+)", candidate.get("meta", ""))
        o["industry"] = m.group(1) if m else o.get("industry")
    if o.get("kind") not in KIND_KEYS and candidate.get("origin") == "Trang theo dõi" and "mời thầu" in hint.lower():
        o["kind"] = "moi_thau"
    if not o.get("province") and candidate.get("province"):
        o["province"] = candidate["province"]
    if not o.get("company") and candidate.get("company"):
        o["company"] = candidate["company"]
    contact = o.get("contact") if isinstance(o.get("contact"), dict) else {}
    o["contact"] = {k: str(contact.get(k) or "").strip() for k in ("name", "phone", "email")}
    for key in ("title", "summary", "province", "location", "progress", "value", "sales_note", "published", "deadline"):
        if o.get(key) is not None and not isinstance(o.get(key), str):
            o[key] = str(o[key])
    return o


# ---------------------------------------------------------------- thu tin


def rotation(name, size):
    """Vong quay qua cac lan quet: moi lan bat dau o vi tri khac, de cac tinh / nhom thiet bi deu duoc quet."""
    os.makedirs(STATE, exist_ok=True)
    path = os.path.join(STATE, "rotation.json")
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        data = {}
    value = data.get(name, 0) % max(size, 1)
    data[name] = value + 1
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return value


def province_chunks(cfg):
    names = []
    for new in cfg["settings"]["provinces"]:
        olds = cfg["provinces"].get(new) or cfg.get("other_provinces", {}).get(new) or [new]
        names.extend(dict.fromkeys([new.replace("TP. ", ""), *olds]))
    names = list(dict.fromkeys(n.replace("TP. ", "") for n in names))
    return [names[i:i + 7] for i in range(0, len(names), 7)] or [[]]


def build_queries(cfg):
    s = cfg["settings"]
    industries = [k for k in s["industries"] if k in INDUSTRY_QUERY]
    priority = [k for k in s.get("priority_industries", []) if k in industries]
    order = priority + [k for k in industries if k not in priority]
    chunks = province_chunks(cfg)
    groups = EQUIPMENT_GROUPS + ([s["extra_keywords"][i:i + 5] for i in range(0, len(s.get("extra_keywords", [])), 5)])
    turn = rotation("queries", 10_000)
    queries = []

    def ors(words):
        return " OR ".join(f'"{w}"' for w in words)

    kinds = s["kinds"]
    for n in range(len(groups)):
        g = groups[(turn + n) % len(groups)]
        if "moi_thau" in kinds:
            queries.append(f'("thư mời chào giá" OR "thư mời báo giá" OR "yêu cầu báo giá" OR "chào giá cạnh tranh") ({ors(g)})')
    for n, ind in enumerate(order):
        chunk = chunks[(turn + n) % len(chunks)]
        place = f" ({ors(chunk)})" if chunk else ""
        if "du_an_moi" in kinds:
            queries.append(f'("khởi công" OR "động thổ" OR "cấp giấy chứng nhận đăng ký đầu tư" OR "chấp thuận chủ trương đầu tư") "nhà máy" ({INDUSTRY_QUERY[ind]}){place}')
        if "mo_rong" in kinds:
            queries.append(f'("mở rộng" OR "nâng công suất" OR "đầu tư dây chuyền" OR "giai đoạn 2") "nhà máy" ({INDUSTRY_QUERY[ind]}){place}')
        if "tin_hieu" in kinds or "du_an_moi" in kinds:
            queries.append(f'"đánh giá tác động môi trường" "nhà máy" ({INDUSTRY_QUERY[ind]}){place}')
    if "tin_hieu" in kinds:
        queries.append('("tuyển" OR "tuyển dụng") ("trưởng ban quản lý dự án" OR "chỉ huy trưởng" OR "kỹ sư cơ điện") '
                       '"nhà máy" ("thủy sản" OR "dược" OR "thực phẩm" OR "thức ăn chăn nuôi")')
    if "moi_thau" in kinds:
        g = groups[turn % len(groups)]
        queries.append(f'site:dauthau.asia OR site:bidwinner.info ({ors(g)})')
        sites = SITE_GROUPS_TENDER[turn % len(SITE_GROUPS_TENDER)]
        queries.append("(" + " OR ".join(f"site:{x}" for x in sites) + ') ("mời thầu" OR "chào giá" OR "báo giá" OR "chào thầu")')
    if "du_an_moi" in kinds or "tin_hieu" in kinds:
        sites = SITE_GROUPS_DTM[turn % len(SITE_GROUPS_DTM)]
        queries.append("(" + " OR ".join(f"site:{x}" for x in sites) + ') ("nhà máy" OR "chế biến") ("tác động môi trường" OR "ĐTM" OR "giấy phép môi trường")')
    # xen ke: moi thau, du an, mo rong... de khi cat bot van du loai
    tender = [q for q in queries if "chào giá" in q or "site:" in q or "tác động môi trường" in q]
    rest = [q for q in queries if q not in tender]
    mixed = []
    while tender or rest:
        if tender:
            mixed.append(tender.pop(0))
        for _ in range(2):
            if rest:
                mixed.append(rest.pop(0))
    return mixed[: int(s.get("google_queries_per_run") or 0)]


def news_queries(cfg):
    s = cfg["settings"]
    days = min(int(s.get("lookback_days") or 30), 60)
    industries = [k for k in s["industries"] if k in INDUSTRY_QUERY]
    out = []
    for ind in industries:
        terms = INDUSTRY_QUERY[ind]
        out.append(f'("khởi công" OR "động thổ" OR "xây dựng nhà máy") ({terms}) when:{days}d')
        out.append(f'("cấp phép đầu tư" OR "chứng nhận đăng ký đầu tư" OR "chủ trương đầu tư") "nhà máy" ({terms}) when:{days}d')
        out.append(f'("mở rộng nhà máy" OR "nâng công suất" OR "dây chuyền mới") ({terms}) when:{days}d')
    return out


def collect_news(cfg):
    items = []
    for q in news_queries(cfg):
        url = "https://news.google.com/rss/search?" + urllib.parse.urlencode({"q": q, "hl": "vi", "gl": "VN", "ceid": "VN:vi"})
        raw, _ = fetch_text(url, timeout=20)
        for it in re.findall(r"(?s)<item>(.*?)</item>", raw):
            title = html.unescape(re.sub(r"<[^>]+>", "", (re.search(r"(?s)<title>(.*?)</title>", it) or [None, ""])[1]))
            link = html.unescape((re.search(r"(?s)<link>(.*?)</link>", it) or [None, ""])[1]).strip()
            pub = (re.search(r"<pubDate>(.*?)</pubDate>", it) or [None, ""])[1]
            source = html.unescape((re.search(r'<source url="([^"]+)"', it) or [None, ""])[1])
            try:
                day = dt.datetime.strptime(pub[5:16], "%d %b %Y").date().isoformat()
            except ValueError:
                day = ""
            if link and title:
                items.append({"origin": "Google News", "hint": source, "title": title, "url": link, "snippet": "",
                              "date": day, "query": q})
        time.sleep(0.6)
    log(f"Google News: {len(news_queries(cfg))} truy vấn, {len(items)} tin")
    return items


def watch_list(cfg):
    pages = [dict(p) for p in WATCH_DEFAULT]
    known = {p["url"] for p in pages}
    for p in cfg["settings"].get("watch_pages") or []:
        if p["url"] not in known:
            pages.append({"url": p["url"], "label": p.get("label") or p["url"], "kind": "custom"})
    return pages


def page_links(page):
    try:
        raw, final = fetch_text(page["url"], timeout=25)
    except Exception:  # noqa: BLE001
        return None
    if not raw:
        return None
    links, seen = [], set()
    host = urllib.parse.urlsplit(final).netloc
    for m in re.finditer(r'(?is)<a\b[^>]*href=["\']([^"\'#]+)["\'][^>]*>(.*?)</a>', raw):
        text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", m.group(2)))).strip()
        href = urllib.parse.urljoin(final, html.unescape(m.group(1)))
        if len(text) < 25 or not href.startswith("http") or href in seen:
            continue
        if urllib.parse.urlsplit(href).netloc != host:
            continue
        seen.add(href)
        links.append({"title": text[:300], "url": href})
    return links


def collect_watch(cfg):
    items, report = [], []
    pages = watch_list(cfg)
    with concurrent.futures.ThreadPoolExecutor(FETCH_WORKERS) as pool:
        for page, links in zip(pages, pool.map(page_links, pages)):
            if links is None:
                report.append(f"{page['label']}: không đọc được")
                continue
            kept = 0
            for link in links:
                f = fold(link["title"])
                if page.get("kind") == "tender":
                    ok = has_any(f, ["chào giá", "báo giá", "mời thầu", "chào thầu", "gói"]) and has_any(f, EQUIPMENT_TERMS)
                elif page.get("kind") == "dtm":
                    ok = has_any(f, ["nhà máy", "chế biến", "sản xuất"]) or any(has_any(f, t) for t in INDUSTRY_TERMS.values())
                else:
                    ok = has_any(f, SIGNAL_TERMS + EQUIPMENT_TERMS)
                if ok:
                    hint = page["label"]
                    if page.get("company"):
                        hint += f"; đơn vị: {page['company']}; tỉnh: {page.get('province', '')}"
                    items.append({"origin": "Trang theo dõi", "hint": hint, "title": link["title"], "url": link["url"],
                                  "snippet": "", "date": "", "company": page.get("company", ""),
                                  "province": page.get("province", ""),
                                  "meta": f"industry={page['industry']}" if page.get("industry") else ""})
                    kept += 1
            report.append(f"{page['label']}: {len(links)} link, {kept} đáng đọc")
    log("Trang theo dõi: " + "; ".join(report))
    return items, report


def prefilter(items):
    """Bo tin chac chan khong lien quan truoc khi ton LLM: khong co nganh, khong co tin hieu, trang rac."""
    out = []
    for it in items:
        host = urllib.parse.urlsplit(it["url"]).netloc.lower()
        if any(n in host for n in NOISE_HOSTS):
            continue
        f = fold(f"{it['title']} {it.get('snippet', '')} {it.get('hint', '')}")
        industry = any(has_any(f, terms) for terms in INDUSTRY_TERMS.values())
        signal_hit = has_any(f, SIGNAL_TERMS) or has_any(f, EQUIPMENT_TERMS)
        if it["origin"] == "Trang theo dõi" or (industry and signal_hit) or "linkedin" in host:
            out.append(it)
    return out


def enrich(items):
    """Doc noi dung trang (tru Google News: link chuyen huong) de LLM co du chi tiet."""
    def one(it):
        if it["origin"] == "Google News" or it["url"].lower().endswith(".pdf"):
            return it
        try:
            raw, _ = fetch_text(it["url"])
            if raw:
                it["text"] = main_text(raw)
                it["date"] = it.get("date") or page_date(raw)
        except Exception as error:  # noqa: BLE001 - 1 trang loi khong lam hong ca lan quet
            log(f"Không đọc được {it['url'][:80]}: {error}")
        return it
    with concurrent.futures.ThreadPoolExecutor(FETCH_WORKERS) as pool:
        return list(pool.map(one, items))


# ---------------------------------------------------------------- nguoi lien he


def short_company(name):
    words = re.sub(r"(?i)\b(công ty|cổ phần|tnhh|một thành viên|mtv|ctcp|jsc|co\.?,? ?ltd\.?|tập đoàn|tổng công ty|"
                   r"việt nam|vietnam|chi nhánh|joint stock company|company|limited|corporation)\b", " ", name)
    words = re.sub(r"[^\w\s&-]", " ", words)
    return re.sub(r"\s+", " ", words).strip()


TITLE_OR = ('("Giám đốc" OR "Director" OR "Manager" OR "Trưởng phòng" OR "Head of" OR "Plant Manager" OR '
            '"Purchasing" OR "Procurement")')


def parse_xray(results):
    """Ket qua Google site:linkedin.com/in -> ho so: ten, chuc danh, cong ty, link."""
    out, seen = [], set()
    for r in results:
        url = r["url"]
        m = re.match(r"https?://([a-z]{2,3}\.)?(www\.)?linkedin\.com/in/[^/?#]+", url, re.I)
        if not m:
            continue
        key = m.group(0).lower()
        if key in seen:
            continue
        seen.add(key)
        title = re.sub(r"\s*\|\s*LinkedIn.*$", "", r["title"]).strip()
        out.append({"linkedin_url": m.group(0), "google_title": title, "google_snippet": r.get("snippet", "")[:300],
                    "country_hint": (m.group(1) or "").strip(".") or "?", "source": "Google (LinkedIn công khai)"})
    return out


def linkedin_search(budget, payload, what):
    items, cost = apify_run(budget, ACTOR_LINKEDIN, payload, PRICE_LINKEDIN_PAGE * int(payload.get("takePages") or 1), what)
    out = []
    for p in items:
        pos = (p.get("currentPositions") or [{}])
        pos = pos[0] if pos else {}
        loc = p.get("location")
        loc = loc.get("linkedinText") if isinstance(loc, dict) else loc
        name = f"{p.get('firstName') or ''} {p.get('lastName') or ''}".strip()
        if not name:
            continue
        out.append({"linkedin_url": p.get("linkedinUrl") or "", "name": name, "title": pos.get("title") or p.get("headline") or "",
                    "company": pos.get("companyName") or "", "location": loc or "", "source": "LinkedIn (Apify)"})
    log(f"{what}: {len(out)} hồ sơ, ${cost:.3f}")
    return out


def people_for(cfg, budget, llm, opps):
    """Nguoi ra quyet dinh cho cac co hoi: Google X-ray (re) truoc, LinkedIn search cho co hoi diem cao nhat neu it ket qua."""
    s = cfg["settings"]
    if not opps or not s["sources"].get("linkedin"):
        return []
    after = (today() - dt.timedelta(days=3650)).isoformat()
    queries = [f'site:linkedin.com/in "{short_company(o["company"])}" {TITLE_OR}' for o in opps]
    results = google_search(budget, queries, after)
    by_query = {}
    for r in results:
        by_query.setdefault(r["query"], []).append(r)
    found = []
    for o, q in zip(opps, queries):
        profiles = parse_xray(by_query.get(q, []))
        if len(profiles) < 2 and o is opps[0] and budget.allow(PRICE_LINKEDIN_PAGE, "tìm LinkedIn"):
            profiles += linkedin_search(budget, {"profileScraperMode": "Short", "searchQuery": short_company(o["company"]),
                                                  "locations": ["Vietnam"], "takePages": 1, "maxItems": 25},
                                         f"LinkedIn: {short_company(o['company'])}")
        if not profiles:
            continue
        context = (f"Công ty mục tiêu: {o['company']} ({o.get('industry_label') or o['industry']}, {o.get('province') or ''}).\n"
                   f"Cơ hội: {o.get('kind_label') or o['kind']}: {o.get('title') or ''}. {o.get('summary') or ''}\n"
                   "Chỉ giữ người hiện làm ở ĐÚNG công ty mục tiêu.")
        kept = classify_people(llm, s["seller"], profiles, context)
        for person in kept[: int(s.get("people_per_opportunity") or 4)]:
            person["opportunity_id"] = o["id"]
            person.setdefault("industry", o["industry"])
            person["plant_status"] = o.get("plant_status") or "chua_ro"
            found.append(person)
    return found


SWEEP_TITLES = [
    ["Plant Manager", "Factory Director", "Technical Director", "Engineering Manager", "Project Manager", "Maintenance Manager"],
    ["Production Manager", "Production Director", "QA Manager", "QC Manager", "R&D Manager", "Operations Manager"],
    ["Purchasing Manager", "Procurement Manager", "Sourcing Manager", "Supply Chain Manager", "General Manager"],
]
SWEEP_WORDS = {"thuy_san": "seafood", "bot_ca": "fishmeal", "duoc": "pharmaceutical", "thu_y": "veterinary",
               "fnb": "food", "my_pham": "cosmetics", "cam_hoa_chat": "feed"}


SWEEP_EVERY_DAYS = 6


def sweep(cfg, budget, llm, force=False):
    """Module 1: tim theo chuc danh x nganh o Viet Nam (moi lan 1 to hop, quay vong)."""
    s = cfg["settings"]
    if not s["sources"].get("linkedin") or int(s.get("linkedin_sweep_per_run") or 0) <= 0:
        return []
    industries = [k for k in (s.get("priority_industries") or []) + s["industries"] if k in SWEEP_WORDS]
    industries = list(dict.fromkeys(industries))
    if not industries:
        return []
    last = os.path.join(STATE, "last-sweep")
    if not force and os.path.exists(last) and time.time() - os.path.getmtime(last) < SWEEP_EVERY_DAYS * 86400:
        return []  # tim theo chuc danh moi tuan 1 lan (ton $0.10 / 25 ho so)
    combos = [(ind, titles) for ind in industries for titles in SWEEP_TITLES]
    ind, titles = combos[rotation("sweep", len(combos)) % len(combos)]
    pages = max(1, min(4, int(s["linkedin_sweep_per_run"]) // 25))
    profiles = linkedin_search(budget, {"profileScraperMode": "Short", "searchQuery": SWEEP_WORDS[ind],
                                        "currentJobTitles": titles, "locations": ["Vietnam"], "takePages": pages,
                                        "maxItems": 25 * pages}, f"LinkedIn theo chức danh ({SWEEP_WORDS[ind]})")
    if not profiles:
        return []
    context = (f"Lượt tìm theo chức danh, ngành {cfg['industries'][ind]}. Giữ người ở công ty Việt Nam thuộc 7 ngành, "
               "có vai trò ra quyết định; ghi industry theo công ty của họ.")
    kept = classify_people(llm, s["seller"], profiles, context)
    if not _wallet_empty:  # chi tinh la da quet tuan nay khi loc duoc ho so
        os.makedirs(STATE, exist_ok=True)
        with open(last, "w", encoding="utf-8") as f:
            f.write(dt.datetime.now(VN).isoformat())
    return kept


# ---------------------------------------------------------------- mot lan quet


def gather(cfg, budget, stats, notes, check_seen=True):
    """Thu tin tu moi nguon, bo trung, bo tin da doc (lan truoc), doc noi dung trang."""
    s = cfg["settings"]
    items = []
    if s["sources"].get("news"):
        news = collect_news(cfg)
        stats["news_items"] = len(news)
        items += news
    if s["sources"].get("watch"):
        watch, _ = collect_watch(cfg)
        stats["watch_links"] = len(watch)
        items += watch
    if s["sources"].get("google") and cfg.get("apify_key"):
        queries = build_queries(cfg)
        stats["google_queries"] = len(queries)
        after = (today() - dt.timedelta(days=int(s.get("lookback_days") or 45))).isoformat()
        for r in google_search(budget, queries, after):
            items.append({"origin": "Google", "hint": "", **r})
    elif s["sources"].get("google"):
        notes.append("chưa có key Apify nên bỏ qua tìm Google")
    unique = {}
    for it in items:
        it["url"] = url_norm(it["url"])
        unique.setdefault(it["url"], it)
    items = prefilter(list(unique.values()))
    if check_seen:
        fresh = set()
        for begin in range(0, len(items), 1000):
            fresh |= set(owui("POST", "/agent/seen/check", {"urls": [it["url"] for it in items[begin:begin + 1000]]})["unseen"])
        items = [it for it in items if it["url"] in fresh]
    # tin Google News trung tieu de voi tin co link that: bo
    titles = {fold(it["title"])[:70] for it in items if it["origin"] != "Google News"}
    items = [it for it in items if it["origin"] != "Google News" or fold(it["title"].rsplit(" - ", 1)[0])[:70] not in titles]
    stats["candidates"] = len(items)
    log(f"{len(items)} tin mới cần đọc")
    return enrich(items)


def resolve_news(cfg, budget, candidates):
    """Tin Google News chi co tieu de (link chuyen huong): tim bai goc qua Google (site:<bao> "<tieu de>"), doc toan van.
    Tra {url Google News: candidate moi (url that, noi dung)}."""
    wanted = []
    for c in candidates:
        headline = c["title"].rsplit(" - ", 1)[0].strip()
        host = urllib.parse.urlsplit(c.get("hint") or "").netloc.removeprefix("www.")
        if len(headline) < 20:
            continue
        query = f'site:{host} "{headline[:110]}"' if host else f'"{headline[:110]}"'
        wanted.append((c, headline, host, query))
    if not wanted:
        return {}
    results = google_search(budget, [w[3] for w in wanted], (today() - dt.timedelta(days=120)).isoformat())
    by_query = {}
    for r in results:
        by_query.setdefault(r["query"], []).append(r)
    found = {}
    for c, headline, host, query in wanted:
        target = fold(headline)[:45]
        for r in by_query.get(query, []):
            r_host = urllib.parse.urlsplit(r["url"]).netloc.removeprefix("www.")
            if (not host or r_host.endswith(host)) and (target[:30] in fold(r["title"]) or fold(r["title"])[:30] in target):
                found[c["url"]] = {**c, "origin": "Google News → bài gốc", "url": url_norm(r["url"]),
                                   "snippet": r.get("snippet", ""), "date": c.get("date") or r.get("date", "")}
                break
    resolved = enrich(list(found.values()))
    log(f"Bài gốc của tin Google News: tìm được {len(resolved)}/{len(wanted)}")
    return {k: v for k, v in zip(found, resolved)}


def region_text(cfg):
    """Vung theo doi kem ten tinh cu: model khong biet Binh Dinh nay thuoc Gia Lai, Bac Lieu nay thuoc Ca Mau..."""
    table = {**cfg.get("other_provinces", {}), **cfg["provinces"]}
    parts = []
    for new_name in cfg["settings"]["provinces"]:
        olds = [o for o in table.get(new_name, []) if o != new_name]
        parts.append(f"{new_name} (gồm cả {', '.join(olds)} cũ)" if olds else new_name)
    return "; ".join(parts) + ". Tỉnh cũ đã sáp nhập vào tỉnh trong danh sách thì VẪN là trong vùng."


def read_items(cfg, items):
    """LLM doc tung lo tin (song song). Tra (verdicts, opportunities, loi)."""
    s = cfg["settings"]
    region = region_text(cfg)
    batches = [items[i:i + LLM_BATCH] for i in range(0, len(items), LLM_BATCH)]

    def read(batch):
        try:
            return batch, extract_batch(cfg["llm"], s["seller"], batch, region), None
        except (RuntimeError, ValueError) as error:
            return batch, {}, error

    verdicts, opportunities, failed = [], [], 0
    with concurrent.futures.ThreadPoolExecutor(LLM_WORKERS) as pool:
        results = list(pool.map(read, batches))
    for batch, result, error in results:
        if error:
            log(f"Đọc tin lỗi (bỏ qua {len(batch)} tin, lần sau đọc lại): {error}")
            failed += len(batch)
            continue
        for n, it in enumerate(batch):
            r = result.get(n)
            if r is None:
                failed += 1
                continue  # model bo sot: khong danh dau da doc, lan sau doc lai
            verdicts.append({"url": it["url"], "verdict": ("giữ: " if r.get("keep") else "loại: ") + str(r.get("reason") or "")[:150]})
            if r.get("keep") and isinstance(r.get("opportunity"), dict):
                o = normalise(r["opportunity"], it)
                o["sources"] = [{"url": it["url"], "title": it["title"], "published": o.get("published") or it.get("date") or ""}]
                if not o.get("published"):
                    o["published"] = it.get("date") or ""
                opportunities.append(o)
    log(f"Đã đọc {len(items) - failed}/{len(items)} tin, giữ {len(opportunities)}")
    return verdicts, opportunities, failed


def run(trigger="chat"):
    cfg = owui("GET", "/agent/config")
    s = cfg["settings"]
    if cfg["llm"].get("error"):
        die(f"Không gọi được LLM của Hermes: {cfg['llm']['error']}")
    run_id = owui("POST", "/agent/runs", {"trigger": trigger})["id"]
    try:  # LLM con goi duoc khong: vi het tien thi dung truoc khi ton tien Apify cho tin khong doc duoc
        llm_chat(cfg["llm"], "Trả lời đúng một chữ.", "ok")  # cung max_tokens voi luot doc that: cong giu tien theo do
    except (WalletEmpty, RuntimeError) as error:
        message = str(error)[:300]
        owui("PATCH", f"/agent/runs/{run_id}", {"status": "error", "stats": {}, "cost_usd": 0, "message": message})
        log(f"Xong lần quét {run_id}: dừng, {message}")
        print(f"**Lần quét không chạy**: {message}. Trang Săn lead: {page_url()}")
        return run_id
    log(f"Bắt đầu lần quét {run_id} ({trigger}). Nguồn: " + ", ".join(k for k, v in s["sources"].items() if v))
    budget = Budget(cfg)
    stats = {"candidates": 0, "created": 0, "merged": 0, "rejected": 0, "people_created": 0, "people_merged": 0,
             "google_queries": 0, "news_items": 0, "watch_links": 0}
    notes = []
    status = "ok"
    try:
        items = gather(cfg, budget, stats, notes)
        verdicts, opportunities, failed = read_items(cfg, items)
        # tin Google News duoc giu: doc bai goc (ten doanh nghiep, KCN, tien do) roi doc lai
        news_kept = [o for o in opportunities if "news.google.com" in o["sources"][0]["url"]]
        if news_kept and s["sources"].get("google") and cfg.get("apify_key") and not _wallet_empty:
            by_url = {it["url"]: it for it in items}
            resolved = resolve_news(cfg, budget, [by_url[o["sources"][0]["url"]] for o in news_kept if o["sources"][0]["url"] in by_url])
            if resolved:
                again_verdicts, again, again_failed = read_items(cfg, list(resolved.values()))
                verdicts += again_verdicts
                replaced = {resolved[k]["url"]: k for k in resolved}
                read_again = {replaced[v["url"]] for v in again_verdicts if v["url"] in replaced}
                again_by_news = {replaced[o["sources"][0]["url"]]: o for o in again if o["sources"][0]["url"] in replaced}
                kept = []
                for o in opportunities:
                    news_url = o["sources"][0]["url"]
                    if news_url in again_by_news:  # doc bai goc van giu: dung ban day du
                        kept.append(again_by_news[news_url])
                    elif news_url in read_again:  # doc bai goc xong thi loai: bo
                        continue
                    else:  # chua doc duoc bai goc: giu ban tu tieu de
                        kept.append(o)
                opportunities = kept
        if failed:
            status = "partial"
            notes.append(f"{failed} tin chưa đọc được, lần quét sau đọc lại")
        if _wallet_empty:
            notes.append(_wallet_empty[0])
        saved = owui("POST", "/agent/opportunities", {"items": opportunities, "run_id": run_id}) if opportunities else {
            "created": [], "merged": [], "rejected": []}
        stats["created"], stats["merged"], stats["rejected"] = len(saved["created"]), len(saved["merged"]), len(saved["rejected"])
        for r in saved["rejected"]:
            log(f"Trang San lead không nhận: {r.get('company')}: {r['reason']}")
            src = opportunities[r["index"]]["sources"][0]["url"]
            for v in verdicts:
                if v["url"] == src:
                    v["verdict"] = f"loại khi lưu: {r['reason']}"
        owui("POST", "/agent/seen", {"items": verdicts})
        # nguoi lien he cho co hoi tot vua tim / vua gap lai
        touched = [x["id"] for x in saved["created"] + saved["merged"]]
        targets = []
        for opp_id in touched:
            o = owui("GET", f"/opportunities/{opp_id}")
            if o["score"] >= int(s.get("min_score_for_people") or 0) and o["people_count"] < int(s.get("people_per_opportunity") or 0):
                targets.append(o)
        targets.sort(key=lambda o: -o["score"])
        people = []
        if targets and cfg.get("apify_key") and not _wallet_empty:
            people += people_for(cfg, budget, cfg["llm"], targets[:8])
        if cfg.get("apify_key") and not _wallet_empty:
            people += sweep(cfg, budget, cfg["llm"])
        if people:
            done = owui("POST", "/agent/people", {"items": people, "run_id": run_id})
            stats["people_created"], stats["people_merged"] = len(done["created"]), len(done["merged"])
            for r in done["rejected"]:
                log(f"Không lưu người {r.get('name')}: {r['reason']}")
        if budget.stopped:
            notes.append(budget.stopped)
    except Exception as error:  # noqa: BLE001 - ghi vao lan quet roi bao
        status = "error"
        notes.append(str(error)[:400])
        log(f"LỖI: {error}")
    message = "; ".join(notes)
    owui("PATCH", f"/agent/runs/{run_id}", {"status": status, "stats": stats, "cost_usd": round(budget.spent, 4), "message": message})
    log(f"Xong lần quét {run_id}: {stats['created']} cơ hội mới, {stats['merged']} gộp, {stats['people_created']} người mới, "
        f"chi phí Apify ${budget.spent:.3f}" + (f" ({message})" if message else ""))
    print("\n" + report_text(hours=None, run_id=run_id, stats=stats, cost=budget.spent, status=status, message=message))
    return run_id


# ---------------------------------------------------------------- bao cao


def page_url():
    base = os.environ.get("LEAD_PUBLIC_URL") or os.environ.get("WEBUI_URL") or ""
    if not base:
        try:
            with open("/opt/open-webui/env", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("WEBUI_URL="):
                        base = line.split("=", 1)[1].strip().strip("'\"")
        except OSError:
            pass
    return (base.rstrip("/") or "") + "/#san-lead"


def report_text(hours=26, run_id=None, stats=None, cost=0.0, status="ok", message=""):
    since = int(time.time() - hours * 3600) if hours else 0
    opps = owui("GET", "/opportunities?" + urllib.parse.urlencode({"state": "moi", "sort": "score", "limit": 200}))["items"]
    new = [o for o in opps if (o.get("run_id") == run_id if run_id else o["first_seen"] >= since)]
    lines = []
    if stats is not None:
        lines.append(f"**Lần quét {'xong' if status == 'ok' else 'xong một phần' if status == 'partial' else 'lỗi'}**: đọc "
                     f"{stats['candidates']} tin mới, **{stats['created']} cơ hội mới**, {stats['merged']} cơ hội gặp lại "
                     f"(thêm nguồn), {stats['people_created']} người liên hệ mới. Chi phí Apify ${cost:.2f}.")
        if message:
            lines.append(f"Lưu ý: {message}.")
    else:
        lines.append(f"**{len(new)} cơ hội mới** trong {hours} giờ qua (đang ở mục Mới).")
    if new:
        lines.append("")
        lines.append("| Điểm | Doanh nghiệp | Loại | Tỉnh | Hạn / ngày tin | Thiết bị |")
        lines.append("|---|---|---|---|---|---|")
        for o in new[:15]:
            when = f"hạn {'/'.join(reversed(o['deadline'].split('-')))}" if o.get("deadline") else (
                dt.datetime.fromtimestamp(o["published_at"], VN).strftime("%d/%m/%Y") if o.get("published_at") else "")
            equip = ", ".join(o["equipment"][:3]) + (" (gợi ý)" if o["equipment_inferred"] and o["equipment"] else "")
            link = next((x["url"] for x in o["sources"] if "news.google.com" not in x["url"]), o["sources"][0]["url"] if o["sources"] else "")
            company = f"[{o['company']}]({link})" if link else o["company"]
            lines.append(f"| {o['score']} | {company} | {o['kind_label']} | {o['province'] or '?'} | {when} | {equip} |")
        if len(new) > 15:
            lines.append(f"\n… và {len(new) - 15} cơ hội khác.")
    lines.append(f"\nXem đủ, đổi trạng thái, xuất CSV: {page_url()}")
    return "\n".join(lines)


# ---------------------------------------------------------------- lenh


def cmd_status(_):
    cfg = owui("GET", "/agent/config")
    s, k = cfg["settings"], cfg["apify"]
    print(f"Key Apify: {'có (••••' + k['last4'] + ')' if k['set'] else 'CHƯA CÓ (Open WebUI > Săn lead > Cài đặt)'}")
    if k.get("limit_usd"):
        print(f"Apify tháng này: ${k.get('used_usd') or 0:.2f} / ${k['limit_usd']:.2f} (gói {k.get('plan')})")
    print(f"Agent đã tiêu tháng này (theo các lần quét): ${cfg['month_cost_usd']:.2f}; trần mỗi lần ${s['max_usd_per_run']}, "
          f"trần tháng ${s['max_usd_per_month']}")
    print(f"LLM: {cfg['llm'].get('model') or cfg['llm'].get('error')}")
    print("Ngành: " + ", ".join(cfg["industries"][i] for i in s["industries"]))
    print("Tỉnh: " + ", ".join(s["provinces"]))
    print("Nguồn: " + ", ".join(k2 for k2, v in s["sources"].items() if v))
    print(f"Hàng bên bán: {s['seller'].get('products') or '(chưa ghi: nhắc user ghi trong Cài đặt để chấm điểm sát hơn)'}")
    runs = owui("GET", "/runs?limit=3")
    for r in runs:
        print(f"Lần quét {dt.datetime.fromtimestamp(r['started_at'], VN).strftime('%d/%m %H:%M')}: {r['status']}, "
              f"{r['stats'].get('created', 0)} mới, ${r['cost_usd']:.2f} {r['message']}")


def cmd_run(args):
    if args.quiet:
        os.makedirs(STATE, exist_ok=True)
        LOG_FILE.append(os.path.join(STATE, f"run-{dt.datetime.now(VN).strftime('%Y%m%d-%H%M%S')}.log"))
    run(args.trigger)


def cmd_start(args):
    os.makedirs(STATE, exist_ok=True)
    stamp = dt.datetime.now(VN).strftime("%Y%m%d-%H%M%S")
    path = os.path.join(STATE, f"run-{stamp}.log")
    with open(path, "w", encoding="utf-8") as out:
        proc = subprocess.Popen([sys.executable, "-I", os.path.abspath(__file__), "run", "--trigger", args.trigger],
                                stdout=out, stderr=subprocess.STDOUT, start_new_session=True, cwd=SKILL,
                                env={**os.environ, "PYTHONUNBUFFERED": "1"})
    with open(os.path.join(STATE, "last-run.json"), "w", encoding="utf-8") as f:
        json.dump({"pid": proc.pid, "log": path, "started": stamp}, f)
    print(f"Đã bắt đầu lần quét ở nền (mã {stamp}). Chạy: python3 -I scripts/lead.py wait {stamp}")


def _alive(pid):
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    try:  # zombie (tien trinh con da xong)
        with open(f"/proc/{pid}/stat", encoding="utf-8") as f:
            return f.read().split()[2] != "Z"
    except OSError:
        return True


def cmd_wait(args):
    path = os.path.join(STATE, f"run-{args.run}.log")
    meta_path = os.path.join(STATE, "last-run.json")
    pid = None
    try:
        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)
        if meta.get("started") == args.run:
            pid = meta["pid"]
    except (OSError, ValueError):
        pass
    if not os.path.exists(path):
        die(f"Không thấy lần quét {args.run}.")
    deadline = time.time() + args.max
    shown = 0
    while True:
        with open(path, encoding="utf-8") as f:
            content = f.read()
        lines = content.splitlines()
        for line in lines[shown:]:
            print(line)
        shown = len(lines)
        done = "Xong lần quét" in content or (pid is not None and not _alive(pid))
        if done:
            if "Xong lần quét" not in content:
                print("Lần quét đã dừng mà không xong (xem log ở trên).")
            return
        if time.time() > deadline:
            print(f"\n(chưa xong, chạy lại: python3 -I scripts/lead.py wait {args.run})")
            return
        time.sleep(5)


def cmd_collect(args):
    """Thu tin (khong goi LLM, khong danh dau da doc) ra file, de do va chinh prompt tren cung 1 bo tin."""
    cfg = owui("GET", "/agent/config")
    stats, notes = {}, []
    items = gather(cfg, Budget(cfg), stats, notes, check_seen=not args.all)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=1)
    print(f"{len(items)} tin -> {args.out} {stats} {notes}")


def cmd_extract(args):
    """Doc 1 file tin bang LLM, in ket qua (khong luu len San lead)."""
    cfg = owui("GET", "/agent/config")
    if args.model:
        cfg["llm"]["model"] = args.model
    with open(args.inp, encoding="utf-8") as f:
        items = json.load(f)
    if args.limit:
        items = items[: args.limit]
    verdicts, opportunities, failed = read_items(cfg, items)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"verdicts": verdicts, "opportunities": opportunities, "failed": failed}, f, ensure_ascii=False, indent=1)
    print(f"{len(opportunities)} giữ / {len(items)} tin, {failed} lỗi -> {args.out}")


def cmd_report(args):
    print(report_text(hours=args.hours))


def cmd_top(args):
    data = owui("GET", "/opportunities?" + urllib.parse.urlencode({"state": "moi", "sort": "score", "limit": args.limit}))
    for o in data["items"]:
        print(f"{o['score']:>3} | {o['company']} | {o['kind_label']} | {o['province'] or '?'} | {o['title'][:60]} | id {o['id']}")
    print(f"\nTổng {data['total']} cơ hội ở mục Mới. Trang: {page_url()}")


def cmd_people(args):
    cfg = owui("GET", "/agent/config")
    o = owui("GET", f"/opportunities/{args.opportunity}")
    budget = Budget(cfg)
    people = people_for(cfg, budget, cfg["llm"], [o])
    if people:
        done = owui("POST", "/agent/people", {"items": people})
        print(f"{len(done['created'])} người mới, {len(done['merged'])} đã có. Chi phí ${budget.spent:.3f}")
        for p in people:
            print(f"- {p.get('name')} | {p.get('title')} | {p.get('linkedin_url')}")
    else:
        print(f"Không tìm thấy người phù hợp. {budget.stopped}")


def cmd_check_sources(_):
    cfg = owui("GET", "/agent/config")
    for page in watch_list(cfg):
        links = page_links(page)
        print(f"{'OK ' if links else 'LỖI'} {page['label']}: {len(links) if links is not None else 'không đọc được'} link | {page['url']}")


def main():
    ap = argparse.ArgumentParser(description="Săn lead B2B (Open WebUI > Săn lead)")
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("status").set_defaults(f=cmd_status)
    for name, fn in (("run", cmd_run), ("start", cmd_start)):
        p = sp.add_parser(name)
        p.add_argument("--trigger", default="chat", choices=["chat", "cron", "test"])
        p.add_argument("--quiet", action="store_true", help="tien do ghi vao state/run-*.log, chi in bao cao (cho cron)")
        p.set_defaults(f=fn)
    p = sp.add_parser("wait")
    p.add_argument("run")
    p.add_argument("--max", type=int, default=170)
    p.set_defaults(f=cmd_wait)
    p = sp.add_parser("report")
    p.add_argument("--hours", type=int, default=26)
    p.set_defaults(f=cmd_report)
    p = sp.add_parser("top")
    p.add_argument("--limit", type=int, default=10)
    p.set_defaults(f=cmd_top)
    p = sp.add_parser("people")
    p.add_argument("--opportunity", required=True)
    p.set_defaults(f=cmd_people)
    sp.add_parser("check-sources").set_defaults(f=cmd_check_sources)
    p = sp.add_parser("collect")
    p.add_argument("--out", required=True)
    p.add_argument("--all", action="store_true", help="ca tin da doc o lan truoc")
    p.set_defaults(f=cmd_collect)
    p = sp.add_parser("extract")
    p.add_argument("--in", dest="inp", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--model", default="")
    p.add_argument("--limit", type=int, default=0)
    p.set_defaults(f=cmd_extract)
    args = ap.parse_args()
    signal.signal(signal.SIGPIPE, signal.SIG_DFL) if hasattr(signal, "SIGPIPE") else None
    try:
        args.f(args)
    except RuntimeError as error:
        die(str(error))


if __name__ == "__main__":
    main()
