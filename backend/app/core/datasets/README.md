# Datasets Module

This module centralizes dataset configuration, loading, splitting, and task-oriented preparation.

## Key Files

- `config.py`: Dataset configuration fields such as path, type, task, batch size, and worker count.
- `base.py`: Base dataset loader contract.
- `factory.py`: Dataset loader selection.
- `main.py`: High-level dataset helper for available datasets and preparation.

## Responsibilities

- Hide dataset source details from training and fine-tuning modules.
- Convert local or external data into consistent train/eval/test structures.
- Keep task-specific dataset decisions close to data loading.

## Extension Points

To add a dataset backend, create a loader that follows the base interface, register it in `factory.py`, and document any required config fields in `config.py`.

## Notes

The current implementation is intentionally lightweight in places. When adding production dataset support, prefer typed loaders and explicit schemas over ad hoc path or field assumptions.
