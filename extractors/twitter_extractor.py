import re
from typing import Optional

from extractors.base_extractor import BaseExtractor, PostData
from utils.html_parser import HtmlParser
from utils.logger import get_logger

logger = get_logger(__name__)


class TwitterExtractor(BaseExtractor):
    """Extracts post metadata from Twitter/X posts."""

    def get_platform_name(self) -> str:
        return "twitter"

    def extract(self, url: str) -> PostData:
        post = PostData(
            platform=self.get_platform_name(),
            post_url=url,
            extraction_status="failed",
            extracted_at=self._now_iso(),
        )

        html = self._fetch_html(url)
        if not html:
            logger.warning("Could not fetch Twitter URL: %s", url)
            return post

        parser = HtmlParser(html)

        caption = parser.get_meta_content("og:description")
        title = parser.get_meta_content("og:title") or parser.get_title() or ""

        username = self._extract_username_from_title(title) or self._extract_username_from_url(url)
        media_type = self._detect_media_type(html)

        post.caption = caption
        post.username = username
        post.media_type = media_type
        post.extraction_status = "success" if caption else "partial"

        return post

    def _extract_username_from_title(self, title: str) -> Optional[str]:
        """Extract @username from title like 'Username (@handle) on X'."""
        match = re.search(r"\(@([^)]+)\)", title)
        if match:
            return match.group(1)
        return None
