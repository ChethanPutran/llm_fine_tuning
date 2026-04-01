from typing import Any

from app.core.deployment.torchserve import TorchServeDeployment
from app.core.deployment.tensorflow_serving import TensorFlowServing
from app.core.deployment.onnx import ONNXDeployment
from app.core.deployment.base import BaseDeployment

class DeploymentFactory:
    """Factory pattern for creating deployment strategies"""

    _deployers = {
        'torchserve': TorchServeDeployment,
        'tensorflow-serving': TensorFlowServing,
        'onnx': ONNXDeployment
    }

    @classmethod
    def get_deployer(cls, framework: str, config: Any) -> BaseDeployment:
        """Get deployment strategy instance by framework"""
        deployer_class = cls._deployers.get(framework)
        if not deployer_class:
            raise ValueError(f"Unknown deployment framework: {framework}")
        return deployer_class(config)

    @classmethod
    def register_deployer(cls, name: str, deployer_class):
        """Register new deployment strategy"""
        cls._deployers[name] = deployer_class
    