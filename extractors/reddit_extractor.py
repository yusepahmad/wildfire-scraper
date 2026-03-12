import re
from typing import Optional

from extractors.base_extractor import BaseExtractor, PostData
from utils.http_client import HttpClient
from utils.html_parser import HtmlParser
from utils.logger import get_logger

logger = get_logger(__name__)


class RedditExtractor(BaseExtractor):
    """Extracts post metadata from Reddit posts."""

    def get_platform_name(self) -> str:
        return "reddit"

    def extract(self, url: str) -> PostData:
        post = PostData(
            platform=self.get_platform_name(),
            post_url=url,
            extraction_status="failed",
            extracted_at=self._now_iso(),
        )

        json_url = self._to_json_url(url)
        if json_url:
            data = self._fetch_json(json_url)
            if data:
                return self._parse_json(post, data)

        return self._parse_html(post, url)

    def _to_json_url(self, url: str) -> Optional[str]:
        """Convert a Reddit post URL to its JSON API endpoint."""
        clean = url.rstrip("/")
        if not clean.endswith(".json"):
            return clean + ".json"
        return clean

    def _fetch_json(self, url: str) -> Optional[list]:
        resp = self._client.get(url, headers={"Accept": "application/json"})
        if resp and resp.status_code == 200:
            try:
                return resp.json()
            except Exception:
                pass
        return None

    def _parse_json(self, post: PostData, data: list) -> PostData:
        """Parse Reddit JSON API response."""
        try:
            listing = data[0]["data"]["children"]
            if not listing:
                return post
            item = listing[0]["data"]

            post.caption = item.get("title")
            post.username = item.get("author")
            post.location_tag = item.get("subreddit_name_prefixed")

            created_utc = item.get("created_utc")
            if created_utc:
                from datetime import datetime, timezone
                post.post_datetime = datetime.fromtimestamp(
                    float(created_utc), tz=timezone.utc
                ).strftime("%Y-%m-%dT%H:%M:%S")

            is_video = item.get("is_video", False)
            post.media_type = "video" if is_video else "image"
            post.extraction_status = "success"
        except (KeyError, IndexError, TypeError) as exc:
            logger.warning("Reddit JSON parse error: %s", exc)

        return post

    def _parse_html(self, post: PostData, url: str) -> PostData:
        """Fallback HTML parsing for Reddit posts."""
        html = self._fetch_html(url)
        if not html:
            return post

        parser = HtmlParser(html)
        post.caption = parser.get_meta_content("og:title") or parser.get_meta_content("og:description")
        subreddit_match = re.search(r"reddit\.com/r/([^/]+)", url)
        if subreddit_match:
            post.location_tag = f"r/{subreddit_match.group(1)}"
        post.username = self._extract_username_from_url(url)
        post.media_type = self._detect_media_type(html)
        post.extraction_status = "partial" if post.caption else "failed"

        return post
