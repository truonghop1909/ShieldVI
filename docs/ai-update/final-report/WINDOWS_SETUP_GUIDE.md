# Windows setup and verification

Open PowerShell at ShieldVI_V3_Hybrid_Review. Existing environments required:

- Root `.venv/Scripts/python.exe`: torch/transformers and the local checkpoints.
- `services/social-api/.venv/Scripts/python.exe`: FastAPI/SQLAlchemy/Alembic.
- Node/npm, existing node_modules in both apps, Chrome and @playwright/test.

This task installs/downloads nothing. The default checkpoint must already be
present and approved. A missing dependency/model is an explicit startup failure.
Ports are selected dynamically on127.0.0.1; no public binding is needed.

```powershell
.\scripts\demo_realtime_studio.ps1
# Another PowerShell window:
.\scripts\demo_realtime_stop.ps1
```

The launcher creates only a fresh demo DB/root, runs additive schemas there,
generates short-lived account/service credentials and opens seven logged-in
browser contexts. It preserves existing DBs, source pack, checkpoint/default,
threshold0.41 and readiness locks. Stop only signals the owning launcher;
it never kills processes by port or deletes databases. Demo logs contain
synthetic content and local metadata; treat retained Studio private_key and DBs
as local artifacts rather than public uploads.

Checks without new training:

```powershell
.\scripts\demo_realtime_studio.ps1 -HeadlessCheck
.\scripts\demo_realtime_studio.ps1 -InteractiveCheck
.\scripts\demo_realtime_studio.ps1 -FeedCheck
.\scripts\demo_realtime_studio.ps1 -StudioCheck
node --test apps/shared/live-transport.test.mjs
.\services\social-api\.venv\Scripts\python.exe -X utf8 -m pytest services/social-api/tests -q --basetemp reports/task_rollout_20261104/tmp_manual_social
.\.venv\Scripts\python.exe -X utf8 -m pytest -q --basetemp reports/task_rollout_20261104/tmp_manual_root
.\.venv\Scripts\python.exe scripts/verify_ai_readiness_lock.py --lock reports/ai_update/stabilization_20261103/READINESS_LOCK_T028_v2.json
```

Use a new basetemp name when retaining prior test evidence. Never point pytest
basetemp at a dataset/model/production directory. The separate T041 training
E2E runner is retained for reproducibility but is not part of these checks;
it starts a new actual CPU run and should not be rerun implicitly.

Use `-X utf8` on Windows for Vietnamese fixture/report readers; the default
cp1252 locale can raise UnicodeDecodeError. The demo Social server explicitly
uses `scripts/demo_loop.py` (Selector loop) after Proactor accept WinError64
was observed in a seven-browser run. This is an opt-in demo setting only.

Frontend verification uses `vite.live.config.js` → dist-live. Original app
regression builds use a separate dist-regression-t043 output so sealed dist
artifacts remain intact. Detailed commands, logs and source hashes are linked
in [T034_T043_FINAL_REPORT.md](T034_T043_FINAL_REPORT.md).
