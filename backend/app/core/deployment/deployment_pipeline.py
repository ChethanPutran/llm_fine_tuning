from typing import List, Dict, Any, Optional
from .base import BaseDeployment
import asyncio

class DeploymentPipeline:
    """Pipeline for managing multiple deployments"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.deployments: List[BaseDeployment] = []
        self.active_deployments: Dict[str, Dict] = {}
        
    def add_deployment(self, deployment: BaseDeployment) -> None:
        """Add a deployment to the pipeline"""
        self.deployments.append(deployment)
    
    async def deploy_all(self, model_path: str, target: str) -> List[Dict[str, Any]]:
        """Deploy to all configured targets"""
        results = []
        
        for deployment in self.deployments:
            try:
                result = await deployment.deploy(model_path, target)
                results.append(result)
                self.active_deployments[result['deployment_id']] = {
                    'deployment': deployment,
                    'info': result
                }
            except Exception as e:
                results.append({
                    'error': str(e),
                    'deployment': deployment.__class__.__name__
                })
        
        return results
    
    async def undeploy_all(self) -> List[bool]:
        """Undeploy all deployments"""
        results = []
        
        for deployment_id, info in self.active_deployments.items():
            result = await info['deployment'].undeploy(deployment_id)
            results.append(result)
        
        return results
    
    async def get_all_statuses(self) -> Dict[str, Dict]:
        """Get status of all deployments"""
        statuses = {}
        
        for deployment_id, info in self.active_deployments.items():
            status = await info['deployment'].get_status(deployment_id)
            statuses[deployment_id] = status
        
        return statuses
    
    async def predict_all(self, data: Any) -> Dict[str, Any]:
        """Make predictions using all deployed models"""
        predictions = {}
        
        for deployment_id, info in self.active_deployments.items():
            try:
                prediction = await info['deployment'].predict(deployment_id, data)
                predictions[deployment_id] = prediction
            except Exception as e:
                predictions[deployment_id] = {'error': str(e)}
        
        return predictions
    
    def execute(self) -> Dict[str, Any]:
        """Execute the deployment pipeline"""
        return {
            'total_deployments': len(self.deployments),
            'active_deployments': len(self.active_deployments),
            'config': self.config
        }