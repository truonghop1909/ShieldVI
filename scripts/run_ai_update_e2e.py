"""Run existing five-process fixture E2E with fresh artifacts and temporary DBs."""
import os,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'services/social-api/tests'))
import run_fullstack
out=ROOT/'reports/ai_update/autonomous_20261103/e2e_v2';out.mkdir(parents=True,exist_ok=True)
tmp=ROOT/'reports/ai_update/test_tmp/fullstack_autonomous500';tmp.mkdir(parents=True,exist_ok=True)
tempfile.tempdir=str(tmp);os.environ.update(TEMP=str(tmp),TMP=str(tmp))
run_fullstack.ARTIFACTS=out
if __name__=='__main__':raise SystemExit(run_fullstack.main())

