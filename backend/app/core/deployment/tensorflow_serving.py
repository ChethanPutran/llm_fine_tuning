import aiohttp
import asyncio
import subprocess
import os
import json
from typing import Dict, Any, Optional
from .base import BaseDeployment

class TensorFlowServing(BaseDeployment):
    """TensorFlow Serving deployment"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.port = config.get('port', 8501)
        self.rest_port = config.get('rest_port', 8501)
        self.grpc_port = config.get('grpc_port', 8500)
        self.model_name = config.get('model_name', 'default')
        self.process = None
        
    async def deploy(self, model_path: str, target: str) -> Dict[str, Any]:
        """Deploy model with TensorFlow Serving"""
        if not self.validate_model(model_path):
            raise ValueError(f"Invalid model at {model_path}")
        
        self.deployment_id = f"tfserving_{self.model_name}"
        
        # Convert PyTorch model to TensorFlow if needed
        tf_model_path = await self._convert_to_tf(model_path)
        
        # Start TensorFlow Serving
        if target == 'local':
            cmd = [
                'tensorflow_model_server',
                '--port={}'.format(self.grpc_port),
                '--rest_api_port={}'.format(self.rest_port),
                '--model_name={}'.format(self.model_name),
                '--model_base_path={}'.format(tf_model_path)
            ]
            
            self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for server to start
            await asyncio.sleep(5)
            
            self.endpoint = f"http://localhost:{self.rest_port}/v1/models/{self.model_name}"
            self.status = "active"
            
            deployment_info = {
                'deployment_id': self.deployment_id,
                'endpoint': self.endpoint,
                'grpc_port': self.grpc_port,
                'rest_port': self.rest_port,
                'model_name': self.model_name,
                'status': self.status
            }
            
            self.save_deployment_info(deployment_info)
            return deployment_info
        
        elif target == 'cloud':
            # Deploy to cloud (simplified)
            self.endpoint = f"https://tfserving-cloud.example.com/v1/models/{self.model_name}"
            self.status = "active"
            return {
                'deployment_id': self.deployment_id,
                'endpoint': self.endpoint,
                'status': self.status
            }
        
        else:
            raise ValueError(f"Unsupported target: {target}")
    
    async def _convert_to_tf(self, pytorch_path: str) -> str:
        """Convert PyTorch model to TensorFlow format"""
        # Simplified conversion - in production use ONNX or direct conversion
        tf_path = f"{pytorch_path}_tf"
        os.makedirs(tf_path, exist_ok=True)
        
        # Create a saved_model.pb placeholder
        with open(f"{tf_path}/saved_model.pb", 'w') as f:
            f.write("placeholder")
        
        with open(f"{tf_path}/variables/variables.index", 'w') as f:
            f.write("placeholder")
        
        return tf_path
    
    async def undeploy(self, deployment_id: str) -> bool:
        """Stop TensorFlow Serving"""
        if self.process:
            self.process.terminate()
            self.process = None
        
        self.status = "inactive"
        return True
    
    async def get_status(self, deployment_id: str) -> Dict[str, Any]:
        """Get deployment status"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.endpoint}") as response:
                    if response.status == 200:
                        return {
                            'deployment_id': deployment_id,
                            'status': 'active',
                            'endpoint': self.endpoint
                        }
            except:
                pass
        
        return {
            'deployment_id': deployment_id,
            'status': self.status,
            'endpoint': self.endpoint
        }
    
    async def predict(self, deployment_id: str, data: Any) -> Any:
        """Make prediction using TensorFlow Serving"""
        async with aiohttp.ClientSession() as session:
            payload = {
                'instances': data if isinstance(data, list) else [data]
            }
            
            async with session.post(f"{self.endpoint}:predict", json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('predictions', [])
                else:
                    raise Exception(f"Prediction failed: {response.status}")