"""Synthetic browser fixtures only. Never a publish/seed endpoint in the app."""
import os
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "services/social-api/src"))
from shieldvi_social.config import Settings
from shieldvi_social.db import make_engine, session_factory
from shieldvi_social.models import Comment, Post, User
from shieldvi_social.security import PASSWORD_HASHER


def seed():
    settings = Settings.from_env()
    engine = make_engine(settings)
    database = Path(engine.url.database).resolve()
    if os.environ.get("SOCIAL_WEB_TEST_FIXTURES") != "1" or Path(tempfile.gettempdir()).resolve() not in database.parents:
        raise RuntimeError("Fixture setup only supports an explicitly enabled temporary test database")
    password = os.environ["SOCIAL_WEB_TEST_PASSWORD"]
    now = int(time.time())
    with session_factory(engine).begin() as db:
        owner = User(username="fixture_author", email="author@example.com", password_hash=PASSWORD_HASHER.hash(password))
        viewer = User(username="fixture_viewer", email="viewer@example.com", password_hash=PASSWORD_HASHER.hash(password))
        db.add_all([owner, viewer]); db.flush()
        for i in range(1, 13):
            db.add(Post(id=f"10000000-0000-4000-8000-{i:012x}", author_id=owner.id,
                body=f"Câu chuyện công khai {i:02d}. Một góc nhìn mới để cùng lắng nghe.",
                create_key=f"fixture-post-{i}", request_hash="synthetic", visibility_status="PUBLISHED",
                review_status="APPROVED", risk_tier="LOW", created_at=now-i*60))
        db.add(Post(id="10000000-0000-4000-8000-0000000000f0", author_id=owner.id,
            body="TOP-SECRET-FIXTURE", create_key="private-fixture", request_hash="synthetic", visibility_status="HIDDEN"))
        db.flush()
        db.add(Comment(id="20000000-0000-4000-8000-000000000001", author_id=owner.id,
            post_id="10000000-0000-4000-8000-000000000001", body='<img src=x onerror="window.__shieldviXss=1"> '+"dài"*160,
            create_key="comment-fixture", request_hash="synthetic", visibility_status="PUBLISHED",
            review_status="APPROVED", risk_tier="LOW"))
    engine.dispose()
    print("Seeded synthetic public/private content in temporary browser DB; no AI inference")


if __name__ == "__main__":
    seed()
