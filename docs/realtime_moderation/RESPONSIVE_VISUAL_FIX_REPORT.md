# Sửa responsive theo cửa sổ Chrome thực — 05/11/2026

Trạng thái: DONE_VERIFIED trong phạm vi Live/Studio và các kích thước được đo.
Báo cáo này bổ sung bằng chứng cho đợt responsive trước, không ghi đè receipt cũ.

## Nguyên nhân đã đo được

1. `scripts/demo_open_browsers.mjs` tạo **mọi context**, kể cả Chrome có cửa sổ,
   bằng `viewport: {width:1250,height:950}`. Playwright giữ viewport CSS ở 1250px
   khi người dùng thay đổi kích thước cửa sổ hệ điều hành. Đây là nguyên nhân
   khác biệt giữa giao diện thực và test cũ dùng `page.setViewportSize()`.
2. Các giới hạn CSS còn áp dụng lên shell: Social1480px, Moderator main/JSON/nav
   1500px, Studio1440px. Chúng không phải lỗi 1075px duy nhất, nhưng khiến các
   workspace không dùng hết chiều ngang khi viewport thực đã được sửa.
3. Tablet đang hiện nhiều cột vì media query nhìn thấy **1250px**, không thấy
   cửa sổ850px. Không phải suy đoán file CSS responsive chưa nạp.

Số đo baseline từ **script demo thật**, Chrome có cửa sổ, trước khi gọi bất kỳ
`setViewportSize()` nào:

| Trang | Chrome window width | CSS innerWidth | #root width | Filter columns |
| --- | ---: | ---: | ---: | --- |
| Social | 1650 | 1250 | 1235 | — |
| Social | 850 | 1250 | 1250 | — |
| Moderator | 1650 | 1250 | 1235 | 3 × ~388px |
| Moderator | 850 | 1250 | 1250 | 3 × ~393px |
| Studio | 1650 | 1250 | 1235 | — |
| Studio | 850 | 1250 | 1250 | — |

Scrollbar giải thích chênh lệch15px ở một số trạng thái; DPR đo được là1.
Không khẳng định con số1075px trong ảnh bằng1250px CSS: không có số đo zoom/DPI
của ảnh đó. Sự lệch giữa cửa sổ và CSS viewport đã được tái hiện trực tiếp.

Baseline đầy đủ: `reports/task_rollout_20261104/demo_a53a25230d622b48/visual_result.json`.
70 ảnh/measurements trên7 trạng thái có dữ liệu;14 trường hợp vi phạm tiêu chí
độ phủ shell/workspace mới. Native probes lưu riêng; ảnh baseline theo viewport
được ghi sau probe để có cặp cùng kích thước cho CSS trước/sau.

## Thay đổi source

- `scripts/demo_open_browsers.mjs`: headed Chrome dùng `viewport:null`; headless
  smoke cũ giữ viewport rõ ràng. Cửa sổ người dùng resize tự nhiên.
- `apps/shared/responsive.css`: html/body/#root block, width100%, min-width0,
  không max-width hoặc margin khóa shell. Chỉ các entrypoint Live/Studio nạp file
  này; không sửa source/style legacy đã khóa.
- `apps/social-web/src/live-responsive.css`: shell và cột feed fluid; sidebar/help
  có giới hạn riêng, cột giữa dùng phần còn lại. Chỉ đoạn văn giới hạn80ch.
- `apps/moderation-web/src/workspace-responsive.css`: bỏ trần shell nav/main/JSON/
  Studio; filters auto-fit và tối đa2 cột ở tablet; field width100%/min-width0;
  queue desktop giới hạn270–440px, detail dùng phần còn lại. Từ1600px, review và
  context/evidence đặt cạnh nhau. Văn bản dài giới hạn84ch, không khóa workspace.
- `scripts/demo_realtime_studio.ps1`, runner hiện có: thêm `-VisualAudit` và
  `-VisualCheck`; vẫn khởi động chính các dịch vụ/demo hiện có.
- Browser visual harness mới lưu computed width, scrollWidth, clientWidth,
  CSS grid tracks, stylesheet thực nạp, field bounds và clipping theo ancestor.

Không dùng `overflow-x:hidden` trên body để che lỗi. Không đổi API, backend,
permission, checkpoint, threshold0.41, readiness lock hoặc nhãn/dataset gốc.

## Phương pháp nghiệm thu

Chạy từ root dự án:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\demo_realtime_studio.ps1 -VisualCheck
```

Launcher tạo session mới, đăng nhập các tài khoản demo vào Chrome thật. Các
desktop/tablet768–1920px được resize bằng CDP Browser window bounds và clear
device metrics, không dùng viewport cố định theo chiều ngang. Windows trên máy
test giới hạn outer height1100px, tương ứng content height1005px. Với các yêu cầu
cao1024/1080px, chỉ height được giả lập (`width:0` giữ chiều ngang native); đã đo
riêng rằng chiều ngang vẫn đổi khi resize cửa sổ. Mobile320/360/375/390px phải
giả lập viewport vì Chrome desktop có độ rộng cửa sổ tối thiểu.

Viewport:320×700,360×780,375×812,390×844,768×1024,850×700,1024×768,
1366×768,1650×900,1920×1080. Mỗi trạng thái/viewport có ảnh toàn trang và JSON
đo riêng. DOM thật có post/comment/reply nhiều cấp, đoạn dài/URL dài, kết quả AI,
queue/detail, dataset import, annotation draft, training config và model registry.

Ngoài overflow, test yêu cầu root≥98% và shell≥96% chiều rộng client; shell cân
giữa; workspace Moderator≥92% trên desktop rộng. Từng field phải trong viewport
và không bị ancestor clipping. Thread filter tablet phải có đủ160px và không
quá2 cột. Hai negative controls phải phát hiện root1075px sát trái ở1650px và
filter grid bị ép tràn ở850px; CSS chèn thử được gỡ ngay, không sửa source.

Training chỉ kiểm tra config/lựa chọn dataset có sẵn; không tạo training run.
Annotation được browser thực hiện trên fixture synthetic trong DB session mới,
không phải human gold. Session người dùng cũ được giữ nguyên; session audit riêng
đã dừng bằng stop.request đúng thư mục sở hữu.

## Kết quả cuối / ảnh / URL

Session cuối: `reports/task_rollout_20261104/demo_8ffee4b4a52cc384/`.
70/70 layout measurements PASS,10/10 nhóm thao tác PASS,0 JS page errors.
28 trường hợp hoàn toàn native;14 giữ native width + giả lập height;28 mobile
giả lập. Không sử dụng144/144 của đợt trước làm bằng chứng cho đợt này.

| Trang | innerWidth yêu cầu/đo được | #root / shell | Lề trái / phải | Thread field |
| --- | ---: | ---: | --- | ---: |
| Social | 1650 / 1650 | 1635 / 1635 | 0 / 0 | — |
| Moderator | 1650 / 1650 | 1635 / 1635 | 0 / 0 | 307,8 |
| Studio datasets | 1650 / 1650 | 1635 / 1635 | 0 / 0 | — |
| Social | 850 / 850 | 835 / 835 | 0 / 0 | — |
| Moderator | 850 / 850 | 835 / 835 | 0 / 0 | 394,5 |
| Studio datasets | 850 / 850 | 835 / 835 | 0 / 0 | — |
| Social | 390 / 390 | 375 / 375 | 0 / 0 | — |
| Moderator | 390 / 390 | 375 / 375 | 0 / 0 | 351 |
| Studio datasets | 390 / 390 | 375 / 375 | 0 / 0 | — |

App chiếm100% vùng client;15px còn lại là scrollbar, không phải khoảng trống
do max-width. Bộ lọc850px còn2 cột. Các field đều được kiểm tra bounds và ancestor
clipping. Đã xem trực tiếp ảnh Social1650, Moderator1650/850 và ảnh mobile.

Negative controls PASS: test từ chối shell1075px sát trái ở1650px, và từ chối
filter grid ép3×400px tại850px. Không nới các ngưỡng sau khi sửa source.

Hồi quy E2E qua chính launcher `-HeadlessCheck`:8/8 PASS,3 tài khoản, AI mặc định
thật, repeated evidence, bảo toàn nháp review, manual hide, appeal/restore và audit.
Evidence: `reports/task_rollout_20261104/demo_c36e3823760cb65e/`.
Startup13/13 PASS. Social + Moderator/Studio build PASS, output riêng
`dist-live-visual-fix-20261105`, không ghi đè legacy/dist đã khóa.

### Ảnh before/after cùng viewport

| Trang | Before | After |
| --- | --- | --- |
| Moderator1650 | [before](../../reports/task_rollout_20261104/demo_a53a25230d622b48/before_moderator_review_1650.png) | [after](../../reports/task_rollout_20261104/demo_8ffee4b4a52cc384/after_moderator_review_1650.png) |
| Moderator850 | [before](../../reports/task_rollout_20261104/demo_a53a25230d622b48/before_moderator_review_850.png) | [after](../../reports/task_rollout_20261104/demo_8ffee4b4a52cc384/after_moderator_review_850.png) |
| Moderator390 | [before](../../reports/task_rollout_20261104/demo_a53a25230d622b48/before_moderator_review_390.png) | [after](../../reports/task_rollout_20261104/demo_8ffee4b4a52cc384/after_moderator_review_390.png) |
| Social1650 | [before](../../reports/task_rollout_20261104/demo_a53a25230d622b48/before_social_feed_detail_1650.png) | [after](../../reports/task_rollout_20261104/demo_8ffee4b4a52cc384/after_social_feed_detail_1650.png) |
| Social850 | [before](../../reports/task_rollout_20261104/demo_a53a25230d622b48/before_social_feed_detail_850.png) | [after](../../reports/task_rollout_20261104/demo_8ffee4b4a52cc384/after_social_feed_detail_850.png) |
| Social390 | [before](../../reports/task_rollout_20261104/demo_a53a25230d622b48/before_social_feed_detail_390.png) | [after](../../reports/task_rollout_20261104/demo_8ffee4b4a52cc384/after_social_feed_detail_390.png) |

Mỗi thư mục còn có đủ ảnh datasets/annotation/training_config/evaluation/JSON
cho10 kích thước. Native launch probes1650/850 lưu riêng để chứng minh lỗi
viewport cố định; các ảnh trong bảng có cùng CSS viewport để đối chiếu sửa CSS.

### URL session đang giữ chạy

- [Social User](http://127.0.0.1:53351/live.html?thread=00810990-0e49-4c75-b4b2-cd820bc498f1)
- [Moderator Admin](http://127.0.0.1:53352/live.html)
- [ML Studio](http://127.0.0.1:53352/studio.html)

Các cửa sổ của session mới đã đăng nhập. Link mở ở browser/profile khác sẽ cần
đăng nhập lại; không xuất token/mật khẩu vào báo cáo. Các port chỉ hợp lệ khi
session này còn chạy. Default demo vẫn mở5 nick + Moderator + Studio; chế độ
VisualCheck chỉ mở2 nick + Moderator + Studio để kiểm thử đủ workflow.

### Lượt kiểm thử chưa thành công và giới hạn

Giữ nguyên bằng chứng các lượt sau, không tính là PASS:

- `demo_f1546dee97472af1`: harness trộn Playwright viewport mobile với resize
  native; viewport390px bị áp lại trong bước JSON. Đổi mobile sang CDP metrics
  trên context `viewport:null`, không thay tiêu chí layout.
- `demo_32f502108f6bf97a`: phát hiện chiều cao native bị Windows giới hạn1005px.
  Giữ yêu cầu1024/1080 bằng height-only emulation, vẫn assert đủ width/height.
- `demo_7fb3ec1e7c588046`: target trang đóng trước upload; chưa xác định nguyên
  nhân. Lượt cuối mở4 context cần thiết và có lifecycle log; đã đi hết70 trường
  hợp. Không coi lượt bị ngắt là lỗi CSS đã xác minh hoặc đổ lỗi người dùng.

Không có ảnh mới đính kèm truy cập được trong lượt yêu cầu này; đối chiếu các
triệu chứng1650px sát trái và850px cắt Thread bằng ảnh tự chụp/số đo kể trên.
Chưa test điện thoại vật lý/bàn phím ảo, DPI/zoom khác hoặc trình duyệt ngoài
Chrome. Source legacy đã khóa giữ nguyên. Các kết quả này là UI/integration
verification trên DB demo, không phải đánh giá độc lập/human gold.


### Kiểm tra chất lượng ảnh và khởi động lại

Ảnh cuối chụp qua CDP ở đúng innerWidth; xác minh PNG IHDR khớp từng width yêu
cầu. Trong capture, giữ nguyên gutter scrollbar đang có và assert DOM width
không đổi trước/trong/sau chụp, rồi gỡ style tạm. Không thêm overflow-x:hidden
hoặc thay CSS app để hợp thức hóa ảnh. Lượt demo_4f894a4ffc8a55d2 đã phát hiện
capture làm biến đổi gutter; bị loại, giữ bằng chứng, không tính PASS.
Lượt demo_f53e637975139804 đạt DOM tests nhưng ảnh Playwright bị crop15px; giữ
nguyên như lịch sử. Ảnh final liên kết phía trên thuộc session nghiệm thu mới.

Cửa sổ cũ được tạo với viewport1250px phải khởi tạo lại bằng launcher; refresh
không gỡ override của Playwright. Dùng các cửa sổ/URL session mới ở trên. Không
tự dừng session người dùng ban đầu hoặc reset dữ liệu cũ.

Readiness1311/1311 PASS. DB Studio session cuối có0 training run và0 evaluation
run; không thực hiện train/evaluate mô hình trong đợt sửa layout. Có inference
thật phục vụ các comment/JSON test. Manifest SHA và URL snapshot:
`reports/visual_fix_20261105_verified.json`.
