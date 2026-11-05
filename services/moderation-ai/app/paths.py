"""Repository assets and legacy storage stay stable when service cwd changes."""
import os
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent
SERVICE_ROOT = APP_ROOT.parent
REPOSITORY_ROOT = SERVICE_ROOT.parents[1]


def storage_path(variable: str, default: str) -> str:
    path = Path(os.environ.get(variable, default)).expanduser()
    return str(path if path.is_absolute() else REPOSITORY_ROOT / path)
