"""Existing five-process E2E in a new disposable workspace, never live DB."""
import os,sys,tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'services/social-api/tests'))
import run_fullstack
run_fullstack.ARTIFACTS=P/'e2e'
tmp=P/'temporary';tmp.mkdir(parents=True,exist_ok=True)
tempfile.tempdir=str(tmp);os.environ.update(TEMP=str(tmp),TMP=str(tmp))
if __name__=='__main__':raise SystemExit(run_fullstack.main())
