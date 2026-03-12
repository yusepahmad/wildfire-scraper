import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from utils.http_client import HttpClient
from utils.html_parser import HtmlParser
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PostData:
    platform: str
    post_url: str
    username: Optional[str] = None
    post_datetime: Optional[str] = None
    caption: Optional[str] = None
    location_tag: Optional[str] = None
    flame_visible: Optional[bool] = None
    ocean_visible: Optional[bool] = None
    media_type: Optional[str] = None
    relevance_score: int = 0
    extraction_status: str = "pending"
    extracted_at: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "platform": self.platform,
            "post_url": self.post_url,
            "username": self.username,
            "post_datetime": self.post_datetime,
            "caption": self.caption,
            "location_tag": self.location_tag,
            "flame_visible": self.flame_visible,
            "ocean_visible": self.ocean_visible,
            "media_type": self.media_type,
            "relevance_score": self.relevance_score,
            "extraction_status": self.extraction_status,
            "extracted_at": self.extracted_at,
        }


class BaseExtractor(ABC):
    """Abstract base class for platform-specific post extractors."""

    def __init__(self, client: HttpClient = None):
        self._client = client or HttpClient(delay=1.5)
        self._owns_client = client is None

    @abstractmethod
    def extract(self, url: str) -> PostData:
        """Extract post data from the given URL."""

    @abstractmethod
    def get_platform_name(self) -> str:
        """Return the platform name."""

    def _fetch_html(self, url: str) -> Optional[str]:
        resp = self._client.get(url)
        if resp and resp.status_code == 200:
            return resp.text
        return None

    def _detect_media_type(self, html: str) -> str:
        """Detect whether the post contains video or image."""
        parser = HtmlParser(html)
        if parser.get_meta_content("og:video") or parser.get_meta_content("og:video:url"):
            return "video"
        og_type = parser.get_meta_content("og:type") or ""
        if "video" in og_type.lower():
            return "video"
        return "image"

    def _extract_username_from_url(self, url: str) -> Optional[str]:
        """Extract username from a social media URL using regex patterns."""
        patterns = [
            r"twitter\.com/([^/]+)/status/",
            r"x\.com/([^/]+)/status/",
            r"instagram\.com/([^/]+)/",
            r"tiktok\.com/@([^/]+)",
            r"youtube\.com/(?:c|channel|user)/([^/]+)",
            r"reddit\.com/u(?:ser)?/([^/]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    def close(self):
        if self._owns_client:
            self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
