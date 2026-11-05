import os,sys,tempfile
from pathlib import Path
R=Path.cwd();sys.path.insert(0,str(R/'services/social-api/tests'))
import run_fullstack
out=R/'reports/ai_update/context_recovery_20261103/social_e2e';out.mkdir(parents=True,exist_ok=True)
tmp=R/'reports/ai_update/test_tmp/recovery_social_e2e';tmp.mkdir(parents=True,exist_ok=True)
run_fullstack.ARTIFACTS=out;tempfile.tempdir=str(tmp);os.environ.update(TEMP=str(tmp),TMP=str(tmp))
if __name__=='__main__':raise SystemExit(run_fullstack.main())
