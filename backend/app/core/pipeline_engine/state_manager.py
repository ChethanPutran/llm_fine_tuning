# app/core/pipeline_engine/state_manager.py

import json
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timezone
from abc import ABC, abstractmethod
import logging
from redis.asyncio import Redis as AsyncRedis
from app.core.pipeline_engine.models import NodeStatus, Pipeline


logger = logging.getLogger(__name__)


class StateStorage(ABC):
    """Strategy pattern for state storage backends"""
    
    @abstractmethod
    async def save(self, key: str, state: Dict[str, Any]) -> None:
        pass
    
    @abstractmethod
    async def load(self, key: str) -> Optional[Dict[str, Any] | Any]:
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> None:
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        pass
    
    @abstractmethod
    async def list_keys(self, pattern: str) -> list:
        pass


class RedisStateStorage(StateStorage):
    """Redis-based state storage with async support"""
    
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0, 
                 password: Optional[str] = None, ttl: int = 3600):
        """
        Initialize Redis state storage
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password (optional)
            ttl: Time to live in seconds (default: 1 hour)
        """
        self.redis = AsyncRedis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True  # Automatically decode responses
        )
        self.prefix = "pipeline:state:"
        self.checkpoint_prefix = "pipeline:checkpoint:"
        self.ttl = ttl
        self._connected = False
    
    async def _ensure_connection(self):
        """Ensure Redis connection is established"""
        if not self._connected:
            try:
                self.redis.ping()
                self._connected = True
                logger.info("Redis connection established")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                raise
    
    async def save(self, key: str, state: Dict[str, Any]) -> None:
        """
        Save state to Redis
        
        Args:
            key: Storage key
            state: State dictionary to save
        """
        try:
            await self._ensure_connection()
            
            full_key = f"{self.prefix}{key}"
            
            # Convert datetime objects to ISO format strings
            serialized_state = self._serialize_state(state)
            
            # Save with TTL
            await self.redis.setex(
                full_key,
                self.ttl,
                json.dumps(serialized_state, default=str)
            )
            
            logger.debug(f"State saved for key: {key}")
            
        except Exception as e:
            logger.error(f"Failed to save state for key {key}: {e}")
            raise
    
    async def load(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Load state from Redis
        
        Args:
            key: Storage key
        
        Returns:
            State dictionary or None if not found
        """
        try:
            await self._ensure_connection()
            
            full_key = f"{self.prefix}{key}"
            data = await self.redis.get(full_key)
            
            if data:
                state = json.loads(data)
                logger.debug(f"State loaded for key: {key}")
                return state
            
            logger.debug(f"No state found for key: {key}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to load state for key {key}: {e}")
            return None
    
    async def delete(self, key: str) -> None:
        """
        Delete state from Redis
        
        Args:
            key: Storage key
        """
        try:
            await self._ensure_connection()
            
            full_key = f"{self.prefix}{key}"
            deleted = await self.redis.delete(full_key)
            
            if deleted:
                logger.debug(f"State deleted for key: {key}")
            else:
                logger.debug(f"No state found to delete for key: {key}")
                
        except Exception as e:
            logger.error(f"Failed to delete state for key {key}: {e}")
            raise
    
    async def exists(self, key: str) -> bool:
        """
        Check if state exists
        
        Args:
            key: Storage key
        
        Returns:
            True if state exists, False otherwise
        """
        try:
            await self._ensure_connection()
            
            full_key = f"{self.prefix}{key}"
            exists = await self.redis.exists(full_key)
            return exists > 0
            
        except Exception as e:
            logger.error(f"Failed to check existence for key {key}: {e}")
            return False
    
    async def list_keys(self, pattern: str = "*") -> list:
        """
        List keys matching pattern
        
        Args:
            pattern: Key pattern to match
        
        Returns:
            List of keys
        """
        try:
            await self._ensure_connection()
            
            full_pattern = f"{self.prefix}{pattern}"
            keys = await self.redis.keys(full_pattern)
            
            # Remove prefix
            return [key.replace(self.prefix, "") for key in keys]
            
        except Exception as e:
            logger.error(f"Failed to list keys with pattern {pattern}: {e}")
            return []
    
    async def cleanup_expired(self) -> int:
        """
        Clean up expired keys (Redis handles this automatically, but we can trigger)
        
        Returns:
            Number of keys cleaned up
        """
        try:
            await self._ensure_connection()
            # Redis automatically handles TTL expiration
            return 0
        except Exception as e:
            logger.error(f"Failed to cleanup expired keys: {e}")
            return 0
    
    async def close(self):
        """Close Redis connection"""
        try:
            if self._connected:
                await self.redis.close()
                self._connected = False
                logger.info("Redis connection closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")
    
    def _serialize_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize state for JSON storage"""
        serialized = {}
        for key, value in state.items():
            if isinstance(value, datetime):
                serialized[key] = value.isoformat()
            elif isinstance(value, UUID):
                serialized[key] = str(value)
            elif isinstance(value, dict):
                serialized[key] = self._serialize_state(value)
            elif isinstance(value, list):
                serialized[key] = [
                    self._serialize_state(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                serialized[key] = value
        return serialized


class PipelineStateManager:
    """Manages pipeline state persistence and checkpointing"""
    
    def __init__(self, storage: StateStorage):
        self.storage = storage
    
    async def save_state(self, execution_id: UUID, pipeline: Pipeline) -> None:
        """
        Save current pipeline state
        
        Args:
            execution_id: Execution identifier
            pipeline: Pipeline to save
        """
        try:
            state = {
                "execution_id": str(execution_id),
                "pipeline_id": str(pipeline.id),
                "pipeline_name": pipeline.name,
                "nodes": {
                    node_id: node.to_dict()
                    for node_id, node in pipeline.nodes.items()
                },
                "edges": [
                    {"source": edge.source, "target": edge.target, "condition": edge.condition}
                    for edge in pipeline.edges
                ],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "version": pipeline.version,
                "tags": pipeline.tags
            }
            
            await self.storage.save(str(execution_id), state)
            logger.debug(f"State saved for execution {execution_id}")
            
        except Exception as e:
            logger.error(f"Failed to save state for execution {execution_id}: {e}")
            raise
    
    async def load_state(self, execution_id: UUID) -> Optional[Pipeline]:
        """
        Load pipeline state from storage
        
        Args:
            execution_id: Execution identifier
        
        Returns:
            Reconstructed pipeline or None if not found
        """
        try:
            state = await self.storage.load(str(execution_id))
            if not state:
                logger.debug(f"No state found for execution {execution_id}")
                return None
            
            # Reconstruct pipeline from state
            from app.core.pipeline_engine.models import Pipeline, PipelineNode, PipelineEdge, NodeType, NodeConfig
            
            pipeline = Pipeline(
                id=UUID(state["pipeline_id"]),
                name=state["pipeline_name"],
                version=state.get("version", 1),
                tags=state.get("tags", [])
            )
            
            # Reconstruct nodes
            for node_id, node_data in state["nodes"].items():
                node = PipelineNode(
                    id=node_id,
                    name=node_data["name"],
                    type=NodeType(node_data["type"]),
                    config=NodeConfig(
                        parameters=node_data["config"].get("parameters", {}),
                        resources=node_data["config"].get("resources", {}),
                        retry_policy=node_data["config"].get("retry_policy", {})
                    ),
                    status=NodeStatus(node_data.get("status", "pending")),
                    metadata=node_data.get("metadata", {})
                )
                pipeline.add_node(node)
            
            # Reconstruct edges
            for edge_data in state.get("edges", []):
                edge = PipelineEdge(
                    source=edge_data["source"],
                    target=edge_data["target"],
                    condition=edge_data.get("condition")
                )
                pipeline.add_edge(edge)
            
            logger.debug(f"State loaded for execution {execution_id}")
            return pipeline
            
        except Exception as e:
            logger.error(f"Failed to load state for execution {execution_id}: {e}")
            return None
    
    async def create_checkpoint(self, execution_id: UUID, pipeline: Pipeline) -> str:
        """
        Create a checkpoint that can be resumed from
        
        Args:
            execution_id: Execution identifier
            pipeline: Pipeline to checkpoint
        
        Returns:
            Checkpoint identifier
        """
        try:
            checkpoint_id = f"{execution_id}:{datetime.now(timezone.utc).timestamp()}"
            
            # Serialize pipeline
            serialized_pipeline = await self._serialize_pipeline(pipeline)
            
            checkpoint_data = {
                "execution_id": str(execution_id),
                "pipeline": serialized_pipeline,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "checkpoint_type": "auto"
            }
            
            await self.storage.save(checkpoint_id, checkpoint_data)
            logger.info(f"Checkpoint created: {checkpoint_id}")
            return checkpoint_id
            
        except Exception as e:
            logger.error(f"Failed to create checkpoint for execution {execution_id}: {e}")
            raise
    
    async def load_checkpoint(self, checkpoint_id: str) -> Optional[Pipeline]:
        """
        Load pipeline from checkpoint
        
        Args:
            checkpoint_id: Checkpoint identifier
        
        Returns:
            Reconstructed pipeline or None if not found
        """
        try:
            checkpoint_data = await self.storage.load(checkpoint_id)
            if not checkpoint_data:
                logger.debug(f"No checkpoint found: {checkpoint_id}")
                return None
            
            # Deserialize pipeline
            pipeline = await self._deserialize_pipeline(checkpoint_data["pipeline"])
            logger.info(f"Checkpoint loaded: {checkpoint_id}")
            return pipeline
            
        except Exception as e:
            logger.error(f"Failed to load checkpoint {checkpoint_id}: {e}")
            return None
    
    async def cleanup_checkpoints(self, execution_id: UUID) -> int:
        """
        Clean up checkpoints for an execution
        
        Args:
            execution_id: Execution identifier
        
        Returns:
            Number of checkpoints cleaned up
        """
        try:
            pattern = f"{execution_id}:*"
            keys = await self.storage.list_keys(pattern)
            
            cleaned = 0
            for key in keys:
                await self.storage.delete(key)
                cleaned += 1
            
            if cleaned > 0:
                logger.info(f"Cleaned up {cleaned} checkpoints for execution {execution_id}")
            
            return cleaned
            
        except Exception as e:
            logger.error(f"Failed to cleanup checkpoints for execution {execution_id}: {e}")
            return 0
    
    async def get_latest_checkpoint(self, execution_id: UUID) -> Optional[str]:
        """
        Get the latest checkpoint for an execution
        
        Args:
            execution_id: Execution identifier
        
        Returns:
            Latest checkpoint ID or None
        """
        try:
            pattern = f"{execution_id}:*"
            keys = await self.storage.list_keys(pattern)
            
            if not keys:
                return None
            
            # Sort by timestamp (second part of key)
            keys.sort(key=lambda k: float(k.split(":")[1]), reverse=True)
            return keys[0]
            
        except Exception as e:
            logger.error(f"Failed to get latest checkpoint for execution {execution_id}: {e}")
            return None
    
    async def _serialize_pipeline(self, pipeline: Pipeline) -> str:
        """
        Serialize pipeline for storage
        
        Args:
            pipeline: Pipeline to serialize
        
        Returns:
            Serialized pipeline as hex string
        """
        try:
            # Convert pipeline to dict first
            pipeline_dict = {
                "id": str(pipeline.id),
                "name": pipeline.name,
                "description": pipeline.description,
                "version": pipeline.version,
                "nodes": {
                    node_id: node.to_dict()
                    for node_id, node in pipeline.nodes.items()
                },
                "edges": [
                    {"source": e.source, "target": e.target, "condition": e.condition}
                    for e in pipeline.edges
                ],
                "tags": pipeline.tags
            }
            
            # Serialize to JSON then to bytes
            json_str = json.dumps(pipeline_dict, default=str)
            return json_str
            
        except Exception as e:
            logger.error(f"Failed to serialize pipeline: {e}")
            raise
    
    async  def get_logs(self, execution_id: UUID, node_id: str = "*") -> Optional[list]:
        """Get execution logs"""
        try:
            logs_key = f"logs:{execution_id}"
            logs = await self.storage.load(logs_key)
            if type(logs) == list: 
                return logs
        except Exception as e:
            logger.error(f"Failed to get logs for execution {execution_id}: {e}")
        return None
    
    async def append_log(self, execution_id: UUID, log_entry: str) -> None:
        """Append a log entry for an execution"""
        try:
            logs_key = f"logs:{execution_id}"
            existing_logs = await self.storage.load(logs_key) or []
            existing_logs.append(f"{datetime.now(timezone.utc).isoformat()} - {log_entry}")
            await self.storage.save(logs_key, existing_logs)
        except Exception as e:
            logger.error(f"Failed to append log for execution {execution_id}: {e}")

    async def _deserialize_pipeline(self, serialized: str) -> Pipeline:
        """
        Deserialize pipeline from storage
        
        Args:
            serialized: Serialized pipeline string
        
        Returns:
            Reconstructed pipeline
        """
        try:
            from app.core.pipeline_engine.models import Pipeline, PipelineNode, PipelineEdge, NodeType, NodeConfig
            
            pipeline_dict = json.loads(serialized)
            
            pipeline = Pipeline(
                id=UUID(pipeline_dict["id"]),
                name=pipeline_dict["name"],
                description=pipeline_dict.get("description"),
                version=pipeline_dict.get("version", 1),
                tags=pipeline_dict.get("tags", [])
            )
            
            # Reconstruct nodes
            for node_id, node_data in pipeline_dict["nodes"].items():
                node = PipelineNode(
                    id=node_id,
                    name=node_data["name"],
                    type=NodeType(node_data["type"]),
                    config=NodeConfig(
                        parameters=node_data["config"].get("parameters", {}),
                        resources=node_data["config"].get("resources", {}),
                        retry_policy=node_data["config"].get("retry_policy", {})
                    ),
                    status=NodeStatus(node_data.get("status", "pending")),
                    metadata=node_data.get("metadata", {})
                )
                pipeline.add_node(node)
            
            # Reconstruct edges
            for edge_data in pipeline_dict.get("edges", []):
                edge = PipelineEdge(
                    source=edge_data["source"],
                    target=edge_data["target"],
                    condition=edge_data.get("condition")
                )
                pipeline.add_edge(edge)
            
            return pipeline
            
        except Exception as e:
            logger.error(f"Failed to deserialize pipeline: {e}")
            raise