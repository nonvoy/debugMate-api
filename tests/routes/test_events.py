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

EVENTS_FETCH_DATA = [
    {
        "id": "fe9715a9-c68e-4f8d-b3f3-7442d96549b2",
        "batch_id": "c377f421-f65c-4850-a73e-46619d19f18e",
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
    },
    {
        "id": "fe9715a9-c98e-5f8d-b3f3-7442d9651234",
        "batch_id": "c377f421-f65c-4850-a73e-46619d19f18e",
        "service": "payment-service",
        "severity": "warning",
        "message": "Payment 23304473-9844-4cec-a348-4385d01dc720 processing delayed due to network issues",
        "normalized_message": "payment <uuid> processing delayed due to network issues",
        "fingerprint": "031edd7d41651593c5fe5c006fa5752b37fddff7bc4e843aa6af0c950f4b9406",
        "environment": "staging",
        "event_type": "payment",
        "metadata": {"transaction_id": "abcde"},
        "timestamp": "2024-06-01T12:05:00Z",
        "published_at": "2024-06-01T12:06:00Z",
        "received_at": "2024-06-01T12:06:05Z",
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
    event_data = EVENTS_FETCH_DATA[0]
    event_id = event_data["id"]

    class OpenSearchClientStub:
        @staticmethod
        def get_event_by_id(requested_event_id: str):
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


def test_fetch_events_by_batch_id(client: TestClient):
    """Test fetching events by batch ID from OpenSearch."""

    # Given
    events_data = EVENTS_FETCH_DATA
    batch_id = events_data[0]["batch_id"]

    class OpenSearchClientStub:
        @staticmethod
        def get_events_by_batch_id(requested_batch_id: str):
            return events_data

    app.dependency_overrides[get_opensearch_client] = lambda: OpenSearchClientStub()

    # When
    try:
        fetch_response = client.get(f"/api/v1/events/batch/{batch_id}")
    finally:
        app.dependency_overrides.clear()

    # Then
    assert fetch_response.status_code == status.HTTP_200_OK
    fetched_events = fetch_response.json()
    assert isinstance(fetched_events, list)
    assert len(fetched_events) == len(events_data)

    for i, event in enumerate(events_data):
        assert fetched_events[i]["id"] == event["id"]
        assert fetched_events[i]["batch_id"] == event["batch_id"]
        assert fetched_events[i]["service"] == event["service"]
        assert fetched_events[i]["severity"] == event["severity"]
        assert fetched_events[i]["message"] == event["message"]
        assert fetched_events[i]["normalized_message"] == event["normalized_message"]
        assert fetched_events[i]["fingerprint"] == event["fingerprint"]
        assert fetched_events[i]["environment"] == event["environment"]
        assert fetched_events[i]["event_type"] == event["event_type"]
        assert fetched_events[i]["metadata"] == event["metadata"]
        assert fetched_events[i]["timestamp"] == event["timestamp"]
        assert fetched_events[i]["published_at"] == event["published_at"]
        assert fetched_events[i]["received_at"] == event["received_at"]
