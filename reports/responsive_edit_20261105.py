"""Scoped, assertive edits to additive Live/Studio UI. Never edits sealed sources."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def edit(relative, changes):
    p=ROOT/relative
    text=p.read_text(encoding='utf-8')
    for old,new in changes:
        assert old in text, (relative,old[:100])
        text=text.replace(old,new)
    p.write_text(text,encoding='utf-8')

edit('apps/moderation-web/src/live.jsx',[
 ("import './live.css'","import './live.css'\nimport '../../shared/responsive.css'\nimport './workspace-responsive.css'"),
 ('<section aria-label="Hàng chờ trực tiếp">','<section className="queue-list" aria-label="Hàng chờ trực tiếp">{!data&&!error&&<p role="status">Đang tải hàng chờ…</p>}{data&&rows?.length===0&&<p>Không có nội dung phù hợp bộ lọc.</p>}'),
 ('className="queue-item" data-content-id={item.content.id}', 'className="queue-item" aria-pressed={selected?.content.id===item.content.id} data-content-id={item.content.id}'),
 ('<small>{item.entity_type} · {item.content.risk_tier}', '<small>Người viết: {item.content.author_username||item.content.author_id}</small><small>Bài: {item.content.post_id||item.content.id}</small><small>{item.entity_type} · {item.content.risk_tier}'),
 ('<div>{selected?<><ReviewDetail', '<div id="live-review-detail" className="live-detail" onClickCapture={event=>{const button=event.target.closest("button.danger");if(button&&!button.disabled&&!window.confirm("Ẩn nội dung này? Tác giả có thể gửi kháng nghị.")){event.preventDefault();event.stopPropagation()}}}>{selected?<><ReviewDetail'),
 ("function choose(item){setSelected(item);", "function choose(item){setSelected(item);if(matchMedia('(max-width:1023px)').matches)requestAnimationFrame(()=>document.getElementById('live-review-detail')?.scrollIntoView({block:'start',behavior:'instant'}));"),
 ('<span data-testid="moderator-connection">{status}</span>', '<span role="status" data-testid="moderator-connection" title={status}>{status}</span>'),
 ('return <div className="live-admin"><header>', 'return <div className="live-admin"><a className="ui-skip" href="#live-review-detail">Đến chi tiết kiểm duyệt</a><header>'),
])
edit('apps/moderation-web/src/QuickAiTest.jsx',[
 ('className="quick-ai-table"','className="quick-ai-table responsive-table"'),
 ('<td><strong>{row.comment_id}', '<td data-label="Bình luận"><strong>{row.comment_id}'),
 ('<td>{(a.toxicity_score', '<td data-label="Điểm gốc">{(a.toxicity_score'),
 ('<td>{c.assessment_label}', '<td data-label="Assessment">{c.assessment_label}'),
 ('<td>{c.reply_to_user_id', '<td data-label="Trả lời">{c.reply_to_user_id'),
 ('<td>{c.directed_at_user_id', '<td data-label="Target công kích">{c.directed_at_user_id'),
 ('<td><details>', '<td data-label="Chi tiết"><details>'),
])
edit('apps/moderation-web/src/studio.jsx',[
 ("import './studio.css'", "import './studio.css'\nimport '../../shared/responsive.css'\nimport './workspace-responsive.css'"),
 ('<label>Nội dung nhập', '<label className="import-wide">Nội dung nhập'),
 ('<label>Mapping cột', '<label className="import-wide">Mapping cột'),
 ('<label>Provenance / license', '<label className="import-wide">Provenance / license'),
 ('<button onClick={()=>setTab(\'datasets\')}>', '<button aria-pressed={tab===\'datasets\'} onClick={()=>setTab(\'datasets\')}>'),
 ('<button onClick={()=>setTab(\'labeling\')}>', '<button aria-pressed={tab===\'labeling\'} onClick={()=>setTab(\'labeling\')}>'),
 ('<button onClick={()=>setTab(\'training\')}>', '<button aria-pressed={tab===\'training\'} onClick={()=>setTab(\'training\')}>'),
 ('<button onClick={()=>setTab(\'evaluation\')}>', '<button aria-pressed={tab===\'evaluation\'} onClick={()=>setTab(\'evaluation\')}>'),
])
edit('apps/moderation-web/src/AnnotationStudio.jsx',[
 ("const draftRef=useRef(null)", "const [controlsOpen,setControlsOpen]=useState(()=>!matchMedia('(max-width:1023px)').matches)\n const draftRef=useRef(null)"),
 ('activate(latest,cid,r);setHistory([])', "activate(latest,cid,r);setHistory([]);setControlsOpen(true);if(matchMedia('(max-width:1023px)').matches)requestAnimationFrame(()=>document.getElementById('annotation-controls')?.scrollIntoView({block:'start',behavior:'instant'}))"),
 ('{draft&&row&&<section><h3>', '{draft&&row&&<details id="annotation-controls" className="annotation-controls" open={controlsOpen} onToggle={e=>setControlsOpen(e.currentTarget.open)}><summary>Gán nhãn · {current} · Round {round}</summary><section><h3>'),
 ("JSON.stringify(history,null,2):''}</pre></section>}", "JSON.stringify(history,null,2):''}</pre></section></details>}"),
])
edit('apps/moderation-web/src/EvaluationStudio.jsx',[
 ('<table>', '<div className="responsive-table" tabIndex={0} role="region" aria-label="Bảng đánh giá mô hình"><table>'),
 ('</table>', '</table></div>'),
 ('<td>{m.id}', '<td data-label="Model">{m.id}'),
 ('<td>{m.state}', '<td data-label="Scope">{m.state}'),
 ('<td className="studio-hash">', '<td data-label="SHA256" className="studio-hash">'),
 ('<td>{m.threshold}', '<td data-label="Threshold">{m.threshold}'),
 ('<td>{id}', '<td data-label="Model">{id}'),
 ('<td>{m.raw.macro_f1', '<td data-label="Raw Macro-F1">{m.raw.macro_f1'),
 ('<td>{m.final.macro_f1', '<td data-label="Final Macro-F1">{m.final.macro_f1'),
 ('<td>{m.final.toxic_precision', '<td data-label="Toxic P/R">{m.final.toxic_precision'),
 ('<td>{m.final.tp}', '<td data-label="TP / FP / FN / TN">{m.final.tp}'),
])
edit('apps/moderation-web/src/TrainingStudio.jsx',[
 ("import {saveBlob} from './studio-api.js'", "import {saveBlob} from './studio-api.js'\nimport TrainingProgress from './TrainingProgress.jsx'"),
 ('<p data-testid="training-status">{run.status}</p>', '<p role="status" data-testid="training-status">{run.status}</p><TrainingProgress run={run}/>'),
 ('{runs.map(r=><button', '<div className="studio-run-list">{runs.map(r=><button'),
 ("setLogs('')}}>{r.id} · {r.status}</button>)}{run&&", "setLogs('')}}>{r.id} · {r.status}</button>)}</div>{run&&"),
])
print('Updated six additive frontend sources; frozen sources untouched.')
