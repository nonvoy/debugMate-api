import datetime as dt
from functools import lru_cache
from uuid import UUID

from pydantic import PositiveInt
from sqlalchemy import Column, DateTime
from sqlmodel import Field, Session, SQLModel, create_engine, select

from src.config.basic_config import get_config
from src.config.logger import get_logger

config = get_config()
logger = get_logger(__name__)


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
    status: str = Field(..., nullable=False)
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


class DBClient:
    """Singleton class to manage database read operations."""

    def __init__(self):
        self.engine = create_engine(config.db_url)

    def get_incident_by_id(self, incident_id: int) -> Incident | None:
        """Returns the incident with the given ID, or None if not found."""
        with Session(self.engine) as session:
            return session.get(Incident, incident_id)

    def get_incidents(self) -> list[Incident]:
        """Returns all incidents."""
        with Session(self.engine) as session:
            return list(session.exec(select(Incident)).all())

    def get_incident_id_for_event(self, event_id: UUID) -> int | None:
        """Returns the incident ID associated with the given event ID, or None if not found."""
        with Session(self.engine) as session:
            result = session.exec(select(EventsInIncident.incident_id).where(EventsInIncident.event_id == event_id)).first()
            return result


@lru_cache()
def get_db_client() -> DBClient:
    """Returns a singleton instance of the DBClient."""
    return DBClient()
