from typing import List, Optional
from urllib.parse import urlparse

from search.google_search import SearchEngineScraper
from utils.logger import get_logger

logger = get_logger(__name__)

PLATFORM_MAP = {
    "twitter.com": "twitter",
    "x.com": "twitter",
    "instagram.com": "instagram",
    "tiktok.com": "tiktok",
    "youtube.com": "youtube",
    "youtu.be": "youtube",
    "reddit.com": "reddit",
}


class UrlCollector:
    """Collects and normalizes social media URLs from search engine results."""

    def collect_from_queries(
        self,
        queries: List[str],
        search_engine: str = "bing",
        max_results_per_query: int = 10,
    ) -> List[str]:
        """Collect URLs by running all queries against the given search engine."""
        all_urls = []
        seen = set()

        with SearchEngineScraper(engine=search_engine) as scraper:
            for i, query in enumerate(queries, 1):
                logger.info("Running query %d/%d: %s", i, len(queries), query)
                try:
                    raw_urls = scraper.search(query, max_results=max_results_per_query)
                    for url in raw_urls:
                        normalized = self.normalize_url(url)
                        if normalized and normalized not in seen:
                            seen.add(normalized)
                            all_urls.append(normalized)
                except Exception as exc:
                    logger.error("Query failed '%s': %s", query, exc)

        logger.info("Collected %d unique URLs from %d queries", len(all_urls), len(queries))
        return all_urls

    def normalize_url(self, url: str) -> Optional[str]:
        """Remove query parameters and normalize the URL."""
        if not url:
            return None
        try:
            parsed = urlparse(url)
            clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")
            clean = self._platform_normalize(clean)
            return clean
        except Exception:
            return None

    def _platform_normalize(self, url: str) -> str:
        """Apply platform-specific URL normalizations."""
        url = url.replace("//x.com/", "//twitter.com/")
        url = url.replace("//www.x.com/", "//twitter.com/")

        if "//youtu.be/" in url:
            video_id = url.split("//youtu.be/")[-1].split("/")[0]
            url = f"https://www.youtube.com/watch?v={video_id}"

        return url

    def filter_by_platform(self, urls: List[str], platform: str) -> List[str]:
        """Return only URLs belonging to the specified platform."""
        return [u for u in urls if self.get_platform(u) == platform.lower()]

    def get_platform(self, url: str) -> Optional[str]:
        """Detect the social media platform from a URL."""
        try:
            netloc = urlparse(url).netloc.lower().lstrip("www.")
            for domain, platform in PLATFORM_MAP.items():
                if netloc == domain or netloc.endswith("." + domain):
                    return platform
        except Exception:
            pass
        return None
