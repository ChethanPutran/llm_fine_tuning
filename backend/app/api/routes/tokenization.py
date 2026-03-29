import asyncio

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, List
import uuid
from app.core.tokenization.tokenizer_factory import TokenizerFactory
from ..models import TokenizationRequest, JobResponse

router = APIRouter(prefix="/tokenization", tags=["tokenization"])

# Store tokenization jobs
tokenization_jobs = {}

class TokenizationJob:
    def __init__(self, job_id: str, request: TokenizationRequest):
        self.job_id = job_id
        self.request = request
        self.status = "pending"
        self.progress = 0
        self.result = None
        self.error = None

@router.post("/train", response_model=JobResponse)
async def train_tokenizer(
    background_tasks: BackgroundTasks,
    request: TokenizationRequest
):
    """Train a tokenizer"""
    job_id = str(uuid.uuid4())
    tokenization_jobs[job_id] = TokenizationJob(job_id, request)
    
    background_tasks.add_task(
        run_tokenizer_training,
        job_id,
        request
    )
    
    return JobResponse(job_id=job_id, status="started", message="Tokenizer training started")

@router.get("/status/{job_id}", response_model=Dict[str, Any])
async def get_status(job_id: str):
    """Get tokenization status"""
    job = tokenization_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Tokenization job not found")
    
    return {
        "status": job.status,
        "progress": job.progress,
        "result": job.result,
        "error": job.error
    }

@router.get("/types", response_model=List[str])
async def get_tokenizer_types():
    """Get available tokenizer types"""
    return ["bpe", "wordpiece", "sentencepiece"]

@router.post("/encode")
async def encode_text(
    tokenizer_path: str,
    text: str
):
    """Encode text using a trained tokenizer"""
    try:
        # Load tokenizer
        tokenizer = TokenizerFactory.get_tokenizer("bpe", {})
        tokenizer.load(tokenizer_path)
        
        # Encode
        tokens = tokenizer.encode(text)
        
        return {
            "tokens": tokens,
            "num_tokens": len(tokens),
            "text": text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/decode")
async def decode_tokens(
    tokenizer_path: str,
    token_ids: List[int]
):
    """Decode token IDs to text"""
    try:
        # Load tokenizer
        tokenizer = TokenizerFactory.get_tokenizer("bpe", {})
        tokenizer.load(tokenizer_path)
        
        # Decode
        text = tokenizer.decode(token_ids)
        
        return {
            "text": text,
            "token_ids": token_ids
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def run_tokenizer_training(job_id: str, request: TokenizationRequest):
    """Background task for tokenizer training"""
    job = tokenization_jobs[job_id]
    job.status = "running"
    
    try:
        # Update progress
        job.progress = 10
        
        def load_corpus():
            with open(request.corpus_path, 'r', encoding='utf-8') as f:
                return f.readlines()
            
        # Load corpus
        corpus = await asyncio.to_thread(load_corpus)
        
        job.progress = 30
        
        # Get tokenizer
        tokenizer = TokenizerFactory.get_tokenizer(
            request.tokenizer_type,
            request.config
        )
        
        job.progress = 50
        
        # Train tokenizer
        await asyncio.to_thread(tokenizer.train, corpus)
        
        job.progress = 80
        
        # Save tokenizer
        await asyncio.to_thread(tokenizer.save, request.output_path)
        
        job.result = {
            "output_path": request.output_path,
            "tokenizer_type": request.tokenizer_type,
            "vocab_size": tokenizer.get_vocab_size(),
            "config": request.config
        }
        job.status = "completed"
        job.progress = 100
        
    except Exception as e:
        job.status = "failed"
        job.error = str(e)