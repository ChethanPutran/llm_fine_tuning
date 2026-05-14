# Deployment Module

This module packages trained or optimized models for serving and tracks deployment metadata.

## Key Files

- `base.py`: Deployment target interface.
- `config.py`: Deployment configuration including model path, target, framework, endpoint, and status data.
- `factory.py`: Selects a deployment implementation.
- `pipeline.py`: High-level deployment pipeline.
- `torchserve.py`: TorchServe packaging and deployment behavior.
- `tensorflow_serving.py`: TensorFlow Serving export behavior.
- `onnx.py`: ONNX export and serving behavior.

## Flow

1. A deployment job receives a `DeploymentConfig`.
2. The factory selects the serving framework.
3. The selected implementation packages or exports the model.
4. Deployment metadata is returned to the pipeline engine and API layer.

## Extension Points

Add a new serving backend by implementing the base deployer, registering it in `factory.py`, and adding any framework-specific config fields to `DeploymentConfig.additional_params`.

## Operational Notes

Deployment code should validate that model artifacts exist before packaging. Local/demo deployers may create placeholders, but production deployers should return actionable errors for missing artifacts or unsupported frameworks.
