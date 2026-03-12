import re
from typing import List, Optional
from urllib.parse import urlencode, urlparse, parse_qs, urljoin

from utils.http_client import HttpClient
from utils.html_parser import HtmlParser
from utils.logger import get_logger

logger = get_logger(__name__)

SOCIAL_DOMAINS = {
    "twitter.com", "x.com",
    "instagram.com",
    "tiktok.com",
    "youtube.com", "youtu.be",
    "reddit.com",
}


class SearchEngineScraper:
    """Scrapes search results from Bing and DuckDuckGo."""

    ENGINES = {
        "bing": {
            "url": "https://www.bing.com/search",
            "param": "q",
            "selector": "li.b_algo h2 a",
        },
        "duckduckgo": {
            "url": "https://html.duckduckgo.com/html/",
            "param": "q",
            "selector": "a.result__a",
        },
    }

    def __init__(self, engine: str = "bing", delay: float = 2.0, max_pages: int = 3):
        if engine not in self.ENGINES:
            raise ValueError(f"Unsupported engine '{engine}'. Choose from: {list(self.ENGINES)}")
        self.engine = engine
        self.max_pages = max_pages
        self._cfg = self.ENGINES[engine]
        self._client = HttpClient(delay=delay)

    def search(self, query: str, max_results: int = 10) -> List[str]:
        """Return a list of social media URLs matching the query."""
        urls = []
        page = 1

        while len(urls) < max_results:
            search_url = self._build_search_url(query, page)
            resp = self._client.get(search_url)
            if resp is None or resp.status_code != 200:
                logger.warning("Search failed for query '%s' on page %d", query, page)
                break

            new_links = self._extract_links(resp.text)
            if not new_links:
                break

            for link in new_links:
                cleaned = self._clean_url(link)
                if cleaned and self._is_social_media_url(cleaned):
                    if cleaned not in urls:
                        urls.append(cleaned)
                if len(urls) >= max_results:
                    break

            page += 1
            if page > self.max_pages:
                break

        logger.info("Query '%s' -> %d URLs", query, len(urls))
        return urls

    def _build_search_url(self, query: str, page: int = 1) -> str:
        """Build paginated search URL."""
        params = {self._cfg["param"]: query}
        if self.engine == "bing":
            params["first"] = (page - 1) * 10 + 1
        elif self.engine == "duckduckgo":
            if page > 1:
                params["s"] = (page - 1) * 30
        return f"{self._cfg['url']}?{urlencode(params)}"

    def _extract_links(self, html: str) -> List[str]:
        """Extract result links from search engine HTML."""
        parser = HtmlParser(html)
        links = []
        for element in parser.select_all(self._cfg["selector"]):
            href = element.get("href")
            if href:
                links.append(href)
        return links

    def _clean_url(self, url: str) -> Optional[str]:
        """Remove tracking parameters from a URL."""
        if not url or not url.startswith("http"):
            return None
        try:
            parsed = urlparse(url)
            clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            clean = clean.rstrip("/")
            return clean if clean else None
        except Exception:
            return None

    def _is_social_media_url(self, url: str) -> bool:
        """Return True if URL belongs to a known social media platform."""
        try:
            netloc = urlparse(url).netloc.lower().lstrip("www.")
            return any(netloc == d or netloc.endswith("." + d) for d in SOCIAL_DOMAINS)
        except Exception:
            return False

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
