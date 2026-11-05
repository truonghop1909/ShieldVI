"""Read-only source/DB schema verification; writes evidence in this folder only."""
import hashlib
import json
from pathlib import Path
import sqlite3

HERE=Path(__file__).resolve().parent
DESIGN=HERE.parents[2]
SOURCE=DESIGN.parent / "ShieldVI_V3_Hybrid_Review"


def digest(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle,"sha256").hexdigest()


def changed(manifest):
    rows=json.loads(manifest.read_text(encoding="utf-8"))
    return len(rows),[row["path"] for row in rows if not (SOURCE/row["path"]).is_file() or digest(SOURCE/row["path"])!=row["sha256"]]


original_count,original_changes=changed(HERE.parent/"T007/source-manifest.json")
previous_count,previous_changes=changed(HERE.parent/"T012_T017/source-manifest.json")
database=SOURCE / "services/social-api/data/social.sqlite3"
versions=None
if database.is_file():
    with sqlite3.connect(database.resolve().as_uri()+"?mode=ro",uri=True) as connection:
        versions=[row[0] for row in connection.execute("SELECT version_num FROM alembic_version")]
record={"original_files_checked":original_count,"original_changes_since_T007":original_changes,
    "previous_files_checked":previous_count,"changes_since_T012_T017":previous_changes,
    "legacy_changes_this_stage":[p for p in previous_changes if not p.startswith("services/social-api/")],
    "default_social_db_schema_read_only":versions,"real_checkpoint_inference":"NOT_RUN",
    "live_database_migration":"NOT_RUN"}
(HERE/"integrity-check.json").write_text(json.dumps(record,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
manifest=[]
for directory in ("services/social-api/src/shieldvi_social","services/social-api/tests","services/social-api/migrations",
                  "apps/social-web/src","apps/moderation-web"):
    for path in sorted((SOURCE/directory).rglob("*")):
        relative=path.relative_to(SOURCE)
        if not path.is_file() or any(part in {"__pycache__","node_modules","dist","test-results"} for part in relative.parts):continue
        if path.name.startswith(".env") and path.name!=".env.example":continue
        manifest.append({"path":relative.as_posix(),"bytes":path.stat().st_size,"sha256":digest(path)})
(HERE/"source-manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
print(json.dumps(record,ensure_ascii=True))
assert original_changes==["app/main.py"],"Unexpected original source/checkpoint/static change"
assert not record["legacy_changes_this_stage"],"Unexpected legacy change during T013/T018"
