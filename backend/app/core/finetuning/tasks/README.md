# Fine-Tuning Tasks

This package contains task-specific behavior used by the fine-tuning pipeline.

## Key Files

- `factory.py`: Selects a task implementation.
- `classification.py`: Text classification fine-tuning behavior.
- `summarization.py`: Summarization fine-tuning behavior.
- `qa.py`: Question-answering fine-tuning behavior.
- `generation.py`: Text generation fine-tuning behavior.

## Responsibilities

- Prepare raw examples for the target objective.
- Define task-specific labels, prompts, targets, or metrics.
- Keep model adaptation strategy independent from the task.

## Adding a Task

Add a new task module, register it in `factory.py`, and make sure the task can consume the common dataset config. Prefer explicit input and target field names in config for non-standard datasets.
