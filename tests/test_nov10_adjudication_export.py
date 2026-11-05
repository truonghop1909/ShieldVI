import csv,json,re,subprocess
from pathlib import Path
from scripts.prepare_nov10_adjudication import export

def test_all24_cases_keep20_full_context_comments_and_empty_owner_decisions(tmp_path):
    output=tmp_path/'review';export(output)
    rows=list(csv.DictReader((output/'cases_with_full_context.csv').open(encoding='utf-8-sig',newline='')))
    assert len(rows)==24
    for row in rows:
        assert row['full_conversation_context'].count(' · reference=')==20
        assert row['text'] in row['full_conversation_context']
        assert not any(row[k] for k in ('adjudicated_label','adjudicated_target','decision_reason','reviewer'))
    meta=json.loads((output/'manifest.json').read_text());assert meta['human_decisions']==0 and not meta['human_gold']

def test_generated_html_script_parses_and_empty_form_exports_no_human_labels(tmp_path):
    output=tmp_path/'review';export(output)
    page=(output/'NOV10_ADJUDICATION.html').read_text(encoding='utf-8')
    script=re.search(r'<script>([\s\S]*)</script>',page)[1];path=tmp_path/'review.js';path.write_text(script,encoding='utf-8')
    assert page.count('class="decision"')==24 and page.count('<details open>')==24
    parsed=subprocess.run(['node','--check',str(path)],capture_output=True,text=True);assert parsed.returncode==0,parsed.stderr
    probe=tmp_path/'probe.js'
    probe.write_text("const fs=require('fs'),vm=require('vm');const els={reviewer:{value:''},export:{},notice:{textContent:''}};const context={document:{getElementById:id=>els[id],querySelectorAll:()=>[]}};vm.createContext(context);vm.runInContext(fs.readFileSync(process.argv[2],'utf8'),context);els.export.onclick();if(!els.notice.textContent)process.exit(1);",encoding='utf-8')
    result=subprocess.run(['node',str(probe),str(path)],capture_output=True,text=True);assert result.returncode==0,result.stderr
