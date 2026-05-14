# RAG Module

This module provides Retrieval-Augmented Generation primitives for document indexing, retrieval, and generation workflows.

## Key Files

- `config.py`: RAG configuration.
- `rag.py`: Retrieval, indexing, and generation orchestration.

## Responsibilities

- Build or load a vector index.
- Convert documents into retrievable chunks.
- Retrieve relevant context for a query.
- Combine retrieved context with a generator model or response pipeline.

## Extension Points

Add retrieval backends by abstracting vector-store operations behind a focused interface. Add embedding or chunking options through config rather than hardcoding them inside retrieval logic.

## Notes

RAG quality depends heavily on preprocessing, chunking, embedding model choice, and retrieval thresholds. Keep retrieved context and source metadata in responses for debuggability.
