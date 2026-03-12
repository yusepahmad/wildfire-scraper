"""
Wildfire Social Media Data Collection System
Main entry point for the collection pipeline.
"""

import argparse
import sys
import os

from utils.logger import setup_logger
from pipeline.search_pipeline import SearchPipeline
from pipeline.extraction_pipeline import ExtractionPipeline
from storage.dataset_writer import DatasetWriter

logger = setup_logger("wildfire_main")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Collect wildfire social media posts using search engine indexing."
    )
    parser.add_argument(
        "--config-dir",
        default="config",
        help="Path to the config directory (default: config)",
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Path to the output directory (default: output)",
    )
    parser.add_argument(
        "--search-engine",
        default="bing",
        choices=["bing", "duckduckgo"],
        help="Search engine to use (default: bing)",
    )
    parser.add_argument(
        "--max-queries",
        type=int,
        default=None,
        help="Maximum number of queries to run (default: all)",
    )
    parser.add_argument(
        "--min-score",
        type=int,
        default=6,
        help="Minimum relevance score to include a post (default: 6)",
    )
    parser.add_argument(
        "--platform",
        default=None,
        help="Collect from a specific platform only (e.g. twitter, instagram)",
    )
    return parser


def run_full_pipeline(args: argparse.Namespace) -> None:
    """Execute the complete search -> extract -> save pipeline."""
    logger.info("=== Wildfire Social Media Data Collection ===")
    logger.info("Search engine : %s", args.search_engine)
    logger.info("Config dir    : %s", args.config_dir)
    logger.info("Output dir    : %s", args.output_dir)
    logger.info("Min score     : %d", args.min_score)
    if args.platform:
        logger.info("Platform      : %s", args.platform)
    if args.max_queries:
        logger.info("Max queries   : %d", args.max_queries)

    # --- Search & collect URLs ---
    search_pipeline = SearchPipeline(config_dir=args.config_dir)

    if args.platform:
        urls = search_pipeline.run_for_platform(
            platform=args.platform,
            search_engine=args.search_engine,
        )
    else:
        urls = search_pipeline.run(
            search_engine=args.search_engine,
            max_queries=args.max_queries,
        )

    logger.info("Collected %d unique URLs", len(urls))

    if not urls:
        logger.warning("No URLs collected. Exiting.")
        return

    # --- Extract & classify posts ---
    with ExtractionPipeline(config_dir=args.config_dir) as extraction_pipeline:
        posts = extraction_pipeline.run(urls, min_relevance_score=args.min_score)

    logger.info("Accepted %d posts", len(posts))

    if not posts:
        logger.warning("No posts passed the relevance filter. Exiting.")
        return

    # --- Write output files ---
    writer = DatasetWriter(output_dir=args.output_dir)
    files = writer.write_both(posts)
    summary_file = writer.write_summary(posts)

    # --- Print summary ---
    summary = writer.generate_summary(posts)
    print("\n=== Collection Summary ===")
    print(f"Total posts     : {summary['total_posts']}")
    print(f"By platform     : {summary['by_platform']}")
    print(f"By media type   : {summary['by_media_type']}")
    print(f"By decision     : {summary['by_decision']}")
    print(f"Score dist.     : {summary['score_distribution']}")
    print(f"\nCSV  : {files['csv']}")
    print(f"JSON : {files['json']}")
    print(f"Summary : {summary_file}")


def main():
    parser = build_arg_parser()
    args = parser.parse_args()
    run_full_pipeline(args)


if __name__ == "__main__":
    main()
