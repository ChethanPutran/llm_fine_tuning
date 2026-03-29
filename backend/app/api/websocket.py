from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Any, Set
import asyncio
import json
import logging


logger = logging.getLogger(__name__)

class ConnectionManager:
    """WebSocket connection manager"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.job_subscribers: Dict[str, Set[str]] = {}
        self.client_subscriptions: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Connect websocket client"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.client_subscriptions[client_id] = set()
        print(f"Client {client_id} connected")
        logger.info(f"Client {client_id} connected")
    
    def disconnect(self, websocket: WebSocket, client_id: str):
        """Disconnect websocket client"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]

            if not self.active_connections[client_id]:
                del self.active_connections[client_id]

        # Remove client from all job subscriptions
        if client_id in self.client_subscriptions:
            for job_id in self.client_subscriptions[client_id]:
                if job_id in self.job_subscribers:
                    self.job_subscribers[job_id].discard(client_id)
            del self.client_subscriptions[client_id]

        logger.info(f"Client {client_id} disconnected")
    
    async def subscribe_to_job(self, client_id: str, job_id: str):
        """Subscribe client to job updates"""
        # Add to job subscribers
        if job_id not in self.job_subscribers:
            self.job_subscribers[job_id] = set()

        self.job_subscribers[job_id].add(client_id)
        
        # Add to client subscriptions
        if client_id not in self.client_subscriptions:
            self.client_subscriptions[client_id] = set()
        self.client_subscriptions[client_id].add(job_id)
        
        logger.info(f"Client {client_id} subscribed to job {job_id}")
    
    async def unsubscribe_from_job(self, client_id: str, job_id: str):
        """Unsubscribe client from job updates"""
        if job_id in self.job_subscribers:
            self.job_subscribers[job_id].discard(client_id)
        
        if client_id in self.client_subscriptions:
            self.client_subscriptions[client_id].discard(job_id)
        
        logger.info(f"Client {client_id} unsubscribed from job {job_id}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send message to specific client"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Failed to send message: {str(e)}")

    async def notify_job_update(self, job_id: str, update: dict):
        """Notify all subscribers of a job about updates"""
        if job_id in self.job_subscribers:
            message = json.dumps({
                "type": "job_update",
                "job_id": job_id,
                "data": update,
                "timestamp": datetime.now().isoformat()
            })
            
            for client_id in self.job_subscribers[job_id]:
                if client_id in self.active_connections:
                    await self.send_personal_message(
                        message, 
                        self.active_connections[client_id]
                    )

    async def broadcast(self, message: str):
        """Broadcast message to all connected clients"""
        for client_id, connection in self.active_connections.items():
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Failed to broadcast to {client_id}: {str(e)}")
    
    async def get_connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.active_connections)
manager = ConnectionManager()

async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint handler"""
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get('type') == 'subscribe':
                job_id = message.get('job_id')
                if job_id:
                    await manager.subscribe_to_job(client_id, job_id)
                    await websocket.send_text(json.dumps({
                        'type': 'subscribed',
                        'job_id': job_id
                    }))
            
            elif message.get('type') == 'ping':
                await websocket.send_text(json.dumps({'type': 'pong'}))
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, client_id)