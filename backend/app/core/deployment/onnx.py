import aiohttp
import asyncio
import subprocess
import os
import json
import torch
import onnx
import onnxruntime as ort
from typing import Dict, Any, Optional
from .base import BaseDeployment

class ONNXDeployment(BaseDeployment):
    """ONNX Runtime deployment"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.port = config.get('port', 8000)
        self.model_name = config.get('model_name', 'default')
        self.session = None
        self.ort_session = None
        
    async def deploy(self, model_path: str, target: str) -> Dict[str, Any]:
        """Deploy model with ONNX Runtime"""
        if not self.validate_model(model_path):
            raise ValueError(f"Invalid model at {model_path}")
        
        self.deployment_id = f"onnx_{self.model_name}"
        
        # Convert to ONNX if needed
        onnx_path = await self._convert_to_onnx(model_path)
        
        if target == 'local':
            # Load ONNX model with ONNX Runtime
            self.ort_session = ort.InferenceSession(onnx_path)
            
            self.endpoint = f"http://localhost:{self.port}/predict"
            self.status = "active"
            
            # Start simple HTTP server for predictions
            await self._start_server()
            
            deployment_info = {
                'deployment_id': self.deployment_id,
                'endpoint': self.endpoint,
                'model_name': self.model_name,
                'onnx_path': onnx_path,
                'status': self.status
            }
            
            self.save_deployment_info(deployment_info)
            return deployment_info
        
        elif target == 'cloud':
            # Deploy to cloud (simplified)
            self.endpoint = f"https://onnx-cloud.example.com/predict"
            self.status = "active"
            return {
                'deployment_id': self.deployment_id,
                'endpoint': self.endpoint,
                'status': self.status
            }
        
        else:
            raise ValueError(f"Unsupported target: {target}")
    
    async def _convert_to_onnx(self, model_path: str) -> str:
        """Convert PyTorch model to ONNX format"""
        onnx_path = f"{model_path}/model.onnx"
        
        # Load PyTorch model
        if os.path.isdir(model_path):
            from transformers import AutoModel
            model = AutoModel.from_pretrained(model_path)
        else:
            model = torch.load(model_path)
        
        model.eval()
        
        # Create dummy input
        dummy_input = torch.randn(1, 512)
        
        # Export to ONNX
        torch.onnx.export(
            model,
            dummy_input,
            onnx_path,
            input_names=['input'],
            output_names=['output'],
            dynamic_axes={'input': {0: 'batch_size'}, 'output': {0: 'batch_size'}},
            opset_version=11
        )
        
        # Verify ONNX model
        onnx_model = onnx.load(onnx_path)
        onnx.checker.check_model(onnx_model)
        
        return onnx_path
    
    async def _start_server(self):
        """Start a simple HTTP server for predictions"""
        # This would normally start a proper server
        # Simplified for demonstration
        pass
    
    async def undeploy(self, deployment_id: str) -> bool:
        """Stop ONNX deployment"""
        self.session = None
        self.ort_session = None
        self.status = "inactive"
        return True
    
    async def get_status(self, deployment_id: str) -> Dict[str, Any]:
        """Get deployment status"""
        return {
            'deployment_id': deployment_id,
            'status': self.status,
            'endpoint': self.endpoint,
            'model_name': self.model_name
        }
    
    async def predict(self, deployment_id: str, data: Any) -> Any:
        """Make prediction using ONNX Runtime"""
        if not self.ort_session:
            raise Exception("Model not loaded")
        
        # Convert input to numpy array
        if isinstance(data, list):
            input_data = data
        else:
            input_data = [data]
        
        # Get input name
        input_name = self.ort_session.get_inputs()[0].name
        
        # Run inference
        ort_inputs = {input_name: input_data}
        ort_outputs = self.ort_session.run(None, ort_inputs)
        
        return ort_outputs[0].tolist()