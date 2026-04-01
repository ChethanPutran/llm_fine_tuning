# app/core/pipeline_engine/handlers/tokenization_handler.py

from typing import Dict, Any
import os
import logging

from app.common.job_models import TokenizationJob
from app.core.pipeline_engine.handlers.base_handler import BaseHandler
from app.core.tokenization.tokenizer_factory import TokenizerFactory
from app.core.config import settings

logger = logging.getLogger(__name__)


class TokenizationHandler(BaseHandler):
    """Handler for tokenization jobs"""
    
    async def execute(self, job: TokenizationJob) -> Dict[str, Any]:
        """Execute tokenizer training"""
        
        await self._mark_started(job.job_id)
        
        try:
            config = job.config 
            await self._update_progress(job.job_id, 10, f"Loading dataset from {config.dataset_path}")
            
            # Load dataset
            texts = await self._load_dataset(config.dataset_path)
            
            await self._update_progress(job.job_id, 30, f"Training {config.tokenizer_type} tokenizer")
            
            # Get tokenizer
            tokenizer = TokenizerFactory.get_tokenizer(config.tokenizer_type, config)
            
            await self._update_progress(job.job_id, 50, "Building vocabulary")
            
            # Train tokenizer
            tokenizer.train(texts)
            
            await self._update_progress(job.job_id, 80, "Saving tokenizer")
            
            # Save tokenizer
            output_path = f"{settings.MODEL_STORAGE_PATH}/tokenizers/{job.job_id}"
            os.makedirs(output_path, exist_ok=True)
            tokenizer.save(output_path)
            
            result = {
                "success": True,
                "output_path": output_path,
                "tokenizer_type": config.tokenizer_type,
                "vocab_size": config.vocab_size,
                "config": config
            }
            
            config.tokenizer_path = output_path
            job.result = result
            
            await self._mark_completed(job.job_id, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Tokenizer training failed: {e}")
            await self._mark_failed(job.job_id, str(e))
            raise
    
    async def _load_dataset(self, dataset_path: str) -> list:
        """Load dataset for tokenizer training"""
        texts = []
        
        if os.path.isfile(dataset_path):
            if dataset_path.endswith('.txt'):
                with open(dataset_path, 'r', encoding='utf-8') as f:
                    texts = [line.strip() for line in f.readlines() if line.strip()]
            elif dataset_path.endswith('.csv'):
                import pandas as pd
                df = pd.read_csv(dataset_path)
                if 'text' in df.columns:
                    texts = df['text'].tolist()
                elif 'content' in df.columns:
                    texts = df['content'].tolist()
                else:
                    # Take first column
                    texts = df.iloc[:, 0].tolist()
            elif dataset_path.endswith('.json'):
                import json
                with open(dataset_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        if isinstance(data[0], str):
                            texts = data
                        elif isinstance(data[0], dict):
                            if 'text' in data[0]:
                                texts = [item['text'] for item in data]
                            elif 'content' in data[0]:
                                texts = [item['content'] for item in data]
        else:
            # Assume it's a directory
            for root, dirs, files in os.walk(dataset_path):
                for file in files:
                    if file.endswith('.txt'):
                        with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                            texts.extend([line.strip() for line in f.readlines() if line.strip()])
        
        if not texts:
            raise ValueError(f"No text data found in {dataset_path}")
        
        return texts