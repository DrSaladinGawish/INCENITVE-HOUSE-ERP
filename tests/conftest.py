import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import InterfaceError

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

os.environ["DEBUG"] = "false"
os.environ["LOG_LEVEL"] = "CRITICAL"

from app.config import settings
from app.main import app


def _has_sql_server() -> bool:
    try:
        eng = create_engine(settings.SYNC_DATABASE_URL)
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        eng.dispose()
        return True
    except (InterfaceError, Exception):
        return False


has_db = _has_sql_server()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_headers(client):
    resp = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    token = resp.json().get("access_token", "") if resp.status_code == 200 else ""
    return {"Authorization": f"Bearer {token}"} if token else {}


def pytest_collection_modifyitems(config, items):
    if has_db:
        return
    skip_db = pytest.mark.skip(reason="Requires SQL Server (not available)")
    for item in items:
        if "test_api_endpoints" in item.nodeid:
            item.add_marker(skip_db)
