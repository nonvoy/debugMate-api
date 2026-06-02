from fastapi import status
from fastapi.testclient import TestClient

from src.routes import liveness


def test_liveness_check(client: TestClient):
    """Test the liveness check endpoint."""

    # When
    response = client.get("/health/live")

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "OK"}


def test_readiness_check(client: TestClient, monkeypatch):
    """Test the readiness check endpoint."""

    class CeleryControlStub:
        @staticmethod
        def ping(timeout: int):
            assert timeout == 5
            return [{"worker": {"ok": "pong"}}]

    class CeleryStub:
        control = CeleryControlStub()

    monkeypatch.setattr(liveness, "get_celery_client", lambda: CeleryStub())

    # When
    response = client.get("/health/ready")

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "OK"}


def test_readiness_check_returns_503_when_celery_does_not_respond(client: TestClient, monkeypatch):
    """Test the readiness check endpoint when Celery workers do not respond."""

    class CeleryControlStub:
        @staticmethod
        def ping(timeout: int):
            assert timeout == 5
            return []

    class CeleryStub:
        control = CeleryControlStub()

    monkeypatch.setattr(liveness, "get_celery_client", lambda: CeleryStub())

    # When
    response = client.get("/health/ready")

    # Then
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.json() == {"detail": "No Celery workers responded"}
