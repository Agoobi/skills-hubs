#!/usr/bin/env python3
"""San lead B2B cho Hermes: quet tin hieu mua thiet bi, doc tin bang LLM, tim nguoi ra quyet dinh, ghi vao trang
"San lead" cua Open WebUI (openwebui-custom, /api/v1/cqf/lead).

Chi can Python 3 (thu vien chuan). Key Apify, cai dat va LLM lay tu Open WebUI qua token trong
<DATA_DIR cua Open WebUI>/cqf/lead/agent.json (cung may). Dia chi API: env LEAD_API, mac dinh
http://127.0.0.1:8080/api/v1/cqf/lead.

    lead.py status                     key, cai dat, chi phi thang, lan quet gan nhat
    lead.py start [--trigger chat]     chay 1 lan quet o nen, in run id (lan quet dai hon gioi han lenh cua agent)
    lead.py start --full               quet day du: moi nhom truy van, doc lai nhieu link hon (lan dau / quet lai)
    lead.py wait <run_id>              cho toi 170 giay, in tien do; xong thi in bao cao
    lead.py run [--trigger chat]       chay 1 lan quet ngay trong lenh nay (in tien do + bao cao)
    lead.py report [--hours 26]        bao cao co hoi / nguoi moi tim thay
    lead.py top [--limit 10]           co hoi diem cao dang o trang thai Moi
    lead.py people --opportunity <id>  tim nguoi ra quyet dinh cho 1 co hoi
    lead.py contacts [--limit 10]      tim website, SDT, email, MST, LinkedIn cong ty cho co hoi chua co lien he
    lead.py check-sources              thu tung trang theo doi (doc duoc khong, bao nhieu link)
"""

import argparse
import concurrent.futures
import datetime as dt
import email.utils
import gzip
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
FULL = os.environ.get("LEAD_FULL") == "1"  # quet day du: moi nhom truy van trong 1 luot (lan dau / quet lai tu dau)
FULL_MAX_USD = float(os.environ.get("LEAD_FULL_MAX_USD") or 1.5)  # tran 1 luot quet day du (tran thang van giu)
APIFY_NOTES = []  # Apify bao het luot / loi: ghi vao lan quet
LIMITED = set()  # actor Apify da het luot trong lan quet nay: khong goi nua
LLM_WORKERS = int(os.environ.get("LEAD_LLM_WORKERS") or 1)  # 1: cong LLM giu tien theo tung request dong thoi, vi it tien thi song song bi 402
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
    ["tủ sấy", "tủ ấm", "lò nung", "cân phân tích", "máy ly tâm"],
    ["tủ cấy vi sinh", "nồi hấp tiệt trùng", "tủ lạnh âm sâu", "máy đếm khuẩn lạc", "tủ hút khí độc"],
    ["máy đo TOC", "máy đo BOD", "máy phân tích NIR", "máy phá mẫu vi sóng", "máy đo pH"],
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
    # --- DTM cua tinh
    {"url": "https://www.camau.gov.vn/danh-gia-tac-dong-moi-truong-child", "label": "ĐTM tỉnh Cà Mau", "kind": "dtm"},
    {"url": "https://snnmt.khanhhoa.gov.vn/danh-sach-tin/categoryid/quyet-dinh-phe-duyet-dtm?BCMenu=BCM_9066",
     "label": "ĐTM tỉnh Khánh Hòa", "kind": "dtm"},
    # --- Ban Quan ly KCN / KKT va Xuc tien dau tu (sau sap nhap 1/7/2025, moi tinh 1 trang)
    {"url": "https://investdanang.gov.vn/web/guest/dau-thau-mua-sam-cong", "label": "XTĐT Đà Nẵng: đấu thầu", "kind": "kcn"},
    {"url": "https://investdanang.gov.vn/web/guest/thong-tin-dau-tu", "label": "XTĐT Đà Nẵng: thông tin đầu tư", "kind": "kcn"},
    {"url": "https://chulaikkt.danang.gov.vn/tin-tuc-su-kien", "label": "BQL KKT Chu Lai", "kind": "kcn"},
    {"url": "https://dungquat.quangngai.gov.vn/page/cong-khai-va-thong-bao-110913", "label": "BQL KKT Dung Quất: thông báo", "kind": "kcn"},
    {"url": "https://dungquat.quangngai.gov.vn/category/3135363-3135372/kinh-te-xuc-tien-dau-tu", "label": "BQL KKT Dung Quất: xúc tiến đầu tư", "kind": "kcn"},
    {"url": "https://bqlkkt.gialai.gov.vn/vi/news/tin-tuc/", "label": "BQL KKT Gia Lai: tin tức", "kind": "kcn"},
    {"url": "https://bqlkcn.daklak.gov.vn/thong-bao.html", "label": "BQL KCN Đắk Lắk: thông báo", "kind": "kcn"},
    {"url": "https://bqlkcn.daklak.gov.vn/p/tin-tuc-su-kien/thong-tin-doanh-nghiep-khu-cong-nghiep.html", "label": "BQL KCN Đắk Lắk: doanh nghiệp", "kind": "kcn"},
    {"url": "https://ipc.daklakdpi.gov.vn/tin-nhom/chu-truong-du-an-1.html", "label": "XTĐT Đắk Lắk: chủ trương dự án", "kind": "kcn"},
    {"url": "https://vanphong.khanhhoa.gov.vn/thong-bao-moi-thau", "label": "BQL KKT Vân Phong: mời thầu", "kind": "kcn"},
    {"url": "https://vanphong.khanhhoa.gov.vn/doanh-nghiep-606", "label": "BQL KKT Vân Phong: doanh nghiệp", "kind": "kcn"},
    {"url": "https://dnieza.dongnai.gov.vn/Pages/thongbao.aspx", "label": "BQL KCN Đồng Nai: thông báo", "kind": "kcn"},
    {"url": "https://dnieza.dongnai.gov.vn/Pages/news.aspx?CatId=100", "label": "BQL KCN Đồng Nai: đầu tư", "kind": "kcn"},
    {"url": "https://dnieza.dongnai.gov.vn/Pages/news.aspx?CatId=105", "label": "BQL KCN Đồng Nai: tin", "kind": "kcn"},
    # cac cong duoi day chan may chu nuoc ngoai: can proxy Viet Nam (state/proxy), khong co thi doc qua Google site:
    {"url": "https://ipc.quangngai.gov.vn/tin-tuc-thuong-mai", "label": "XTĐT Quảng Ngãi", "kind": "kcn"},
    {"url": "https://bqlkkt.gialai.gov.vn/vi/news/thong-bao/", "label": "BQL KKT Gia Lai: thông báo", "kind": "kcn"},
    {"url": "https://ipa.khanhhoa.gov.vn/du-an-chap-thuan-nha-dau-tu", "label": "XTĐT Khánh Hòa: dự án chấp thuận", "kind": "kcn"},
    {"url": "https://ipa.khanhhoa.gov.vn/du-an-dau-thau-dau-gia", "label": "XTĐT Khánh Hòa: đấu thầu", "kind": "kcn"},
    {"url": "https://liza.lamdong.gov.vn/tin-tuc-su-kien", "label": "BQL KCN Lâm Đồng", "kind": "kcn"},
    {"url": "https://liza.lamdong.gov.vn/thong-tin-doanh-nghiep", "label": "BQL KCN Lâm Đồng: doanh nghiệp", "kind": "kcn"},
    {"url": "https://bqlkkt.tayninh.gov.vn/thong-bao", "label": "BQL KKT Tây Ninh: thông báo", "kind": "kcn"},
    {"url": "https://bqlkkt.tayninh.gov.vn/tin-tuc-trong-nganh-74829", "label": "BQL KKT Tây Ninh: tin ngành", "kind": "kcn"},
    {"url": "https://bqlkkt.dongthap.gov.vn/tin-tuc", "label": "BQL KKT Đồng Tháp", "kind": "kcn"},
    {"url": "https://bqlkkt.dongthap.gov.vn/đấu-thầu", "label": "BQL KKT Đồng Tháp: đấu thầu", "kind": "kcn"},
    {"url": "https://bqlkkt.vinhlong.gov.vn/tin-tuc-su-kien", "label": "BQL KKT Vĩnh Long", "kind": "kcn"},
    {"url": "https://cepiza.cantho.gov.vn/du-an-dau-thau-va-mua-sam-cong", "label": "BQL KCX-KCN Cần Thơ: đấu thầu", "kind": "kcn"},
    {"url": "https://cepiza.cantho.gov.vn/thong-bao", "label": "BQL KCX-KCN Cần Thơ: thông báo", "kind": "kcn"},
    {"url": "https://cepiza.cantho.gov.vn/ke-hoach-dau-tu", "label": "BQL KCX-KCN Cần Thơ: đầu tư", "kind": "kcn"},
    {"url": "https://dav.gov.vn/thong-bao-cn1.html", "label": "Cục Quản lý Dược: thông báo", "kind": "assoc"},
    {"url": "https://banqlkkt.camau.gov.vn/tin-tuc-su-kien", "label": "BQL KKT Cà Mau", "kind": "kcn"},
    {"url": "https://banqlkkt.camau.gov.vn/hoat-dong-kinh-doanh-xuc-tien-dau-tu", "label": "BQL KKT Cà Mau: xúc tiến đầu tư", "kind": "kcn"},
    {"url": "https://bqlkkt.angiang.gov.vn/thong-tin-dau-thau", "label": "BQL KKT An Giang: đấu thầu", "kind": "kcn"},
    {"url": "https://bqlkkt.angiang.gov.vn/tin-doanh-nghiep", "label": "BQL KKT An Giang: doanh nghiệp", "kind": "kcn"},
    # --- Hiep hoi, Cuc, bao dau thau
    {"url": "https://vasep.com.vn/thong-bao", "label": "VASEP: thông báo", "kind": "assoc"},
    {"url": "https://vasep.com.vn/tieu-diem", "label": "VASEP: tiêu điểm", "kind": "assoc"},
    {"url": "https://cucthuy.gov.vn/web/guest/tin-tuyen-dung-dau-thau", "label": "Cục Chăn nuôi và Thú y: đấu thầu", "kind": "assoc"},
    {"url": "https://baodauthau.vn/thong-bao-moi-thau/", "label": "Báo Đấu thầu: thông báo mời thầu", "kind": "tender_board"},
    # --- don vi cong co phong thi nghiem: thong bao moi chao gia / chao hang canh tranh (thiet bi, vat tu, sua chua)
    {"url": "https://kiemnghiemhcm.gov.vn/", "label": "TT Kiểm nghiệm TP.HCM: thông báo", "kind": "lab_buyer",
     "company": "Trung tâm Kiểm nghiệm thuốc, mỹ phẩm, thực phẩm TP. Hồ Chí Minh", "industry": "duoc", "province": "TP. Hồ Chí Minh"},
    {"url": "https://vienkiemnghiem.gov.vn/", "label": "Viện Kiểm nghiệm thuốc TP.HCM", "kind": "lab_buyer",
     "company": "Viện Kiểm nghiệm thuốc TP. Hồ Chí Minh", "industry": "duoc", "province": "TP. Hồ Chí Minh"},
    {"url": "https://ump.edu.vn/thong-tin-dau-thau/thong-bao-moi-chao-gia", "label": "ĐH Y Dược TP.HCM: mời chào giá",
     "kind": "lab_buyer", "company": "Đại học Y Dược Thành phố Hồ Chí Minh", "industry": "duoc", "province": "TP. Hồ Chí Minh"},
    {"url": "https://kiemnghiemgialai.vn/chuyen-muc/mua-sam/thu-moi-bao-gia/", "label": "TT Kiểm nghiệm Gia Lai: thư mời báo giá",
     "kind": "lab_buyer", "company": "Trung tâm Kiểm nghiệm thuốc, mỹ phẩm, thực phẩm Gia Lai", "industry": "duoc",
     "province": "Gia Lai"},
    {"url": "https://sochemvn.com/", "label": "Hóa chất Cơ bản Miền Nam: thư mời chào giá", "kind": "tender",
     "company": "Công ty Cổ phần Hóa chất Cơ bản Miền Nam", "industry": "cam_hoa_chat", "province": "Đồng Nai"},
    {"url": "https://kiemnghiemdanang.vn/", "label": "TT Kiểm nghiệm Đà Nẵng", "kind": "lab_buyer",
     "company": "Trung tâm Kiểm nghiệm thuốc, mỹ phẩm, thực phẩm Đà Nẵng", "industry": "duoc", "province": "Đà Nẵng"},
    # --- trang moi thau / tin tuc cua doanh nghiep lon
    {"url": "https://dhgpharma.com.vn/vi/thong-bao", "label": "Thông báo DHG Pharma", "kind": "tender",
     "company": "Công ty Cổ phần Dược Hậu Giang", "industry": "duoc", "province": "Cần Thơ"},
    {"url": "https://bidiphar.com/category/thong-tin-moi-thau/", "label": "Mời thầu Bidiphar", "kind": "tender",
     "company": "Công ty Cổ phần Dược - Trang thiết bị Y tế Bình Định (Bidiphar)", "industry": "duoc", "province": "Gia Lai"},
    {"url": "https://domesco.com/tin-tuc/thong-bao-moi-thau.html", "label": "Mời thầu Domesco", "kind": "tender",
     "company": "Công ty Cổ phần Xuất nhập khẩu Y tế Domesco", "industry": "duoc", "province": "Đồng Tháp"},
    {"url": "https://navicorp.com.vn/vi/thong-bao-moi-thau", "label": "Mời thầu Navico", "kind": "tender",
     "company": "Công ty Cổ phần Nam Việt (Navico)", "industry": "thuy_san", "province": "An Giang"},
    {"url": "https://www.minhphu.com/tin-tuc/", "label": "Tin Minh Phú", "kind": "company",
     "company": "Công ty Cổ phần Tập đoàn Thủy sản Minh Phú", "industry": "thuy_san", "province": "Cà Mau"},
    {"url": "https://www.vinhhoan.com/category/news/", "label": "Tin Vĩnh Hoàn", "kind": "company",
     "company": "Công ty Cổ phần Vĩnh Hoàn", "industry": "thuy_san", "province": "Đồng Tháp"},
    {"url": "https://vietuc.com/truyen-thong/thong-tin-bao-chi/tin-tuc-su-kien/", "label": "Tin Việt Úc", "kind": "company",
     "company": "Công ty Cổ phần Tập đoàn Việt Úc", "industry": "thuy_san"},
    {"url": "https://www.masangroup.com/news/masan-news/", "label": "Tin Masan", "kind": "company",
     "company": "Công ty Cổ phần Tập đoàn Masan", "industry": "fnb"},
    {"url": "https://www.greenfeed.com.vn/chuyen-muc/tin-tuc-va-su-kien/", "label": "Tin GreenFeed", "kind": "company",
     "company": "Công ty Cổ phần GreenFeed Việt Nam", "industry": "cam_hoa_chat"},
]
WATCH_FIRST_VISIT = 30 if FULL else 10  # trang moi them: lan dau chi doc vai link dau (moi nhat)
# Cong chan IP nuoc ngoai (may chu o Singapore khong mo duoc) hoac chi co file: doc qua Google (site:), khong vuot chan.
SITE_GROUPS_DTM = [
    ["sonnmt.cantho.gov.vn", "snnmt.tayninh.gov.vn", "snnmt.angiang.gov.vn"],
    ["lamdong.gov.vn", "snnmt.dongnai.gov.vn", "vinhlong.gov.vn"],
    ["dongthap.gov.vn", "hepza.hochiminhcity.gov.vn", "sonnmt.hochiminhcity.gov.vn"],
    ["snnmt.daklak.gov.vn", "snnmt.gialai.gov.vn", "chulaikkt.danang.gov.vn", "thamvan.mae.gov.vn"],
]
# Ban quan ly KCN / KKT: trang chay JavaScript hoac chan IP nuoc ngoai -> doc qua Google (cap GCN, chu truong, khoi cong)
# (cac cong nay chan may chu o nuoc ngoai hoac chay JavaScript: kiem tra 18/11/2026 tu may chu Singapore)
SITE_GROUPS_KCN = [
    ["hepza.hochiminhcity.gov.vn", "dseza.danang.gov.vn", "cepiza.cantho.gov.vn", "ipc.quangngai.gov.vn"],
    ["bqlkkt.dongthap.gov.vn", "bqlkkt.vinhlong.gov.vn", "bqlkkt.tayninh.gov.vn", "liza.lamdong.gov.vn"],
    ["ipa.khanhhoa.gov.vn", "bqlkkt.gialai.gov.vn", "dav.gov.vn", "bqlkkt.angiang.gov.vn"],
]
# Mua sam cong: muasamcong khong co du lieu mo; doc cac trang tong hop cong khai qua Google
LAB_BUYER_QUERIES = [
    '"mời chào giá" ("trung tâm kiểm nghiệm" OR "viện kiểm nghiệm")',
    '"chào hàng cạnh tranh" "thiết bị" ("kiểm nghiệm" OR "thí nghiệm")',
    '"mời chào giá" ("chi cục thú y" OR "chẩn đoán thú y" OR "chăn nuôi và thú y")',
    '"mời chào giá" ("viện nghiên cứu" OR "trường đại học") "thiết bị thí nghiệm"',
    '"mời báo giá" ("HPLC" OR "sắc ký" OR "quang phổ" OR "tủ an toàn sinh học")',
    '"mời chào giá" ("chất lượng nông lâm thủy sản" OR "kiểm định" OR "Quatest")',
    '"mời chào giá" ("hóa chất" OR "vật tư") ("thí nghiệm" OR "kiểm nghiệm")',
    '"thông báo mời chào giá" ("thủy sản" OR "thức ăn chăn nuôi" OR "dược phẩm" OR "thực phẩm") "thiết bị"',
]
SITE_TENDER_PORTALS = ["muasamcong.mof.gov.vn", "dauthau.asia", "bidwinner.info", "baodauthau.vn", "thongtindauthau.com.vn"]
JOB_SITES = ["jobsgo.vn", "careerviet.vn", "vietnamworks.com", "123job.vn", "topcv.vn", "joboko.com"]
SITE_GROUPS_TENDER = [
    ["domesco.com", "navicorp.com.vn", "imexpharm.com", "pymepharco.com"],
    ["vinhhoan.com", "minhphu.com", "fimexvn.com", "idiseafood.com"],
    ["vienkiemnghiem.gov.vn", "nifc.gov.vn", "vinamilk.com.vn", "greenfeed.com.vn"],
    ["cp.com.vn", "vietuc.com", "masangroup.com", "deheus.com.vn", "vissan.com.vn", "dav.gov.vn", "cucthuy.gov.vn"],
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


def _proxy_url():
    """Proxy Viet Nam (tuy chon): env LEAD_PROXY hoac file state/proxy (1 dong http://user:pass@host:port, chmod 600).
    Chi dung cho trang chan IP nuoc ngoai (.gov.vn) - doc nhu nguoi o Viet Nam, khong vuot captcha / chong bot."""
    value = os.environ.get("LEAD_PROXY", "").strip()
    if not value:
        try:
            with open(os.path.join(STATE, "proxy"), encoding="utf-8") as f:
                value = f.read().strip()
        except OSError:
            value = ""
    if value and not value.startswith(("http://", "https://", "socks")):
        parts = value.split(":")  # host:port:user:pass
        if len(parts) == 4:
            value = f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
    return value


PROXY = _proxy_url()


def _use_proxy_first(url):
    return bool(PROXY) and _host_of(url).endswith(".gov.vn")


def _host_of(url):
    return urllib.parse.urlsplit(url).netloc.lower().split("@")[-1].split(":")[0]


def _fetch_once(url, timeout, limit, proxy):
    """(html, final_url, ok)."""
    url = urllib.parse.quote(url, safe=":/?&=%#+,;@!$'()*[]~")  # duong dan co dau (VD /đấu-thầu)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "vi,en;q=0.8", "Accept-Encoding": "gzip"})
    for lenient in (False, True):
        handlers = [urllib.request.HTTPSHandler(context=_ssl_context(lenient))]
        handlers.append(urllib.request.ProxyHandler({"http": proxy, "https": proxy} if proxy else {}))
        opener = urllib.request.build_opener(*handlers)
        try:
            with opener.open(req, timeout=timeout) as res:
                ctype = res.headers.get("Content-Type", "")
                if "html" not in ctype and "xml" not in ctype and ctype:
                    return "", res.geturl(), True
                raw = res.read(limit)
                if res.headers.get("Content-Encoding", "").lower() == "gzip" or raw[:2] == bytes([0x1F, 0x8B]):
                    try:
                        raw = gzip.decompress(raw)
                    except (OSError, EOFError):
                        pass
                charset = (res.headers.get_content_charset() or "utf-8").split(",")[0].strip()
                try:
                    return raw.decode(charset, "replace"), res.geturl(), True
                except LookupError:  # bang ma la ("utf-8,gbk", "none"...)
                    return raw.decode("utf-8", "replace"), res.geturl(), True
        except ssl.SSLError:
            continue
        except urllib.error.HTTPError:
            return "", url, False
        except urllib.error.URLError as error:
            if isinstance(getattr(error, "reason", None), ssl.SSLError) and not lenient:
                continue
            return "", url, False
        except (TimeoutError, OSError, ValueError):
            return "", url, False
    return "", url, False


def fetch_text(url, timeout=18, limit=1_600_000):
    """(html, final_url) of a page; '' on failure. Lenient TLS for .gov.vn. Cong .gov.vn di qua proxy Viet Nam neu co;
    loi thi thu duong con lai (truc tiep <-> proxy)."""
    first = PROXY if _use_proxy_first(url) else ""
    raw, final, ok = _fetch_once(url, timeout, limit, first)
    if not ok and PROXY:
        raw, final, ok = _fetch_once(url, timeout, limit, "" if first else PROXY)
    return raw, final


def load_config():
    """Cau hinh tu trang San lead; proxy nhap o Cai dat (uu tien hon env LEAD_PROXY / file state/proxy)."""
    global PROXY
    cfg = owui("GET", "/agent/config")
    if cfg.get("proxy"):
        PROXY = cfg["proxy"]
    return cfg


def strip_html(raw):
    raw = re.sub(r"(?is)<(script|style|noscript|svg|header|footer|nav|form|iframe)\b.*?</\1>", " ", raw)
    raw = re.sub(r"(?is)<br\s*/?>|</p>|</div>|</li>|</h\d>", "\n", raw)
    text = html.unescape(re.sub(r"(?s)<[^>]+>", " ", raw))
    lines = [re.sub(r"[ \t ]+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if len(line) > 1)


def plain_text(raw):
    """Toan bo chu cua trang, giu header / footer (noi hay ghi dia chi, SDT, email)."""
    raw = re.sub(r"(?is)<(script|style|noscript|svg|iframe)\b.*?</\1>", " ", raw)
    raw = re.sub(r"(?is)<br\s*/?>|</p>|</div>|</li>|</h\d>|</tr>|</td>", "\n", raw)
    text = html.unescape(re.sub(r"(?s)<[^>]+>", " ", raw))
    lines = [re.sub(r"[ \t\u00a0]+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if len(line) > 1)


PHONE_RE = re.compile(r"(?<![\d.,])(?:\(?\+?84\)?[ \t.\-]?\(?0?\)?|\(?0)(?:\d[ \t.\-)]{0,2}){8,10}(?![\d])"
                      r"|(?<![\d.,])(?:1800[\s.\-]?\d{2}[\s.\-]?\d{2}|1900[\s.\-]?\d{2,3}[\s.\-]?\d{2,3})(?![\d])")
EMAIL_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._%+-]*@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
CONTACT_WORDS = ("liên hệ", "điện thoại", "đt:", "đt :", "tel", "hotline", "email", "e-mail", "fax", "di động", "zalo")


def contact_lines(text, limit=700):
    """Dong co SDT / email / 'lien he' trong trang (thu moi chao gia ghi dau moi o cuoi, hay bi cat)."""
    out, used = [], 0
    for line in text.splitlines():
        low = line.lower()
        if PHONE_RE.search(line) or EMAIL_RE.search(line) or any(w in low for w in CONTACT_WORDS):
            line = line[:220]
            if used + len(line) > limit:
                break
            out.append(line)
            used += len(line) + 1
    return "\n".join(out)


def phone_digits(value):
    d = re.sub(r"\D", "", str(value or ""))
    if d.startswith("84") and len(d) in (11, 12):
        d = "0" + d[2:]
    return d


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


DEADLINE_RE = re.compile(
    r"(?i)(hạn cuối|hạn chót|hạn nộp|thời hạn (?:nhận|nộp|gửi)|thời điểm đóng thầu|đóng thầu|hết hạn|trước \d{1,2}\s*(?:h|giờ))"
    r"[^\n]{0,80}?\b(\d{1,2})[/.-](\d{1,2})[/.-](20\d\d)\b")


def deadline_in(text):
    """Han nop ho so / bao gia ghi trong trang -> YYYY-MM-DD; khong thay thi ""."""
    m = DEADLINE_RE.search(text or "")
    if not m:
        return ""
    try:
        return dt.date(int(m.group(4)), int(m.group(3)), int(m.group(2))).isoformat()
    except ValueError:
        return ""


def text_date(text):
    """Ngay dd/mm/yyyy (hoac dd-mm-yyyy) trong tieu de / doan trich -> YYYY-MM-DD; khong co thi ""."""
    m = re.search(r"\b(\d{1,2})[/.-](\d{1,2})[/.-](20\d\d)\b", text or "")
    if not m:
        return ""
    try:
        return dt.date(int(m.group(3)), int(m.group(2)), int(m.group(1))).isoformat()
    except ValueError:
        return ""


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
        if FULL:
            self.per_run = max(self.per_run, FULL_MAX_USD)
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
    if actor in LIMITED:
        return [], 0.0
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
    message = str(final.get("statusMessage") or "")
    if final.get("status") not in ("SUCCEEDED",):
        log(f"{what}: Apify trạng thái {final.get('status')} ({message})")
    if "limit reached" in message.lower():  # goi Apify mien phi het luot dung actor nay
        name = "LinkedIn" if actor == ACTOR_LINKEDIN else "Google"
        note = f"{name} (Apify): gói miễn phí hết lượt dùng ({message}); cần nâng gói Apify để tìm tiếp"
        LIMITED.add(actor)
        if note not in APIFY_NOTES:
            log(note)
            APIFY_NOTES.append(note)
    return items if isinstance(items, list) else [], cost


GOOGLE_BATCH = 40  # moi luot Apify toi da 40 truy van (~3 phut), nhieu hon thi qua thoi gian cho


def google_search(budget, queries, after):
    if not queries:
        return []
    if len(queries) > GOOGLE_BATCH:  # quet day du: chia lo
        out = []
        for i in range(0, len(queries), GOOGLE_BATCH):
            out += google_search(budget, queries[i:i + GOOGLE_BATCH], after)
        return out
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


# Model du phong: LEAD_LLM_MODELS="a,b,c". Model dang dung het tien (402) hoac het luot (429) thi chuyen sang model sau.
_models = {"list": [], "at": 0}
_models_lock = __import__("threading").Lock()


def _current_model(llm):
    with _models_lock:
        if not _models["list"]:
            extra = [m.strip() for m in os.environ.get("LEAD_LLM_MODELS", "").split(",") if m.strip()]
            _models["list"] = extra or [llm["model"]]
        return _models["list"][_models["at"]] if _models["at"] < len(_models["list"]) else None


def _next_model(failed):
    with _models_lock:
        if _models["at"] < len(_models["list"]) and _models["list"][_models["at"]] == failed:
            _models["at"] += 1
            if _models["at"] < len(_models["list"]):
                log(f"Model {failed} hết tiền / hết lượt, chuyển sang {_models['list'][_models['at']]}")
        return _models["at"] < len(_models["list"])


def llm_chat(llm, system, user, max_tokens=3500):
    if llm.get("error"):
        raise RuntimeError(f"LLM: {llm['error']}")
    if _wallet_empty:
        raise WalletEmpty(_wallet_empty[0])
    last = None
    for attempt in range(4):
        model = _current_model(llm)
        if model is None:
            raise WalletEmpty(_wallet_empty[0] if _wallet_empty else "mọi model đều hết tiền / hết lượt")
        body = {"model": model, "temperature": 0, "max_tokens": max_tokens,
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
            if "-> 402" in str(error) or ("-> 429" in str(error) and "hết lượt" in str(error)):
                if _next_model(model):
                    continue
                message = ("ví LLM của Hermes hết tiền (402): nạp thêm rồi quét lại" if "-> 402" in str(error)
                           else "model LLM hết lượt hôm nay (429)")
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
  moi_thau = mời thầu / thư mời chào giá / chào giá cạnh tranh / chào hàng cạnh tranh / yêu cầu báo giá cho MÁY MÓC,
             THIẾT BỊ, DÂY CHUYỀN, THIẾT BỊ PHÒNG THÍ NGHIỆM, ĐO LƯỜNG, KIỂM NGHIỆM, HỆ THỐNG ĐÓNG GÓI. Gồm cả gói mua
             thiết bị lab / kiểm nghiệm của viện nghiên cứu, trường đại học, trung tâm kiểm nghiệm, chi cục, cơ quan nhà
             nước thuộc lĩnh vực thủy sản, thú y, chăn nuôi, dược, thực phẩm, nông nghiệp, hóa học (ghi industry là ngành
             gần nhất trong 7 mã); company = tên đơn vị mời thầu. Cũng là moi_thau: gói bảo dưỡng, sửa chữa, hiệu
             chuẩn, phụ tùng thiết bị phòng thí nghiệm / kiểm nghiệm (HPLC, sắc ký, quang phổ, tủ an toàn sinh học...),
             gói hóa chất, vật tư, dụng cụ thí nghiệm. KHÔNG phải: thiết bị y tế khám chữa bệnh của bệnh viện, phòng
             khám; xây lắp; tư vấn; phần mềm; xe; văn phòng phẩm
  du_an_moi = dự án nhà máy mới: được cấp phép / chấp thuận đầu tư, đang lập ĐTM, động thổ, khởi công, đang xây
  mo_rong = nhà máy đang chạy mở rộng, nâng công suất, thêm dây chuyền, cải tạo, tự động hóa
  tin_hieu = tín hiệu khác: tuyển trưởng ban QLDA / chỉ huy trưởng / kỹ sư cơ điện cho nhà máy mới, phê duyệt ĐTM...

LOẠI (keep=false) khi: quảng cáo của nhà cung cấp thiết bị; tin thị trường, giá cả, xuất khẩu chung chung; nhà máy ở
nước ngoài; mời thầu dịch vụ (du lịch, sự kiện, truyền thông, vé máy bay, thuê xe, phần mềm, bảo hiểm, xây lắp thuần,
văn phòng phẩm, quà tặng) hay mua xe, máy tính văn phòng; thiết bị y tế cho bệnh viện; ngành ngoài 7 ngành (điện, xi
măng, may mặc, cảng, đường giao thông, bất động sản...); nhà máy đã khánh thành mà không nói giai đoạn tiếp theo; tin
không nêu được tên doanh nghiệp / chủ đầu tư; trang danh sách, trang tìm việc chung, trang giới thiệu dịch vụ;
trang "dự án đã thực hiện" / "công trình tiêu biểu" của nhà thầu, nhà cung cấp, đơn vị thiết kế (việc đã xong, không
phải nhu cầu mới); tin chuyển nhượng, mua bán nhà máy; mời thầu đã có kết quả / đã đóng; tin hợp tác, ký kết ghi nhớ
(MoU), "triển vọng", hội thảo mà không có dự án nhà máy cụ thể (tên, địa điểm, vốn hoặc mốc thời gian); báo cáo tài
chính / kết quả kinh doanh, bài phân tích cổ phiếu, bài tổng hợp hay phỏng vấn chỉ NHẮC LẠI việc đã xảy ra từ lâu (VD bài
tháng 10 kể lễ động thổ tháng 3) mà không có mốc mới (reason "việc cũ"); mời thầu đã quá hạn nộp hồ sơ.

Quy tắc điền:
- company: tên đầy đủ nhất có trong nguồn (VD "Công ty Cổ phần Dược Hậu Giang"). Nguồn không có tên doanh nghiệp /
  chủ đầu tư thì company = "" (vẫn được giữ nếu là tin Google News chỉ có tiêu đề: hệ thống sẽ đọc bài gốc). Không bịa.
- title: tên gói thầu / tên dự án như nguồn. moi_thau bắt buộc có.
- summary: 1-2 câu tiếng Việt, chỉ sự thật trong nguồn (quy mô, vốn, công suất nếu có).
- province: tỉnh/thành NƠI ĐẶT nhà máy / dự án chính, viết như nguồn (tên cũ hay mới đều được); tin nhắc nhiều nơi thì
  lấy nơi đặt nhà máy được nói tới chính, không chọn tỉnh chỉ để lọt vùng. Tên xã / phường / nhà máy giống tên tỉnh
  (VD xã Khánh An ở Cà Mau, "Minh Phú Hậu Giang") không phải là tỉnh đó. Không rõ thì "". location: KCN/CCN/xã nếu có.
- equipment: thiết bị nguồn NÊU RÕ (equipment_inferred=false). Nếu nguồn KHÔNG nêu thiết bị cụ thể ("dây chuyền công
  nghệ tiên tiến" không tính), chỉ gợi ý tối đa 5 món LẤY TỪ "Hàng bên bán có" mà loại nhà máy đó thật sự cần (phòng
  QA/QC, kiểm nghiệm), đặt equipment_inferred=true; không liệt kê máy sản xuất (máy nghiền, ép viên, sấy...) nếu bên bán
  không bán; không chắc thì để []. Mỗi hạng mục là MỘT thiết bị, tối đa 6 từ (VD "Tủ an toàn sinh học", "Máy phân tích
  NIR"), không gộp nhiều thiết bị, không mở ngoặc liệt kê.
- deadline: hạn nộp hồ sơ / báo giá YYYY-MM-DD, chỉ khi nguồn ghi. progress: tiến độ CHÉP ĐÚNG mốc thời gian trong
  nguồn ("được cấp phép 9/2026, khởi công quý 1/2027"); không tự suy ra năm hay ngày nguồn không ghi. Với moi_thau,
  progress ghi HÌNH THỨC lựa chọn (chào giá cạnh tranh, chào hàng cạnh tranh, đấu thầu rộng rãi, mua sắm trực tiếp...),
  số TBMT / mã gói nếu có, thời điểm đóng / mở thầu. value: chỉ số tiền (giá gói thầu, dự toán, giá trần, vốn đầu tư,
  VD "1,25 tỷ đồng"); không có số tiền thì "". equipment của moi_thau: liệt kê đúng các mặt hàng trong danh mục mời
  chào giá (tối đa 12).
- contact: {name, phone, email} của đầu mối / bộ phận nhận hồ sơ, báo giá khi nguồn ghi (xem cả "Dòng liên hệ trong
  trang"). Chép đúng số và email như nguồn; nhiều số thì cách nhau dấu phẩy. Không lấy số của tòa soạn báo, của trang
  đăng tin, của nhà cung cấp, hay của cơ quan nhà nước / ban xúc tiến đầu tư / sở ngành / UBND khi doanh nghiệp là bên
  khác (để trống). Không bịa.
- published: ngày đăng tin YYYY-MM-DD nếu biết, không thì "".
- event_date: ngày (YYYY-MM-DD) hoặc tháng (YYYY-MM) của SỰ KIỆN CHÍNH tin nói tới (khởi công, cấp GCN đầu tư, phê duyệt
  ĐTM, quyết định mở rộng, ngày phát hành thư mời); nếu tin chỉ nói kế hoạch tương lai thì ghi ngày tin; không rõ thì "".
  Hệ thống loại tin có sự kiện cũ hơn "Chỉ giữ việc trong" (xem tin nhắn).
- plant_status: dang_chay | du_an_moi | chua_ro.
- industry và kind BẮT BUỘC có khi keep=true (dùng đúng mã ở trên). equipment là JSON array các chuỗi.
- Tỉnh nằm NGOÀI vùng theo dõi (danh sách trong tin nhắn) thì keep=false, reason "ngoài vùng".
- sales_note: 1-3 câu cho sale: nên gặp ai (phòng/chức danh), chào thiết bị gì của bên bán, vì sao lúc này. Không bịa số liệu.
Trả về ĐÚNG MỘT JSON array, mỗi phần tử: {"i": số thứ tự tin, "keep": true/false, "reason": "lý do ngắn",
"opportunity": {...các trường trên..., "industry": "<mã ngành>", "kind": "<mã loại>"}} (opportunity chỉ khi keep=true).
Không viết gì ngoài JSON."""


def extract_batch(llm, seller, batch, region="", lookback=30):
    lines = []
    for n, c in enumerate(batch):
        lines.append(f"### Tin {n}\nNguồn: {c['url']}\nLoại nguồn: {c['origin']}" + (f" ({c['hint']})" if c.get("hint") else "")
                     + f"\nNgày (nếu biết): {c.get('date') or 'không rõ'}\nTiêu đề: {c['title']}\n"
                     + (f"Đoạn trích: {c['snippet']}\n" if c.get("snippet") else "")
                     + (f"Nội dung trang:\n{c['text'][:TEXT_CHARS]}\n" if c.get("text") else "")
                     + (f"Dòng liên hệ trong trang:\n{c['contact_hint']}\n" if c.get("contact_hint") else ""))
    user = (f"Bên bán: {seller.get('company') or '(chưa ghi tên)'}\nHàng bên bán có: {seller.get('products') or '(chưa ghi)'}\n"
            f"Không cần tìm: {seller.get('avoid') or '(không)'}\nVùng theo dõi: {region}\n"
            f"Hôm nay: {today().isoformat()}. Chỉ giữ việc trong {lookback} ngày gần đây (mời thầu: còn hạn).\n\n"
            + "\n".join(lines))
    try:
        value = parse_json(llm_chat(llm, EXTRACT_SYSTEM, user))
    except WalletEmpty:
        raise
    except (ValueError, Truncated) as error:
        if len(batch) > 1:  # chia doi, doc lai tung nua
            half = len(batch) // 2
            left = extract_batch(llm, seller, batch[:half], region, lookback)
            right = extract_batch(llm, seller, batch[half:], region, lookback)
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
Nếu tin nhắn có dòng "ĐẦU MỐI GIÁN TIẾP", làm theo dòng đó cho trường hợp không có ai ra quyết định.
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
    if o["equipment_inferred"]:
        o["equipment"] = o["equipment"][:5]
    if o["equipment"] and not o["equipment_inferred"]:
        # model noi "nguon co neu" ma bai khong co thiet bi nao trong danh sach: la goi y
        source = fold(" ".join(str(candidate.get(k) or "") for k in ("title", "snippet", "text")))
        def stated(item):
            words = [w for w in fold(item).split() if len(w) >= 3]
            return fold(item) in source or (words and all(f" {w} " in f" {source} " for w in words))
        if not any(stated(e) for e in o["equipment"]):
            o["equipment_inferred"] = True
    hint = candidate.get("hint") or ""
    if o.get("industry") not in INDUSTRY_KEYS:
        m = re.search(r"industry=(\w+)", candidate.get("meta", ""))
        o["industry"] = m.group(1) if m else o.get("industry")
    if o.get("kind") not in KIND_KEYS and candidate.get("origin") == "Trang theo dõi" and "mời thầu" in hint.lower():
        o["kind"] = "moi_thau"
    if o.get("kind") == "moi_thau" and not o.get("deadline") and candidate.get("deadline_hint"):
        o["deadline"] = candidate["deadline_hint"]  # model sot dong han cuoi
    if not o.get("province") and candidate.get("province"):
        o["province"] = candidate["province"]
    if not o.get("company") and candidate.get("company"):
        o["company"] = candidate["company"]
    contact = o.get("contact") if isinstance(o.get("contact"), dict) else {}
    contact = {k: str(contact.get(k) or "").strip() for k in ("name", "phone", "email")}
    seen_text = " ".join(str(candidate.get(k) or "") for k in ("title", "snippet", "text", "contact_hint"))
    seen_digits = {phone_digits(m.group(0)) for m in PHONE_RE.finditer(seen_text)}
    phones = [p.strip() for p in re.split(r"[,;/]", contact["phone"]) if p.strip()]
    contact["phone"] = ", ".join(p for p in phones if phone_digits(p) in seen_digits)  # so khong co trong nguon: bo
    if contact["email"] and contact["email"].lower() not in seen_text.lower():
        contact["email"] = ""
    if contact["name"] and fold(contact["name"]) not in fold(seen_text):
        contact["name"] = ""
    o["contact"] = contact
    for key in ("title", "summary", "province", "location", "progress", "value", "sales_note", "published", "deadline",
                "event_date"):
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


def full_queries(cfg, cap=150):
    """Moi nhom thiet bi x nganh x nhom tinh trong 1 luot (quet day du)."""
    s = cfg["settings"]
    rounds = max(len(EQUIPMENT_GROUPS), len(province_chunks(cfg)), 4)
    out = {}
    for _ in range(rounds):
        for q in build_queries(cfg, limit=10_000):
            out.setdefault(q, None)
    return list(out)[:cap]


def build_queries(cfg, limit=None):
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
    portals = " OR ".join(f"site:{x}" for x in SITE_TENDER_PORTALS)
    if "moi_thau" in kinds:  # don vi cong mua thiet bi / vat tu / dich vu phong thi nghiem: moi lan quet deu tim
        queries.extend(LAB_BUYER_QUERIES)
    for n in range(len(groups)):
        g = groups[(turn + n) % len(groups)]
        if "moi_thau" in kinds:
            queries.append(f'("chào giá" OR "báo giá") ({ors(g[:3])})')
            queries.append(f'("mời thầu" OR "mua sắm" OR "chào hàng cạnh tranh") ({ors(g[2:])})')
            queries.append(f'({portals}) ({ors(g[:3])})')
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
        jobs = " OR ".join(f"site:{x}" for x in JOB_SITES)
        queries.append(f'({jobs}) ("chỉ huy trưởng" OR "trưởng ban quản lý dự án" OR "ban QLDA" OR "kỹ sư dự án") '
                       '("nhà máy mới" OR "dự án nhà máy" OR "xây dựng nhà máy") '
                       '("thủy sản" OR "dược" OR "thực phẩm" OR "thức ăn chăn nuôi" OR "bột cá")')
    if "moi_thau" in kinds:
        sites = SITE_GROUPS_TENDER[turn % len(SITE_GROUPS_TENDER)]
        queries.append("(" + " OR ".join(f"site:{x}" for x in sites) + ') ("mời thầu" OR "chào giá" OR "báo giá" OR "chào thầu")')
    if "du_an_moi" in kinds or "mo_rong" in kinds:
        sites = SITE_GROUPS_KCN[turn % len(SITE_GROUPS_KCN)]
        queries.append("(" + " OR ".join(f"site:{x}" for x in sites) + ') ("giấy chứng nhận đăng ký đầu tư" OR '
                       '"chủ trương đầu tư" OR "khởi công" OR "mời chào giá" OR "nhà máy")')
    if "du_an_moi" in kinds or "tin_hieu" in kinds:
        sites = SITE_GROUPS_DTM[turn % len(SITE_GROUPS_DTM)]
        queries.append("(" + " OR ".join(f"site:{x}" for x in sites) + ') ("nhà máy" OR "chế biến") ("tác động môi trường" OR "ĐTM" OR "giấy phép môi trường")')
    # xen ke: moi thau, du an, mo rong... de khi cat bot van du loai
    # uu tien moi thau / chao gia: 2 truy van moi thau roi 1 truy van du an
    tender = [q for q in queries if any(w in q for w in ("chào giá", "mời thầu", "báo giá", "gói thầu", "chào hàng")) or
              any(f"site:{x}" in q for x in SITE_TENDER_PORTALS)]
    rest = [q for q in queries if q not in tender]
    mixed = []
    while tender or rest:
        for _ in range(2):
            if tender:
                mixed.append(tender.pop(0))
        if rest:
            mixed.append(rest.pop(0))
    return mixed[: limit or int(s.get("google_queries_per_run") or 0)]


def news_queries(cfg):
    s = cfg["settings"]
    days = min(int(s.get("lookback_days") or 30), 60)
    industries = [k for k in s["industries"] if k in INDUSTRY_QUERY]
    # han che bao: chi 2 truy van moi chao gia + 1 truy van du an nha may moi nganh
    out = [f'("thư mời chào giá" OR "chào giá cạnh tranh" OR "mời báo giá" OR "chào hàng cạnh tranh") ("thiết bị" OR "máy") when:{days}d',
           f'("mời thầu" OR "gói thầu") ("thiết bị phòng thí nghiệm" OR "thiết bị kiểm nghiệm" OR "máy móc thiết bị") when:{days}d']
    for ind in industries:
        terms = INDUSTRY_QUERY[ind]
        out.append(f'("khởi công" OR "cấp phép đầu tư" OR "chứng nhận đăng ký đầu tư" OR "mở rộng") "nhà máy" ({terms}) when:{days}d')
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


def rss_links(raw):
    """RSS / Atom: tieu de, link, ngay dang."""
    out = []
    for block in re.findall(r"(?is)<(?:item|entry)\b.*?</(?:item|entry)>", raw):
        title = re.search(r"(?is)<title[^>]*>(.*?)</title>", block)
        link = re.search(r"(?is)<link[^>]*>(.*?)</link>", block) or re.search(r'(?is)<link[^>]*href=["\']([^"\']+)', block)
        date = re.search(r"(?is)<(?:pubDate|published|updated|dc:date)[^>]*>(.*?)</", block)
        if not (title and link):
            continue
        text = html.unescape(re.sub(r"<!\[CDATA\[|\]\]>|<[^>]+>", "", title.group(1))).strip()
        href = html.unescape(re.sub(r"<!\[CDATA\[|\]\]>", "", link.group(1))).strip()
        day = ""
        if date:
            try:
                day = email.utils.parsedate_to_datetime(date.group(1).strip()).date().isoformat()
            except (TypeError, ValueError):
                day = date.group(1).strip()[:10]
        if href.startswith("http") and len(text) >= 15:
            out.append({"title": text[:300], "url": href, "date": day})
    return out


def page_links(page):
    try:
        raw, final = fetch_text(page["url"], timeout=25)
    except Exception:  # noqa: BLE001
        return None
    if not raw:
        return None
    if re.search(r"(?is)<(rss|feed)\b", raw[:2000]):
        return rss_links(raw)
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


KCN_TERMS = ["nhà máy", "dự án", "chứng nhận đăng ký đầu tư", "giấy chứng nhận", "chủ trương đầu tư", "cấp mới",
             "điều chỉnh", "khởi công", "động thổ", "mở rộng", "chào giá", "báo giá", "mời thầu", "gói thầu",
             "mua sắm", "nhà đầu tư", "sản xuất", "chế biến"]


LAB_BUYERS = ["viện", "đại học", "trường", "học viện", "kiểm nghiệm", "phòng thí nghiệm", "trung tâm kỹ thuật",
              "quan trắc", "kiểm định", "đo lường", "chất lượng", "thú y", "chăn nuôi", "nông nghiệp", "thủy sản",
              "dược", "thực phẩm", "sữa", "bia", "nước giải khát", "thức ăn", "hóa chất", "mỹ phẩm", "y tế dự phòng",
              "an toàn thực phẩm", "nuôi trồng"]
NOT_BUYERS = ["bệnh viện", "phòng khám", "cảng", "điện gió", "điện mặt trời", "năng lượng", "hàng không", "ngân hàng", "tín dụng", "bảo hiểm",
              "viễn thông", "xăng dầu", "than", "khoáng sản", "đường sắt", "cao tốc", "nhiệt điện", "thủy điện",
              "truyền tải điện", "điện lực", "bưu điện", "vận tải", "xi măng", "thép"]


# goi thau khong phai thiet bi (cong BQL KCN dang rat nhieu): bo tu tieu de, khong ton LLM
NOT_EQUIPMENT_TENDER = ["tư vấn", "quy hoạch", "khảo sát", "xây lắp", "thi công", "giao thông", "kiểm toán", "giám sát",
                        "thẩm tra", "lập hồ sơ", "đo đạc", "xây dựng", "san lấp", "bảo hiểm", "sơn tường", "phần mềm"]


def _watch_ok(page, title):
    f = fold(title)
    kind = page.get("kind")
    if kind in ("kcn", "tender", "tender_board", "lab_buyer") and has_any(f, NOT_EQUIPMENT_TENDER):
        return False
    industry = any(has_any(f, t) for t in INDUSTRY_TERMS.values())
    if kind == "lab_buyer":  # don vi cong co phong thi nghiem: thong bao moi chao gia / chao hang
        return has_any(f, ["chào giá", "chào hàng", "mời thầu", "báo giá", "mua sắm"])
    if kind == "tender_board":  # Bao Dau thau: tieu de chi co ten don vi -> giu don vi co the mua thiet bi lab / 7 nganh
        return has_any(f, ["chào giá", "mời thầu", "báo giá", "chào hàng"]) and (industry or has_any(f, LAB_BUYERS))             and not has_any(f, NOT_BUYERS)
    if kind == "tender":
        return has_any(f, ["chào giá", "báo giá", "mời thầu", "chào thầu", "gói", "mua sắm"]) and has_any(f, EQUIPMENT_TERMS)
    if kind == "dtm":
        return has_any(f, ["nhà máy", "chế biến", "sản xuất"]) or industry
    if kind == "kcn":  # BQL KCN / XTDT: cap GCN, chu truong, nha may moi, moi chao gia (LLM loc nganh sau)
        return has_any(f, KCN_TERMS)
    if kind == "company":  # tin cua chinh doanh nghiep: nha may, mo rong, khoi cong
        return has_any(f, SIGNAL_TERMS + ["nhà máy", "đầu tư", "công suất"])
    if kind in ("news", "assoc"):
        return (industry and has_any(f, SIGNAL_TERMS + ["nhà máy", "đầu tư"])) or has_any(
            f, ["khởi công nhà máy", "động thổ nhà máy", "xây dựng nhà máy", "chứng nhận đăng ký đầu tư", "mời chào giá"])
    return has_any(f, SIGNAL_TERMS + EQUIPMENT_TERMS)


def _first_visit(pages):
    """Trang theo doi lan dau: tra ve tap url trang da tung doc (de gioi han lan dau)."""
    path = os.path.join(STATE, "watch-visited.json")
    try:
        with open(path, encoding="utf-8") as f:
            visited = set(json.load(f))
    except (OSError, ValueError):
        visited = set()
    return visited, path


def collect_watch(cfg):
    items, report = [], []
    pages = watch_list(cfg)
    visited, visited_path = _first_visit(pages)
    with concurrent.futures.ThreadPoolExecutor(FETCH_WORKERS) as pool:
        for page, links in zip(pages, pool.map(page_links, pages)):
            if links is None:
                report.append(f"{page['label']}: không đọc được")
                continue
            kept = 0
            first = page["url"] not in visited
            visited.add(page["url"])
            for link in links:
                if first and kept >= WATCH_FIRST_VISIT * (3 if page.get("kind") == "tender_board" else 1):
                    break  # lan dau: chi tin dau trang (moi nhat), khong doc ca kho tin cu
                if _watch_ok(page, link["title"]):
                    hint = page["label"]
                    if page.get("company"):
                        hint += f"; đơn vị: {page['company']}; tỉnh: {page.get('province', '')}"
                    items.append({"origin": "Trang theo dõi", "hint": hint, "title": link["title"], "url": link["url"],
                                  "snippet": "", "date": link.get("date", ""), "company": page.get("company", ""),
                                  "province": page.get("province", ""),
                                  "meta": f"industry={page['industry']}" if page.get("industry") else ""})
                    kept += 1
            report.append(f"{page['label']}: {len(links)} link, {kept} đáng đọc")
    try:
        os.makedirs(STATE, exist_ok=True)
        with open(visited_path, "w", encoding="utf-8") as f:
            json.dump(sorted(visited), f)
    except OSError:
        pass
    log("Trang theo dõi: " + "; ".join(report))
    return items, report


TENDER_WORDS = ["mời thầu", "chào giá", "báo giá", "gói thầu", "chào hàng", "mua sắm", "đấu thầu", "TBMT", "chào thầu"]
LAB_WORDS = ["thí nghiệm", "kiểm nghiệm", "xét nghiệm", "phân tích", "hiệu chuẩn", "kiểm định", "bảo dưỡng", "bảo trì",
             "sửa chữa thiết bị", "phụ tùng", "linh kiện", "hóa chất", "vật tư", "thiết bị", "máy", "HPLC", "sắc ký",
             "quang phổ", "vi sinh", "tủ "]
# trang khong phai thu moi: danh ba nha cung cap, ket qua lua chon nha thau (goi da dong), mang xa hoi
DROP_URL_PARTS = ("/businesslistings/", "/ketqua", "ketquamothau", "ket-qua-lua-chon", "facebook.com", "/tag/", "/tags/")


def prefilter(items):
    """Bo tin chac chan khong lien quan truoc khi ton LLM. Thu moi chao gia / moi thau co nhac thiet bi, phong thi nghiem
    thi luon giu (tieu de thu moi thuong khong ghi nganh: 'Thu moi chao gia may ly tam')."""
    out = []
    for it in items:
        host = urllib.parse.urlsplit(it["url"]).netloc.lower()
        if any(n in host for n in NOISE_HOSTS) or any(p in it["url"].lower() for p in DROP_URL_PARTS):
            continue
        f = fold(f"{it['title']} {it.get('snippet', '')} {it.get('hint', '')}")
        industry = any(has_any(f, terms) for terms in INDUSTRY_TERMS.values())
        signal_hit = has_any(f, SIGNAL_TERMS) or has_any(f, EQUIPMENT_TERMS)
        tender = has_any(f, TENDER_WORDS) and has_any(f, LAB_WORDS) and not has_any(f, NOT_EQUIPMENT_TENDER)
        if it["origin"] == "Trang theo dõi" or tender or (industry and signal_hit) or "linkedin" in host:
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
                full = plain_text(raw)
                it["contact_hint"] = contact_lines(full)
                it["deadline_hint"] = deadline_in(full)
                it["date"] = it.get("date") or page_date(raw)
        except Exception as error:  # noqa: BLE001 - 1 trang loi khong lam hong ca lan quet
            log(f"Không đọc được {it['url'][:80]}: {error}")
        return it
    with concurrent.futures.ThreadPoolExecutor(FETCH_WORKERS) as pool:
        return list(pool.map(one, items))


# ---------------------------------------------------------------- lien he doanh nghiep


REGISTRY_HOSTS = ("dulieuphapluat.vn", "chogia.vn", "dailychukyso.com.vn", "yp.com.vn", "masocongty", "thongtincongty",
                  "doanhnghiep.me", "vnr500.vn", "huba.vn", "hosocongty", "vietnamcredit", "kompass", "vietnamdoanhnghiep", "doanhnghiepvn",
                  "masothue.com", "hsctvn.com", "thongtindoanhnghiep.co", "infodoanhnghiep.com", "trangvangvietnam.com",
                  "yellowpages.vn", "doanhnghiep.biz", "tratencongty.com", "vinabiz.org", "thuvienphapluat.vn",
                  "masocongty.vn", "trangthongtin.vn", "dnb.com", "emis.com", "timcongty", "vietnamworks.com",
                  "topcv.vn", "careerviet.vn", "itviec.com", "congty.vn", "doanhnghiepmoi.vn")
NEWS_HOSTS = ("vnexpress", "tuoitre", "thanhnien", "baodautu", "cafef", "vietnamnet", "vneconomy", "dantri", "nld.com",
              "plo.vn", "sggp", "laodong", "znews", "nhandan", "qdnd", "vov.vn", "vtv.vn", "vietnamplus", "vietstock",
              "dauthau", "bidwinner", "muasamcong", "thesaigontimes", "doanhnhan", "kinhtedothi", "congthuong", "vnbusiness")
CONTACTS_PER_RUN = int(os.environ.get("LEAD_CONTACTS_PER_RUN") or (25 if FULL else 10))
CONTACT_RECHECK_DAYS = 14

CONTACT_SYSTEM = """Bạn xác minh thông tin liên hệ CÔNG KHAI của một doanh nghiệp Việt Nam cho sale B2B.
Bạn nhận: công ty mục tiêu và các bằng chứng E0, E1... (mỗi bằng chứng: link trang + đoạn văn bản trên trang đó).
Chỉ chọn thông tin THUỘC CHÍNH công ty mục tiêu (cùng tên hoặc thương hiệu; trụ sở, chi nhánh, nhà máy của công ty đó
đều được). LOẠI: số / email của trang tra cứu, báo chí, sàn việc làm, nhà cung cấp, đối tác, cơ quan nhà nước; công ty
khác trùng tên một phần; số fax; số trong quảng cáo. Không chắc thì bỏ.
CHÉP ĐÚNG giá trị như trong bằng chứng, không sửa, không đoán, không ghép số.
Trả về ĐÚNG MỘT JSON object:
{"website": {"e": số} hoặc null  (bằng chứng là trang web CHÍNH THỨC của công ty mục tiêu),
 "phones": [{"e": số, "value": "số như bằng chứng", "label": "Tổng đài / Phòng kinh doanh / Mua hàng / Nhà máy ..."}],
 "emails": [{"e": số, "value": "email", "label": ""}],
 "address": {"e": số, "value": "địa chỉ trụ sở hoặc nhà máy"} hoặc null,
 "tax_code": {"e": số, "value": "mã số thuế"} hoặc null,
 "representative": {"e": số, "value": "người đại diện pháp luật"} hoặc null,
 "linkedin_company": {"e": số} hoặc null  (trang linkedin.com/company của đúng công ty),
 "facebook": {"e": số} hoặc null  (fanpage chính thức),
 "reason": "1 câu"}
Tối đa 4 số điện thoại và 4 email, ưu tiên số tổng đài, phòng kinh doanh, mua hàng, kỹ thuật. Không viết gì ngoài JSON."""


def _host(url):
    return urllib.parse.urlsplit(url).netloc.lower().removeprefix("www.")


GENERIC_NAME_WORDS = {"dau tu", "nong lam", "xuat nhap khau", "thuong mai", "dich vu", "san xuat", "che bien", "phat trien",
                      "cong nghe", "ky thuat", "nong nghiep", "cong nghiep", "thuc pham", "thuy san", "xay dung"}


def core_name(company):
    """Phan ten rieng (bo cum chung): 'Dau tu Nong lam Xuat nhap khau Nhat Nhat An' -> 'Nhat Nhat An'. Con < 2 tu thi
    giu ten ngan (tranh tim theo dia danh)."""
    short = short_company(company)
    words = short.split()
    folded = [fold(w) for w in words]
    keep = [True] * len(words)
    for i in range(len(words)):
        for j in (3, 2):
            if i + j <= len(words) and " ".join(folded[i:i + j]) in GENERIC_NAME_WORDS:
                for k in range(i, i + j):
                    keep[k] = False
    core = " ".join(w for w, k in zip(words, keep) if k)
    return core if len(core.split()) >= 2 else short


def _distinct_words(company):
    """Tu rieng cua ten cong ty (bo tu chung, dia danh) + chu viet tat (Duoc Hau Giang -> dhg)."""
    words = fold(short_company(company)).split()
    common = {"thuc", "pham", "duoc", "thuy", "san", "che", "bien", "xuat", "nhap", "khau", "dau", "tu", "phat", "trien",
              "thuong", "mai", "dich", "vu", "san", "xuat", "cong", "nghe", "sinh", "hoc", "hoa", "chat", "chan", "nuoi",
              "thuc", "an", "my", "va", "nong", "lam", "tap", "doan", "group", "food", "foods", "seafood", "pharma",
              "viet", "nam", "sai", "gon", "mien", "nam", "bac", "trung", "quoc", "te", "do", "uong", "sua", "ky", "nghe"}
    distinct = [w for w in words if len(w) >= 3 and w not in common]
    if len(words) >= 2:
        distinct.append("".join(w[0] for w in words if w))
    return [w for w in distinct if len(w) >= 3]


def _own_site(url, title, company):
    host = _host(url)
    if not host or any(h in host for h in REGISTRY_HOSTS + NEWS_HOSTS + NOISE_HOSTS) or host.endswith("gov.vn") \
            or any(h in host for h in ("linkedin.", "facebook.", "google.", "youtube.", "zalo.")) or host.startswith("bao"):
        return False
    label = host.split(".")[0].replace("-", "")
    words = _distinct_words(company)
    return any(w in label for w in words) or (fold(short_company(company)) in fold(title) and len(host.split(".")) <= 4)


def _contact_page(raw, base):
    for m in re.finditer(r"""href=["']([^"'#]+)["']""", raw or ""):
        href = m.group(1)
        if re.search(r"(?i)lien[-_]?he|contact|lienhe", href):
            return urllib.parse.urljoin(base, href)
    return ""


def _evidence(url, text, raw=""):
    """Doan van ban quanh moi SDT / email / dia chi / MST tren trang."""
    out = []
    hits = []
    for m in PHONE_RE.finditer(text):
        hits.append((m.start(), m.end()))
    for m in EMAIL_RE.finditer(text):
        hits.append((m.start(), m.end()))
    for m in re.finditer(r"(?i)(địa chỉ|trụ sở|address|mã số thuế|mst|người đại diện|đại diện pháp luật)", text):
        hits.append((m.start(), m.end() + 120))
    hits.sort()
    last_end = -1
    for start, end in hits:
        if start < last_end:
            continue
        a, b = max(0, start - 90), min(len(text), end + 60)
        out.append({"url": url, "text": re.sub(r"\s+", " ", text[a:b]).strip()})
        last_end = b
        if len(out) >= 10:
            break
    mails = set(re.findall(r"(?i)mailto:([^\"'?\s>]+)", raw or "")) | set(re.findall(r"(?i)tel:([+\d][\d\s.\-()]{7,})", raw or ""))
    for m in sorted(mails)[:4]:
        out.append({"url": url, "text": f"liên kết trên trang: {m}"})
    return out


def find_contacts(cfg, budget, llm, opps):
    """Website, SDT, email, MST, LinkedIn cong ty cua tung co hoi. Moi gia tri phai co trong 1 trang nguon."""
    if not opps or not cfg.get("apify_key"):
        return 0
    after = (today() - dt.timedelta(days=3650)).isoformat()
    queries = {}
    for o in opps:
        short = short_company(o["company"]) or o["company"]
        queries[o["id"]] = [f'"{short}" liên hệ điện thoại email', f'"{core_name(o["company"])}" mã số thuế',
                            f'"{o["company"]}"', f'site:linkedin.com/company "{short}"']
    flat = [q for qs in queries.values() for q in qs]
    results = google_search(budget, flat, after)
    by_query = {}
    for r in results:
        by_query.setdefault(r["query"], []).append(r)
    found = 0
    for o in opps:
        qs = queries[o["id"]]
        res = [r for q in qs for r in by_query.get(q, [])]
        if not res and budget.stopped:
            break
        evidence = []
        # ket qua Google: doan trich (trang tra cuu doanh nghiep hay co MST, dia chi, SDT)
        for r in res[:24]:
            host = _host(r["url"])
            if "linkedin.com/company/" in r["url"] or "facebook.com" in host or any(h in host for h in REGISTRY_HOSTS) \
                    or _own_site(r["url"], r["title"], o["company"]):
                evidence.append({"url": r["url"], "text": f"[Google] {r['title']} | {r['snippet']}"[:400]})
        # doc trang chinh thuc (trang chu + trang lien he) va trang tra cuu
        own = []
        for r in res:
            if _own_site(r["url"], r["title"], o["company"]):
                root = f"{urllib.parse.urlsplit(r['url']).scheme}://{urllib.parse.urlsplit(r['url']).netloc}/"
                for u in (r["url"], root):
                    if u not in own:
                        own.append(u)
        # trang tra cuu / doan trich hay ghi "Website: ..." cua cong ty
        for r in res:
            for dom in re.findall(r"(?i)\b(?:https?://)?(?:www\.)?((?:[a-z0-9-]+\.)+(?:com\.vn|vn|com|net))\b", f"{r['title']} {r['snippet']}"):
                url = f"https://{dom.lower()}/"
                if _own_site(url, "", o["company"]) and url not in own:
                    own.append(url)
        registry = [r["url"] for r in res if any(h in _host(r["url"]) for h in REGISTRY_HOSTS)
                    and _names_company(f"{r['title']} {r['snippet']}", o["company"])][:3]
        # trang khac nhac DUNG ten cong ty (thong bao tiep nhan ho so cua so / ban xuc tien, trang danh sach doanh nghiep):
        # thuong ghi dia chi, dien thoai cua nha dau tu
        mentions = [r["url"] for r in res if r["url"] not in registry and not _own_site(r["url"], r["title"], o["company"])
                    and _names_company(f"{r['title']} {r['snippet']}", o["company"])
                    and not any(n in _host(r["url"]) for n in NOISE_HOSTS)][:3]
        pages = own[:3] + registry + mentions
        fetched = {}
        with concurrent.futures.ThreadPoolExecutor(6) as pool:
            for u, (raw, final) in zip(pages, pool.map(lambda u: fetch_text(u, timeout=15), pages)):
                fetched[u] = raw
        extra = []
        for u in own[:3]:
            page = _contact_page(fetched.get(u, ""), u)
            if page and page not in fetched and page not in extra:
                extra.append(page)
        for u in extra[:2]:
            fetched[u] = fetch_text(u, timeout=15)[0]
        # trang danh sach (tra cuu theo xa...): theo link co ten cong ty sang trang chi tiet
        for u in registry + mentions:
            detail = _company_link(fetched.get(u, ""), u, o["company"])
            if detail and detail not in fetched:
                fetched[detail] = fetch_text(detail, timeout=15)[0]
        for u, raw in fetched.items():
            if not raw:
                continue
            text = plain_text(raw)
            if u in mentions or _is_listing(text, o["company"]):
                evidence += _name_evidence(u, text, o["company"])  # chi doan quanh ten cong ty
            else:
                evidence += _evidence(u, text, raw)
        evidence = evidence[:40]
        record = {"sources": []}
        if evidence:
            lines = [f"E{n}: {e['url']}\n{e['text']}" for n, e in enumerate(evidence)]
            user = (f"Công ty mục tiêu: {o['company']}\nNgành: {o.get('industry_label') or o['industry']}; tỉnh: "
                    f"{o.get('province') or '?'}; địa điểm: {o.get('location') or '?'}\nCơ hội: {o.get('title') or ''}\n\n"
                    + "\n\n".join(lines))
            try:
                picked = parse_json(llm_chat(llm, CONTACT_SYSTEM, user, max_tokens=1800))
            except WalletEmpty:
                raise
            except (ValueError, RuntimeError) as error:
                log(f"Liên hệ {o['company'][:40]}: lỗi đọc ({error})")
                continue
            record = check_contact(picked if isinstance(picked, dict) else {}, evidence, o["company"])
        owui("POST", f"/agent/opportunities/{o['id']}/contact", record)
        got = [f"{len(record.get('phones', []))} SĐT", f"{len(record.get('emails', []))} email"]
        if record.get("website"):
            got.append("website")
        if record.get("linkedin_company"):
            got.append("LinkedIn")
        if record.get("phones") or record.get("emails"):
            found += 1
        log(f"Liên hệ {o['company'][:50]}: " + ", ".join(got))
    return found


def _names_company(text, company):
    """Doan van co nhac dung cong ty (ten rieng, khong phan biet hoa thuong / dau)."""
    core = fold(core_name(company))
    return bool(core) and core in fold(text)


def _is_listing(text, company):
    """Trang liet ke nhieu doanh nghiep (danh sach theo xa, ket qua tim kiem)."""
    return len(re.findall(r"(?i)c[ôo]ng ty", text)) > 8


def _company_link(raw, base, company):
    """Link co ten cong ty trong trang danh sach -> trang chi tiet cua cong ty do."""
    core = fold(core_name(company))
    for m in re.finditer(r'(?is)<a\b[^>]*href=["\']([^"\'#]+)["\'][^>]*>(.*?)</a>', raw or ""):
        label = fold(html.unescape(re.sub(r"<[^>]+>", " ", m.group(2))))
        href = m.group(1)
        if core and (core in label or core.replace(" ", "-") in fold(href).replace(" ", "-")):
            return urllib.parse.urljoin(base, html.unescape(href))
    return ""


def _name_evidence(url, text, company, width=350):
    """Doan quanh ten cong ty tren trang (dia chi, dien thoai, MST cua chinh cong ty, khong lay cua don vi khac)."""
    core = fold(core_name(company))
    folded = fold(text)
    out = []
    start = 0
    while core and len(out) < 3:
        i = folded.find(core, start)
        if i < 0:
            break
        # vi tri trong text goc ~ vi tri trong ban fold (fold giu do dai tuong doi): lay rong ra
        ratio = len(text) / max(1, len(folded))
        a, b = max(0, int(i * ratio) - 80), min(len(text), int(i * ratio) + width)
        out.append({"url": url, "text": re.sub(r"\s+", " ", text[a:b]).strip()})
        start = i + len(core)
    return out


def check_contact(picked, evidence, company=""):
    """Chi giu gia tri co that trong bang chung model chi ra (chong bia)."""
    def ev(item):
        if isinstance(item, dict) and isinstance(item.get("e"), int) and 0 <= item["e"] < len(evidence):
            return evidence[item["e"]]
        return None

    used = []
    out = {"phones": [], "emails": []}
    for item in (picked.get("phones") or [])[:6]:
        e = ev(item)
        if not e:
            continue
        digits = phone_digits(item.get("value"))
        ok = False
        for m in PHONE_RE.finditer(e["text"]):
            if phone_digits(m.group(0)) != digits:
                continue
            before = fold(re.split(r"\d", e["text"][max(0, m.start() - 28):m.start()])[-1])  # chu ngay truoc so nay
            if not re.search(r"\b(fax|ma so thue|mst|tax|so dkkd|giay phep)\b", before):  # MST / fax giong SDT
                ok = True
        if len(digits) >= 8 and ok:
            label = str(item.get("label") or "")[:60]
            if any(h in _host(e["url"]) for h in REGISTRY_HOSTS):
                label = f"đăng ký kinh doanh ({_host(e['url'])})"  # so dang ky, co the la ke toan / dich vu
            out["phones"].append({"value": item["value"], "label": label, "url": e["url"]})
            used.append(e["url"])
    for item in (picked.get("emails") or [])[:6]:
        e = ev(item)
        value = str((item or {}).get("value") or "").strip().lower()
        if e and value and value in e["text"].lower():
            out["emails"].append({"value": value, "label": str(item.get("label") or "")[:60], "url": e["url"]})
            used.append(e["url"])
    for key in ("address", "tax_code", "representative"):
        item = picked.get(key)
        e = ev(item)
        value = str((item or {}).get("value") or "").strip()
        ok = e and value and (re.sub(r"\D", "", value) in re.sub(r"\D", "", e["text"]) if key == "tax_code"
                              else fold(value) in fold(e["text"]))
        if ok:
            out[key] = value
            used.append(e["url"])
    for key in ("website", "linkedin_company", "facebook"):
        e = ev(picked.get(key))
        if not e:
            continue
        url = e["url"]
        if key == "website":
            parts = urllib.parse.urlsplit(url)
            if not _own_site(url, "", company):  # ten mien phai mang ten cong ty (khong lay trang xep hang, tra cuu)
                continue
            url = f"{parts.scheme}://{parts.netloc}/"
        elif key == "linkedin_company" and "linkedin.com/company/" not in url:
            continue
        elif key == "facebook":
            m = re.match(r"https?://([a-z]+\.)?facebook\.com/([^/?#]+)", url)
            if not m or m.group(2) in ("permalink.php", "profile.php", "groups", "watch", "story.php"):
                continue
            if not any(w in fold(m.group(2)).replace(" ", "") for w in _distinct_words(company)):
                continue  # trang cua bao / nguoi khac dang lai
            url = f"https://www.facebook.com/{m.group(2)}"
        out[key] = url
        used.append(e["url"])
    out["sources"] = [{"url": u} for u in dict.fromkeys(used)]
    return out


def contact_targets(limit):
    """Co hoi chua co SDT / email (hoac chua tim), diem cao truoc, bo qua thi thoi, moi co hoi tim lai sau 14 ngay."""
    data = owui("GET", "/opportunities?" + urllib.parse.urlencode({"contact": "can_tim", "sort": "score", "limit": 200,
                                                                   "fresh": "1"}))
    now_ts = time.time()
    out = []
    for o in data["items"]:
        checked = (o.get("company_contact") or {}).get("checked_at") or 0
        if o["state"] == "bo_qua" or now_ts - checked < CONTACT_RECHECK_DAYS * 86400:
            continue
        out.append(o)
    return out[:limit]


# ---------------------------------------------------------------- nguoi lien he


def short_company(name):
    words = re.sub(r"(?i)\b(công ty|cty|cổ phần|cp|tnhh|một thành viên|mtv|ctcp|jsc|co\.?,? ?ltd\.?|tập đoàn|tổng công ty|"
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


DECISION_TITLES = ["Director", "Giám đốc", "Plant Manager", "Factory Manager", "Production Manager", "Technical Manager",
                   "Engineering Manager", "Maintenance Manager", "Project Manager", "QA Manager", "QC Manager",
                   "R&D Manager", "Purchasing Manager", "Procurement Manager", "Trưởng phòng", "Head of"]
LINKEDIN_SEARCHES_PER_RUN = int(os.environ.get("LEAD_LINKEDIN_SEARCHES_PER_RUN") or 2)
PEOPLE_RECHECK_DAYS = 30


def _searched(opp_id=None, mark=False):
    """Co hoi da tim nguoi gan day (khong ton tien tim lai trong 30 ngay)."""
    path = os.path.join(STATE, "people-searched.json")
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        data = {}
    if mark and opp_id:
        data[opp_id] = time.time()
        os.makedirs(STATE, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
    return data


def people_targets(cfg, limit=8):
    s = cfg["settings"]
    data = owui("GET", "/opportunities?" + urllib.parse.urlencode({"sort": "score", "limit": 200, "fresh": "1",
                                                                   "min_score": int(s.get("min_score_for_people") or 0)}))
    done = _searched()
    out = []
    for o in data["items"]:
        if o["state"] == "bo_qua" or o["people_count"] >= int(s.get("people_per_opportunity") or 4):
            continue
        if time.time() - done.get(o["id"], 0) < PEOPLE_RECHECK_DAYS * 86400:
            continue
        out.append(o)
    return out[:limit]


def people_for(cfg, budget, llm, opps):
    """Nguoi ra quyet dinh cho cac co hoi: Google X-ray (re, ca ten dau moi trong nguon), roi LinkedIn loc dung cong ty
    (trang LinkedIn cong ty tim duoc o buoc lien he) cho vai co hoi diem cao con it ket qua."""
    s = cfg["settings"]
    if not opps or not s["sources"].get("linkedin"):
        return []
    after = (today() - dt.timedelta(days=3650)).isoformat()
    queries = {}
    for o in opps:
        short = short_company(o["company"])
        qs = [f'site:linkedin.com/in "{short}"', f'site:linkedin.com/in "{short}" {TITLE_OR}']
        lead_name = re.sub(r"(?i)^(ông|bà|anh|chị|mr\.?|ms\.?)\s+", "", (o.get("contact") or {}).get("name", "")).strip()
        if lead_name:
            qs.append(f'site:linkedin.com/in "{lead_name}"')
        queries[o["id"]] = qs
    results = google_search(budget, [q for qs in queries.values() for q in qs], after)
    by_query = {}
    for r in results:
        by_query.setdefault(r["query"], []).append(r)
    found = []
    searches = 0
    for o in opps:
        profiles = []
        for q in queries[o["id"]]:
            profiles += [p for p in parse_xray(by_query.get(q, [])) if p["linkedin_url"] not in {x["linkedin_url"] for x in profiles}]
        company_page = (o.get("company_contact") or {}).get("linkedin_company")
        if len(profiles) < 3 and searches < LINKEDIN_SEARCHES_PER_RUN and budget.allow(PRICE_LINKEDIN_PAGE, "tìm LinkedIn"):
            payload = {"profileScraperMode": "Short", "locations": ["Vietnam"], "takePages": 1, "maxItems": 25}
            if company_page:  # dung cong ty: chinh xac nhat
                payload.update({"currentCompanies": [company_page], "currentJobTitles": DECISION_TITLES})
            else:
                payload["searchQuery"] = short_company(o["company"])
            profiles += linkedin_search(budget, payload, f"LinkedIn: {short_company(o['company'])}"
                                        + (" (đúng trang công ty)" if company_page else ""))
            searches += 1
        _searched(o["id"], mark=True)
        if not profiles:
            continue
        context = (f"Công ty mục tiêu: {o['company']} ({o.get('industry_label') or o['industry']}, {o.get('province') or ''}).\n"
                   f"Cơ hội: {o.get('kind_label') or o['kind']}: {o.get('title') or ''}. {o.get('summary') or ''}\n"
                   "Chỉ giữ người hiện làm ở ĐÚNG công ty mục tiêu.\n"
                   "ĐẦU MỐI GIÁN TIẾP: nếu trong danh sách không có ai ra quyết định ở công ty mục tiêu, vẫn giữ tối đa 2 người "
                   "HIỆN làm ở đúng công ty đó (ưu tiên quản lý, hành chính, văn phòng, nhân sự, IT; vẫn loại người ở công ty "
                   "khác), role_group=khac, sales_note bắt đầu bằng \"Đầu mối gián tiếp:\" và gợi ý nhờ họ giới thiệu phòng "
                   "kỹ thuật / mua hàng.")
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
        queries = full_queries(cfg) if FULL else build_queries(cfg)
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
            return batch, extract_batch(cfg["llm"], s["seller"], batch, region, int(s.get("lookback_days") or 30)), None
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
                if not (o.get("published") or it.get("date")) and it.get("origin") != "Trang theo dõi" and o.get("kind") != "moi_thau":
                    verdicts[-1]["verdict"] = "loại: không rõ ngày tin (trang không chính thức, có thể là việc cũ)"
                    continue
                if not (o.get("published") or it.get("date")):
                    it["date"] = text_date(f"{it['title']} {it.get('snippet') or ''}")
                o["sources"] = [{"url": it["url"], "title": it["title"], "published": o.get("published") or it.get("date") or ""}]
                if not o.get("published"):
                    o["published"] = it.get("date") or ""
                opportunities.append(o)
    log(f"Đã đọc {len(items) - failed}/{len(items)} tin, giữ {len(opportunities)}")
    return verdicts, opportunities, failed


def run(trigger="chat"):
    cfg = load_config()
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
             "google_queries": 0, "news_items": 0, "watch_links": 0, "contacts_found": 0}
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
        # lien he doanh nghiep (website, SDT, email, MST, LinkedIn) cho moi co hoi chua co, diem cao truoc
        if cfg.get("apify_key") and not _wallet_empty and not budget.stopped:
            stats["contacts_found"] = find_contacts(cfg, budget, cfg["llm"], contact_targets(CONTACTS_PER_RUN))
        # nguoi ra quyet dinh: co hoi du diem con thieu nguoi (ca co hoi cu), moi co hoi tim lai sau 30 ngay
        people = []
        targets = people_targets(cfg) if cfg.get("apify_key") and not _wallet_empty and not budget.stopped else []
        if targets:
            people += people_for(cfg, budget, cfg["llm"], targets)
        if cfg.get("apify_key") and not _wallet_empty:
            people += sweep(cfg, budget, cfg["llm"])
        if people:
            done = owui("POST", "/agent/people", {"items": people, "run_id": run_id})
            stats["people_created"], stats["people_merged"] = len(done["created"]), len(done["merged"])
            for r in done["rejected"]:
                log(f"Không lưu người {r.get('name')}: {r['reason']}")
        if budget.stopped:
            notes.append(budget.stopped)
        notes.extend(n for n in APIFY_NOTES if n not in notes)
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


def contact_cell(o):
    """SDT / email dau tien cho bang bao cao; khong co thi so nguoi tren LinkedIn hoac '-'."""
    cc = o.get("company_contact") or {}
    lead = o.get("contact") or {}
    phone = (lead.get("phone") or "").split(",")[0].strip() or next((p["value"] for p in cc.get("phones", [])), "")
    email = lead.get("email") or next((e["value"] for e in cc.get("emails", [])), "")
    parts = [x for x in (phone, email) if x]
    if o.get("people_count"):
        parts.append(f"{o['people_count']} người")
    return " · ".join(parts[:3]) or "chưa có"


def report_text(hours=26, run_id=None, stats=None, cost=0.0, status="ok", message=""):
    since = int(time.time() - hours * 3600) if hours else 0
    opps = owui("GET", "/opportunities?" + urllib.parse.urlencode({"state": "moi", "sort": "score", "limit": 200,
                                                                   "fresh": "1"}))["items"]
    new = [o for o in opps if (o.get("run_id") == run_id if run_id else o["first_seen"] >= since)]
    lines = []
    if stats is not None:
        lines.append(f"**Lần quét {'xong' if status == 'ok' else 'xong một phần' if status == 'partial' else 'lỗi'}**: đọc "
                     f"{stats['candidates']} tin mới, **{stats['created']} cơ hội mới**, {stats['merged']} cơ hội gặp lại "
                     f"(thêm nguồn), {stats['people_created']} người liên hệ mới, tìm được SĐT / email cho "
                     f"{stats.get('contacts_found', 0)} doanh nghiệp. Chi phí Apify ${cost:.2f}.")
        if message:
            lines.append(f"Lưu ý: {message}.")
    else:
        lines.append(f"**{len(new)} cơ hội mới** trong {hours} giờ qua (đang ở mục Mới).")
    if new:
        lines.append("")
        lines.append("| Điểm | Doanh nghiệp | Loại | Tỉnh | Hạn / ngày tin | Liên hệ | Thiết bị |")
        lines.append("|---|---|---|---|---|---|---|")
        for o in new[:15]:
            when = f"hạn {'/'.join(reversed(o['deadline'].split('-')))}" if o.get("deadline") else (
                dt.datetime.fromtimestamp(o["published_at"], VN).strftime("%d/%m/%Y") if o.get("published_at") else "")
            equip = ", ".join(o["equipment"][:3]) + (" (gợi ý)" if o["equipment_inferred"] and o["equipment"] else "")
            link = next((x["url"] for x in o["sources"] if "news.google.com" not in x["url"]), o["sources"][0]["url"] if o["sources"] else "")
            company = f"[{o['company']}]({link})" if link else o["company"]
            lines.append(f"| {o['score']} | {company} | {o['kind_label']} | {o['province'] or '?'} | {when} | "
                         f"{contact_cell(o)} | {equip} |")
        if len(new) > 15:
            lines.append(f"\n… và {len(new) - 15} cơ hội khác.")
    lines.append(f"\nXem đủ, đổi trạng thái, xuất CSV: {page_url()}")
    return "\n".join(lines)


# ---------------------------------------------------------------- lenh


def cmd_status(_):
    cfg = load_config()
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
    if args.full and not FULL:  # chay lai chinh no voi LEAD_FULL=1 (hang so doc luc import)
        os.execve(sys.executable, [sys.executable, "-I", os.path.abspath(__file__), *sys.argv[1:]],
                  {**os.environ, "LEAD_FULL": "1"})
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
                                env={**os.environ, "PYTHONUNBUFFERED": "1", **({"LEAD_FULL": "1"} if args.full else {})})
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
    cfg = load_config()
    stats, notes = {}, []
    items = gather(cfg, Budget(cfg), stats, notes, check_seen=not args.all)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=1)
    print(f"{len(items)} tin -> {args.out} {stats} {notes}")


def cmd_extract(args):
    """Doc 1 file tin bang LLM, in ket qua (khong luu len San lead)."""
    cfg = load_config()
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
    data = owui("GET", "/opportunities?" + urllib.parse.urlencode({"state": "moi", "sort": "score", "limit": args.limit,
                                                                   "fresh": "1"}))
    for o in data["items"]:
        print(f"{o['score']:>3} | {o['company']} | {o['kind_label']} | {o['province'] or '?'} | {o['title'][:60]} | id {o['id']}")
    print(f"\nTổng {data['total']} cơ hội ở mục Mới. Trang: {page_url()}")


def cmd_people(args):
    cfg = load_config()
    budget = Budget(cfg)
    if args.opportunity == "all":  # moi co hoi du diem con thieu nguoi (bo qua moc 30 ngay)
        if os.path.exists(os.path.join(STATE, "people-searched.json")):
            os.remove(os.path.join(STATE, "people-searched.json"))
        opps = people_targets(cfg, limit=args.limit)
    else:
        opps = [owui("GET", f"/opportunities/{args.opportunity}")]
    people = people_for(cfg, budget, cfg["llm"], opps)
    if people:
        done = owui("POST", "/agent/people", {"items": people})
        print(f"{len(done['created'])} người mới, {len(done['merged'])} đã có. Chi phí ${budget.spent:.3f}")
        for p in people:
            print(f"- {p.get('name')} | {p.get('title')} | {p.get('linkedin_url')}")
    else:
        print(f"Không tìm thấy người phù hợp. {budget.stopped}")


def cmd_contacts(args):
    cfg = load_config()
    budget = Budget(cfg)
    opps = [owui("GET", f"/opportunities/{args.opportunity}")] if args.opportunity else contact_targets(args.limit)
    found = find_contacts(cfg, budget, cfg["llm"], opps)
    print(f"Tìm liên hệ cho {len(opps)} cơ hội: {found} có SĐT / email. Chi phí ${budget.spent:.3f}. {budget.stopped}")


def cmd_check_sources(_):
    cfg = load_config()
    pages = watch_list(cfg)
    with concurrent.futures.ThreadPoolExecutor(FETCH_WORKERS) as pool:
        for page, links in zip(pages, pool.map(page_links, pages)):
            useful = sum(1 for x in links or [] if _watch_ok(page, x["title"]))
            print(f"{'OK ' if links else 'LỖI'} {page['label']}: "
                  f"{(str(len(links)) + ' link, ' + str(useful) + ' đáng đọc') if links is not None else 'không đọc được'} | {page['url']}")


def main():
    ap = argparse.ArgumentParser(description="Săn lead B2B (Open WebUI > Săn lead)")
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("status").set_defaults(f=cmd_status)
    for name, fn in (("run", cmd_run), ("start", cmd_start)):
        p = sp.add_parser(name)
        p.add_argument("--trigger", default="chat", choices=["chat", "cron", "test"])
        p.add_argument("--quiet", action="store_true", help="tien do ghi vao state/run-*.log, chi in bao cao (cho cron)")
        p.add_argument("--full", action="store_true", help="quet day du: moi nhom truy van trong 1 luot (ton hon)")
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
    p.add_argument("--opportunity", required=True, help="id co hoi, hoac all")
    p.add_argument("--limit", type=int, default=8)
    p.set_defaults(f=cmd_people)
    p = sp.add_parser("contacts")
    p.add_argument("--opportunity", default="")
    p.add_argument("--limit", type=int, default=CONTACTS_PER_RUN)
    p.set_defaults(f=cmd_contacts)
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
