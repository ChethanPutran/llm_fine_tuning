# Optimization Module

This module applies post-training optimization techniques to reduce model size, memory use, or latency.

## Key Files

- `base.py`: Base optimizer interface.
- `config.py`: Optimization configuration and output metrics.
- `optimizer_factory.py`: Selects optimization implementation.
- `quantization.py`: Quantization behavior.
- `pruning.py`: Pruning behavior.
- `distillation.py`: Distillation behavior.
- `pipeline.py`: Optimization pipeline wrapper.

## Flow

1. Receive an `OptimizationConfig` with input model path and optimization type.
2. Select an optimizer implementation.
3. Run optimization and write optimized artifacts.
4. Report compression and performance metrics when available.

## Extension Points

Register new optimization methods in `optimizer_factory.py`. Store method-specific options in `additional_params` unless the field is shared across optimization types.

## Notes

Optimizers should validate input artifact paths and return clear errors. Metrics should include original size, optimized size, and compression ratio whenever possible.
