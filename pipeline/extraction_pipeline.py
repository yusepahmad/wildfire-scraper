from typing import List, Optional
from urllib.parse import urlparse

from extractors.twitter_extractor import TwitterExtractor
from extractors.instagram_extractor import InstagramExtractor
from extractors.tiktok_extractor import TiktokExtractor
from extractors.youtube_extractor import YoutubeExtractor
from extractors.reddit_extractor import RedditExtractor
from classifiers.relevance_classifier import RelevanceClassifier
from classifiers.location_classifier import LocationClassifier
from utils.http_client import HttpClient
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


class ExtractionPipeline:
    """Orchestrates post extraction, relevance classification and location enrichment."""

    def __init__(self, config_dir: str = "config"):
        shared_client = HttpClient(delay=1.5)
        self._client = shared_client

        self._extractors = {
            "twitter": TwitterExtractor(client=shared_client),
            "instagram": InstagramExtractor(client=shared_client),
            "tiktok": TiktokExtractor(client=shared_client),
            "youtube": YoutubeExtractor(client=shared_client),
            "reddit": RedditExtractor(client=shared_client),
        }

        self._relevance = RelevanceClassifier(config_dir=config_dir)
        self._location = LocationClassifier()

    def _detect_platform(self, url: str) -> Optional[str]:
        try:
            netloc = urlparse(url).netloc.lower().lstrip("www.")
            for domain, platform in PLATFORM_MAP.items():
                if netloc == domain or netloc.endswith("." + domain):
                    return platform
        except Exception:
            pass
        return None

    def extract_post(self, url: str) -> Optional[dict]:
        """Extract a single post and return as dict."""
        platform = self._detect_platform(url)
        extractor = self._extractors.get(platform) if platform else None

        if not extractor:
            logger.warning("No extractor for URL: %s", url)
            return None

        try:
            post_data = extractor.extract(url)
            return post_data.to_dict()
        except Exception as exc:
            logger.error("Extraction failed for %s: %s", url, exc)
            return None

    def run(self, urls: List[str], min_relevance_score: int = 6) -> List[dict]:
        """Extract, classify and enrich all URLs, returning accepted posts."""
        results = []
        total = len(urls)

        for i, url in enumerate(urls, 1):
            logger.info("Extracting %d/%d: %s", i, total, url)
            post = self.extract_post(url)
            if post is None:
                continue

            caption = post.get("caption") or ""
            has_media = bool(post.get("media_type"))
            classification = self._relevance.classify(caption, has_media)
            post["relevance_score"] = classification["score"]
            post["relevance_decision"] = classification["decision"]

            post = self._location.enrich_post_data(post)

            if classification["score"] >= min_relevance_score:
                results.append(post)
                logger.info(
                    "Accepted (score=%d): %s", classification["score"], url
                )
            else:
                logger.debug(
                    "Rejected (score=%d): %s", classification["score"], url
                )

        logger.info(
            "Extraction complete: %d/%d posts accepted (min_score=%d)",
            len(results), total, min_relevance_score,
        )
        return results

    def close(self):
        """Close shared HTTP client."""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
