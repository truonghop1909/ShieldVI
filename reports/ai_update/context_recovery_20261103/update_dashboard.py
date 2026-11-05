from pathlib import Path
p=Path('services/moderation-ai/app/context_signals.py');s=p.read_text(encoding='utf-8')
s=s.replace("INTERVENTION=re.compile(r'", "INTERVENTION=re.compile(r'\\b(?:xuc pham|nhuc ma|cong kich).{0,30}(?:thi dung|thi ngung|khong phai (?:phe binh|gop y))|\\bdo la cong kich (?:nguoi|ca nhan)|",1)
s=s.replace("DEFENSE=re.compile(r'", "DEFENSE=re.compile(r'\\b(?:cau|ve|loi) (?:sau|dau|do|ay).{0,30}(?:xuc pham|ha nhuc).{0,25}(?:khong chap nhan|minh|toi)|\\b(?:ban|cau|ong|ba).{0,18}(?:dang )?xuc pham (?:minh|toi|tui)|",1)
s=s.replace("or match.group()=='cam di':attack=True", "or match.group()=='cam di' or (match.group()=='do ngu' and not prefix.strip()):attack=True")
p.write_text(s,encoding='utf-8')
p=Path('apps/moderation-web/legacy-v3/src/App.jsx');s=p.read_text(encoding='utf-8')
s=s.replace("INTERVENTION:'Can ngăn',DIRECT_ATTACK", "INTERVENTION:'Can ngăn',ACKNOWLEDGEMENT:'Nhận lỗi',DIRECT_ATTACK")
# Keep the original raw badge and add a visibly separate contextual assessment/policy signal.
needle="{c.analysis_signals && <div className=\"lexical-small\">"
replacement="""{c.moderation_assessment && <div className="context-assessment" data-testid={`assessment-${c.comment_id}`}><span className={`table-badge ${c.moderation_assessment.label==='TOXIC'?'toxic':c.moderation_assessment.label==='CLEAN'?'clear':''}`}>Kết quả hỗ trợ: {c.moderation_assessment.label}</span><div className="lexical-small">Policy risk: {c.policy_risk?.band || 'UNKNOWN'} · chưa thực thi</div></div>}{c.analysis_signals && <div className="lexical-small">"""
assert needle in s;s=s.replace(needle,replacement,1)
needle="<span className=\"target-text\">{c.analysis_signals ? (c.analysis_signals.target_candidate || 'Chưa rõ') : (c.target_user_id || 'Chưa rõ')}</span>"
replacement="""<span className="target-text">Công kích: {c.analysis_signals ? (c.directed_at_user_id || 'Chưa xác định') : (c.target_user_id || 'Chưa xác định')}</span><div className="lexical-small">Trả lời: {c.reply_to_user_id || 'Không có'}</div>"""
assert needle in s;s=s.replace(needle,replacement)
s=s.replace("const targetCount = result?new Set(result.comments.map(x=>x.target_user_id).filter(Boolean)).size:0", "const targetCount = result?new Set(result.comments.map(x=>x.analysis_signals?x.directed_at_user_id:x.target_user_id).filter(Boolean)).size:0\n  const assessedToxicCount = result?.comments?.filter(x=>x.moderation_assessment?.label==='TOXIC').length||0")
s=s.replace('label="Bình luận nghi toxic" value={result?toxicCount:', 'label="ViSoBERT nghi toxic (raw)" value={result?toxicCount:')
s=s.replace("sub={result?'Theo ngưỡng kiểm duyệt':'Chưa có kết quả'}", "sub={result?`Hỗ trợ ngữ cảnh: ${assessedToxicCount} TOXIC; cần kiểm duyệt`:'Chưa có kết quả'}")
s=s.replace('sub="Target suy luận, có thể sai"','sub="Đối tượng công kích có bằng chứng; tách khỏi người nhận reply"')
p.write_text(s,encoding='utf-8')
p=Path('apps/moderation-web/legacy-v3/src/utils.js');s=p.read_text(encoding='utf-8')
s=s.replace("'target_user_id','target_method','target_confidence']", "'target_user_id','target_method','target_confidence','reply_to_user_id','directed_at_user_id','context_tags','context_assessment_label','policy_risk_band']")
needle="escape(k==='lexical_matched_forms' ? (r.lexical_signals||[]).map(x=>x.matched_form).join(' | ') : r[k])"
replace="escape(k==='lexical_matched_forms' ? (r.lexical_signals||[]).map(x=>x.matched_form).join(' | ') : k==='context_tags' ? (r.analysis_signals?.context_tags||[]).join(' | ') : k==='context_assessment_label' ? r.moderation_assessment?.label : k==='policy_risk_band' ? r.policy_risk?.band : r[k])"
assert needle in s;s=s.replace(needle,replace)
p.write_text(s,encoding='utf-8')
