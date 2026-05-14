# Core Backend Modules

The `app.core` package contains the domain logic for the LLM fine-tuning platform. API routes and controllers should stay thin and delegate pipeline work, model operations, data preparation, execution, and deployment behavior to these modules.

## Module Map

- `data_collection`: Scrapes or loads raw text sources and produces raw datasets.
- `datasets`: Normalizes dataset configuration and loading behavior.
- `preprocessing`: Cleans, deduplicates, extracts knowledge, and writes processed data.
- `tokenization`: Trains and uses BPE, WordPiece, and SentencePiece tokenizers.
- `models`: Wraps supported model families and model factory creation.
- `training`: Runs supervised training tasks and tracks metrics.
- `finetuning`: Runs task-specific fine-tuning with PEFT-style strategies.
- `optimization`: Applies pruning, quantization, and distillation.
- `evaluation`: Computes task and quality metrics.
- `rag`: Provides retrieval-augmented generation primitives.
- `deployment`: Packages and serves models through supported serving targets.
- `pipeline_engine`: Builds, validates, schedules, executes, and tracks DAG pipelines.
- `execution`: Provides async workers, queues, resource management, and distributed coordination helpers.
- `tasks`: Lists task categories, task types, datasets, and model suggestions.

## Cross-Cutting Files

- `config.py`: Application-level core settings.
- `exceptions.py`: Shared platform exceptions.
- `logging_config.py`: Logging setup used by the FastAPI app.

## Development Notes

Keep business logic in these modules rather than in API routes. When adding a new pipeline stage, update the relevant core module, add or update a pipeline handler in `pipeline_engine/handlers`, and expose it through the controller/API layer only after the core behavior is testable.
