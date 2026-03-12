import csv
import json
import os
from datetime import datetime, timezone
from typing import List, Optional

from utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_FIELDS = [
    "platform",
    "post_url",
    "username",
    "post_datetime",
    "caption",
    "location_tag",
    "location_type",
    "flame_visible",
    "ocean_visible",
    "smoke_visible",
    "media_type",
    "relevance_score",
    "relevance_decision",
    "extracted_at",
]


class DatasetWriter:
    """Writes collected post data to CSV and JSON files."""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def _generate_filename(self, prefix: str, extension: str) -> str:
        """Generate a timestamped filename."""
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return os.path.join(self.output_dir, f"{prefix}_{ts}.{extension}")

    def write_csv(
        self,
        data: List[dict],
        filename: Optional[str] = None,
        fields: List[str] = None,
    ) -> str:
        """Write data to a CSV file."""
        if not filename:
            filename = self._generate_filename("wildfire_dataset", "csv")
        if not fields:
            fields = DEFAULT_FIELDS

        os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
        with open(filename, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(data)

        logger.info("Wrote %d rows to CSV: %s", len(data), filename)
        return filename

    def write_json(
        self,
        data: List[dict],
        filename: Optional[str] = None,
        indent: int = 2,
    ) -> str:
        """Write data to a JSON file."""
        if not filename:
            filename = self._generate_filename("wildfire_dataset", "json")

        os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
        with open(filename, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=indent, ensure_ascii=False, default=str)

        logger.info("Wrote %d records to JSON: %s", len(data), filename)
        return filename

    def write_both(self, data: List[dict], prefix: str = "wildfire_dataset") -> dict:
        """Write data to both CSV and JSON files."""
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        csv_file = os.path.join(self.output_dir, f"{prefix}_{ts}.csv")
        json_file = os.path.join(self.output_dir, f"{prefix}_{ts}.json")
        self.write_csv(data, filename=csv_file)
        self.write_json(data, filename=json_file)
        return {"csv": csv_file, "json": json_file}

    def append_csv(self, data: List[dict], filename: str) -> str:
        """Append rows to an existing CSV file."""
        file_exists = os.path.isfile(filename)
        os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
        with open(filename, "a", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=DEFAULT_FIELDS, extrasaction="ignore")
            if not file_exists:
                writer.writeheader()
            writer.writerows(data)
        logger.info("Appended %d rows to %s", len(data), filename)
        return filename

    def generate_summary(self, data: List[dict]) -> dict:
        """Generate statistics from collected data."""
        by_platform = {}
        by_decision = {}
        by_media_type = {}
        by_location_type = {}
        score_distribution = {"high (>=8)": 0, "medium (6-7)": 0, "low (4-5)": 0}
        extraction_stats = {"success": 0, "failed": 0, "error": 0, "partial": 0}

        for post in data:
            platform = post.get("platform", "unknown")
            by_platform[platform] = by_platform.get(platform, 0) + 1

            decision = post.get("relevance_decision", "unknown")
            by_decision[decision] = by_decision.get(decision, 0) + 1

            media = post.get("media_type", "unknown") or "unknown"
            by_media_type[media] = by_media_type.get(media, 0) + 1

            loc_type = post.get("location_type", "unknown") or "unknown"
            by_location_type[loc_type] = by_location_type.get(loc_type, 0) + 1

            score = post.get("relevance_score", 0) or 0
            if score >= 8:
                score_distribution["high (>=8)"] += 1
            elif score >= 6:
                score_distribution["medium (6-7)"] += 1
            elif score >= 4:
                score_distribution["low (4-5)"] += 1

            status = post.get("extraction_status", "error") or "error"
            if status in extraction_stats:
                extraction_stats[status] += 1
            else:
                extraction_stats["error"] += 1

        return {
            "total_posts": len(data),
            "by_platform": by_platform,
            "by_decision": by_decision,
            "by_media_type": by_media_type,
            "by_location_type": by_location_type,
            "score_distribution": score_distribution,
            "extraction_stats": extraction_stats,
        }

    def write_summary(self, data: List[dict], filename: Optional[str] = None) -> str:
        """Write a summary JSON file."""
        if not filename:
            filename = self._generate_filename("summary", "json")
        summary = self.generate_summary(data)
        os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
        with open(filename, "w", encoding="utf-8") as fh:
            json.dump(summary, fh, indent=2)
        logger.info("Summary written to %s", filename)
        return filename
