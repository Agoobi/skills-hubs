# Creative (PAOHF) và phân tích đối thủ

## PAOHF

| Ô | Nghĩa |
|---|---|
| **P**ersonal | Người nhận và bối cảnh, mức nhận thức |
| **A**ngle | Lý do quan tâm, góc thuyết phục (một luận điểm) |
| **O**ffer | Đề nghị trao đổi: giá, quyền lợi, quà, điều kiện |
| **H**ook | Câu/khung mở đầu |
| **F**ormat | Cách thể hiện: POV, demo, review, hỏi–đáp, so sánh… |

- Không dùng một ý cho cả Angle, Hook và Format. Feedback/demo/so sánh thường là Format; Angle nằm bên trong.
- Ma trận P × A × O × H × F có chọn lọc, không ghép mọi tổ hợp. Phân biệt kho ý tưởng với số mẫu đem chạy.
- Test Angle thì giữ Personal/Offer; test Hook/Format thì giữ Angle. Khám phá nhiều biến cùng lúc thì ghi nhiễu.
- Đổi vài từ không phải concept mới.

## Quy trình viết

1. Nhận từ nhánh Ads: hành động cần thúc đẩy (mua web, đăng ký, chat, tương tác, xem live), sự kiện, giả thuyết. Không tự đổi mục tiêu hay ngân sách.
2. Chưa chốt số lượng: đề xuất **3 concept** khác biệt thực chất, không tự sinh 15 tài sản.
3. Khung nội dung gợi ý (CHẠM): Câu mở móc → Hiện thực vấn đề → Áp dụng giải pháp → Mở lòng câu chuyện → Hành động. Caption/kịch bản chứa đủ; chữ trên ảnh chỉ giữ ý chính.
4. Viết caption, headline, mô tả, CTA khớp đích. Giá VND rõ, ship/quà/điều kiện rõ. Không bịa giá, claim, chứng nhận, feedback, khan hiếm. Không ám chỉ thuộc tính nhạy cảm của người xem ("bạn bị…").
5. Rà chính sách (`chinh-sach-preflight.md`) cho caption, chữ trong ảnh, lời thoại/phụ đề, offer, đích.
6. Tạo ảnh nếu có công cụ: giữ đúng bao bì/sản phẩm thật, kiểm chữ tiếng Việt và tỷ lệ. Công cụ làm sai thì dùng ảnh gốc hoặc báo cần sửa. Không có công cụ video thì giao kịch bản / storyboard / shot list và ghi "chưa dựng".
7. Kích thước theo placement: feed 1:1 hoặc 4:5, Reels/Stories 9:16; vùng an toàn, chữ đọc được trên điện thoại, phụ đề cho video. Xác minh bằng preview trong tài khoản.
8. QA: đúng sản phẩm/offer/CTA/đích, không lỗi chữ, bằng chứng thật. Trạng thái `DRAFT` / `NEEDS_FIX` / `READY_FOR_HANDOFF` (READY không bảo đảm Meta duyệt).

Giới hạn chữ gợi ý của Meta: tiêu đề ~25 ký tự, nội dung chính ~90–125 ký tự hiển thị trước "Xem thêm"; tiêu đề và nội dung không bắt đầu bằng dấu câu.

## Mã mẫu và bàn giao

- `creative_id` dạng `[dự án]-[concept]-v[phiên bản]`; sửa = phiên bản mới, lưu `parent_id`.
- Bảng: creative_id | Personal | Angle | Offer | Hook | Format | biến test | caption / headline / CTA | đường dẫn tài sản hoặc URL | placement | điểm đến | giả thuyết | QA.
- Tài sản chưa tạo ghi `planned`, không bịa URL. Giữ `product_id`, `offer_id` để đối chiếu.
- Nhận lại spend/kết quả/chất lượng từ nhánh Ads để làm vòng sau. Không gọi mẫu thắng vì đẹp hoặc chỉ vì CTR.
- Đăng bài Page là việc riêng (skill `viet-bai-facebook-fanpage`), chỉ làm khi người dùng yêu cầu.

## Phân tích quảng cáo đối thủ

**Nguồn:** Thư viện quảng cáo Meta (`https://www.facebook.com/ads/library/`; qua Zernio `GET /v1/ads/library`), bài Page công khai, ảnh chụp News Feed người dùng gửi, trang đích. Mặc định khảo sát 5 mẫu khác nhau và ghi rõ đây là phạm vi khảo sát, không đại diện thị trường.

**Quy trình:**
1. Xác minh đúng Page/thương hiệu (tránh Page trùng tên). Định danh bằng ad ID / post ID; gộp mẫu trùng nội dung để đếm concept nhưng giữ các ID.
2. Thu caption, headline, chữ trong ảnh, lời thoại/phụ đề, CTA, media, đích, offer. Video không xem được thì ghi giới hạn, không suy từ thumbnail.
3. Phân loại phễu quan sát được (bán web, lead web, lead form, tin nhắn, tương tác, live, chưa rõ). CTA "Mua ngay" không chứng minh objective Sales. Tách **objective xác nhận** (thường N/A) với **phễu suy luận** (ghi căn cứ và mức chắc chắn thấp/vừa/cao).
4. Ghi tương tác hiển thị đúng như nguồn (1,2K giữ nguyên), kèm thời điểm đọc. Không tính CTR/CPC/CPE từ tương tác công khai.
5. Mốc thời gian tách riêng: `observed_at`, `screenshot_at`, `post_published_at`, `ad_started_at`, `ad_ended_at`, `page_created_at`. Không lấy thời điểm quét làm ngày tạo; "active" chỉ đúng tại thời điểm xem.
6. Bóc PAOHF, hành trình lời hứa → CTA → đích → hành động. Không gửi form, nhắn tin hay đặt hàng với đối thủ để khảo sát nếu chưa được yêu cầu.
7. Kết luận: điểm lặp lại, khoảng trống, giả thuyết cần test bằng dữ liệu của mình. Quảng cáo chạy lâu / nhiều bản / nhiều tương tác **không chứng minh có lãi**. Không dựng CPA, ROAS, ngân sách, tệp từ dữ liệu công khai.
8. Bàn giao 3 concept **của mình** (không sao chép caption, hình, video, feedback đối thủ) sang phần viết creative.

**Đầu ra:** bảng kiểm kê (sample_id, Page, nguồn, ad ID, post ID, loại phễu, objective xác nhận hoặc N/A, CTA/đích, offer, các mốc thời gian, tương tác, giới hạn) + bảng PAOHF (sample_id, Personal suy luận, Angle, Offer, Hook, Format, điểm mạnh, điểm cản, giả thuyết, mức chắc chắn). Thiếu ghi N/A, không ghi 0.
