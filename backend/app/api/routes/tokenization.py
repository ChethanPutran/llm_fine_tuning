# app/api/routes/tokenization.py

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import logging

from app.dependencies.controller import get_tokenization_controller
from app.controllers.tokenization_controller import TokenizationController
from app.api.models import TrainTokenizerRequest, EncodeRequest, DecodeRequest
from app.api.models import ListResourcesResponse, MetricResponse, RequestBase, StartOptimizationRequest, ExecutionStatusResponse, JobCreationResponse, JobStatusResponse, ListJobsResponse, StartCollectionRequest, StatisticsResponse 

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tokenization", tags=["tokenization"])


@router.post("/add", response_model=JobCreationResponse)
async def create_tokenizer_job(
    request: TrainTokenizerRequest,
    controller: TokenizationController = Depends(get_tokenization_controller)
):
    """Create a tokenizer training job"""
    try:
        # Create the job
        result = await controller.add_job(
            config=request.config,
            user_id="system",  # In real implementation, get from auth context
            tags=request.tags,
            auto_execute=request.auto_execute
        )
        
        return JobCreationResponse(**result)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create tokenizer job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute/{job_id}", response_model=ExecutionStatusResponse)
async def execute_tokenizer_job(
    job_id: str,
    controller: TokenizationController = Depends(get_tokenization_controller)
):
    """Execute an existing tokenizer training job"""
    try:
        result = await controller.execute_job(job_id)
        
        if result.get("error"):
            raise HTTPException(status_code=404, detail=result["error"])
        
        return ExecutionStatusResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute tokenizer job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/encode", response_model=Dict[str, Any])
async def encode_text(
    request: EncodeRequest,
    controller: TokenizationController = Depends(get_tokenization_controller)
):
    """Encode text using a trained tokenizer"""
    try:
        result = await controller.encode_text(
            tokenizer_path=request.tokenizer_path,
            text=request.text,
            max_length=request.max_length
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Encoding failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/decode", response_model=Dict[str, Any])
async def decode_tokens(
    request: DecodeRequest,
    controller: TokenizationController = Depends(get_tokenization_controller)
):
    """Decode token IDs to text"""
    try:
        result = await controller.decode_tokens(
            tokenizer_path=request.tokenizer_path,
            token_ids=request.token_ids
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Decoding failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_tokenization_status(
    job_id: str,
    controller: TokenizationController = Depends(get_tokenization_controller)
):
    """Get tokenization job status"""
    status = await controller.get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(**status)


@router.get("/jobs", response_model=ListJobsResponse)
async def list_tokenization_jobs(
    status: Optional[str] = Query(None, description="Filter by job status"),
    tokenizer_type: Optional[str] = Query(None, description="Filter by tokenizer type"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    limit: int = Query(50, ge=1, le=100, description="Number of jobs to return"),
    offset: int = Query(0, ge=0, description="Number of jobs to skip"),
    controller: TokenizationController = Depends(get_tokenization_controller)
):
    """List all tokenization jobs with pagination and filters"""
    result = await controller.list_jobs(
        status=status,
        tokenizer_type=tokenizer_type,
        user_id=user_id,
        limit=limit,
        offset=offset
    )
    return ListJobsResponse(**result)


@router.delete("/jobs/{job_id}", response_model=JobStatusResponse)
async def cancel_tokenization_job(
    job_id: str,
    controller: TokenizationController = Depends(get_tokenization_controller)
):
    """Cancel a tokenization job"""
    cancelled = await controller.cancel_job(job_id)
    if cancelled:
        return JobStatusResponse(**cancelled)
    raise HTTPException(status_code=400, detail="Job cannot be cancelled or not found")


@router.get("/statistics", response_model=StatisticsResponse)
async def get_tokenization_statistics(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    controller: TokenizationController = Depends(get_tokenization_controller)
):
    """Get tokenization statistics"""
    try:
        stats = await controller.get_statistics(user_id=user_id)
        return StatisticsResponse(**stats)
    except Exception as e:
        logger.error(f"Failed to get tokenization statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/types", response_model=ListResourcesResponse)
async def get_tokenizer_types(
    request: RequestBase = Field(..., description="Request model for getting tokenizer types"),
    controller: TokenizationController = Depends(get_tokenization_controller)
):
    """Get available tokenizer types"""

    return ListResourcesResponse(
        items=[
            {"name": "BertWordPieceTokenizer", "description": "BERT WordPiece tokenizer"},
            {"name": "GPT2BPETokenizer", "description": "GPT-2 Byte-Pair Encoding tokenizer"},
            {"name": "SentencePieceTokenizer", "description": "SentencePiece tokenizer"},
            {"name": "ByteLevelBPETokenizer", "description": "Byte-level BPE tokenizer"},
            {"name": "UnigramTokenizer", "description": "Unigram tokenizer based on SentencePiece"},
            {"name": "WordLevelTokenizer", "description": "Word-level tokenizer"},
            {"name": "CharacterTokenizer", "description": "Character-level tokenizer"},
            {"name": "MosesTokenizer", "description": "Moses tokenizer for NLP preprocessing"},
            {"name": "CustomTokenizer", "description": "Custom tokenizer defined by user"}
        ],
        **request.dict()
    )