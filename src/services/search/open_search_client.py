from functools import lru_cache

from opensearchpy import OpenSearch

from src.config.basic_config import get_config
from src.config.logger import get_logger

config = get_config()
logger = get_logger(__name__)


EVENTS_INDEX = "debugmate-events"
INCIDENTS_INDEX = "debugmate-incidents"


class OpenSearchClient:
    """Singleton class to manage OpenSearch client instance."""

    def __init__(self):
        http_auth = None
        if config.opensearch.username and config.opensearch.password:
            http_auth = (
                config.opensearch.username,
                config.opensearch.password,
            )
        self.__client = OpenSearch(
            hosts=[config.opensearch.url],
            http_compress=config.opensearch.http_compress,
            verify_certs=config.opensearch.verify_certs,
            timeout=config.opensearch.timeout,
            max_retries=config.opensearch.max_retries,
            retry_on_timeout=config.opensearch.retry_on_timeout,
            http_auth=http_auth,
        )


@lru_cache()
def get_opensearch_client() -> OpenSearchClient:
    """Initializes OpenSearch client and creates required indexes. Returns the initialized client."""
    return OpenSearchClient()
