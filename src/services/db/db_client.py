from functools import lru_cache
from uuid import UUID

from pydantic import PositiveInt
from sqlmodel import Session, create_engine, select

from src.config.basic_config import get_config
from src.config.logger import get_logger
from src.models.incident import EventsInIncident, Incident
from src.routes.schemas.incidents import IncidentQuery

config = get_config()
logger = get_logger(__name__)


class DBClient:
    """Singleton class to manage database read operations."""

    def __init__(self):
        self.engine = create_engine(config.db_url)

    def get_incident_by_id(self, incident_id: PositiveInt) -> Incident | None:
        """Returns the incident with the given ID, or None if not found."""
        with Session(self.engine) as session:
            return session.get(Incident, incident_id)

    def get_incidents(self, query: IncidentQuery) -> list[Incident]:
        """Returns incidents matching the provided query."""
        statement = select(Incident)
        if query.service is not None:
            statement = statement.where(Incident.service == query.service)
        if query.environment is not None:
            statement = statement.where(Incident.environment == query.environment)
        if query.status is not None:
            statement = statement.where(Incident.status == query.status)
        if query.start_time_from is not None:
            statement = statement.where(Incident.start_time >= query.start_time_from)
        if query.start_time_to is not None:
            statement = statement.where(Incident.start_time <= query.start_time_to)

        with Session(self.engine) as session:
            return list(session.exec(statement).all())

    def get_incident_id_for_event(self, event_id: UUID) -> PositiveInt | None:
        """Returns the incident ID associated with the given event ID, or None if not found."""
        with Session(self.engine) as session:
            result = session.exec(select(EventsInIncident.incident_id).where(EventsInIncident.event_id == event_id)).first()
            return result


@lru_cache()
def get_db_client() -> DBClient:
    """Returns a singleton instance of the DBClient."""
    return DBClient()
