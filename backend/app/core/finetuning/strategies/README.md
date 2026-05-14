# Fine-Tuning Strategies

This package contains interchangeable strategy implementations for adapting a base model during fine-tuning.

## Key Files

- `factory.py`: Selects a strategy from configuration.
- `full_finetune.py`: Updates all trainable model parameters.
- `lora.py`: Applies Low-Rank Adaptation style parameter-efficient tuning.
- `adapter.py`: Adds adapter-style bottleneck modules.
- `prefix_tuning.py`: Uses trainable prefix parameters.

## Strategy Contract

Strategies should expose a consistent interface for preparing a model, selecting trainable parameters, saving artifacts, and reporting trainable parameter counts.

## Adding a Strategy

1. Create a new strategy module.
2. Follow the existing strategy interface.
3. Register it in `factory.py`.
4. Add config fields through `FinetuningConfig.additional_params` when the option is strategy-specific.

## Notes

Strategies should avoid task-specific formatting. Task preparation belongs in `finetuning/tasks`.
