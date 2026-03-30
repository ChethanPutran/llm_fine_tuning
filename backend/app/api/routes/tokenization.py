# app/api/routes/tokenization.py

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import logging

from app.dependencies.controller import get_tokenization_controller
from app.controllers.tokenization_controller import TokenizationController

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tokenization", tags=["tokenization"])


class TrainTokenizerRequest(BaseModel):
    """Request model for training tokenizer"""
    tokenizer_type: str = Field(..., description="Type of tokenizer (bpe, wordpiece, sentencepiece)")
    dataset_path: str = Field(..., description="Path to training dataset")
    vocab_size: int = Field(32000, ge=1000, le=100000, description="Vocabulary size")
    config: Dict[str, Any] = Field(default_factory=dict, description="Additional configuration")


class EncodeRequest(BaseModel):
    """Request model for encoding text"""
    tokenizer_path: str = Field(..., description="Path to tokenizer")
    text: str = Field(..., description="Text to encode")
    max_length: Optional[int] = Field(None, description="Maximum sequence length")


class DecodeRequest(BaseModel):
    """Request model for decoding tokens"""
    tokenizer_path: str = Field(..., description="Path to tokenizer")
    token_ids: List[int] = Field(..., description="Token IDs to decode")


@router.post("/train", response_model=Dict[str, Any])
async def train_tokenizer(
    request: TrainTokenizerRequest,
    controller: TokenizationController = Depends(get_tokenization_controller)
):
    """Train a tokenizer"""
    try:
        result = await controller.start_job(
            tokenizer_type=request.tokenizer_type,
            dataset_path=request.dataset_path,
            vocab_size=request.vocab_size,
            config=request.config
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to train tokenizer: {e}")
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


@router.get("/status/{job_id}", response_model=Dict[str, Any])
async def get_tokenization_status(
    job_id: str,
    controller: TokenizationController = Depends(get_tokenization_controller)
):
    """Get tokenization job status"""
    status = await controller.get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    return status


@router.get("/types", response_model=List[str])
async def get_tokenizer_types():
    """Get available tokenizer types"""
    return ["bpe", "wordpiece", "sentencepiece"]