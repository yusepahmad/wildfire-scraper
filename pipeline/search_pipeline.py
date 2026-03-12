from typing import List, Optional

from search.query_builder import QueryBuilder
from collectors.url_collector import UrlCollector
from utils.logger import get_logger

logger = get_logger(__name__)


class SearchPipeline:
    """Orchestrates query building and URL collection."""

    def __init__(self, config_dir: str = "config"):
        self._query_builder = QueryBuilder(config_dir=config_dir)
        self._collector = UrlCollector()

    def run(
        self,
        search_engine: str = "bing",
        max_results_per_query: int = 10,
        max_queries: Optional[int] = None,
    ) -> List[str]:
        """Run the full search pipeline and return collected URLs."""
        queries = self._query_builder.build_queries()
        if max_queries:
            queries = queries[:max_queries]
        logger.info("Running %d queries on %s", len(queries), search_engine)
        return self._collector.collect_from_queries(
            queries,
            search_engine=search_engine,
            max_results_per_query=max_results_per_query,
        )

    def run_for_platform(
        self,
        platform: str,
        search_engine: str = "bing",
        max_results: int = 10,
    ) -> List[str]:
        """Run search pipeline for a specific platform."""
        domains = self._query_builder.get_platform_domains()
        matched = [d for d in domains if platform.lower() in d]
        if not matched:
            logger.warning("Platform '%s' not found in config", platform)
            return []

        all_urls = []
        for domain in matched:
            queries = self._query_builder.build_queries_for_platform(domain)
            urls = self._collector.collect_from_queries(
                queries,
                search_engine=search_engine,
                max_results_per_query=max_results,
            )
            all_urls.extend(urls)
        return all_urls
