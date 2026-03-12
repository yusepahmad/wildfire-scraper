import os
import yaml
from typing import List, Optional
from utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_EVENT_NAMES = [
    "Palisades Fire", "Pacific Palisades fire", "Malibu fire",
    "Topanga fire", "LA fire", "Los Angeles wildfire",
]
DEFAULT_LOCATIONS = [
    "Pacific Palisades", "Malibu", "Topanga Canyon", "Pacific Coast Highway",
    "PCH", "Sunset Boulevard", "Santa Monica Mountains", "Temescal Canyon",
    "Brentwood", "Santa Monica", "Calabasas", "Will Rogers State Park",
    "Getty Villa", "Pepperdine",
]
DEFAULT_EVENT_KEYWORDS = [
    "fire", "wildfire", "smoke", "flames", "burning",
    "evacuation", "emergency", "destroyed", "ash",
]
DEFAULT_MEDIA_KEYWORDS = [
    "video", "photo", "footage", "pics", "images", "captured", "recorded",
]


class RelevanceClassifier:
    """Scores and classifies posts based on relevance to the wildfire event."""

    def __init__(self, config_dir: str = "config"):
        self._event_names = DEFAULT_EVENT_NAMES
        self._locations = DEFAULT_LOCATIONS
        self._event_keywords = DEFAULT_EVENT_KEYWORDS
        self._media_keywords = DEFAULT_MEDIA_KEYWORDS
        self._load_config(config_dir)

    def _load_config(self, config_dir: str):
        keywords_path = os.path.join(config_dir, "keywords.yaml")
        locations_path = os.path.join(config_dir, "locations.yaml")
        try:
            with open(keywords_path, "r", encoding="utf-8") as fh:
                kw = yaml.safe_load(fh) or {}
            self._event_names = kw.get("event_names", self._event_names)
            self._event_keywords = kw.get("event_keywords", self._event_keywords)
            self._media_keywords = kw.get("media_keywords", self._media_keywords)
        except FileNotFoundError:
            logger.warning("keywords.yaml not found, using defaults")
        try:
            with open(locations_path, "r", encoding="utf-8") as fh:
                loc = yaml.safe_load(fh) or {}
            self._locations = loc.get("locations", self._locations)
        except FileNotFoundError:
            logger.warning("locations.yaml not found, using defaults")

    def classify(self, text: str, has_media: bool = False) -> dict:
        """Classify a text and return score, decision, and matched terms."""
        if not text:
            text = ""
        text_lower = text.lower()
        score = 0
        matched_terms = []
        breakdown = {}

        for name in self._event_names:
            if name.lower() in text_lower:
                score += 5
                matched_terms.append(name)
        breakdown["event_name"] = score

        loc_score = 0
        for loc in self._locations:
            if loc.lower() in text_lower:
                loc_score += 3
                matched_terms.append(loc)
        score += loc_score
        breakdown["location"] = loc_score

        kw_score = 0
        for kw in self._event_keywords:
            if kw.lower() in text_lower:
                kw_score = min(kw_score + 2, 4)
                matched_terms.append(kw)
        score += kw_score
        breakdown["event_keyword"] = kw_score

        media_score = 2 if has_media else 0
        score += media_score
        breakdown["media_present"] = media_score

        if score >= 6:
            decision = "accept"
        elif score >= 4:
            decision = "review"
        else:
            decision = "reject"

        return {
            "score": score,
            "decision": decision,
            "breakdown": breakdown,
            "matched_terms": list(set(matched_terms)),
        }

    def batch_classify(self, posts: List[dict]) -> List[dict]:
        """Classify a list of post dicts."""
        for post in posts:
            text = post.get("caption") or ""
            has_media = bool(post.get("media_type"))
            result = self.classify(text, has_media)
            post["relevance_score"] = result["score"]
            post["relevance_decision"] = result["decision"]
        return posts

    def filter_accepted(self, posts: List[dict]) -> List[dict]:
        """Return only posts with decision 'accept'."""
        return [p for p in posts if p.get("relevance_decision") == "accept"]
