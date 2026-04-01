# app/api/routes/general.py

from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect, APIRouter, Depends, HTTPException
import logging


from app.core.config import settings
from app.dependencies.controller import get_general_controller
from app.controllers.general_controller import GeneralController

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/data-collection", tags=["data-collection"])
from app.api.websocket import manager 


# WebSocket endpoint for real-time updates
@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str,
                             controller: GeneralController = Depends(get_general_controller)):
    """
    WebSocket endpoint for real-time job status updates
    """
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            # Process message based on type
            if data.startswith("subscribe:"):
                job_id = data.split(":")[1]
                await manager.subscribe_to_job(websocket, job_id)
                await manager.send_personal_message(
                    f"Subscribed to job {job_id}", 
                    websocket
                )
            
            elif data.startswith("subscribe-execution:"):
                execution_id = data.split(":")[1]
                await manager.subscribe_to_execution(websocket, execution_id)
                await manager.send_personal_message(
                    f"Subscribed to execution {execution_id}", 
                    websocket
                )
            
            elif data.startswith("unsubscribe:"):
                job_id = data.split(":")[1]
                await manager.unsubscribe_from_job(websocket, job_id)
                await manager.send_personal_message(
                    f"Unsubscribed from job {job_id}", 
                    websocket
                )
            
            elif data == "status":
                # Send current status of all jobs
                status = await controller.get_system_status()
                await manager.send_personal_message(
                    str(status), 
                    websocket
                )
            
            elif data == "ping":
                await websocket.send_text("pong")
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, client_id)
        logger.info(f"Client {client_id} disconnected")


# Health check endpoint
@router.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }


# System info endpoint
@router.get("/system/info")
async def system_info():
    """
    Get system information
    """
    import torch
    import psutil
    import platform
    
    return {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "cuda_available": torch.cuda.is_available(),
        "cuda_version": torch.version.cuda if torch.cuda.is_available() else None,
        "gpu_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
        "memory_total_gb": round(psutil.virtual_memory().total/(1024**3), 2),
        "memory_available_gb": round(psutil.virtual_memory().available/(1024**3), 2),
        "cpu_count": psutil.cpu_count(),
        "workers": settings.PIPELINE_WORKERS
    }


# Root endpoint
@router.get("/")
async def root():
    """
    Root endpoint with API information
    """
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "description": "LLM Fine-tuning Platform",
        "docs_url": "/docs",
        "api_prefix": settings.API_V1_PREFIX,
        "websocket_url": "/ws/{client_id}",
        "endpoints": {
            "health": "/health",
            "system_info": "/system/info",
            "models": "/models/available",
            "datasets": "/datasets/available"
        }
    }

# Available models endpoint
@router.get("/models/available")
async def list_available_models(
        controller: GeneralController = Depends(get_general_controller)
):
    """
    List all available pre-trained models
    """
    try:
        models = controller.get_models()
        return {"models": models}
    except Exception as e:
        logger.error(f"Failed to list available models: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    


# Available datasets endpoint
@router.get("/datasets/available")
async def list_available_datasets(
        controller: GeneralController = Depends(get_general_controller)
):
    """
    List available datasets
    """
    try:
        datasets = controller.get_datasets()
        return {"datasets": datasets}
    except Exception as e:
        logger.error(f"Failed to list available datasets: {e}")
        raise HTTPException(status_code=500, detail=str(e))
