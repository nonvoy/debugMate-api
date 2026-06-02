import uuid

from fastapi import status
from fastapi.testclient import TestClient

from main import app
from src.services.search.open_search_client import get_opensearch_client

EVENTS_PUBLISH_DATA = [
    {
        "service": "auth-service",
        "severity": "error",
        "message": "User login failed due to invalid credentials",
        "environment": "production",
        "event_type": "authentication",
        "metadata": {"user_id": "12345"},
        "timestamp": "2024-06-01T12:00:00Z",
    },
    {
        "service": "payment-service",
        "severity": "warning",
        "message": "Payment processing delayed due to network issues",
        "environment": "staging",
        "event_type": "payment",
        "metadata": {"transaction_id": "abcde"},
        "timestamp": "2024-06-01T12:05:00Z",
    },
]


def test_publish_event(client: TestClient):
    """Test the publishing of an event via the /events/ endpoint."""

    # Given
    event_data = EVENTS_PUBLISH_DATA[0]

    # When
    response = client.post("/api/v1/events/", json=event_data)

    # Then
    assert response.status_code == status.HTTP_202_ACCEPTED

    response_data = response.json()
    assert "id" in response_data
    assert "published_at" in response_data
    assert response_data["service"] == event_data["service"]
    assert response_data["severity"] == event_data["severity"]
    assert response_data["message"] == event_data["message"]
    assert response_data["environment"] == event_data["environment"]
    assert response_data["event_type"] == event_data["event_type"]
    assert response_data["metadata"] == event_data["metadata"]
    assert response_data["timestamp"] == event_data["timestamp"]


def test_publish_events_in_batch(client: TestClient):
    """Test the publishing of multiple events via the /events/batch endpoint."""

    # Given
    events_data = EVENTS_PUBLISH_DATA

    # When
    response = client.post("/api/v1/events/batch", json=events_data)

    # Then
    assert response.status_code == status.HTTP_202_ACCEPTED

    response_data = response.json()
    assert isinstance(response_data, list)
    assert len(response_data) == len(events_data)

    for i, event in enumerate(events_data):
        assert "id" in response_data[i]
        assert response_data[i]["service"] == event["service"]
        assert response_data[i]["severity"] == event["severity"]
        assert response_data[i]["message"] == event["message"]
        assert response_data[i]["environment"] == event["environment"]
        assert response_data[i]["event_type"] == event["event_type"]
        assert response_data[i]["metadata"] == event["metadata"]
        assert response_data[i]["timestamp"] == event["timestamp"]
        assert "published_at" in response_data[i]
        assert "batch_id" in response_data[i]

    assert response_data[0]["batch_id"] == response_data[1]["batch_id"]


def test_fetch_event_by_id(client: TestClient):
    """Test fetching an event by its ID from OpenSearch."""

    # Given
    event_id = uuid.uuid4()
    event_data = {
        "id": str(event_id),
        "service": "auth-service",
        "severity": "error",
        "message": "User <john@example.com> login failed due to invalid credentials",
        "normalized_message": "user <email> login failed due to invalid credentials",
        "fingerprint": "031edd7d41651593c5fe5c006fa5752b37fddff7bc4e843aa6af0c950f4b9406",
        "environment": "production",
        "event_type": "authentication",
        "metadata": {"user_id": "12345"},
        "timestamp": "2024-06-01T12:00:00Z",
        "published_at": "2024-06-01T12:01:00Z",
        "received_at": "2024-06-01T12:01:05Z",
    }

    class OpenSearchClientStub:
        @staticmethod
        def get_event_by_id(requested_event_id: str):
            assert requested_event_id == str(event_id)
            return event_data

    app.dependency_overrides[get_opensearch_client] = lambda: OpenSearchClientStub()

    # When
    try:
        fetch_response = client.get(f"/api/v1/events/{event_id}")
    finally:
        app.dependency_overrides.clear()

    # Then
    assert fetch_response.status_code == status.HTTP_200_OK
    fetched_event = fetch_response.json()
    assert fetched_event["id"] == str(event_id)
    assert fetched_event["service"] == event_data["service"]
    assert fetched_event["severity"] == event_data["severity"]
    assert fetched_event["message"] == event_data["message"]
    assert fetched_event["normalized_message"] == event_data["normalized_message"]
    assert fetched_event["fingerprint"] == event_data["fingerprint"]
    assert fetched_event["environment"] == event_data["environment"]
    assert fetched_event["event_type"] == event_data["event_type"]
    assert fetched_event["metadata"] == event_data["metadata"]
    assert fetched_event["timestamp"] == event_data["timestamp"]
    assert fetched_event["published_at"] == event_data["published_at"]
    assert fetched_event["received_at"] == event_data["received_at"]
