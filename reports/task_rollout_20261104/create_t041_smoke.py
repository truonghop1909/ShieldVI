"""A small hand-authored synthetic workflow fixture, not a language benchmark."""
import json,hashlib
from pathlib import Path
pairs=[
 ('đổi sách','Nhóm đổi sách đã chọn hiên thư viện làm chỗ nhận sách vào sáng thứ bảy.','Mày ngu đến mức đọc nhãn thùng sách cũng không hiểu à?'),
 ('bể cá','Mình đang ghi lại lịch thay nước cho chiếc bể nhỏ mới đặt ở phòng khách.','Cái đầu mày vô dụng, chăm mấy con cá cũng chỉ phá thêm.'),
 ('làm bánh','Mẻ bánh yến mạch hôm nay dùng ít mật ong hơn để bà ngoại ăn thử.','Mày đúng là đồ ngu, cân nguyên liệu ba lần vẫn sai.'),
 ('đạp xe','Đoạn đường qua vườn ổi có bóng mát nên đoàn mình sẽ nghỉ chân ở đó.','Thằng ngu như mày chỉ giỏi làm cả đoàn chờ dưới nắng.'),
 ('lập trình','Nhánh thử nghiệm đã có phần ghi log để nhóm tìm lỗi khi đồng bộ lịch.','Mày là đồ ngu, viết có cái hàm nhỏ cũng làm hỏng dự án.'),
 ('cầu lông','Sân chiều nay đổi sang ô số bốn vì mái che bên khu cũ đang sửa chữa.','Mày chơi dở như cứt, đừng mò vào đội tao nữa.'),
 ('bảo tàng','Buổi tham quan cuối tháng có hướng dẫn viên giới thiệu hiện vật bằng thủ ngữ.','Đồ vô dụng như mày đứng đâu cũng cản đường người khác.'),
 ('thiết bị bay','Mình muốn thử quay bãi cỏ trống lúc sáng sớm khi chưa có người tập thể dục.','Mày ngu thật, không phân biệt nổi nút hạ cánh và nút quay về.'),
 ('ủ phân','Thùng ủ mới được thêm lá khô và đặt tấm lưới để thoát hơi tốt hơn.','Mày đúng là một đứa đần độn, việc gì qua tay mày cũng hỏng.'),
 ('tìm việc','Bản mô tả công việc mới đã ghi rõ lịch linh hoạt và khoản hỗ trợ đi lại.','Mày bất tài mà còn đòi hỏi, công ty nào nhận nổi đồ ngu như mày.'),
 ('sách nói','Tập truyện vừa thu có chèn khoảng nghỉ giữa các đoạn để người nghe dễ theo dõi.','Giọng mày nghe ngu vãi, đừng tra tấn tai cả nhóm nữa.'),
 ('học ngoại ngữ','Buổi trao đổi tuần này mình chọn chủ đề mua vé tàu để mọi người dễ nhập vai.','Your brain is useless, mày học kiểu gì cũng chỉ là đồ ngu.'),
 ('xe buýt','Tuyến đi qua trung tâm có chuyến sớm hơn nên mình ghi thêm giờ khởi hành mới.','Mày ngu như bò, nhìn bản đồ có hai trạm cũng đi nhầm.'),
 ('dọn khu nhà','Nhóm dọn kho chia riêng thùng giấy sạch để gửi cho điểm thu gom cuối phố.','Đồ mất dạy như mày chỉ biết đẩy việc dọn rác sang người khác.'),
 ('gây quỹ','Sổ thu chi gian hàng gây quỹ đã bổ sung hóa đơn mua băng dính và túi giấy.','Mày là đồ ngu vô dụng, đếm tiền lẻ cũng khiến người khác phải sửa.'),
 ('chụp ảnh','Bộ ảnh chợ sớm sẽ được in cỡ nhỏ để thử cân bằng màu trên giấy nhám.','Mày chụp như cứt mà vẫn tưởng mình là nghệ sĩ tài giỏi.'),
 ('bàn phím','Mình đã thay miếng lót ở phím cách và ghi lại tiếng gõ trước lúc ráp vỏ.','Cái thứ ngu ngốc như mày chỉ biết khoe đồ mà chẳng hiểu gì.'),
 ('du lịch','Lịch đi làng gốm dành thêm một giờ để mọi người tự thử nặn chiếc cốc nhỏ.','Mày vô dụng hết chỗ nói, đặt lịch đâu cũng làm phiền cả nhóm.')]
rows=[]
for i,(topic,clean,toxic) in enumerate(pairs,1):
 for j,(text,label) in enumerate(((clean,'CLEAN'),(toxic,'TOXIC')),1):
  rows.append({'thread_id':f'T041_SMOKE_{i:03d}','comment_id':f'c{j}','parent_id':'c1' if j==2 else None,'user_id':f'P{j}','timestamp':f'2026-11-04T00:{i:02d}:{j:02d}Z','text':text,'label':label,'category':'directed_insult' if j==2 else 'normal','source':'AI-authored synthetic T041 CPU workflow smoke; not human gold'})
path=Path(__file__).resolve().parent/'T041_synthetic_smoke.json';content=json.dumps(rows,ensure_ascii=False,indent=2)+'\n'
if path.exists() and path.read_text(encoding='utf-8')!=content:raise ValueError('Smoke fixture changed; use a new version')
path.write_text(content,encoding='utf-8')
print(json.dumps({'threads':len(pairs),'comments':len(rows),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'label_source':'synthetic_reference'}))
