import re
from typing import Optional
from utils.logger import get_logger

logger = get_logger(__name__)

LOCATION_PATTERNS = {
    "highway": [
        r"\bPCH\b", r"Pacific Coast Highway", r"highway", r"freeway", r"road", r"Sunset Boulevard",
    ],
    "beach": [
        r"beach", r"shore", r"coast", r"ocean front", r"Malibu\s+beach",
    ],
    "hillside": [
        r"Topanga", r"canyon", r"hillside", r"mountain", r"Santa Monica Mountains",
        r"Temescal", r"ridge",
    ],
    "residential": [
        r"Pacific Palisades", r"Brentwood", r"neighborhood", r"homes?", r"houses?",
        r"street", r"residential",
    ],
    "landmark": [
        r"Getty Villa", r"Pepperdine", r"Will Rogers", r"park", r"landmark",
    ],
}

SPECIFIC_LOCATIONS = {
    r"\bPCH\b": "Pacific Coast Highway",
    r"Pacific Coast Highway": "Pacific Coast Highway",
    r"Sunset\s+Boulevard": "Sunset Boulevard",
    r"Pacific\s+Palisades": "Pacific Palisades",
    r"Malibu": "Malibu",
    r"Topanga\s+Canyon": "Topanga Canyon",
    r"Topanga": "Topanga Canyon",
    r"Santa\s+Monica\s+Mountains": "Santa Monica Mountains",
    r"Temescal\s+Canyon": "Temescal Canyon",
    r"Brentwood": "Brentwood",
    r"Santa\s+Monica\b": "Santa Monica",
    r"Calabasas": "Calabasas",
    r"Will\s+Rogers\s+State\s+Park": "Will Rogers State Park",
    r"Getty\s+Villa": "Getty Villa",
    r"Pepperdine": "Pepperdine",
}


class LocationClassifier:
    """Classifies location information from post text."""

    def detect_location_type(self, text: str) -> str:
        """Detect the general location type (highway, beach, hillside, etc.)."""
        if not text:
            return "unknown"
        for loc_type, patterns in LOCATION_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return loc_type
        return "unknown"

    def detect_specific_location(self, text: str) -> Optional[str]:
        """Detect a specific named location."""
        if not text:
            return None
        for pattern, name in SPECIFIC_LOCATIONS.items():
            if re.search(pattern, text, re.IGNORECASE):
                return name
        return None

    def classify(self, text: str) -> dict:
        """Return location_type, specific_location, and confidence."""
        loc_type = self.detect_location_type(text)
        specific = self.detect_specific_location(text)
        confidence = "high" if specific else ("medium" if loc_type != "unknown" else "low")
        return {
            "location_type": loc_type,
            "specific_location": specific,
            "confidence": confidence,
        }

    def detect_visual_elements(self, text: str) -> dict:
        """Detect flame, ocean, and smoke mentions in text."""
        if not text:
            text = ""
        text_lower = text.lower()
        return {
            "flame_visible": bool(re.search(r"flame|fire|burning|blaze", text_lower)),
            "ocean_visible": bool(re.search(r"ocean|sea|beach|water|coast|malibu", text_lower)),
            "smoke_visible": bool(re.search(r"smoke|haze|ash|plume", text_lower)),
        }

    def enrich_post_data(self, post: dict) -> dict:
        """Add location and visual element fields to a post dict."""
        text = post.get("caption") or ""
        location_result = self.classify(text)
        visual = self.detect_visual_elements(text)

        if not post.get("location_tag"):
            post["location_tag"] = location_result.get("specific_location")
        post["location_type"] = location_result.get("location_type", "unknown")
        post.setdefault("flame_visible", visual["flame_visible"])
        post.setdefault("ocean_visible", visual["ocean_visible"])
        post.setdefault("smoke_visible", visual["smoke_visible"])

        return post
