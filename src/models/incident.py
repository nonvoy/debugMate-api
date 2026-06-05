import datetime as dt
from uuid import UUID

from pydantic import PositiveInt
from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel

from src.routes.schemas.incidents import IncidentStatus


class Incident(SQLModel, table=True):
    """SQLModel table definition for incidents (read-only in this service)."""

    __tablename__ = "incidents"

    id: PositiveInt | None = Field(default=None, primary_key=True)
    type: str = Field(..., nullable=False)
    fingerprint: str | None = Field(None, nullable=True)
    environment: str = Field(..., nullable=False)
    service: str = Field(..., nullable=False)
    start_time: dt.datetime = Field(..., sa_column=Column(DateTime(timezone=True), nullable=False))
    end_time: dt.datetime = Field(..., sa_column=Column(DateTime(timezone=True), nullable=False))
    status: IncidentStatus = Field(..., nullable=False)
    comment: str | None = Field(None, nullable=True)
    assigned_to: str | None = Field(None, nullable=True)
    created_at: dt.datetime = Field(..., sa_column=Column(DateTime(timezone=True), nullable=False))
    updated_at: dt.datetime = Field(..., sa_column=Column(DateTime(timezone=True), nullable=False))


class EventsInIncident(SQLModel, table=True):
    """SQLModel table definition for the event-incident relationship (read-only in this service)."""

    __tablename__ = "events_in_incidents"

    event_id: UUID = Field(..., primary_key=True, nullable=False)
    incident_id: PositiveInt = Field(..., foreign_key="incidents.id", nullable=False)
    associated_at: dt.datetime = Field(..., sa_column=Column(DateTime(timezone=True), nullable=False))
