# T016 — Policy và state machine MVP

Ngày: 30/10/2026 (Asia/Saigon). **Đặc tả thiết kế `social-policy-draft-0.2`**, chưa phải cấu hình runtime được duyệt. Owner thiết kế: chủ dự án ShieldVI; người phê duyệt triển khai/kích hoạt: chủ dự án. `approved_by=null`, `activated_at=null`. T016 không triển khai Social API, worker hay policy engine.

## 1. Quyết định MVP và phạm vi

- Demo local/private với tài khoản thử, chưa mở đăng ký công khai/Internet hoặc nhận dữ liệu người dùng thật. Endpoint register sau này vẫn được test; public registration cần cờ bật riêng, mặc định tắt. Không tự tạo tài khoản thật.
- Hai backend, Social API là nơi duy nhất quyết định visibility và ghi Social DB. AI chỉ cung cấp prediction/evidence; human annotation V3 không phải quyết định social.
- Mọi nội dung mới, từ mọi tài khoản, bắt đầu pending; lưu content+job cùng transaction. Không trả thông báo “đã công khai” trước policy/manual decision.
- Chế độ đầu tiên **shadow**: LOW tự đăng, REVIEW đăng kèm cờ nội bộ, HIGH chỉ là đề xuất shadow và đăng kèm cờ/queue ưu tiên. UNKNOWN giữ pending. Shadow HIGH không bật auto-hold; moderator vẫn có quyền ẩn thủ công với lý do.
- Chưa có luật định lượng HIGH được kiểm định. Trong MVP, heuristic repeated của V3 chỉ vào REVIEW ưu tiên cao, **không tự gán HIGH**. HIGH trong decision table là nhánh tương lai/fixture hoặc nhận định của người duyệt, không tuyên bố classifier hiện có tạo HIGH hợp lệ.
- Không auto-ban, không auto-delete vĩnh viễn. Threshold model giữ `0.41`; điểm heuristic risk của V3 và `research_synthetic/0.03` không phải policy threshold.

## 2. Năm trường tách biệt và mapping legacy

| Trường chuẩn social | Ý nghĩa |
|---|---|
| `ai_label`, `ai_score` | Output model, score trong [0,1]; không phải mức vi phạm cộng đồng. AI lỗi thì null/unknown, không gán score=0. |
| `risk_tier` | LOW, REVIEW, HIGH, UNKNOWN theo policy; lưu reason và policy version. |
| `visibility_status` | PENDING_MODERATION, PUBLISHED, PUBLISHED_FLAGGED, HELD_FOR_REVIEW, HIDDEN, DELETED_BY_AUTHOR. |
| `review_status` | NOT_REQUIRED, QUEUED, UNDER_REVIEW, APPROVED, REJECTED, APPEALED, RESOLVED. |
| `moderation_jobs.status` | QUEUED, PROCESSING, SUCCEEDED, RETRY_WAIT, FAILED_PERMANENTLY; độc lập visibility. |

Social API dùng enum **uppercase** trên, không thêm cột `status` gom mọi nghĩa. Legacy V3 giữ nguyên response. Adapter T011 ánh xạ `toxicity_score → ai_score`, giữ `model_threshold`, `model_version`, `lexicon_version`, timestamp và evidence; không đổi response `/api/analyze`.

Các tên cũ trong ARCHITECTURE/DATABASE: `pending_moderation` tương ứng visibility PENDING_MODERATION; `needs_review` là review QUEUED, thường visibility PUBLISHED_FLAGGED trong shadow; `approved` tương ứng visibility PUBLISHED, nhưng LOW tự đăng có review NOT_REQUIRED, manual approve có APPROVED. `hidden` tương ứng HIDDEN; `failed_review` **không còn là visibility**, dùng job FAILED_PERMANENTLY + manual queue. Không áp mapping máy móc lên database legacy.

## 3. Decision table, ưu tiên theo thứ tự

Guard quyền/revision ở mục 5 chạy trước bảng. “Queue” là persistent queue của Social DB, không phụ thuộc admin đang online. Cờ nội bộ không hiển thị danh tính reporter hoặc gắn huy hiệu “toxic” công khai cho user.

| Ưu tiên / tình huống | risk_tier | Visibility ban đầu → sau xử lý | Review / queue |
|---|---|---|---|
| Timeout/503, response sai schema/version/correlation, thiếu score hoặc context không nhất quán | UNKNOWN | PENDING_MODERATION → PENDING_MODERATION | QUEUED; retry/manual, không fail-open |
| Kết quả hợp lệ, đủ dữ liệu phân tích text, không tín hiệu đáng kể | LOW | PENDING_MODERATION → PUBLISHED | NOT_REQUIRED, không queue thường lệ |
| Chỉ score ≥0.41; chỉ từ tục; hướng người; bất đồng AI/lexicon; trích dẫn hoặc teencode mơ hồ | REVIEW | PENDING_MODERATION → PUBLISHED_FLAGGED | QUEUED, ưu tiên thường |
| Repeated candidate V3 với provenance hợp lệ, nhiều comment/thời điểm cùng actor-target | REVIEW | PENDING_MODERATION → PUBLISHED_FLAGGED | QUEUED, ưu tiên cao; không HIGH chỉ theo heuristic |
| HIGH hợp lệ theo policy được hiệu chuẩn trong tương lai, **shadow** hoặc kill switch review-only | HIGH | PENDING_MODERATION → PUBLISHED_FLAGGED | QUEUED, ưu tiên cao; `proposed_visibility=HELD_FOR_REVIEW` chỉ audit |
| HIGH + policy được duyệt + tất cả gate đạt + hold_enabled + không kill switch | HIGH | PENDING_MODERATION → HELD_FOR_REVIEW | QUEUED, ưu tiên cao; **nhánh chưa được phép bật** |
| Report mới trên nội dung public | Giữ risk hiện có, ghi report riêng | Giữ visibility | QUEUED; report count không tự HIGH/ẩn |

Trích dẫn/giải thích được xác nhận không có tín hiệu khác có thể là LOW; nếu lexicon/model vẫn báo thì REVIEW, không hạ mọi trích dẫn thành clean. Một lời xúc phạm không chứng minh repeated. Context vắng nhưng khai báo rõ không có thread chỉ có thể phân tích comment-level, ghi limitation, không tạo repeated; context cung cấp bị sai/không nhất quán là UNKNOWN. Thiếu calibration HIGH không làm mọi kết quả hợp lệ thành UNKNOWN.

## 4. Version và flags — thiết kế, không tạo active config

Tên dự kiến để T012 triển khai sau phê duyệt:

| Trường | Giá trị thiết kế ban đầu / ràng buộc |
|---|---|
| `policy_version` | `social-policy-draft-0.2`; bất biến sau phát hành, thay luật tạo version mới |
| `mode` | `shadow`; chỉ cho `enforce` sau phê duyệt riêng |
| `high_rule_version`, `validation_report_id` | null; chưa có classifier/gate được hiệu chuẩn |
| `high_auto_hold_enabled` | false |
| `review_only_kill_switch` | true cho MVP; HIGH luôn flag/manual |
| `auto_delete_enabled`, `auto_ban_enabled` | false; ngoài phạm vi policy MVP |
| `approved_by`, `activated_at` | null; không tự điền người duyệt hoặc ngày kích hoạt |

`contracts/moderation_policy.example.json` vẫn là ví dụ `draft-0.1`, **không được nạp thành cấu hình runtime**: dòng HIGH/HELD trong ví dụ là đề xuất, phải áp guard shadow ở đặc tả này. Không sửa/tạo active policy config trong T016. Khi có duyệt, đồng bộ example/schema với version phát hành trước triển khai. Chỉ đổi `mode` hoặc boolean không đủ bypass gate; startup validator tương lai phải từ chối enforce/hold nếu thiếu approval/report/rule version.

Kill switch ngừng phát sinh auto-hold mới; không tự công khai nội dung đã HELD/HIDDEN. Rollback policy: ngừng worker claim khi cần, chuyển về review-only, giữ quyết định/version cũ trong audit; re-evaluate bằng job mới có guard, không mass-unhide. Người có role admin đổi policy; moderator chỉ quyết định nội dung.

## 5. Visibility transitions và quyền actor

| Event / actor | Trạng thái nguồn | Trạng thái đích | Điều kiện / side effect |
|---|---|---|---|
| Create / author | Chưa tồn tại | PENDING_MODERATION | Cùng transaction tạo revision=1, job QUEUED, risk UNKNOWN, review QUEUED |
| Valid result / social worker | PENDING_MODERATION | Theo decision table | Worker không gọi API quyết định bằng quyền user |
| Retry/failure / social worker | PENDING_MODERATION | Giữ pending | Risk UNKNOWN, review QUEUED; không làm mất body |
| Claim review / moderator, admin | Pending/flagged/held/hidden/public | Không đổi visibility | QUEUED hoặc APPEALED → UNDER_REVIEW; optimistic lock |
| Approve / moderator, admin | Pending/flagged/held | PUBLISHED | Review APPROVED, reason bắt buộc |
| Hide / moderator, admin | Pending/public/flagged/held | HIDDEN | Review REJECTED, reason bắt buộc |
| Appeal / chính author | HIDDEN hoặc HELD_FOR_REVIEW | Không đổi visibility | Review APPEALED, một appeal đang mở/revision; không tự restore |
| Resolve appeal accepted / moderator, admin | HIDDEN/HELD_FOR_REVIEW | PUBLISHED | Review RESOLVED, outcome RESTORED; giữ lịch sử quyết định cũ |
| Resolve appeal denied / moderator, admin | HIDDEN/HELD_FOR_REVIEW | HIDDEN | Review RESOLVED, outcome UPHELD, reason bắt buộc |
| Restore sai sót / moderator, admin | HIDDEN/HELD_FOR_REVIEW | PUBLISHED | Reason/audit; APPROVED, hoặc RESOLVED nếu có appeal |
| Report / user đã xác thực | Public/flagged | Không đổi visibility | Dedupe reporter/content/revision; không auto-hide do số report |
| Edit / chính author | Mọi trạng thái trừ DELETED_BY_AUTHOR | PENDING_MODERATION | Revision tăng, job mới cùng transaction; vô hiệu score cũ, giữ audit/appeal cũ gắn revision |
| Delete / chính author | Mọi trạng thái chưa xóa | DELETED_BY_AUTHOR | Soft delete, hủy hiệu lực job, đóng queue/appeal với outcome AUTHOR_DELETED; không còn phục vụ body |

`DELETED_BY_AUTHOR` là terminal trong MVP; kể cả moderator không restore qua API thông thường. Approve không khôi phục nội dung đã xóa. Author sửa nội dung HIDDEN được tạo revision mới nhưng không xóa quyết định vi phạm cũ; rate limit và audit chống sửa lặp để né duyệt. Cả revision mới lẫn revision cũ tạm ngừng public khi edit, không phục vụ body cũ như bản hiện tại; chỉ author/moderator có quyền xem revision cũ theo retention.

Guard bắt buộc cho worker: request_id đúng job + content_id/content_revision khớp hiện tại; policy version đúng snapshot job đang được cho phép áp dụng; content chưa deleted; `decision_version` khớp snapshot trước gọi AI; chưa có quyết định moderator của revision hiện tại. Không đủ thì lưu outcome stale/ignored, không mutate visibility. Hai người duyệt gửi `expected_decision_version`; transaction compare-and-swap, một thành công, còn lại 409. Mọi quyết định chấp nhận tăng decision_version; duplicate request/job/decision không tạo audit/action trùng.

Review lifecycle: create/flag/error/report → QUEUED; claim → UNDER_REVIEW; quyết định → APPROVED/REJECTED; appeal → APPEALED; claim appeal → UNDER_REVIEW (giữ appeal_id); resolve → RESOLVED + outcome. Claim có lease, hết hạn trở về QUEUED/APPEALED đúng nguồn; không thay visibility. LOW tự publish → NOT_REQUIRED. `RESOLVED` không tự nói nội dung đang public hay hidden, phải đọc visibility/outcome.

## 6. Worker và offline

Job: QUEUED → PROCESSING (claim/lease nguyên tử) → SUCCEEDED hoặc RETRY_WAIT → PROCESSING. Lease hết hạn phải reclaim bằng token mới, worker cũ không được finalize. Sau giới hạn attempts hoặc lỗi không retry được → FAILED_PERMANENTLY, content vẫn pending và manual queue. SUCCEEDED nghĩa job kết thúc hợp lệ; outcome có thể APPLIED hoặc STALE_IGNORED, không đồng nghĩa đã public.

Đề xuất budget dev: connect timeout 3s/read 60s, tối đa 3 attempts; delay 5s rồi 30s + jitter 0–20%, tôn trọng Retry-After trong budget. Network/timeout/429/5xx retry; 4xx validation/auth/version lỗi cấu hình không retry mù, alert + manual. Đây là tham số dev dự kiến, chưa deploy; T017 đo latency để chốt lease > request budget, claim token và lịch retry bền vững. Không giữ transaction DB trong lúc gọi model.

Admin offline: queue lưu bền, không reset status khi reload; sắp ưu tiên lỗi pending/held và repeated candidate, sau đó thời gian chờ để tránh starvation, reports chỉ hỗ trợ sau dedupe. Không có timeout tự approve/hide, không hứa SLA 24/24. Sau lỗi vĩnh viễn manual review vẫn hoạt động không cần GPU. Người viết nhận success khi lưu content+job thành công kèm trạng thái pending; lỗi lưu transaction phải trả failure.

## 7. Quyền xem, parent và audit

- Public/feed/direct URL/search/count: chỉ PUBLISHED/PUBLISHED_FLAGGED **và mọi ancestor còn public**, bao gồm post và chuỗi parent comments. Check server-side cho cả direct ID, attachment/preview/export nếu có; không chỉ lọc UI.
- Post hoặc comment ancestor pending/held/hidden/deleted: che toàn bộ descendants đối với người khác, **không sửa hàng loạt state con**. Restore ancestor chỉ làm hiện lại descendants vốn public và không có ancestor khác bị chặn. Child hidden/pending/deleted vẫn không public. Không tự restore child bị ẩn riêng.
- Author xem nội dung hiện tại của mình khi pending/held/hidden + lý do tổng quát/appeal; không được đọc body ancestor ẩn của người khác qua reply/context. Moderator/admin đọc theo quyền audit. Deleted không trả body qua API thường, chỉ tombstone.
- Audit: actor type/id (system worker cũng có actor), timestamp UTC, event/reason code và reason, request/job id, content/revision, before/after, decision_version, policy version, model/lexicon version khi có, appeal outcome. Không bắt buộc model version cho quyết định manual lúc AI lỗi; ghi null + reason.
- Không đưa reporter id/email/IP/token/context riêng tư vào user response; logs mặc định không full text. Report không phải nhãn gold.

## 8. Các quyết định còn mở và gate

| Câu hỏi | Chốt cho demo MVP | Chưa thể chốt / điều kiện mở rộng |
|---|---|---|
| Đăng ký và hosting | Local/private, tài khoản thử; không public registration | Chủ dự án duyệt đối tượng/Internet, security/privacy readiness trước mở |
| Nội dung vi phạm | Review ưu tiên công kích hướng người, đe dọa, quấy rối lặp lại có provenance; tranh luận/phản biện, trích dẫn và từ tục không tự vi phạm | Quy tắc cộng đồng công khai và guideline nhãn severity/HIGH chưa có validation; chưa bật luật HIGH |
| Nội dung tài khoản mới | Pending như mọi tài khoản | Không có đặc quyền bypass AI theo tuổi tài khoản |
| Appeal/SLA | Manual, không cam kết giờ xử lý, không auto restore; không giới hạn thời gian nộp trong demo | SLA, cửa sổ appeal và nguồn lực trước production |
| Parent bị ẩn/restore | Effective visibility qua ancestor, giữ state con riêng | Test integration recursive lookup/pagination ở T009/T018 |
| Edit public | Revision mới pending, bản cũ ngừng public, job mới | Không tối ưu bằng publish bản cũ trong MVP |
| Retention/dữ liệu | Chỉ fixture/synthetic local; không tự ingest dữ liệu thật, không tự purge DB/audit hiện có | Chủ dự án duyệt số ngày riêng cho content/audit/evidence/log/backups, quyền sử dụng dữ liệu và quy trình xóa trước production. Không chọn số ngày tùy tiện |
| Model baseline | Giữ 0.41, không đổi selection/checkpoint V3 | T007 thấy refined V1.1 approved auto-select; T011 phải ghi model path/version/hash thực, không lẫn với V1 baseline |

Gate HIGH auto-hold (tất cả đều cần): guideline và gold thread/content gán nhãn thủ công có provenance/quyền dùng; tách validation khỏi final test theo thread/actor để chống leakage; annotator count/adjudication rõ (single-reviewer phải ghi giới hạn); đo policy hold precision/recall, FPR trên benign, FNR trên harmful, confusion matrix, target precision/unknown, repeated event precision/recall, coverage/abstention và CI/support theo teencode/English/không dấu/trích dẫn/cảm thán/tranh luận. Đo queue load/age, latency, failure/retry, appeal overturn và khả năng rollback.

**Chưa có số liệu nên chưa chốt** HIGH threshold, FPR/FNR budget, minimum support/CI hoặc cửa sổ theo dõi vận hành. Phải chốt mục tiêu với chủ dự án **trước** chọn rule trên validation, giữ final test không dùng tuning, chạy shadow trên dữ liệu được phép, cung cấp report/version/hash, thử kill switch/rollback/recovery và có phê duyệt kích hoạt rõ. Bất kỳ gate thiếu: HIGH không auto-hold. Test synthetic pass chỉ chứng minh ràng buộc thiết kế, không chứng minh chất lượng AI.

## 9. Bằng chứng và bàn giao

Test cases máy đọc: `contracts/policy_acceptance_cases.json` (**test vectors**, không active config). Tests: `tests/test_policy_design.py`; kiểm tra invariants đặc tả và đối chiếu lexicon/engine thật V3 với predictor giả. Không triển khai policy reference engine để giả lập một service đã tồn tại. Những transitions/roles/concurrency/retry/ancestor ở trên là acceptance contract cho T009/T012/T017/T018, chưa có DB/API thực để xác nhận end-to-end.

File thiết kế này giải quyết khác biệt state nêu ở T007; báo cáo T007 là snapshot lịch sử, không sửa baseline. Task tiếp theo khi người dùng yêu cầu: T008, theo `docs/design/10_KE_HOACH_CODEX.md`; không tự bắt đầu trong T016.

### Kết quả kiểm chứng

| Lệnh / kiểm chứng | Kết quả |
|---|---|
| V3 venv Python `-m pytest tests/test_policy_design.py -v -p no:cacheprovider` tại design root | **17 passed**, 0.17s; [log](../baseline/T016/policy-tests.txt) |
| V3 venv Python `-m pytest -q -p no:cacheprovider` tại V3 root, STORE_SUMMARIES=0 | **111 passed, 1 warning**, 1.35s; [log](../baseline/T016/legacy-pytest.txt) |
| Đối chiếu SHA-256 manifest T007 | **68/68 file V3 không đổi**; [evidence](../baseline/T016/legacy-integrity.json) |
| Frontend build | Không chạy lại vì không đổi frontend; xem baseline T007 |

Warning regression là Starlette/httpx deprecation hiện có. Chưa kiểm chứng real inference, calibration HIGH và thực thi transitions/roles/concurrency/worker/ancestor visibility qua Social DB/API/UI (chưa triển khai). Những giới hạn này không được diễn giải thành integration pass.
