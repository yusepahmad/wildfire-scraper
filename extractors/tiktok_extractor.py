import json
import re
from typing import Optional

from extractors.base_extractor import BaseExtractor, PostData
from utils.html_parser import HtmlParser
from utils.logger import get_logger

logger = get_logger(__name__)


class TiktokExtractor(BaseExtractor):
    """Extracts post metadata from TikTok posts."""

    def get_platform_name(self) -> str:
        return "tiktok"

    def extract(self, url: str) -> PostData:
        post = PostData(
            platform=self.get_platform_name(),
            post_url=url,
            media_type="video",
            extraction_status="failed",
            extracted_at=self._now_iso(),
        )

        html = self._fetch_html(url)
        if not html:
            logger.warning("Could not fetch TikTok URL: %s", url)
            return post

        parser = HtmlParser(html)

        caption = parser.get_meta_content("og:description") or parser.get_meta_content("og:title")
        username = self._extract_username_from_url(url) or self._extract_tiktok_username(html)

        if not caption:
            caption = self._extract_from_sigi_state(html)

        post.caption = caption
        post.username = username
        post.extraction_status = "success" if caption else "partial"

        return post

    def _extract_tiktok_username(self, html: str) -> Optional[str]:
        match = re.search(r'"uniqueId"\s*:\s*"([^"]+)"', html)
        if match:
            return match.group(1)
        return None

    def _extract_from_sigi_state(self, html: str) -> Optional[str]:
        """Try to extract caption from SIGI_STATE script data."""
        match = re.search(r'<script\s+id="SIGI_STATE"[^>]*>(.*?)</script>', html, re.DOTALL)
        if not match:
            return None
        try:
            data = json.loads(match.group(1))
            item_module = data.get("ItemModule", {})
            for item_id, item in item_module.items():
                desc = item.get("desc")
                if desc:
                    return desc
        except (json.JSONDecodeError, AttributeError):
            pass
        return None
