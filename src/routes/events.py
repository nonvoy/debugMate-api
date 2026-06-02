import datetime as dt
import uuid
from typing import Annotated

from celery import Celery
from fastapi import APIRouter, Depends, HTTPException, status

from src.config.basic_config import get_config
from src.config.logger import get_logger
from src.routes.schemas.events import EventCreate, EventGet
from src.services.celery.client import get_celery_client
from src.services.search.open_search_client import OpenSearchClient, get_opensearch_client

config = get_config()
logger = get_logger(__name__)

router = APIRouter(prefix="/events", tags=["events"])


@router.post("/batch", response_model=list[EventGet], status_code=status.HTTP_202_ACCEPTED)
async def create_events_batch(events: list[EventCreate], celery_app: Annotated[Celery, Depends(get_celery_client)]) -> list[EventGet]:
    """
    Publish multiple events in a batch to the Celery task queue for processing.

    This endpoint allows you to publish multiple events at once by providing a list of event details.
    Each event should include the necessary information such as service name, severity, message, environment, event type, metadata, and timestamp.

    - **service**: The name of the service that generated the event (e.g., 'auth-service', 'payment-service').
    - **severity**: The severity level of the event (e.g., 'info', 'warning', 'error').
    - **message**: A descriptive message about the event (e.g., 'User login successful', 'Payment failed due to insufficient funds').
    - **environment**: (Optional)The environment where the event occurred (e.g., 'production', 'staging').
    - **event_type**: (Optional) The type of event (e.g., 'authentication', 'payment').
    - **metadata**: (Optional) Additional metadata related to the event (e.g., {'user_id': '12345', 'transaction_id': 'abcde'}).
    - **timestamp**: The timestamp when the event occurred in ISO 8601 format (e.g., '2024-06-01T12:00:00Z').

    Returns a list of published events with their unique identifiers and batch ID.
    """
    created_events = []
    batch_id = uuid.uuid4()
    published_at = dt.datetime.now(dt.timezone.utc)
    for event in events:
        event_id = uuid.uuid4()
        created_event = EventGet(id=event_id, batch_id=batch_id, published_at=published_at, **event.model_dump())
        created_events.append(created_event)

    celery_app.send_task(config.celery.task_name, task_id=str(batch_id), args=[[event.model_dump() for event in created_events]])
    logger.info(f"{len(created_events)} events published in batch with ID: {batch_id} to Celery task queue.")
    return created_events


@router.post("/", response_model=EventGet, status_code=status.HTTP_202_ACCEPTED)
async def publish_event(event: EventCreate, celery_app: Annotated[Celery, Depends(get_celery_client)]) -> EventGet:
    """
    Publish an event to the Celery task queue for processing.

    This endpoint allows you to publish an event by providing the necessary details such as service name, severity, message, environment,
    event type, metadata, and timestamp.

    - **service**: The name of the service that generated the event (e.g., 'auth-service', 'payment-service').
    - **severity**: The severity level of the event (e.g., 'info', 'warning', 'error').
    - **message**: A descriptive message about the event (e.g., 'User login successful', 'Payment failed due to insufficient funds').
    - **environment**: (Optional)The environment where the event occurred (e.g., 'production', 'staging').
    - **event_type**: (Optional) The type of event (e.g., 'authentication', 'payment').
    - **metadata**: (Optional) Additional metadata related to the event (e.g., {'user_id': '12345', 'transaction_id': 'abcde'}).
    - **timestamp**: The timestamp when the event occurred in ISO 8601 format (e.g., '2024-06-01T12:00:00Z').

    Returns the published event with its unique identifier.
    """
    event_id = uuid.uuid4()
    created_event = EventGet(id=event_id, published_at=dt.datetime.now(dt.timezone.utc), **event.model_dump())
    celery_app.send_task(config.celery.task_name, task_id=str(event_id), args=[[created_event.model_dump()]])
    logger.info(f"Event with ID: {event_id} published to Celery task queue.")
    return created_event


@router.get("/{event_id}", response_model=EventGet, status_code=status.HTTP_200_OK)
async def get_event(event_id: uuid.UUID, opensearch_client: Annotated[OpenSearchClient, Depends(get_opensearch_client)]) -> EventGet:
    """
    Retrieve an event by its unique identifier.

    This endpoint allows you to fetch the details of a specific event using its unique identifier (UUID).

    - **event_id**: The unique identifier of the event to retrieve.

    Returns the details of the requested event.
    """
    logger.info(f"Retrieving event with ID: {event_id}")
    event_data = opensearch_client.get_event_by_id(str(event_id))
    if not event_data:
        logger.warning(f"Event with ID: {event_id} not found.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    return EventGet(**event_data)
