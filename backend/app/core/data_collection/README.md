# Data Collection Module

This module gathers raw source material for downstream preprocessing and training. It supports web and book-oriented scraping through a common scraper interface.

## Key Files

- `base.py`: Abstract scraper contract.
- `config.py`: Pydantic config models for data collection and scraper settings.
- `web_scraper.py`: Web search and page extraction implementation.
- `book_scraper.py`: Book/source collection implementation.
- `scraper_factory.py`: Factory for selecting a scraper implementation.
- `pipeline.py`: Pipeline wrapper for running collection jobs.

## Flow

1. A controller creates a data collection job with `DataCollectionConfig`.
2. The factory selects the correct scraper from the configured source.
3. The scraper collects raw documents and metadata.
4. Results are persisted under the configured raw data location.
5. The pipeline engine reports job progress and status.

## Extension Points

Add a new source by implementing the base scraper interface, registering it in `scraper_factory.py`, and adding any source-specific configuration to `config.py`.

## Operational Notes

Network collection should respect rate limits and timeouts from config. Scrapers should return structured records with content, metadata, source, and timestamp whenever possible so preprocessing does not need source-specific logic.
