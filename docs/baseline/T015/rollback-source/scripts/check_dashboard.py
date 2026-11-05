"""Offline smoke test for FastAPI and optional React static assets."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from app.main import app

with TestClient(app) as client:
    health = client.get('/health')
    print('health', health.status_code, health.json()['status'])
    assert health.status_code == 200
    if (Path(__file__).resolve().parents[1] / 'app/static/index.html').exists():
        dash = client.get('/dashboard/')
        print('dashboard', dash.status_code)
        assert dash.status_code == 200
    else:
        print('Dashboard source present. Build with npm install && npm run build first.')
