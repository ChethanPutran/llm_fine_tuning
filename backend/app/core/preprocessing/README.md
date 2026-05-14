# Preprocessing Module

This module transforms raw collected data into clean, deduplicated, training-ready records.

## Key Files

- `base.py`: Base processor interface.
- `config.py`: Preprocessing configuration such as cleaning method, dedup threshold, entity extraction, text normalization, and output format.
- `pipeline.py`: End-to-end preprocessing pipeline.
- `deduplicator.py`: Duplicate and near-duplicate removal helpers.
- `knowledge_extractor.py`: Entity and keyword extraction helpers.
- `spark_processor.py`: Spark-backed processing implementation.
- `spark_manager.py`: Spark session management.

## Flow

1. Load raw records from the configured input path.
2. Clean and normalize text.
3. Remove duplicates according to threshold/config.
4. Extract optional metadata such as entities and keywords.
5. Write processed output to the configured output path and format.

## Extension Points

Add new processors by following `base.py` and wiring them through `pipeline.py`. Add new extraction or cleaning options to `PreprocessingConfig` before exposing them in the frontend.

## Notes

Keep preprocessing deterministic where possible. Stable preprocessing makes experiments reproducible and helps compare fine-tuning runs.
