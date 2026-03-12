from extractors.base_extractor import BaseExtractor, PostData
from utils.html_parser import HtmlParser
from utils.logger import get_logger

logger = get_logger(__name__)


class YoutubeExtractor(BaseExtractor):
    """Extracts post metadata from YouTube videos."""

    def get_platform_name(self) -> str:
        return "youtube"

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
            logger.warning("Could not fetch YouTube URL: %s", url)
            return post

        parser = HtmlParser(html)

        title = parser.get_meta_content("og:title") or parser.get_title() or ""
        description = parser.get_meta_content("og:description") or ""
        caption = f"{title} {description}".strip() if title or description else None

        channel_tag = parser.select_one('span[itemprop="author"] link[itemprop="name"]')
        channel_name = None
        if channel_tag:
            channel_name = channel_tag.get("content")

        if not channel_name:
            json_ld = parser.find_json_ld()
            if json_ld:
                channel_name = (
                    json_ld.get("author", {}).get("name")
                    if isinstance(json_ld.get("author"), dict)
                    else None
                )
                if not post.post_datetime:
                    post.post_datetime = json_ld.get("uploadDate") or json_ld.get("datePublished")

        post.caption = caption if caption else None
        post.username = channel_name
        post.extraction_status = "success" if caption else "partial"

        return post
