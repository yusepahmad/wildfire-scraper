import time
from typing import Optional

import requests
from utils.logger import get_logger

logger = get_logger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Safari/605.1.15",
]


class HttpClient:
    """HTTP client with user agent rotation, retry mechanism, and rate limiting."""

    def __init__(self, delay: float = 1.5, timeout: int = 10, retries: int = 3):
        self.delay = delay
        self.timeout = timeout
        self.retries = retries
        self._agent_index = 0
        self._session = requests.Session()
        self._last_request_time = 0.0

    def _next_agent(self) -> str:
        agent = USER_AGENTS[self._agent_index % len(USER_AGENTS)]
        self._agent_index += 1
        return agent

    def _rate_limit(self):
        elapsed = time.time() - self._last_request_time
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self._last_request_time = time.time()

    def get(self, url: str, params: dict = None, headers: dict = None) -> Optional[requests.Response]:
        """Perform a GET request with retries and rate limiting."""
        self._rate_limit()

        default_headers = {
            "User-Agent": self._next_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        if headers:
            default_headers.update(headers)

        for attempt in range(1, self.retries + 1):
            try:
                resp = self._session.get(
                    url,
                    params=params,
                    headers=default_headers,
                    timeout=self.timeout,
                    allow_redirects=True,
                )
                logger.debug("GET %s -> %s", url, resp.status_code)
                return resp
            except requests.RequestException as exc:
                logger.warning("Attempt %d/%d failed for %s: %s", attempt, self.retries, url, exc)
                if attempt < self.retries:
                    time.sleep(2 * attempt)

        logger.error("All retries exhausted for %s", url)
        return None

    def close(self):
        """Close the underlying session."""
        self._session.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
