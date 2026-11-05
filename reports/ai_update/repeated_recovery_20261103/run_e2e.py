"""Reuse existing disposable five-process browser E2E, not production."""
import os,sys,tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'services/social-api/tests'))
import run_fullstack
tmp=R/'reports/ai_update/test_tmp/repeated_e2e';tmp.mkdir(parents=True,exist_ok=True)
tempfile.tempdir=str(tmp);os.environ.update(TEMP=str(tmp),TMP=str(tmp))
run_fullstack.ARTIFACTS=P/'e2e'
if __name__=='__main__':raise SystemExit(run_fullstack.main())
