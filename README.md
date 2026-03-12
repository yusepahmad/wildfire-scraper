# Wildfire Social Media Data Collection System

A Python system to collect **public social media posts containing photos/videos** related to the **Palisades Fire (January 7, 2025)** using search engine indexing — no platform authentication required.

Output is a **structured dataset (CSV/JSON)** containing post metadata and relevance classification.

---

## Pipeline Architecture

```
Search Query Builder
        │
        ▼
Search Engine Scraper (Bing / DuckDuckGo)
        │
        ▼
URL Normalizer
        │
        ▼
Post Extractor (per-platform)
        │
        ▼
Relevance Classifier
        │
        ▼
Dataset Builder (CSV + JSON)
```

| Stage           | Description                                  |
|-----------------|----------------------------------------------|
| Query Builder   | Generates keyword combination queries        |
| Search Scraper  | Fetches result URLs from search engines      |
| URL Normalizer  | Cleans tracking parameters from URLs         |
| Post Extractor  | Retrieves metadata from individual posts     |
| Classifier      | Scores posts for wildfire relevance          |
| Dataset Builder | Saves results to CSV/JSON                    |

---

## Project Structure

```
wildfire-scraper/
├── config/
│   ├── __init__.py
│   ├── keywords.yaml
│   ├── locations.yaml
│   └── platforms.yaml
├── search/
│   ├── __init__.py
│   ├── query_builder.py
│   └── google_search.py
├── collectors/
│   ├── __init__.py
│   └── url_collector.py
├── extractors/
│   ├── __init__.py
│   ├── base_extractor.py
│   ├── twitter_extractor.py
│   ├── instagram_extractor.py
│   ├── tiktok_extractor.py
│   ├── youtube_extractor.py
│   └── reddit_extractor.py
├── classifiers/
│   ├── __init__.py
│   ├── relevance_classifier.py
│   └── location_classifier.py
├── pipeline/
│   ├── __init__.py
│   ├── search_pipeline.py
│   └── extraction_pipeline.py
├── storage/
│   ├── __init__.py
│   └── dataset_writer.py
├── utils/
│   ├── __init__.py
│   ├── http_client.py
│   ├── html_parser.py
│   └── logger.py
├── output/
│   └── example/
│       ├── wildfire_dataset_example.csv
│       ├── wildfire_dataset_example.json
│       └── summary_example.json
├── logs/
│   └── .gitkeep
├── main.py
├── test_twitter_production.py
└── requirements.txt
```

---

## Installation

```bash
pip install -r requirements.txt
```

---

## Usage

### Full pipeline (all platforms)

```bash
python main.py
```

### Specify search engine

```bash
python main.py --search-engine duckduckgo
```

### Specific platform only

```bash
python main.py --platform twitter
python main.py --platform instagram
```

### Limit number of queries

```bash
python main.py --max-queries 20
```

### Custom output directory

```bash
python main.py --output-dir my_output
```

### All options

```
usage: main.py [-h] [--config-dir CONFIG_DIR] [--output-dir OUTPUT_DIR]
               [--search-engine {bing,duckduckgo}] [--max-queries MAX_QUERIES]
               [--min-score MIN_SCORE] [--platform PLATFORM]

Options:
  --config-dir    Config directory (default: config)
  --output-dir    Output directory (default: output)
  --search-engine Search engine: bing or duckduckgo (default: bing)
  --max-queries   Limit number of search queries (default: all)
  --min-score     Minimum relevance score to include post (default: 6)
  --platform      Collect from a specific platform only
```

### Twitter production test

```bash
# Full test with live search
python test_twitter_production.py

# Quick test with sample URLs
python test_twitter_production.py --quick
```

---

## Output Format

| Field              | Description                              |
|--------------------|------------------------------------------|
| `platform`         | Social media platform name               |
| `post_url`         | Direct URL to the post                   |
| `username`         | Post author username                     |
| `post_datetime`    | Post creation timestamp (ISO 8601)       |
| `caption`          | Post text/description                    |
| `location_tag`     | Specific location detected               |
| `location_type`    | Location category (beach, highway, etc.) |
| `flame_visible`    | Whether flames are mentioned             |
| `ocean_visible`    | Whether ocean/coast is mentioned         |
| `smoke_visible`    | Whether smoke is mentioned               |
| `media_type`       | `video` or `image`                       |
| `relevance_score`  | Numeric relevance score                  |
| `relevance_decision` | `accept`, `review`, or `reject`        |
| `extracted_at`     | Extraction timestamp (ISO 8601)          |

---

## Relevance Scoring Rules

| Feature              | Score |
|----------------------|-------|
| Event name match     | +5    |
| Location keyword     | +3    |
| Fire keyword (max 2) | +2 ea |
| Media present        | +2    |

### Acceptance Thresholds

| Score | Decision |
|-------|----------|
| ≥ 6   | accept   |
| 4–5   | review   |
| < 4   | reject   |

---

## Target Output

| Platform  | Estimated Posts |
|-----------|-----------------|
| Twitter   | 150             |
| TikTok    | 120             |
| Instagram | 80              |
| YouTube   | 50              |
| Reddit    | 30              |
| **Total** | **~200–500**    |
