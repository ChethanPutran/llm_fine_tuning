# app/api/websocket.py

from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from typing import Dict, Set, Any, Optional
import json
import logging
from uuid import UUID

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


class ConnectionManager:
    """WebSocket connection manager for real-time updates"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.execution_subscribers: Dict[str, Set[WebSocket]] = {}
        self.job_subscribers: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Connect a client"""
        await websocket.accept()
        if client_id not in self.active_connections:
            self.active_connections[client_id] = set()
        self.active_connections[client_id].add(websocket)
        logger.info(f"Client {client_id} connected")
    
    def disconnect(self, websocket: WebSocket, client_id: str):
        """Disconnect a client"""
        if client_id in self.active_connections:
            self.active_connections[client_id].discard(websocket)
            if not self.active_connections[client_id]:
                del self.active_connections[client_id]
        logger.info(f"Client {client_id} disconnected")
    
    async def subscribe_to_execution(self, websocket: WebSocket, execution_id: str):
        """Subscribe to execution updates"""
        if execution_id not in self.execution_subscribers:
            self.execution_subscribers[execution_id] = set()
        self.execution_subscribers[execution_id].add(websocket)
        logger.debug(f"WebSocket subscribed to execution {execution_id}")
    
    async def unsubscribe_from_execution(self, websocket: WebSocket, execution_id: str):
        """Unsubscribe from execution updates"""
        if execution_id in self.execution_subscribers:
            self.execution_subscribers[execution_id].discard(websocket)
            if not self.execution_subscribers[execution_id]:
                del self.execution_subscribers[execution_id]
            logger.debug(f"WebSocket unsubscribed from execution {execution_id}")
    
    async def subscribe_to_job(self, websocket: WebSocket, job_id: str):
        """Subscribe to job updates"""
        if job_id not in self.job_subscribers:
            self.job_subscribers[job_id] = set()
        self.job_subscribers[job_id].add(websocket)
        logger.debug(f"WebSocket subscribed to job {job_id}")
    
    async def unsubscribe_from_job(self, websocket: WebSocket, job_id: str):
        """Unsubscribe from job updates"""
        if job_id in self.job_subscribers:
            self.job_subscribers[job_id].discard(websocket)
            if not self.job_subscribers[job_id]:
                del self.job_subscribers[job_id]
            logger.debug(f"WebSocket unsubscribed from job {job_id}")
    
    async def broadcast_execution_update(self, execution_id: str, data: Dict[str, Any]):
        """Broadcast execution update to subscribers"""
        if execution_id in self.execution_subscribers:
            message = json.dumps({
                "type": "execution_update",
                "execution_id": execution_id,
                "data": data
            })
            disconnected = []
            for websocket in self.execution_subscribers[execution_id]:
                try:
                    await websocket.send_text(message)
                except Exception as e:
                    logger.error(f"Failed to send execution update: {e}")
                    disconnected.append(websocket)
            
            # Clean up disconnected websockets
            for ws in disconnected:
                await self.unsubscribe_from_execution(ws, execution_id)
    
    async def broadcast_job_update(self, job_id: str, data: Dict[str, Any]):
        """Broadcast job update to subscribers"""
        if job_id in self.job_subscribers:
            message = json.dumps({
                "type": "job_update",
                "job_id": job_id,
                "data": data
            })
            disconnected = []
            for websocket in self.job_subscribers[job_id]:
                try:
                    await websocket.send_text(message)
                except Exception as e:
                    logger.error(f"Failed to send job update: {e}")
                    disconnected.append(websocket)
            
            # Clean up disconnected websockets
            for ws in disconnected:
                await self.unsubscribe_from_job(ws, job_id)
    
    async def broadcast_to_client(self, client_id: str, data: Dict[str, Any]):
        """Broadcast to all connections of a client"""
        if client_id in self.active_connections:
            message = json.dumps(data)
            disconnected = []
            for websocket in self.active_connections[client_id]:
                try:
                    await websocket.send_text(message)
                except Exception as e:
                    logger.error(f"Failed to send message to client {client_id}: {e}")
                    disconnected.append(websocket)
            
            # Clean up disconnected websockets
            for ws in disconnected:
                self.disconnect(ws, client_id)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a personal message to a specific websocket"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")
    
    async def notify_job_update(self, job_id: str, data: Dict[str, Any]):
        """Notify all subscribers about job update"""
        await self.broadcast_job_update(job_id, data)
    
    async def notify_execution_update(self, execution_id: str, data: Dict[str, Any]):
        """Notify all subscribers about execution update"""
        await self.broadcast_execution_update(execution_id, data)


# Global instance
manager = ConnectionManager()


@router.websocket("/executions/{execution_id}")
async def websocket_execution_endpoint(websocket: WebSocket, execution_id: str):
    """
    WebSocket endpoint for real-time execution updates
    """
    client_id = f"exec_client_{id(websocket)}"
    
    try:
        await manager.connect(websocket, client_id)
        await manager.subscribe_to_execution(websocket, execution_id)
        
        # Send initial connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connected",
            "execution_id": execution_id,
            "message": "Connected to execution updates"
        }))
        
        # Keep connection alive and listen for client messages
        while True:
            data = await websocket.receive_text()
            
            # Handle client messages
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                if message_type == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                    
                elif message_type == "cancel":
                    # Cancel execution
                    try:
                        from app.dependencies.controller import get_orchestrator
                        orchestrator = get_orchestrator()
                        await orchestrator.cancel_execution(UUID(execution_id))
                        await websocket.send_text(json.dumps({
                            "type": "cancelled",
                            "execution_id": execution_id
                        }))
                    except Exception as e:
                        logger.error(f"Failed to cancel execution: {e}")
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": f"Failed to cancel execution: {str(e)}"
                        }))
                
                elif message_type == "status":
                    # Get current status
                    try:
                        from app.dependencies.controller import get_orchestrator
                        orchestrator = get_orchestrator()
                        status = await orchestrator.get_execution_status(UUID(execution_id))
                        await websocket.send_text(json.dumps({
                            "type": "status",
                            "execution_id": execution_id,
                            "data": status
                        }))
                    except Exception as e:
                        logger.error(f"Failed to get status: {e}")
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": f"Failed to get status: {str(e)}"
                        }))
                        
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON message: {data}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON message"
                }))
                
    except WebSocketDisconnect:
        await manager.unsubscribe_from_execution(websocket, execution_id)
        manager.disconnect(websocket, client_id)
        logger.info(f"WebSocket disconnected for execution {execution_id}")


@router.websocket("/jobs/{job_id}")
async def websocket_job_endpoint(websocket: WebSocket, job_id: str):
    """
    WebSocket endpoint for real-time job updates
    """
    client_id = f"job_client_{id(websocket)}"
    
    try:
        await manager.connect(websocket, client_id)
        await manager.subscribe_to_job(websocket, job_id)
        
        await websocket.send_text(json.dumps({
            "type": "connected",
            "job_id": job_id,
            "message": "Connected to job updates"
        }))
        
        # Keep connection alive and listen for client messages
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                if message_type == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                    
                elif message_type == "cancel":
                    # Cancel job
                    try:
                        from app.dependencies.controller import get_orchestrator
                        orchestrator = get_orchestrator()
                        job_uuid = UUID(job_id)
                        job = orchestrator.get_job(job_uuid)
                        
                        if job and hasattr(job, 'execution_id'):
                            await orchestrator.cancel_execution(job.execution_id)
                            await websocket.send_text(json.dumps({
                                "type": "cancelled",
                                "job_id": job_id
                            }))
                        else:
                            await websocket.send_text(json.dumps({
                                "type": "error",
                                "message": "Job not found or cannot be cancelled"
                            }))
                    except Exception as e:
                        logger.error(f"Failed to cancel job: {e}")
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": f"Failed to cancel job: {str(e)}"
                        }))
                
                elif message_type == "status":
                    # Get current status
                    try:
                        from app.dependencies.controller import get_orchestrator
                        orchestrator = get_orchestrator()
                        job = orchestrator.get_job(UUID(job_id))
                        
                        if job:
                            await websocket.send_text(json.dumps({
                                "type": "status",
                                "job_id": job_id,
                                "data": {
                                    "status": job.status.value,
                                    "progress": job.progress,
                                    "result": job.result,
                                    "error": job.error
                                }
                            }))
                        else:
                            await websocket.send_text(json.dumps({
                                "type": "error",
                                "message": "Job not found"
                            }))
                    except Exception as e:
                        logger.error(f"Failed to get job status: {e}")
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": f"Failed to get job status: {str(e)}"
                        }))
                        
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON message: {data}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON message"
                }))
            
    except WebSocketDisconnect:
        await manager.unsubscribe_from_job(websocket, job_id)
        manager.disconnect(websocket, client_id)
        logger.info(f"WebSocket disconnected for job {job_id}")


@router.websocket("/client/{client_id}")
async def websocket_client_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for client-specific updates
    """
    try:
        await manager.connect(websocket, client_id)
        
        await websocket.send_text(json.dumps({
            "type": "connected",
            "client_id": client_id,
            "message": "Connected to client updates"
        }))
        
        # Keep connection alive
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                if message_type == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                elif message_type == "subscribe":
                    # Subscribe to specific execution or job
                    target_type = message.get("target_type")
                    target_id = message.get("target_id")
                    
                    if target_type == "execution":
                        await manager.subscribe_to_execution(websocket, target_id)
                        await websocket.send_text(json.dumps({
                            "type": "subscribed",
                            "target_type": "execution",
                            "target_id": target_id
                        }))
                    elif target_type == "job":
                        await manager.subscribe_to_job(websocket, target_id)
                        await websocket.send_text(json.dumps({
                            "type": "subscribed",
                            "target_type": "job",
                            "target_id": target_id
                        }))
                        
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON message: {data}")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, client_id)
        logger.info(f"WebSocket disconnected for client {client_id}")