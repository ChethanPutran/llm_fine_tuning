import aiohttp
import asyncio
import subprocess
import os
import json
import shutil
from typing import Dict, Any, Optional
from .base import BaseDeployment

class TorchServeDeployment(BaseDeployment):
    """TorchServe deployment"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.port = config.get('port', 8080)
        self.management_port = config.get('management_port', 8081)
        self.model_name = config.get('model_name', 'default')
        self.model_version = config.get('model_version', '1.0')
        self.process = None
        
    async def deploy(self, model_path: str, target: str) -> Dict[str, Any]:
        """Deploy model with TorchServe"""
        if not self.validate_model(model_path):
            raise ValueError(f"Invalid model at {model_path}")
        
        self.deployment_id = f"torchserve_{self.model_name}"
        
        # Package model for TorchServe
        mar_file = await self._package_model(model_path)
        
        # Start TorchServe
        if target == 'local':
            cmd = [
                'torchserve',
                '--start',
                '--model-store', os.path.dirname(mar_file),
                '--models', f"{self.model_name}={mar_file}",
                '--port', str(self.port),
                '--management-port', str(self.management_port)
            ]
            
            self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for server to start
            await asyncio.sleep(5)
            
            self.endpoint = f"http://localhost:{self.port}/predictions/{self.model_name}"
            self.status = "active"
            
            deployment_info = {
                'deployment_id': self.deployment_id,
                'endpoint': self.endpoint,
                'port': self.port,
                'management_port': self.management_port,
                'model_name': self.model_name,
                'model_version': self.model_version,
                'status': self.status
            }
            
            self.save_deployment_info(deployment_info)
            return deployment_info
        
        elif target == 'cloud':
            # Deploy to cloud (simplified)
            self.endpoint = f"https://torchserve-cloud.example.com/predictions/{self.model_name}"
            self.status = "active"
            return {
                'deployment_id': self.deployment_id,
                'endpoint': self.endpoint,
                'status': self.status
            }
        
        else:
            raise ValueError(f"Unsupported target: {target}")
    
    async def _package_model(self, model_path: str) -> str:
        """Package model for TorchServe"""
        # Create model archive
        mar_file = f"/tmp/{self.model_name}.mar"
        
        # Create handler file
        handler_code = """
        import torch
        from ts.torch_handler.base_handler import BaseHandler

        class ModelHandler(BaseHandler):
            def __init__(self):
                super().__init__()
                self.model = None
            
            def initialize(self, context):
                properties = context.system_properties
                model_dir = properties.get("model_dir")
                self.model = torch.load(f"{model_dir}/pytorch_model.bin")
                self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
                self.model.to(self.device)
                self.model.eval()
            
            def preprocess(self, data):
                return data
            
            def inference(self, data):
                with torch.no_grad():
                    return self.model(data)
            
            def postprocess(self, data):
                return data
        """
        
        # Save handler
        handler_path = f"/tmp/handler.py"
        with open(handler_path, 'w') as f:
            f.write(handler_code)
        
        # Create MAR file
        cmd = [
            'torch-model-archiver',
            '--model-name', self.model_name,
            '--version', self.model_version,
            '--model-file', f"{model_path}/config.json",
            '--serialized-file', f"{model_path}/pytorch_model.bin",
            '--handler', handler_path,
            '--export-path', os.path.dirname(mar_file)
        ]
        
        subprocess.run(cmd, check=True)
        
        return mar_file
    
    async def undeploy(self, deployment_id: str) -> bool:
        """Stop TorchServe"""
        if self.process:
            cmd = ['torchserve', '--stop']
            subprocess.run(cmd)
            self.process = None
        
        self.status = "inactive"
        return True
    
    async def get_status(self, deployment_id: str) -> Dict[str, Any]:
        """Get deployment status"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"http://localhost:{self.management_port}/models/{self.model_name}") as response:
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
        """Make prediction using TorchServe"""
        async with aiohttp.ClientSession() as session:
            payload = data if isinstance(data, dict) else {'data': data}
            
            async with session.post(self.endpoint, json=payload) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Prediction failed: {response.status}")