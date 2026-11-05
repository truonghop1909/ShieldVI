"""Update Colab paths without executing cells, installing or opening a proxy."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]/'ShieldVI_V3_Hybrid_Review'
paths=sorted((ROOT/'notebooks').glob('*.ipynb'))
assert len(paths)==2, 'Expected both Colab notebooks'
for path in paths:
    notebook=json.loads(path.read_text(encoding='utf-8'))
    touched=0
    for cell in notebook['cells']:
        original=''.join(cell.get('source',[]));source=original
        if cell['cell_type']=='code':
            source=source.replace('import shutil\n','import tempfile\n').replace('time, shutil, zipfile','time, tempfile, zipfile')
            source=source.replace("ROOT = Path('/content/shieldvi_fullstack')","ROOT = Path(tempfile.mkdtemp(prefix='shieldvi_fullstack_', dir='/content'))")
            source=source.replace('ROOT = Path("/content/shieldvi_v3")',"ROOT = Path(tempfile.mkdtemp(prefix='shieldvi_v3_', dir='/content'))")
            source=source.replace('ShieldVI_V2_Review_Fullstack.zip','ShieldVI_V3_Hybrid_Review.zip')
            source=source.replace('if ROOT.exists():\n    shutil.rmtree(ROOT)\nROOT.mkdir(parents=True, exist_ok=True)\n',
                '# Fresh extraction directory; never remove an earlier session or DB.\n')
            for name in ('archive','z'):
                source=source.replace(f'    {name}.extractall(ROOT)',
                    f"    for member in {name}.infolist():\n        target = (ROOT/member.filename).resolve()\n        if target != ROOT.resolve() and ROOT.resolve() not in target.parents:\n            raise ValueError('ZIP path escapes extraction directory')\n    {name}.extractall(ROOT)")
            if 'extractall(ROOT)' in source:
                position=source.index('assert (ROOT/')
                source=source[:position]+("if not (ROOT/'services/moderation-ai/app/main.py').is_file():\n"
                    "    candidates = [p for p in ROOT.iterdir() if p.is_dir() and (p/'services/moderation-ai/app/main.py').is_file()]\n"
                    "    if len(candidates) == 1: ROOT = candidates[0]\n"
                    "AI_ROOT = ROOT/'services/moderation-ai'\nLEGACY_WEB = ROOT/'apps/moderation-web/legacy-v3'\n")+source[position:]
            source=source.replace('frontend/package.json','apps/moderation-web/legacy-v3/package.json')
            for name in ('main.py','lexical.py','review_store.py','static/index.html'):
                source=source.replace('app/'+name,'services/moderation-ai/app/'+name)
            # The insertion above already contains the canonical main path.
            source=source.replace('services/moderation-ai/services/moderation-ai/app/','services/moderation-ai/app/')
            source=source.replace("ROOT/'frontend'",'LEGACY_WEB').replace("ROOT / 'frontend'",'LEGACY_WEB')
            source=source.replace('cwd=ROOT,env=env','cwd=AI_ROOT,env=env')
            source=source.replace("'--port','8000']","'--port','8000','--no-proxy-headers']")
            if "env['MODEL_PATH']" in source:
                source=source.replace("env['MODEL_PATH'] = MODEL_PATH\n", "env['MODEL_PATH'] = MODEL_PATH\n"
                    "env.setdefault('DB_PATH', str(ROOT/'moderation_summaries.sqlite3'))\n"
                    "env.setdefault('REVIEW_DB_PATH', str(ROOT/'shieldvi_reviews.sqlite3'))\n")
                # Notebook 09 nests startup under a conditional.
                if "    env['MODEL_PATH']=MODEL_PATH\n" in source:
                    source=source.replace("    env['MODEL_PATH']=MODEL_PATH\n", "    env['MODEL_PATH']=MODEL_PATH\n"
                        "    env.setdefault('DB_PATH', str(ROOT/'moderation_summaries.sqlite3'))\n")
        elif cell is notebook['cells'][0]:
            source += ('\nT015 layout: AI source in `services/moderation-ai/app`, research React in '
                '`apps/moderation-web/legacy-v3`. Earlier extraction folders are retained; '
                'set REVIEW_DB_PATH explicitly to reuse review history. Social moderation decisions '
                'use the separate Social API, not the research annotation DB.\n')
        if source!=original:
            cell['source']=source.splitlines(keepends=True);touched+=1
    path.write_text(json.dumps(notebook,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
    print(path.name,'updated cells:',touched)
