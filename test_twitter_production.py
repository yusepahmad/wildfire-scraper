"""
Twitter Production Test Script
Tests the wildfire data collection pipeline specifically for Twitter/X.
"""

import argparse
import sys
import os

from utils.logger import setup_logger
from extractors.twitter_extractor import TwitterExtractor
from classifiers.relevance_classifier import RelevanceClassifier
from classifiers.location_classifier import LocationClassifier
from pipeline.search_pipeline import SearchPipeline
from pipeline.extraction_pipeline import ExtractionPipeline
from storage.dataset_writer import DatasetWriter

logger = setup_logger("twitter_test")

SAMPLE_TWITTER_URLS = [
    "https://twitter.com/firewatch_la/status/1877008837606093126",
    "https://twitter.com/malibu_news/status/1877012345678901234",
    "https://twitter.com/la_emergency/status/1877023456789012345",
    "https://twitter.com/socal_weather/status/1877034567890123456",
    "https://twitter.com/palisades_local/status/1877045678901234567",
]

TWITTER_QUERIES = [
    'site:twitter.com "Palisades Fire" video',
    'site:twitter.com "Pacific Palisades fire" footage',
    'site:twitter.com "Malibu fire" video',
    'site:twitter.com "Pacific Palisades" fire evacuation',
    'site:twitter.com Palisades fire flames',
    'site:x.com "Palisades Fire" smoke',
    'site:twitter.com "LA fire" January 2025 video',
]


def run_quick_test(config_dir: str = "config", output_dir: str = "output") -> None:
    """Quick test using a small set of sample URLs."""
    logger.info("=== Quick Twitter Test (sample URLs) ===")

    extractor = TwitterExtractor()
    relevance = RelevanceClassifier(config_dir=config_dir)
    location = LocationClassifier()
    results = []

    for i, url in enumerate(SAMPLE_TWITTER_URLS, 1):
        logger.info("[%d/%d] Extracting: %s", i, len(SAMPLE_TWITTER_URLS), url)
        try:
            post = extractor.extract(url)
            post_dict = post.to_dict()

            caption = post_dict.get("caption") or ""
            has_media = bool(post_dict.get("media_type"))
            classification = relevance.classify(caption, has_media)
            post_dict["relevance_score"] = classification["score"]
            post_dict["relevance_decision"] = classification["decision"]
            post_dict = location.enrich_post_data(post_dict)

            results.append(post_dict)
            logger.info(
                "  status=%s score=%d decision=%s",
                post_dict.get("extraction_status"),
                classification["score"],
                classification["decision"],
            )
        except Exception as exc:
            logger.error("  Error: %s", exc)

    extractor.close()
    _print_and_save(results, output_dir, prefix="twitter_quick_test")


def run_twitter_test(
    search_engine: str = "bing",
    config_dir: str = "config",
    output_dir: str = "output",
    max_results: int = 10,
) -> None:
    """Full Twitter pipeline test using search engine queries."""
    logger.info("=== Full Twitter Pipeline Test ===")
    logger.info("Search engine: %s", search_engine)

    from collectors.url_collector import UrlCollector
    from search.google_search import SearchEngineScraper

    all_urls = []
    seen = set()
    collector = UrlCollector()

    with SearchEngineScraper(engine=search_engine) as scraper:
        for i, query in enumerate(TWITTER_QUERIES, 1):
            logger.info("[%d/%d] Query: %s", i, len(TWITTER_QUERIES), query)
            try:
                urls = scraper.search(query, max_results=max_results)
                for url in urls:
                    norm = collector.normalize_url(url)
                    if norm and norm not in seen and collector.get_platform(norm) == "twitter":
                        seen.add(norm)
                        all_urls.append(norm)
            except Exception as exc:
                logger.error("Query failed: %s", exc)

    logger.info("Collected %d unique Twitter URLs", len(all_urls))

    if not all_urls:
        logger.warning("No URLs collected.")
        return

    with ExtractionPipeline(config_dir=config_dir) as pipeline:
        results = pipeline.run(all_urls, min_relevance_score=4)

    _print_and_save(results, output_dir, prefix="twitter_production_test")


def _print_and_save(results: list, output_dir: str, prefix: str) -> None:
    """Print stats and save results."""
    writer = DatasetWriter(output_dir=output_dir)

    print(f"\n=== Results: {len(results)} posts ===")
    for post in results:
        print(
            f"  [{post.get('relevance_decision', '?'):6s}] "
            f"score={post.get('relevance_score', 0):2d} "
            f"media={post.get('media_type', '?'):5s} "
            f"status={post.get('extraction_status', '?'):8s}  "
            f"{post.get('post_url', '')}"
        )

    if results:
        files = writer.write_both(results, prefix=prefix)
        summary_file = writer.write_summary(results)
        summary = writer.generate_summary(results)
        print(f"\nSummary: {summary}")
        print(f"CSV     : {files['csv']}")
        print(f"JSON    : {files['json']}")
        print(f"Summary : {summary_file}")
    else:
        print("No results to save.")


def main():
    parser = argparse.ArgumentParser(description="Twitter production test for wildfire scraper.")
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick test with sample URLs instead of live search",
    )
    parser.add_argument("--search-engine", default="bing", choices=["bing", "duckduckgo"])
    parser.add_argument("--config-dir", default="config")
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--max-results", type=int, default=10)
    args = parser.parse_args()

    if args.quick:
        run_quick_test(config_dir=args.config_dir, output_dir=args.output_dir)
    else:
        run_twitter_test(
            search_engine=args.search_engine,
            config_dir=args.config_dir,
            output_dir=args.output_dir,
            max_results=args.max_results,
        )


if __name__ == "__main__":
    main()
