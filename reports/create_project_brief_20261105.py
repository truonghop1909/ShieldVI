"""Create the two-page Vietnamese project brief using standard OOXML only."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from xml.sax.saxutils import escape
import json,re

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/ai-update/final-report/ShieldVI_Tom_tat_de_tai_2_trang.docx'
W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'

def run(text,bold=False,size=None,color=None):
    prop=('<w:b/>' if bold else '')+(f'<w:sz w:val="{size}"/>' if size else '')+(f'<w:color w:val="{color}"/>' if color else '')
    return f'<w:r><w:rPr>{prop}</w:rPr><w:t xml:space="preserve">{escape(text)}</w:t></w:r>'
def rich(text):
    pieces=re.split(r'(\*\*.*?\*\*)',text)
    return ''.join(run(t[2:-2],True) if t.startswith('**') else run(t) for t in pieces if t)
def p(text='',style=None,align=None):
    prop=(f'<w:pStyle w:val="{style}"/>' if style else '')+(f'<w:jc w:val="{align}"/>' if align else '')
    return f'<w:p><w:pPr>{prop}</w:pPr>{rich(text)}</w:p>'
def heading(number,title):return p(f'{number}. {title}','Section')
def bullet(title,text):return p(f'{title}: {text}','Item')
def table(rows):
    body=[]
    for index,row in enumerate(rows):
        cells=[]
        for col,text in enumerate(row):
            fill='E8F0EC' if index==0 else 'F6F8F7' if col==0 else 'FFFFFF'
            cells.append(f'<w:tc><w:tcPr><w:tcW w:w="{1800 if col==0 else 7838}" w:type="dxa"/><w:shd w:fill="{fill}"/><w:vAlign w:val="center"/></w:tcPr>{p(text,"Table")}</w:tc>')
        body.append('<w:tr><w:trPr><w:cantSplit/>'+('<w:tblHeader/>' if index==0 else '')+'</w:trPr>'+''.join(cells)+'</w:tr>')
    return '<w:tbl><w:tblPr><w:tblW w:w="9638" w:type="dxa"/><w:tblLayout w:type="fixed"/><w:tblBorders>'+''.join(f'<w:{edge} w:val="single" w:sz="4" w:color="D5DFDA"/>' for edge in ['top','left','bottom','right','insideH','insideV'])+'</w:tblBorders><w:tblCellMar><w:top w:w="80" w:type="dxa"/><w:left w:w="110" w:type="dxa"/><w:bottom w:w="80" w:type="dxa"/><w:right w:w="110" w:type="dxa"/></w:tblCellMar></w:tblPr><w:tblGrid><w:gridCol w:w="1800"/><w:gridCol w:w="7838"/></w:tblGrid>'+''.join(body)+'</w:tbl>'

page1=[
 p('TÓM TẮT PHỤC VỤ BÁO CÁO · CẬP NHẬT 05/11/2026','Kicker'),
 p('**ShieldVI** Social AI','Title'),
 p('Đề tài, yêu cầu và định hướng phát triển','Subtitle'),
 heading('1','Đề tài và mục tiêu'),
 p('Xây dựng mạng xã hội tích hợp **AI hỗ trợ** kiểm duyệt nội dung tiếng Việt. Hệ thống cho phép đăng bài, bình luận, trả lời và nhận diện tín hiệu độc hại, người bị nhắm tới cùng dấu hiệu công kích lặp lại trong hội thoại.'),
 p('Mục tiêu là cung cấp bằng chứng để người kiểm duyệt xử lý nhất quán, giảm cảnh báo nhầm với lời can ngăn, xin lỗi, trích dẫn và tự bảo vệ. Một từ tục hoặc một điểm toxic cao không đủ để kết luận có hành vi bắt nạt.'),
 heading('2','Phạm vi và hướng triển khai hiện tại'),
 p('Phát triển từ MVP mạng xã hội tối giản sang bình luận realtime và Local ML Studio; chưa mở rộng thành chat riêng, livestream hay ứng dụng mobile native. Kiến trúc gồm React cho Social/Moderator/Studio, hai dịch vụ FastAPI và SQLite trong môi trường local.'),
 p('Luồng xử lý: lưu nội dung → hàng đợi/worker → ViSoBERT và các lớp tín hiệu → cập nhật giao diện qua SSE. Social API sở hữu dữ liệu và quyết định hiển thị; AI trả tư vấn. Quyết định ẩn/khôi phục cuối cùng thuộc **người kiểm duyệt**, có lý do và lịch sử.'),
 heading('3','Yêu cầu chức năng cốt lõi'),
 table([
  ('Nhóm','Yêu cầu'),
  ('Người dùng','Đăng nhập, đăng bài, bình luận/reply đúng parent và tên người nhận; sửa/xóa nội dung của mình; báo cáo và kháng nghị theo quyền.'),
  ('Phân tích AI','Kết hợp **ViSoBERT**, từ điển và ngữ cảnh; tách điểm gốc, target, bằng chứng công kích, repeated và mức rủi ro. Reply không mặc nhiên là công kích.'),
  ('Moderator','Hàng chờ, toàn văn hội thoại, cảnh báo và bằng chứng; duyệt/ẩn/khôi phục, giải quyết kháng nghị và lưu audit.'),
  ('ML Studio','Nhập/kiểm tra dataset; gán nhãn CLEAN/TOXIC/UNCERTAIN; hai vòng review; training thử nghiệm, đánh giá và quản lý phiên bản mô hình.'),
 ]),
 heading('4','Yêu cầu chất lượng và nghiệm thu'),
 p('Phân quyền phía server, bảo vệ nội dung chưa công khai; worker có timeout/retry và chống ghi kết quả cũ; giao diện thích ứng cửa sổ thật, không cắt field/reply. Có kiểm thử API, hồi quy và E2E với dữ liệu truy nguyên được. Giữ checkpoint gốc và ngưỡng **0,41**; ngưỡng nhãn không phải lệnh tự ẩn.'),
]
page2=[
 p('SHIELDVI SOCIAL AI · HIỆN TRẠNG VÀ LỘ TRÌNH','Kicker'),
 p('Đánh giá hiện trạng và hướng phát triển','Subtitle'),
 heading('5','Kết quả đã có bằng chứng'),
 p('Đã có demo local nhiều tài khoản đăng bài/bình luận realtime, Moderator xem cảnh báo, kiểm duyệt và xử lý kháng nghị. Studio có quy trình dataset–annotation–training–evaluation; đã kiểm chứng một lượt huấn luyện classifier head trên CPU, không phải fine-tune toàn bộ encoder.'),
 p('Corpus r06 có 500 hội thoại tổng hợp/5.115 bình luận; phần train dùng 4.398 bình luận nhị phân và giữ encoder đóng băng. Raw Macro-F1 đạt 0,8238 trên validation và 0,8288 trên challenge **synthetic**. Nhãn do AI tạo; các tập đã phục vụ nghiên cứu không phải đánh giá độc lập. r06 không thay mặc định V1.1. Repo còn lưu ViCTSD, ViHOS và ViLexNorm cho các nhiệm vụ khác nhau, không gộp nhãn tự động.'),
 p('Đợt sửa giao diện gần nhất đã kiểm tra 70 tổ hợp màn hình/viewport trên 10 kích thước; các luồng E2E kiểm duyệt–kháng nghị cũng đã chạy thực tế. Bằng chứng này xác nhận chức năng local, không chứng minh chất lượng AI ngoài thực tế hoặc khả năng chịu tải production.'),
 heading('6','Hạn chế và điều kiện chưa hoàn tất'),
 bullet('Dữ liệu','Chưa đủ 200 hội thoại thật có quyền sử dụng, provenance và hai vòng nhãn người duyệt cho nghiệm thu độc lập. Nhãn synthetic không phải **human gold**; đánh giá hình thức T028/T029 còn bị chặn.'),
 bullet('Ngôn ngữ','Mỉa mai, ẩn dụ, teencode và công kích gián tiếp còn khó bao phủ. Target/repeated phụ thuộc bằng chứng và cửa sổ ngữ cảnh; có thể bỏ sót hoặc cảnh báo nhầm. Không suy target chỉ từ điểm toxic.'),
 bullet('Triển khai','Mới xác minh ở local và Chrome; chưa đủ kiểm thử tải lớn, điện thoại vật lý/bàn phím ảo hoặc vận hành dài hạn. Các phần nghiệm thu mở rộng T030–T033 chưa hoàn tất; chưa có cơ sở tuyên bố sẵn sàng production.'),
 heading('7','Hướng phát triển theo thứ tự ưu tiên'),
 bullet('Ưu tiên 1 — dữ liệu thật','Thu thập từ nguồn được phép, giữ URL/license/thời gian và parent-child; ẩn danh, kiểm tra trùng/rò rỉ. Một người duyệt thực hiện Round 1 và Round 2, không giả lập reviewer thứ hai; khóa tập đánh giá độc lập.'),
 bullet('Ưu tiên 2 — chất lượng AI','Cải thiện phạm vi trích dẫn, công kích gián tiếp, target và repeated bằng thí nghiệm có kiểm soát. Giữ negative controls cho xin lỗi/can ngăn/tự vệ; so sánh phiên bản, phân tích FP/FN và báo cáo riêng classification, target, repeated.'),
 bullet('Ưu tiên 3 — vòng đời mô hình','Chỉ huấn luyện ứng viên khi đủ dữ liệu, điều kiện và tài nguyên được phê duyệt. Lưu hash/lineage, đánh giá trên tập khóa, chạy shadow và kiểm chứng rollback trước khi xem xét đổi mô hình mặc định.'),
 bullet('Ưu tiên 4 — vận hành','Kiểm thử tải và thiết bị thật; tăng quan sát độ trễ, lỗi và phục hồi. Khi nhu cầu được chứng minh, xem xét PostgreSQL/hàng đợi chuyên dụng; hoàn thiện bảo mật, sao lưu và quy trình kiểm duyệt trước triển khai.'),
 p('Căn cứ: 01_PHAM_VI_MVP.md; ARCHITECTURE.md; T034_T043_FINAL_REPORT.md; SYNTHETIC_R06_EXPERIMENT.md; FINAL_READINESS_REPORT.md; RESPONSIVE_VISUAL_FIX_REPORT.md. Số liệu thuộc các đợt kiểm chứng riêng, không cộng thành một benchmark.','Source'),
]

styles=f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="{W}"><w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="Times New Roman" w:cs="Times New Roman"/><w:sz w:val="24"/><w:lang w:val="vi-VN"/></w:rPr></w:rPrDefault><w:pPrDefault><w:pPr><w:spacing w:after="90" w:line="259" w:lineRule="auto"/><w:jc w:val="both"/><w:widowControl/></w:pPr></w:pPrDefault></w:docDefaults>
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>
<w:style w:type="paragraph" w:styleId="Kicker"><w:name w:val="Kicker"/><w:pPr><w:spacing w:after="90"/><w:jc w:val="left"/><w:keepNext/></w:pPr><w:rPr><w:sz w:val="18"/><w:color w:val="64736D"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:pPr><w:spacing w:after="40"/><w:jc w:val="left"/><w:keepNext/></w:pPr><w:rPr><w:sz w:val="36"/><w:color w:val="204D3F"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Subtitle"><w:name w:val="Subtitle"/><w:pPr><w:spacing w:after="110"/><w:jc w:val="left"/><w:keepNext/></w:pPr><w:rPr><w:sz w:val="28"/><w:color w:val="204D3F"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Section"><w:name w:val="Section"/><w:pPr><w:spacing w:before="100" w:after="60"/><w:jc w:val="left"/><w:keepNext/><w:outlineLvl w:val="1"/></w:pPr><w:rPr><w:sz w:val="26"/><w:color w:val="204D3F"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Table"><w:name w:val="Table"/><w:pPr><w:spacing w:after="0" w:line="249" w:lineRule="auto"/><w:jc w:val="left"/></w:pPr><w:rPr><w:sz w:val="23"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Item"><w:name w:val="Item"/><w:pPr><w:spacing w:after="85"/></w:pPr></w:style>
<w:style w:type="paragraph" w:styleId="Source"><w:name w:val="Source"/><w:pPr><w:spacing w:before="90" w:after="0" w:line="240" w:lineRule="auto"/><w:jc w:val="left"/></w:pPr><w:rPr><w:sz w:val="17"/><w:color w:val="64736D"/></w:rPr></w:style>
</w:styles>'''
body=''.join(page1)+'<w:p><w:r><w:br w:type="page"/></w:r></w:p>'+''.join(page2)
section='<w:sectPr><w:headerReference w:type="default" r:id="rIdHeader"/><w:footerReference w:type="default" r:id="rIdFooter"/><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1134" w:header="450" w:footer="450"/></w:sectPr>'
document=f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="{W}" xmlns:r="{R}"><w:body>{body}{section}</w:body></w:document>'
footer=f'<w:ftr xmlns:w="{W}"><w:p><w:pPr><w:jc w:val="right"/></w:pPr>{run("ShieldVI · ",size=18,color="64736D")}<w:fldSimple w:instr="PAGE"/>{run(" / ",size=18,color="64736D")}<w:fldSimple w:instr="NUMPAGES"/></w:p></w:ftr>'
header=f'<w:hdr xmlns:w="{W}"><w:p><w:pPr><w:spacing w:after="0"/><w:pBdr><w:bottom w:val="single" w:sz="4" w:color="D5DFDA"/></w:pBdr></w:pPr>{run("SHIELDVI SOCIAL AI  |  BẢN TÓM TẮT ĐỀ TÀI",size=17,color="64736D")}</w:p></w:hdr>'
content_types='''<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>'''+''.join(f'<Override PartName="/{name}" ContentType="{ctype}"/>' for name,ctype in {
 'word/document.xml':'application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml',
 'word/styles.xml':'application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml',
 'word/settings.xml':'application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml',
 'word/header1.xml':'application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml',
 'word/footer1.xml':'application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml',
 'docProps/core.xml':'application/vnd.openxmlformats-package.core-properties+xml',
 'docProps/app.xml':'application/vnd.openxmlformats-officedocument.extended-properties+xml',
}.items())+'</Types>'
relationships=f'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'+''.join(f'<Relationship Id="{i}" Type="{R}/{t}" Target="{target}"/>' for i,t,target in [('rIdStyles','styles','styles.xml'),('rIdSettings','settings','settings.xml'),('rIdHeader','header','header1.xml'),('rIdFooter','footer','footer1.xml')])+'</Relationships>'
root_rels=f'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rIdDoc" Type="{R}/officeDocument" Target="word/document.xml"/><Relationship Id="rIdCore" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/><Relationship Id="rIdApp" Type="{R}/extended-properties" Target="docProps/app.xml"/></Relationships>'
parts={'[Content_Types].xml':content_types,'_rels/.rels':root_rels,'word/document.xml':document,'word/styles.xml':styles,'word/_rels/document.xml.rels':relationships,'word/header1.xml':header,'word/footer1.xml':footer,
 'word/settings.xml':f'<w:settings xmlns:w="{W}"><w:zoom w:percent="100"/><w:defaultTabStop w:val="720"/><w:compat><w:compatSetting w:name="compatibilityMode" w:uri="http://schemas.microsoft.com/office/word" w:val="15"/></w:compat></w:settings>',
 'docProps/core.xml':'<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>ShieldVI Social AI — Tóm tắt đề tài</dc:title><dc:creator>ShieldVI</dc:creator><dc:description>Bản tóm tắt hai trang; nhãn synthetic và nghiệm thu thực tế được phân biệt.</dc:description></cp:coreProperties>',
 'docProps/app.xml':'<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"><Application>ShieldVI OOXML</Application><Pages>2</Pages></Properties>'}
OUT.parent.mkdir(parents=True,exist_ok=True)
with ZipFile(OUT,'w',ZIP_DEFLATED) as z:
    for name,xml in parts.items():z.writestr(name,'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'+xml if not xml.startswith('<?xml') else xml)
from xml.etree import ElementTree as ET
with ZipFile(OUT) as z:
    assert z.testzip() is None
    for name in z.namelist():ET.fromstring(z.read(name))
root=ET.fromstring(document);text=' '.join(n.text or '' for n in root.iter(f'{{{W}}}t'))
bold=[n.text for r in root.iter(f'{{{W}}}r') if r.find(f'{{{W}}}rPr/{{{W}}}b') is not None for n in r.findall(f'{{{W}}}t')]
print(json.dumps({'file':str(OUT),'characters':len(text),'words':len(text.split()),'bold_phrases':bold,'manual_page_breaks':document.count('w:type="page"')},ensure_ascii=False))
