# Opt-in live extension — local only

Original Social API/worker entrypoints remain unchanged. Live extension uses same app/auth/posts/comments/jobs/review tables plus additive live_events, live_thread_members, live_schema_version. Do not initialize on a real DB without separate operational approval. Tests use disposable SQLite; no existing DB migrated automatically.

From root, first create a NEW explicit database path, set SOCIAL_DATABASE_URL to its absolute SQLite URL, run original Alembic upgrade head from services/social-api. Then initialize extension:

```powershell
.\services\social-api\.venv\Scripts\python.exe -m shieldvi_social.live_schema --database-url $env:SOCIAL_DATABASE_URL
```

Set PYTHONPATH to services/social-api/src for module commands, or run from service using its installed editable environment. Start Social API with:

```powershell
.\services\social-api\.venv\Scripts\python.exe -m uvicorn shieldvi_social.live_app:create_app --factory --app-dir services/social-api/src --host 127.0.0.1 --port 8001 --no-proxy-headers
```

Original worker plus event hook wrapper:

```powershell
.\services\social-api\.venv\Scripts\python.exe -m shieldvi_social.live_worker
```

Uses existing SOCIAL_AI_BASE_URL/SOCIAL_AI_SERVICE_TOKEN, no browser service token. The T035 wrapper currently uses existing internal1.0 AI client; T036 adds an explicit incremental adapter/client mode, not a switch to research rules. AI default/model/.41 preserved. Client login uses existing /api/v1/auth/login; join a readable post at POST /api/live/threads/{id}/join, then use snapshot/SSE/send routes from CONTRACTS.md. No private-chat feature or browser UI completion claimed at this stage.

Pending comment is visible only to author/staff under existing policy; peer sees body after publication. All SSE data is minimal, authorized snapshot supplies text. SSE once=true is a bounded integration-check mode; normal streams revalidate session/membership and terminate after25s for client reconnect. since cursor numeric, never put bearer token in query.

Rollback: stop only processes you started, restart original shieldvi_social.main:create_app and original worker against schema0004. Extension tables stay; no DROP/reset. Original API starts on the same base0004 DB with extension tables present, verified in tests. Original content/worker tests remain part of Social regression.
