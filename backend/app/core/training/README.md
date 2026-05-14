# Training Module

This module runs supervised model training and records training metrics.

## Key Files

- `base.py`: Base training contract.
- `config.py`: Training settings, optimizer/scheduler choices, hyperparameters, and task config.
- `trainer.py`: Generic training loop.
- `pipeline.py`: Training pipeline wrapper.
- `metrics.py`: Metric helpers.
- `tasks/`: Task-specific training implementations.

## Flow

1. Receive model, dataset, and training config.
2. Prepare the task-specific dataset and model head.
3. Run the training loop.
4. Evaluate and collect metrics.
5. Save model artifacts and return output paths.

## Extension Points

Add new task behavior under `tasks/` and register it in the task factory. Add shared training options to `TrainingConfig`; task-specific options should live under `TrainingTaskConfig.parameters`.

## Notes

Training should report metrics, artifact paths, and failures in a structured shape so pipeline execution and dashboard views can consume them directly.
