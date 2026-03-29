from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import subprocess
import os
import json

class BaseDeployment(ABC):
    """Abstract base class for model deployment"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.deployment_id = None
        self.endpoint = None
        self.status = "pending"
        
    @abstractmethod
    async def deploy(self, model_path: str, target: str) -> Dict[str, Any]:
        """Deploy model to target"""
        pass
    
    @abstractmethod
    async def undeploy(self, deployment_id: str) -> bool:
        """Undeploy model"""
        pass
    
    @abstractmethod
    async def get_status(self, deployment_id: str) -> Dict[str, Any]:
        """Get deployment status"""
        pass
    
    @abstractmethod
    async def predict(self, deployment_id: str, data: Any) -> Any:
        """Make prediction using deployed model"""
        pass
    
    def validate_model(self, model_path: str) -> bool:
        """Validate model before deployment"""
        if not os.path.exists(model_path):
            return False
        
        # Check for model files
        if os.path.isdir(model_path):
            required_files = ['config.json', 'pytorch_model.bin']
            for file in required_files:
                if not os.path.exists(os.path.join(model_path, file)):
                    return False
        
        return True
    
    def save_deployment_info(self, info: Dict[str, Any]) -> None:
        """Save deployment information"""
        deployment_file = f"./deployments/{self.deployment_id}.json"
        os.makedirs(os.path.dirname(deployment_file), exist_ok=True)
        with open(deployment_file, 'w') as f:
            json.dump(info, f)
    
    def load_deployment_info(self, deployment_id: str) -> Dict[str, Any]:
        """Load deployment information"""
        deployment_file = f"./deployments/{deployment_id}.json"
        if os.path.exists(deployment_file):
            with open(deployment_file, 'r') as f:
                return json.load(f)
        return {}