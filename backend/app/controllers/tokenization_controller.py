# app/controllers/tokenization_controller.py

from typing import Dict, Any, Optional, List
from uuid import UUID
import logging

from app.common.job_models import  JobStatus, JobFactory
from app.controllers.base_controller import BaseController
from app.core.pipeline_engine.models import NodeType
from app.core.tokenization.tokenizer_factory import TokenizerFactory

logger = logging.getLogger(__name__)


class TokenizationController(BaseController):
    """Controller for tokenization operations"""

    def __init__(self, orchestrator):
        super().__init__(orchestrator)
    
    async def start_job(
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
            # Clear pipeline and build tokenization pipeline
            self.orchestrator.clear_pipeline()
            
            self.orchestrator.add_node_to_pipeline(
                node_id="tokenizer",
                name=f"Train {tokenizer_type} tokenizer",
                node_type=NodeType.TOKENIZATION,
                config={
                    "tokenizer_type": tokenizer_type,
                    "dataset_path": dataset_path,
                    "vocab_size": vocab_size,
                    "tokenizer_config": config
                },
                resources={"cpu": 2, "memory_gb": 4},
                metadata={
                    "tokenizer_type": tokenizer_type,
                    "vocab_size": vocab_size
                }
            )
            
            # Create job using factory
            job = JobFactory.create_tokenization_job(
                tokenizer_type=tokenizer_type,
                dataset_path=dataset_path,
                vocab_size=vocab_size,
                config=config,
                user_id=user_id,
                tags=tags or ["tokenization", tokenizer_type]
            )
            
            # Register job
            self._register_job(job.job_id, job)
            
            # Execute pipeline
            result = await self.orchestrator.execute_current_pipeline(user_id=user_id)
            
            # Link execution to job
            execution_id = result.get("execution_id")
            if execution_id:
                job.execution_id = execution_id
                job.mark_started()
                self._update_job(job.job_id, execution_id=execution_id)
            
            logger.info(f"Tokenization job {job.job_id} started for {tokenizer_type} tokenizer")
            
            return {
                "job_id": str(job.job_id),
                "execution_id": str(execution_id) if execution_id else None,
                "status": "started",
                "tokenizer_type": tokenizer_type,
                "vocab_size": vocab_size,
                "message": "Tokenizer training started successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to start tokenization job: {e}")
            raise
    
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
            
            return {
                "job_id": str(job.job_id),
                "job_type": job.job_type.value,
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
                "user_id": job.user_id,
                "tags": job.tags
            }
            
        except ValueError:
            logger.error(f"Invalid job ID: {job_id}")
            return None
    
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
        result = self.orchestrator.list_jobs(
            job_type="tokenization",
            status=status,
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        
        # Add local jobs
        local_jobs = []
        for job in self._jobs.values():
            if tokenizer_type and job.tokenizer_type != tokenizer_type:
                continue
            if status and job.status.value != status:
                continue
            if user_id and job.user_id != user_id:
                continue
            local_jobs.append(self._job_to_dict(job))
        
        # Combine and sort
        all_jobs = result.get("jobs", []) + local_jobs
        all_jobs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        total = len(all_jobs)
        paginated_jobs = all_jobs[offset:offset + limit]
        
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "jobs": paginated_jobs
        }
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a tokenization job"""
        try:
            job_uuid = UUID(job_id)
            job = self._get_job(job_uuid)
            
            if not job:
                job = self.orchestrator.get_job(job_uuid)
                if not job:
                    return False
            
            if job.status not in [JobStatus.RUNNING, JobStatus.QUEUED, JobStatus.PENDING]:
                return False
            
            if job.execution_id:
                cancelled = await self.orchestrator.cancel_execution(job.execution_id)
                if cancelled:
                    job.mark_cancelled()
                    self._update_job(job.job_id, status=job.status, completed_at=job.completed_at)
                    logger.info(f"Job {job_id} cancelled successfully")
                    return True
            
            return False
            
        except ValueError:
            return False
    
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