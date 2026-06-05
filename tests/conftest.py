import os

import pytest
from fastapi.testclient import TestClient

os.environ["DEBUG"] = "false"
os.environ["DB_URL"] = "sqlite:///test.db"
os.environ.setdefault("OPENSEARCH__URL", "http://localhost:9200")

from main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
