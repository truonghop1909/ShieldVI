"""Disposable browser fixtures only; no role provisioning for an existing DB."""
import json
import os
from pathlib import Path
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT / "services/social-api/src"))
from shieldvi_social.config import Settings
from shieldvi_social.db import make_engine, session_factory
from shieldvi_social.models import ModerationJob, ModerationResult, Post, User
from shieldvi_social.security import PASSWORD_HASHER


def seed():
    engine=make_engine(Settings.from_env())
    if os.environ.get("MODERATION_WEB_TEST_FIXTURES") != "1" or Path(tempfile.gettempdir()).resolve() not in Path(engine.url.database).resolve().parents:
        raise RuntimeError("Fixture setup requires an explicitly enabled temporary database")
    password=os.environ["SOCIAL_WEB_TEST_PASSWORD"]
    now=int(time.time())
    with session_factory(engine).begin() as db:
        users=[User(username=name,email=f"{name}@example.com",role=role,password_hash=PASSWORD_HASHER.hash(password))
            for name,role in (("fixture_author","user"),("fixture_viewer","user"),("fixture_mod","moderator"),("fixture_admin","admin"))]
        db.add_all(users);db.flush()
        public=Post(id="10000000-0000-4000-8000-000000000001",author_id=users[0].id,body="Cau chuyen demo cong khai",
            create_key="fixture-public",request_hash="fixture",visibility_status="PUBLISHED",review_status="APPROVED")
        db.add(public)
        for i in range(12):
            db.add(Post(author_id=users[0].id,body=f"Queue fixture {i:02d}",create_key=f"queue-{i}",request_hash="fixture",created_at=now-60+i))
        flagged=Post(author_id=users[0].id,body='<img src=x onerror="window.__adminXss=1"> Evidence fixture',create_key="fixture-evidence",
            request_hash="fixture",visibility_status="PUBLISHED_FLAGGED",review_status="QUEUED",risk_tier="REVIEW",decision_version=1)
        failed=Post(author_id=users[0].id,body="Offline failed fixture",create_key="fixture-failed",request_hash="fixture")
        db.add_all([flagged,failed]);db.flush()
        job=ModerationJob(entity_type="post",entity_id=flagged.id,content_revision=1,expected_decision_version=0,
            status="SUCCEEDED",outcome="APPLIED",policy_version="social-policy-shadow-0.2")
        db.add(job);db.flush()
        example=json.loads((ROOT / "contracts/moderation_response.example.json").read_text(encoding="utf-8"))
        example.update(content_id=flagged.id,content_revision=1,request_id=job.request_id,model_version="browser-synthetic-not-real-inference")
        db.add(ModerationResult(job_id=job.id,request_id=job.request_id,content_revision=1,
            model_version=example["model_version"],lexicon_version=example["lexicon_version"],threshold=.41,ai_label=example["ai_label"],
            score=example["toxicity_score"],policy_version="social-policy-shadow-0.2",risk_tier="REVIEW",
            signals_json=json.dumps(example,ensure_ascii=False),analyzed_at=example["analyzed_at"],created_at=now))
        db.add(ModerationJob(entity_type="post",entity_id=failed.id,content_revision=1,expected_decision_version=0,
            status="FAILED_PERMANENTLY",attempts=3,total_attempts=3,last_error="AI_TIMEOUT"))
    engine.dispose()
    print("Synthetic browser fixtures created in temporary DB; no real checkpoint inference")


if __name__=="__main__":
    seed()
