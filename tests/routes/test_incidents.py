from fastapi import status
from fastapi.testclient import TestClient

from main import app
from src.routes.schemas.incidents import IncidentQuery, IncidentStatus
from src.services.db.db_client import get_db_client

INCIDENTS_FETCH_DATA = [
    {
        "id": 1,
        "type": "fingerprint",
        "fingerprint": "031edd7d41651593c5fe5c006fa5752b37fddff7bc4e843aa6af0c950f4b9406",
        "environment": "production",
        "service": "auth-service",
        "events": ["fe9715a9-c68e-4f8d-b3f3-7442d96549b2"],
        "start_time": "2024-06-01T12:00:00Z",
        "end_time": "2024-06-01T12:10:00Z",
        "status": "open",
        "comment": "This incident is being investigated.",
        "assigned_to": "Team Alpha",
        "created_at": "2024-06-01T12:05:00Z",
        "updated_at": "2024-06-01T12:10:00Z",
    },
    {
        "id": 2,
        "type": "environment_service",
        "fingerprint": None,
        "environment": "staging",
        "service": "payment-service",
        "events": ["fe9715a9-c98e-5f8d-b3f3-7442d9651234"],
        "start_time": "2024-06-02T12:00:00Z",
        "end_time": "2024-06-02T12:10:00Z",
        "status": "assigned",
        "comment": None,
        "assigned_to": "Team Beta",
        "created_at": "2024-06-02T12:05:00Z",
        "updated_at": "2024-06-02T12:10:00Z",
    },
]


def test_fetch_incident_by_id(client: TestClient):
    """Test fetching an incident by its ID from the database."""

    # Given
    incident_data = INCIDENTS_FETCH_DATA[0]
    incident_id = incident_data["id"]

    class DBClientStub:
        @staticmethod
        def get_incident_by_id(requested_incident_id: int):
            assert requested_incident_id == incident_id
            return incident_data

    app.dependency_overrides[get_db_client] = lambda: DBClientStub()

    # When
    try:
        fetch_response = client.get(f"/api/v1/incidents/{incident_id}")
    finally:
        app.dependency_overrides.clear()

    # Then
    assert fetch_response.status_code == status.HTTP_200_OK
    fetched_incident = fetch_response.json()
    assert fetched_incident == incident_data


def test_fetch_incident_by_id_returns_404_when_incident_is_not_found(client: TestClient):
    """Test fetching an incident by ID when the incident does not exist."""

    # Given
    incident_id = 404

    class DBClientStub:
        @staticmethod
        def get_incident_by_id(requested_incident_id: int):
            assert requested_incident_id == incident_id
            return None

    app.dependency_overrides[get_db_client] = lambda: DBClientStub()

    # When
    try:
        fetch_response = client.get(f"/api/v1/incidents/{incident_id}")
    finally:
        app.dependency_overrides.clear()

    # Then
    assert fetch_response.status_code == status.HTTP_404_NOT_FOUND
    assert fetch_response.json() == {"detail": "Incident not found"}


def test_fetch_incidents_with_query(client: TestClient):
    """Test fetching incidents with query filters from the database."""

    # Given
    incidents_data = INCIDENTS_FETCH_DATA[:1]

    class DBClientStub:
        @staticmethod
        def get_incidents(query: IncidentQuery):
            assert query.service == "auth-service"
            assert query.environment == "production"
            assert query.status == IncidentStatus.OPEN
            assert query.start_time_from is not None
            assert query.start_time_from.isoformat() == "2024-06-01T00:00:00+00:00"
            assert query.start_time_to is not None
            assert query.start_time_to.isoformat() == "2024-06-30T23:59:59+00:00"
            return incidents_data

    app.dependency_overrides[get_db_client] = lambda: DBClientStub()

    # When
    try:
        fetch_response = client.get(
            "/api/v1/incidents/",
            params={
                "service": "auth-service",
                "environment": "production",
                "status": "open",
                "start_time_from": "2024-06-01T00:00:00Z",
                "start_time_to": "2024-06-30T23:59:59Z",
            },
        )
    finally:
        app.dependency_overrides.clear()

    # Then
    assert fetch_response.status_code == status.HTTP_200_OK
    assert fetch_response.json() == incidents_data
