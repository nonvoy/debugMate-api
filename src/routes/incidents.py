from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.config.basic_config import get_config
from src.config.logger import get_logger
from src.routes.schemas.incidents import IncidentGet, IncidentQuery
from src.services.db.db_client import DBClient, get_db_client

config = get_config()
logger = get_logger(__name__)

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get(
    "/{incident_id}",
    responses={
        status.HTTP_200_OK: {"description": "Incident retrieved successfully", "model": IncidentGet},
        status.HTTP_404_NOT_FOUND: {"description": "Incident not found"},
    },
)
async def get_incident(incident_id: int, db_client: Annotated[DBClient, Depends(get_db_client)]) -> IncidentGet:
    """
    Retrieve an incident by its unique identifier.

    This endpoint allows you to retrieve detailed information about a specific incident using its unique ID.

    - **incident_id**: The unique identifier of the incident to retrieve.

    Returns the details of the requested incident, including its type, associated events, time frame, status, comments, and assignment information.
    """
    incident = db_client.get_incident_by_id(incident_id)
    if not incident:
        logger.warning(f"Incident with ID {incident_id} not found.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    return IncidentGet.model_validate(incident)


@router.get(
    "/",
    response_model=list[IncidentGet],
    status_code=status.HTTP_200_OK,
)
async def get_incidents(
    db_client: Annotated[DBClient, Depends(get_db_client)],
    query: Annotated[IncidentQuery, Query()],
) -> list[IncidentGet]:
    """
    Retrieve all incidents.

    This endpoint allows you to fetch a list of all incidents currently recorded in the system.

    Returns a list of incidents, each containing details such as type, associated events, time frame, status, comments, and assignment information.
    """
    incidents = db_client.get_incidents(query)
    return [IncidentGet.model_validate(incident) for incident in incidents]
