# Fine-Tuning Module

This module runs task-aware fine-tuning jobs and supports multiple fine-tuning strategies.

## Key Files

- `base.py`: Base fine-tuning interfaces.
- `config.py`: Fine-tuning configuration, including strategy, task, sequence length, batch size, learning rate, and epochs.
- `datasets.py`: Dataset helpers for fine-tuning workflows.
- `pipeline.py`: Fine-tuning pipeline orchestration.
- `strategies/`: Strategy implementations such as LoRA, adapters, prefix tuning, and full fine-tuning.
- `tasks/`: Task-specific preparation and training behavior.

## Flow

1. A fine-tuning request provides base model, dataset, and fine-tuning config.
2. The task factory selects task-specific formatting or loss behavior.
3. The strategy factory selects how model parameters are adapted.
4. The pipeline runs fine-tuning and reports metrics/artifact paths.

## Extension Points

Add new tasks under `tasks/` and new parameter-efficient methods under `strategies/`. Register new implementations in the matching factory module.

## Notes

Keep task logic and strategy logic separate. A task should describe what is learned; a strategy should describe which parameters or modules are trained.
