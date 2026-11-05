"""Prepare a manual full-GPU notebook; no cells executed or external upload."""
import ast,json
from pathlib import Path
R=Path(__file__).resolve().parents[3]
cells=[]
def md(text):cells.append({'cell_type':'markdown','metadata':{},'source':text.splitlines(keepends=True)})
def code(text):
    ast.parse(text);cells.append({'cell_type':'code','metadata':{},'source':text.splitlines(keepends=True),'execution_count':None,'outputs':[]})
md('''# Synthetic-only ViSoBERT full-encoder proposal — NOT EXECUTED

r06 completed a local CPU **frozen encoder + classifier-head** experiment. This notebook prepares a separate full-encoder GPU experiment; it is not evidence that full fine-tuning happened. Real T028/formal T029/T030 acceptance remains blocked. No paid GPU, data upload or production activation is approved by this notebook.

Use only operator-approved local/Drive copies of the project, original V1 and both canonical/derived synthetic datasets. Do not download a checkpoint/dataset automatically. Mount/upload only after separate permission. Pin transformers4.57.3/huggingface-hub0.36.2; if installation is needed, request operator permission and restart the runtime afterward.
''')
code('''from pathlib import Path
import json,sys,os,hashlib
PROJECT=Path('/content/drive/MyDrive/ShieldVI_V3_Hybrid_Review')
BASE=Path('/content/drive/MyDrive/visobert_toxic_final')
PROJECT_ZIP=None  # Optional operator-approved local archive; no automatic upload/download.
if PROJECT_ZIP is not None:
    import zipfile
    destination=Path('/content/shieldvi_synthetic_import_NEW_RUN').resolve()
    assert not destination.exists() or not any(destination.iterdir()), 'Choose a new empty destination; never delete an old session'
    destination.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(PROJECT_ZIP) as archive:
        for item in archive.infolist():
            target=(destination/item.filename).resolve()
            if not target.is_relative_to(destination):
                raise ValueError('ZIP path escapes extraction directory')
            if (item.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError('ZIP symlinks are not allowed')
        archive.extractall(destination)
    roots=[destination]+[p for p in destination.iterdir() if p.is_dir()]
    PROJECT=next(p for p in roots if (p/'scripts/train_t029_candidate.py').is_file())
assert (PROJECT/'scripts/train_t029_candidate.py').is_file(), 'Operator must provide the project bundle first'
assert (BASE/'model.safetensors').is_file(), 'Use an existing approved V1 copy, no automatic download'
os.chdir(PROJECT)
os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',STORE_SUMMARIES='0')
sys.path.insert(0,str(PROJECT/'scripts'))
AI_ROOT=PROJECT/'services/moderation-ai'
DASHBOARD_ROOT=PROJECT/'apps/moderation-web/legacy-v3'
assert (AI_ROOT/'app/main.py').is_file() and DASHBOARD_ROOT.is_dir()

def start_local_research_demo(checkpoint,port=8022):
    # Explicit manual preview only; not invoked by this notebook or a production switch.
    import subprocess
    checkpoint=Path(checkpoint)
    assert (checkpoint/'model.safetensors').is_file()
    env={**os.environ,'MODEL_PATH':str(checkpoint),'STORE_SUMMARIES':'0','HF_HUB_OFFLINE':'1'}
    return subprocess.Popen([sys.executable,'-m','uvicorn','app.main:app','--host','127.0.0.1','--port',str(port)],cwd=AI_ROOT,env=env)
''')
code('''import torch,transformers,importlib.metadata
assert transformers.__version__=='4.57.3'
assert importlib.metadata.version('huggingface-hub')=='0.36.2'
assert torch.cuda.is_available(), 'This full-encoder proposal requires an approved available GPU; no CPU fallback'
from synthetic_data.experiment import verify_view
from refine_model import file_hash
assert file_hash(BASE/'model.safetensors')=='84c149584bb22bde4017ffef1f4ffac7b13e0239df7a73a95eeb32e020e81fd2'
verify_view(PROJECT/'datasets/synthetic_genz',PROJECT/'datasets/synthetic_conversations/genz_v2')
''')
code('''from synthetic_data.pipeline import atomic_json
cfg=json.loads((PROJECT/'configs/t029_synthetic_only_cpu_r06.json').read_text(encoding='utf-8'))
cfg.update(run_id='T029_synthetic_fullgpu_NEW_APPROVAL_REQUIRED',training_strategy='full_finetune_gpu',
           resource='Colab_GPU_NEW_APPROVAL_REQUIRED',output_dir='/content/drive/MyDrive/shieldvi_candidates/synthetic_fullgpu_NEW_RUN',
           batch_size=8,gradient_accumulation_steps=4,learning_rate=1e-5,max_training_seconds=3600,
           approved_for_execution=False,approval_status='NEW_CONFIG_RESOURCE_RECEIPT_REQUIRED',estimated_cost='UNKNOWN_NOT_APPROVED')
CONFIG=PROJECT/'configs/t029_synthetic_fullgpu_proposed.json'
if CONFIG.exists():
    assert json.loads(CONFIG.read_text(encoding='utf-8'))==cfg, 'Never overwrite a different proposal'
else:
    atomic_json(CONFIG,cfg)
PREPARED=Path('/content/t029_synthetic_fullgpu_prepared')
from prepare_t029_training import prepare
if not (PREPARED/'manifest.json').exists():
    prepare(CONFIG,PREPARED,BASE,root=PROJECT)
else:
    info=json.loads((PREPARED/'manifest.json').read_text(encoding='utf-8'))
    assert info['config_sha256']==file_hash(CONFIG)
''')
md('''## Approval before actual full fine-tuning

The current scope exception authorizes only the completed r06 CPU run. A future explicit GPU/resource/config approval, updated scope and matching real receipt are mandatory; changing a boolean alone does not authorize training. Do not fabricate a receipt or reuse the r06 one. Review output path, dataset/weights hashes, split, cost and stopping bound. Keep0.41 and independent real blockers. The challenge is already-viewed synthetic development, never a fresh test. The runner records failure honestly; general mid-optimizer resume is not implemented, so do not assume partial training is a completed checkpoint.
''')
code('''from train_t029_candidate import run
APPROVAL_RECEIPT=PROJECT/'configs/NEW_EXPLICIT_GPU_APPROVAL.json'
preflight=run(CONFIG,PREPARED,BASE,APPROVAL_RECEIPT if APPROVAL_RECEIPT.exists() else None,execute=False,root=PROJECT)
print(json.dumps(preflight,indent=2))
# BLOCKED is expected until all actual approvals/resources match.
''')
code('''APPROVED_FULL_FINE_TUNE=False
assert APPROVED_FULL_FINE_TUNE and APPROVAL_RECEIPT.is_file(), 'Default is preparation only'
preflight=run(CONFIG,PREPARED,BASE,APPROVAL_RECEIPT,execute=False,root=PROJECT)
assert preflight['status']=='READY_TO_RUN', preflight
result=run(CONFIG,PREPARED,BASE,APPROVAL_RECEIPT,execute=True,root=PROJECT)
print(result['status'])
# Full encoder training, if actually approved/executed, writes a NEW checkpoint. Never activate production here.
''')
path=R/'notebooks/T029_Synthetic_Experimental_R06.ipynb'
if path.exists():
    previous=json.loads(path.read_text(encoding='utf-8'))
    if any(c.get('execution_count') is not None or c.get('outputs') for c in previous['cells'] if c['cell_type']=='code'):
        raise FileExistsError('Never overwrite an executed notebook')
path.write_text(json.dumps({'cells':cells,'metadata':{'kernelspec':{'display_name':'Python3','language':'python','name':'python3'},'shieldvi_status':'PREPARED_NOT_EXECUTED_FULL_GPU'},'nbformat':4,'nbformat_minor':5},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'notebook':path.relative_to(R).as_posix(),'code_cells':sum(c['cell_type']=='code' for c in cells),'executed_cells':0,'syntax':'PASS'}))
