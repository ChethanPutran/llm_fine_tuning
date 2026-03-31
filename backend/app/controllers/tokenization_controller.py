# app/controllers/tokenization_controller.py

from typing import Dict, Any, Optional, List
from uuid import UUID
import logging
from datetime import datetime

from app.common.job_models import JobStatus, JobFactory, JobPriority
from app.controllers.base_controller import BaseController
from app.core.pipeline_engine.models import NodeType
from app.core.tokenization.tokenizer_factory import TokenizerFactory
from app.api.websocket import manager

logger = logging.getLogger(__name__)


class TokenizationController(BaseController):
    """Controller for tokenization operations"""

    def __init__(self, orchestrator):
        super().__init__(orchestrator)
    
    async def add_job(
        self,
        *,
        tokenizer_type: str,
        dataset_path: str,
        vocab_size: int = 32000,
        config: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Train a tokenizer
        
        Args:
            tokenizer_type: Type of tokenizer (bpe, wordpiece, sentencepiece)
            dataset_path: Path to training dataset
            vocab_size: Vocabulary size
            config: Additional configuration
            user_id: User ID
            tags: Optional tags for categorization
        
        Returns:
            Job information
        """
        config = config or {}
        
        try:
            metadata = {
                "node_id": "tokenizer",
                "name": f"Train {tokenizer_type} tokenizer",
                "node_type": NodeType.TOKENIZATION,
                "resources": {"cpu": 2, "memory_gb": 4},
                "metadata": {
                    "tokenizer_type": tokenizer_type,
                    "dataset_path": dataset_path,
                    "vocab_size": vocab_size,
                    "tokenizer_config": config
                },
                "retry_policy": config.get("retry_policy", {"retries": 3, "delay_seconds": 5}),
                "position": config.get("position", (0, 0))
            }
            
            # Create job using factory
            job = JobFactory.create_tokenization_job(
                tokenizer_type=tokenizer_type,
                dataset_path=dataset_path,
                vocab_size=vocab_size,
                config=config,
                user_id=user_id,
                tags=tags or ["tokenization", tokenizer_type]
            )
            
            # Register job with orchestrator
            self.orchestrator.register_job(job, metadata)
            
            return {
                "job_id": str(job.job_id),
                "message": "Tokenizer training job created successfully",
            }
            
        except Exception as e:
            logger.error(f"Failed to start tokenization job: {e}")
            raise
    
    async def execute_job(self, job_id: str) -> Dict[str, Any]:
        """
        Execute a registered tokenization job
        
        Args:
            job_id: Job ID to execute
        
        Returns:
            Execution result information
        """
        try:
            job_uuid = UUID(job_id)
            job = self._get_job(job_uuid)
            
            if not job:
                logger.error(f"Job {job_id} not found for execution")
                return {"error": "Job not found"}
            
            # Execute the job using orchestrator
            execution_result = await self.orchestrator.execute_job(job.job_id)
            
            return {
                "job_id": str(job.job_id),
                "execution_id": str(execution_result.get("execution_id", "")),
                "message": "Job execution started successfully"
            }
            
        except ValueError:
            logger.error(f"Invalid job ID: {job_id}")
            return {"error": "Invalid job ID"}
        except Exception as e:
            logger.error(f"Failed to execute job: {e}")
            return {"error": "Failed to execute job"}
    
    async def encode_text(
        self,
        tokenizer_path: str,
        text: str,
        max_length: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Encode text using a trained tokenizer
        
        Args:
            tokenizer_path: Path to tokenizer
            text: Text to encode
            max_length: Maximum sequence length
        
        Returns:
            Encoded tokens
        """
        try:
            # Determine tokenizer type from path
            tokenizer_type = self._detect_tokenizer_type(tokenizer_path)
            
            # Load tokenizer
            tokenizer = TokenizerFactory.get_tokenizer(tokenizer_type, {})
            tokenizer.load(tokenizer_path)
            
            # Encode
            tokens = tokenizer.encode(text, max_length=max_length)
            
            return {
                "tokens": tokens,
                "num_tokens": len(tokens),
                "text": text[:100] + "..." if len(text) > 100 else text,
                "tokenizer_type": tokenizer_type
            }
        except Exception as e:
            logger.error(f"Encoding failed: {e}")
            raise ValueError(f"Failed to encode text: {e}")
    
    async def decode_tokens(
        self,
        tokenizer_path: str,
        token_ids: List[int]
    ) -> Dict[str, Any]:
        """
        Decode token IDs to text
        
        Args:
            tokenizer_path: Path to tokenizer
            token_ids: List of token IDs
        
        Returns:
            Decoded text
        """
        try:
            # Determine tokenizer type from path
            tokenizer_type = self._detect_tokenizer_type(tokenizer_path)
            
            # Load tokenizer
            tokenizer = TokenizerFactory.get_tokenizer(tokenizer_type, {})
            tokenizer.load(tokenizer_path)
            
            # Decode
            text = tokenizer.decode(token_ids)
            
            return {
                "text": text,
                "token_ids": token_ids[:50] if len(token_ids) > 50 else token_ids,
                "num_tokens": len(token_ids),
                "tokenizer_type": tokenizer_type
            }
        except Exception as e:
            logger.error(f"Decoding failed: {e}")
            raise ValueError(f"Failed to decode tokens: {e}")
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get tokenization job status"""
        try:
            job_uuid = UUID(job_id)
            job = self._get_job(job_uuid)
            
            if not job:
                job = self.orchestrator.get_job(job_uuid)
                if not job:
                    return None
            
            # Get execution status if execution exists
            execution_status = None
            if job.execution_id:
                execution_status = await self.orchestrator.get_execution_status(job.execution_id)
            
            return {
                "job_id": str(job.job_id),
                "job_type": job.job_type.value,
                "execution_id": str(job.execution_id) if job.execution_id else None,
                "status": job.status.value if hasattr(job.status, 'value') else job.status,
                "progress": job.progress,
                "result": job.result,
                "error": job.error,
                "tokenizer_type": job.tokenizer_type,
                "vocab_size": job.vocab_size,
                "dataset_path": job.dataset_path,
                "tokenizer_path": job.tokenizer_path,
                "created_at": job.created_at.isoformat(),
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "updated_at": job.updated_at.isoformat(),
                "user_id": job.user_id,
                "tags": job.tags,
                "execution_details": execution_status
            }
            
        except ValueError:
            logger.error(f"Invalid job ID: {job_id}")
            return None
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a tokenization job"""
        try:
            job_uuid = UUID(job_id)
            job = self._get_job(job_uuid)
            
            if not job:
                job = self.orchestrator.get_job(job_uuid)
                if not job:
                    return False
            
            # Check if job can be cancelled
            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                logger.warning(f"Job {job_id} cannot be cancelled in status {job.status}")
                return False
            
            if job.execution_id:
                cancelled = await self.orchestrator.cancel_execution(job.execution_id)
                if cancelled:
                    job.mark_cancelled()
                    self._update_job(job.job_id, status=job.status, completed_at=job.completed_at)
                    await manager.notify_job_update(job_id, {
                        "status": "cancelled",
                        "message": "Job cancelled by user"
                    })
                    logger.info(f"Job {job_id} cancelled successfully")
                    return True
            else:
                # Job hasn't started execution yet
                job.mark_cancelled()
                self._update_job(job.job_id, status=job.status, completed_at=job.completed_at)
                await manager.notify_job_update(job_id, {
                    "status": "cancelled",
                    "message": "Job cancelled before execution"
                })
                logger.info(f"Job {job_id} cancelled before execution")
                return True
            
            return False
            
        except ValueError:
            logger.error(f"Invalid job ID: {job_id}")
            return False
    
    async def list_jobs(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        tokenizer_type: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs    
    ) -> Dict[str, Any]:
        """List tokenization jobs"""
        
        # Get from orchestrator
        orchestrator_jobs = self.orchestrator.list_jobs(
            job_type="tokenization",
            status=status,
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        
        # Combine with local jobs
        jobs_list = list(self._jobs.values())
        
        # Add orchestrator jobs
        for job_dict in orchestrator_jobs.get("jobs", []):
            job_id = UUID(job_dict["job_id"])
            if job_id not in self._jobs:
                # Create job object from dict
                from app.common.job_models import TokenizationJob
                job = TokenizationJob(
                    job_id=job_id,
                    tokenizer_type=job_dict.get("tokenizer_type", ""),
                    dataset_path=job_dict.get("dataset_path", ""),
                    status=JobStatus(job_dict["status"]),
                    progress=job_dict.get("progress", 0),
                    created_at=datetime.fromisoformat(job_dict["created_at"])
                )
                jobs_list.append(job)
        
        # Sort by creation time (newest first)
        jobs_list.sort(key=lambda x: x.created_at, reverse=True)
        
        # Apply filters
        if tokenizer_type:
            jobs_list = [j for j in jobs_list if j.tokenizer_type == tokenizer_type]
        
        total = len(jobs_list)
        paginated_jobs = jobs_list[offset:offset + limit]
        
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "jobs": [self._job_to_dict(job) for job in paginated_jobs]
        }
    
    async def get_statistics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get tokenization statistics"""
        jobs_list = list(self._jobs.values())
        
        if user_id:
            jobs_list = [j for j in jobs_list if j.user_id == user_id]
        
        # Count by status
        status_counts = {}
        for status in JobStatus:
            count = len([j for j in jobs_list if j.status == status])
            if count > 0:
                status_counts[status.value] = count
        
        # Count by tokenizer type
        type_counts = {}
        for job in jobs_list:
            type_counts[job.tokenizer_type] = type_counts.get(job.tokenizer_type, 0) + 1
        
        return {
            "total_jobs": len(jobs_list),
            "by_status": status_counts,
            "by_tokenizer_type": type_counts,
            "completed_jobs": len([j for j in jobs_list if j.status == JobStatus.COMPLETED]),
            "failed_jobs": len([j for j in jobs_list if j.status == JobStatus.FAILED])
        }
    
    def _detect_tokenizer_type(self, path: str) -> str:
        """Detect tokenizer type from path or files"""
        if "bpe" in path.lower():
            return "bpe"
        elif "wordpiece" in path.lower() or "word_piece" in path.lower():
            return "wordpiece"
        elif "sentencepiece" in path.lower() or "sp" in path.lower():
            return "sentencepiece"
        else:
            return "bpe"  # Default