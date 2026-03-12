import os
import yaml
from typing import List
from utils.logger import get_logger

logger = get_logger(__name__)


class QueryBuilder:
    """Builds search queries from YAML configuration files."""

    # Limits for cross-product queries to keep query count manageable
    MAX_EVENTS_FOR_LOCATION_QUERIES = 3
    MAX_LOCATIONS_FOR_EVENT_QUERIES = 5

    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self._keywords = self._load_yaml("keywords.yaml")
        self._locations = self._load_yaml("locations.yaml")
        self._platforms = self._load_yaml("platforms.yaml")

    def _load_yaml(self, filename: str) -> dict:
        path = os.path.join(self.config_dir, filename)
        try:
            with open(path, "r", encoding="utf-8") as fh:
                return yaml.safe_load(fh) or {}
        except FileNotFoundError:
            logger.warning("Config file not found: %s", path)
            return {}

    def get_platform_domains(self) -> List[str]:
        """Return list of enabled platform domains."""
        domains = []
        for name, cfg in self._platforms.get("platforms", {}).items():
            if cfg.get("enabled", False):
                domains.append(cfg["domain"])
        return domains

    def build_queries(self) -> List[str]:
        """Generate search queries for all enabled platforms."""
        queries = []
        for domain in self.get_platform_domains():
            queries.extend(self.build_queries_for_platform(domain))
        return queries

    def build_queries_for_platform(self, domain: str) -> List[str]:
        """Generate search queries for a specific platform domain."""
        queries = []
        event_names = self._keywords.get("event_names", [])
        media_keywords = self._keywords.get("media_keywords", [])
        locations = self._locations.get("locations", [])

        for event_name in event_names:
            for media_kw in media_keywords:
                queries.append(f'site:{domain} "{event_name}" {media_kw}')

        for location in locations:
            queries.append(f'site:{domain} "{location}" fire')

        for event_name in event_names[:self.MAX_EVENTS_FOR_LOCATION_QUERIES]:
            for location in locations[:self.MAX_LOCATIONS_FOR_EVENT_QUERIES]:
                queries.append(f'site:{domain} {event_name} {location}')

        return queries
