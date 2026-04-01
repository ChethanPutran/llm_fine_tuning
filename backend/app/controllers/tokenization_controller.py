# app/controllers/tokenization_controller.py

from typing import Dict, Any, Optional, List
import logging

from app.common.job_models import JobFactory
from app.controllers.base_controller import BaseController
from app.core.pipeline_engine.models import NodeType
from app.core.tokenization.tokenizer_factory import TokenizerFactory
from app.common.job_models import TokenizationConfig

logger = logging.getLogger(__name__)


class TokenizationController(BaseController):
    """Controller for tokenization operations"""

    def __init__(self, orchestrator):
        super().__init__(orchestrator)
    
    async def add_job(
        self,
        *,
        config: TokenizationConfig,
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        auto_execute: bool = True,
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
        try:
            # Create job using factory
            job = JobFactory.create_tokenization_job(
                tokenization_config=config,
                **kwargs
            )
            metadata = JobFactory.create_job_metadata(
                name=f"Train {config.tokenizer_type} tokenizer", 
                node_type=NodeType.TOKENIZATION,
                job=job,
                description=f"Training {config.tokenizer_type} tokenizer on dataset {config.dataset_path} with vocab size {config.vocab_size}",
                config={},
                tags=tags or []
            )
            
            # Register job with orchestrator
            return await self.register(job, metadata, auto_execute=auto_execute, message="Tokenizer training job created successfully")
            
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