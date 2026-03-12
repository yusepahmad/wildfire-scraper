import json
import re
from typing import Optional

from extractors.base_extractor import BaseExtractor, PostData
from utils.html_parser import HtmlParser
from utils.logger import get_logger

logger = get_logger(__name__)


class InstagramExtractor(BaseExtractor):
    """Extracts post metadata from Instagram posts."""

    def get_platform_name(self) -> str:
        return "instagram"

    def extract(self, url: str) -> PostData:
        post = PostData(
            platform=self.get_platform_name(),
            post_url=url,
            extraction_status="failed",
            extracted_at=self._now_iso(),
        )

        html = self._fetch_html(url)
        if not html:
            logger.warning("Could not fetch Instagram URL: %s", url)
            return post

        parser = HtmlParser(html)

        caption = parser.get_meta_content("og:description")
        title = parser.get_meta_content("og:title") or ""
        media_type = self._detect_media_type(html)

        username = self._extract_username_from_url(url) or self._extract_username_from_title(title)

        if not caption:
            json_ld = parser.find_json_ld()
            if json_ld:
                caption = json_ld.get("description") or json_ld.get("caption")

        if not caption:
            caption = self._extract_from_shared_data(html)

        post.caption = caption
        post.username = username
        post.media_type = media_type
        post.extraction_status = "success" if caption else "partial"

        return post

    def _extract_username_from_title(self, title: str) -> Optional[str]:
        match = re.search(r"@([A-Za-z0-9_.]+)", title)
        if match:
            return match.group(1)
        return None

    def _extract_from_shared_data(self, html: str) -> Optional[str]:
        """Try to extract caption from window._sharedData."""
        match = re.search(r"window\._sharedData\s*=\s*({.*?});</script>", html, re.DOTALL)
        if not match:
            return None
        try:
            data = json.loads(match.group(1))
            media = (
                data.get("entry_data", {})
                .get("PostPage", [{}])[0]
                .get("graphql", {})
                .get("shortcode_media", {})
            )
            edges = media.get("edge_media_to_caption", {}).get("edges", [])
            if edges:
                return edges[0].get("node", {}).get("text")
        except (json.JSONDecodeError, IndexError, KeyError):
            pass
        return None
