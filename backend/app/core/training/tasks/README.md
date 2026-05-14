# Training Tasks

This package contains task-specific training behavior used by the training pipeline.

## Key Files

- `base.py`: Base task contract.
- `factory.py`: Selects a task implementation.
- `classification.py`: Classification task behavior.
- `summarization.py`: Summarization task behavior.
- `qa.py`: Question-answering task behavior.
- `generation.py`: Text generation task behavior.
- `captionaning.py`: Image captioning-oriented task behavior.

## Responsibilities

- Convert datasets into task-ready tensors or records.
- Configure labels, targets, prompts, or decoding behavior.
- Provide task-specific metric expectations.

## Adding a Task

Create a task class, register it in `factory.py`, and add config documentation for any required dataset fields. Keep generic optimizer and epoch behavior in the parent training module.
