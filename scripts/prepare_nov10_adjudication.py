"""Export 24 pending cases with full original conversation, no human decisions."""
import argparse,csv,html,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]

def export(output):
    if output.exists():raise FileExistsError('Use a new annotation/export version')
    output.mkdir(parents=True)
    source=R/'reports/ai_update/nov10_audit_20261104/adjudication_candidates.csv'
    cases=list(csv.DictReader(source.open(encoding='utf-8-sig',newline='')));assert len(cases)==24
    d=R/'datasets/fixtures/nov10_regression_v1'
    threads={t['thread_id']:t for t in [json.loads(p.read_text()) for p in (d/'inputs').glob('*.json')]}
    refs={(r['thread_id'],r['comment_id']):r for r in csv.DictReader((d/'expected_reference_labels.csv').open(encoding='utf-8-sig'))}
    rows=[];sections=[]
    for index,case in enumerate(cases):
        thread=threads[case['thread_id']];by_id={c['comment_id']:c for c in thread['comments']};comment=by_id[case['comment_id']]
        context=[];items=[]
        for c in thread['comments']:
            a=refs[(thread['thread_id'],c['comment_id'])];parent=by_id.get(c.get('parent_id'))
            line=f"{c['comment_id']} · {c['user_id']} · reply={parent['user_id'] if parent else '∅'} · {c['timestamp']} · reference={a['expected_label']} · target={a['directed_at_user_id'] or '∅'}\n{c['text']}"
            context.append(line)
            items.append('<li class="'+('focus' if c['comment_id']==comment['comment_id'] else '')+'"><pre>'+html.escape(line)+'</pre></li>')
        row={**case,'actor_user_id':comment['user_id'],'parent_id':comment.get('parent_id') or '',
             'reply_to_user_id':by_id[comment['parent_id']]['user_id'] if comment.get('parent_id') else '',
             'full_conversation_context':'\n\n'.join(context),'adjudicated_label':'','adjudicated_target':'','decision_reason':'','reviewer':''}
        rows.append(row)
        sections.append(f'<section data-index="{index}"><h2>{index+1}. {html.escape(case["thread_id"])} · {case["comment_id"]}</h2>'
            f'<p>Actor: <b>{html.escape(comment["user_id"])}</b> · Target tham khảo: <b>{html.escape(case["original_target"] or "∅")}</b> · Nhãn AI: <b>{case["original_label"]}</b></p>'
            f'<blockquote>{html.escape(comment["text"])}</blockquote><p>{html.escape(case["adjudication_question"])}</p>'
            '<label>Quyết định của bạn <select class="decision"><option value="">— Chưa quyết định —</option><option>CLEAN</option><option>TOXIC</option><option>UNCERTAIN</option></select></label> '
            '<label>Target quyết định <input class="target" value=""></label><br><label>Lý do <textarea class="reason" rows="2"></textarea></label>'
            '<details open><summary>Toàn bộ hội thoại (20 comment, không cắt)</summary><ol>'+''.join(items)+'</ol></details></section>')
    with (output/'cases_with_full_context.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    data=json.dumps([{k:r[k] for k in ('thread_id','comment_id','original_label','original_target')} for r in rows],ensure_ascii=False).replace('<','\\u003c')
    page='''<!doctype html><html lang="vi"><meta charset="utf-8"><title>NOV10 — 24 trường hợp chờ quyết định</title>
<style>body{max-width:1100px;margin:24px auto;font:16px system-ui;padding:16px;background:#f4f6f8}section{background:white;padding:20px;margin:20px 0;border-radius:12px}pre{white-space:pre-wrap;font:14px system-ui}li{padding:8px;border-bottom:1px solid #ddd}.focus{background:#fff0c0}textarea{width:96%;margin:8px}select,input{padding:8px}header{background:#dcefff;padding:18px}button{padding:12px}</style>
<header><h1>NOV10 — 24 trường hợp adjudication</h1><p>Mọi nhãn hiện có đều là synthetic_reference. Chưa có quyết định của bạn; không phải human gold. File này không tự lưu hoặc gửi dữ liệu đi đâu. CSV quyết định xuất thành version riêng, không sửa reference gốc. NOV10 đã dùng nghiên cứu nên không trở thành evaluation độc lập sau review.</p>
<label>Mã người duyệt <input id="reviewer" value=""></label> <button id="export">Xuất các quyết định đã nhập</button><p id="notice"></p></header>'''+''.join(sections)+'''
<script>const cases=__CASES__;document.getElementById('export').onclick=()=>{const reviewer=document.getElementById('reviewer').value.trim();const selected=[...document.querySelectorAll('section')].filter(s=>s.querySelector('.decision').value);const notice=document.getElementById('notice');if(!reviewer||!selected.length){notice.textContent='Nhập mã người duyệt và ít nhất một quyết định của bạn.';return;}const columns=['annotation_version','thread_id','comment_id','original_label','original_target','adjudicated_label','adjudicated_target','decision_reason','reviewer','reviewed_at','human_gold'];const rows=selected.map(s=>{const c=cases[Number(s.dataset.index)];return ['nov10_owner_decisions_v1',c.thread_id,c.comment_id,c.original_label,c.original_target,s.querySelector('.decision').value,s.querySelector('.target').value.trim(),s.querySelector('.reason').value.trim(),reviewer,new Date().toISOString(),'false'];});const esc=v=>'"'+String(v).replaceAll('"','""')+'"';const content='\ufeff'+[columns,...rows].map(r=>r.map(esc).join(',')).join('\\r\\n');const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([content],{type:'text/csv;charset=utf-8'}));a.download='NOV10_owner_decisions_v1.csv';a.click();URL.revokeObjectURL(a.href);notice.textContent='Đã xuất version quyết định riêng. Reference gốc giữ nguyên; file xuất chưa phải independent human gold.';};</script></html>'''.replace('__CASES__',data)
    page=page.replace('const rows=selected.map',"const version='nov10_owner_'+new Date().toISOString().replace(/[-:.TZ]/g,'');const rows=selected.map")
    page=page.replace("['nov10_owner_decisions_v1',c.thread_id","[version,c.thread_id")
    page=page.replace("a.download='NOV10_owner_decisions_v1.csv'","a.download=version+'.csv'")
    (output/'NOV10_ADJUDICATION.html').write_text(page,encoding='utf-8')
    (output/'manifest.json').write_text(json.dumps({'cases':24,'comments_per_full_context':20,'human_decisions':0,'human_gold':False,
        'source_reference_modified':False,'annotation_version':'pending_owner_decisions_v1','html_has_no_network_calls':True},indent=2),encoding='utf-8')
    return {'cases':24,'decision_cells_filled':0,'full_context_rows':len(rows),'output':str(output)}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();print(json.dumps(export(args.output)))
