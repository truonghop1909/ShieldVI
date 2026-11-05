"""Compatibility import for V3 commands; implementation lives in the AI service.

Keep ``uvicorn app.main:app`` and existing research imports working from repo root.
There is one implementation and one set of module globals/dependency overrides.
"""
from pathlib import Path

_canonical = Path(__file__).resolve().parents[1] / "services" / "moderation-ai" / "app"
if not (_canonical / "main.py").is_file():
    raise ImportError("ShieldVI moderation-ai source is missing")
__path__ = [str(_canonical)]
