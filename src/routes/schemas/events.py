import datetime as dt
from enum import StrEnum, auto
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class Severity(StrEnum):
    """Enumeration for severity levels of events."""

    debug = auto()
    info = auto()
    warning = auto()
    error = auto()
    critical = auto()


class Event(BaseModel):
    """Model representing an event in the system."""

    service: str = Field(
        ..., min_length=1, description="The name of the service that generated the event", examples=["auth-service", "payment-service"]
    )
    severity: Severity = Field(
        ..., description="The severity level of the event (e.g., 'info', 'warning', 'error')", examples=["info", "warning", "error"]
    )
    message: str = Field(
        ...,
        min_length=1,
        description="A descriptive message about the event",
        examples=["User login successful", "Payment failed due to insufficient funds"],
    )
    environment: str = Field(
        "unknown",
        min_length=1,
        description="The environment where the event occurred (e.g., 'production', 'staging')",
        examples=["production", "staging"],
    )
    event_type: str = Field(
        "unknown", min_length=1, description="The type of event (e.g., 'authentication', 'payment')", examples=["application_log", "security_event"]
    )
    metadata: dict = Field(
        default_factory=dict, description="Additional metadata related to the event", examples=[{"user_id": "12345", "transaction_id": "abcde"}]
    )
    timestamp: dt.datetime = Field(..., description="The timestamp when the event occurred", examples=["2024-06-01T12:00:00Z"])

    @field_validator("service", "severity", "environment", "event_type", mode="before")
    @classmethod
    def normalize_string_fields(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().lower()
        return value


class EventCreate(Event):
    """Model for creating a new event."""

    pass


class EventGet(Event):
    """Model for retrieving an event, includes an ID."""

    id: UUID = Field(..., description="The unique identifier of the event", examples=["123e4567-e89b-12d3-a456-426614174000"])
    batch_id: UUID | None = Field(
        None, description="The unique identifier of the batch this event belongs to", examples=["123e4567-e89b-12d3-a456-426614174001"]
    )
    published_at: dt.datetime = Field(..., description="The timestamp when the event was published", examples=["2024-06-01T12:00:00Z"])
    normalized_message: str | None = Field(
        None,
        min_length=1,
        description="The normalized message of the event. This field will be non-empty only after the event has been processed.",
        examples=["user <email> login successful", "payment <ID> failed due to insufficient funds"],
    )
    fingerprint: str | None = Field(
        None,
        description="The fingerprint of the event used for grouping similar events. This field will be non-empty only after the event has been processed.",  # noqa: E501
        examples=["031edd7d41651593c5fe5c006fa5752b37fddff7bc4e843aa6af0c950f4b9406"],
    )
    incident_id: UUID | None = Field(
        None,
        description="The unique identifier of the incident this event is associated with (if any)",
        examples=["123e4567-e89b-12d3-a456-426614174002"],
    )
    received_at: dt.datetime | None = Field(
        None,
        description="The timestamp when the event was received for processing. This field will be non-empty only after the event has been processed.",
        examples=["2024-06-01T12:10:00Z"],
    )
    updated_at: dt.datetime | None = Field(None, description="The timestamp when the event was last updated.", examples=["2024-06-01T12:15:00Z"])
