"""Cwd/import/storage/static/Colab regression for the T015 layout."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from app import database,predictor,review_store
from app.lexical import DATA_DIR
from app.paths import APP_ROOT,REPOSITORY_ROOT
from scripts import import_lexicon

ROOT=Path(__file__).resolve().parents[1]
AI=ROOT/'services/moderation-ai'


def test_model_and_storage_defaults_independent_of_cwd(monkeypatch,tmp_path):
    for variable in ('MODEL_PATH','DB_PATH','REVIEW_DB_PATH'):monkeypatch.delenv(variable,raising=False)
    monkeypatch.chdir(tmp_path)
    assert REPOSITORY_ROOT==ROOT
    assert APP_ROOT==AI/'app'
    assert predictor.REFINED_MODEL_PATH==ROOT/'models/visobert_head_refined'
    assert Path(predictor.default_model_path())==predictor.REFINED_MODEL_PATH
    assert Path(database.db_path())==ROOT/'moderation_summaries.sqlite3'
    assert Path(review_store.review_db_path())==ROOT/'shieldvi_reviews.sqlite3'
    monkeypatch.setenv('REVIEW_DB_PATH','private/example.sqlite3')
    assert Path(review_store.review_db_path())==ROOT/'private/example.sqlite3'
    monkeypatch.setenv('REVIEW_DB_PATH',str(tmp_path/'explicit.sqlite3'))
    assert Path(review_store.review_db_path())==tmp_path/'explicit.sqlite3'
    assert DATA_DIR==AI/'app/data/lexicon' and import_lexicon.ROOT==DATA_DIR
    monkeypatch.setenv('MODEL_PATH','models/external-fixture')
    assert Path(predictor.default_model_path())==ROOT/'models/external-fixture'


def test_root_compatibility_and_canonical_service_resolve_same_implementation():
    source="import json;import app.main;from app.paths import REPOSITORY_ROOT;print(json.dumps({'main':app.main.__file__,'root':str(REPOSITORY_ROOT)}))"
    results=[]
    for cwd in (ROOT,AI):
        env=os.environ.copy();env.pop('PYTHONPATH',None)
        output=subprocess.run([sys.executable,'-c',source],cwd=cwd,env=env,capture_output=True,text=True,encoding='utf-8',timeout=15)
        assert output.returncode==0,output.stderr
        results.append(json.loads(output.stdout))
    assert results[0]==results[1]
    assert Path(results[0]['main'])==AI/'app/main.py'


def test_legacy_dashboard_and_assets_keep_original_base_url(client):
    html=client.get('/dashboard/')
    assert html.status_code==200
    assets=re.findall(r'(?:src|href)="(/dashboard/assets/[^\"]+)"',html.text)
    assert len(assets)>=2
    for asset in assets:assert client.get(asset).status_code==200
    assert (ROOT/'apps/moderation-web/src/App.jsx').is_file()
    assert (ROOT/'apps/moderation-web/legacy-v3/src/App.jsx').is_file()


def test_colab_cells_compile_and_use_canonical_service_without_deleting_old_session():
    for path in (ROOT/'notebooks').glob('*.ipynb'):
        notebook=json.loads(path.read_text(encoding='utf-8'));code=[]
        for index,cell in enumerate(notebook['cells']):
            if cell['cell_type']!='code':continue
            source=''.join(cell['source']);code.append(source)
            python='\n'.join(line for line in source.splitlines() if not line.lstrip().startswith(('%','!')))
            compile(python,f'{path.name}:cell{index}','exec')
        all_code='\n'.join(code)
        assert 'cwd=AI_ROOT' in all_code
        assert 'apps/moderation-web/legacy-v3' in all_code
        assert 'shutil.rmtree' not in all_code
        assert 'ZIP path escapes extraction directory' in all_code
