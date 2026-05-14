# Tokenization Module

This module trains and applies tokenizers for text data.

## Key Files

- `base.py`: Tokenizer interface.
- `config.py`: Tokenizer configuration, vocabulary size, paths, special tokens, and SentencePiece options.
- `tokenizer_factory.py`: Selects tokenizer implementation.
- `bpe_tokenizer.py`: Byte Pair Encoding tokenizer.
- `wordpiece_tokenizer.py`: WordPiece tokenizer.
- `sentencepiece_tokenizer.py`: SentencePiece tokenizer.

## Flow

1. Receive a `TokenizationConfig`.
2. Select tokenizer implementation by `tokenizer_type`.
3. Train from the configured dataset path.
4. Save tokenizer artifacts.
5. Optionally encode or decode text through API routes.

## Extension Points

Add a tokenizer by implementing the base interface and registering it in `tokenizer_factory.py`. Keep special-token handling consistent with `DefaultTokens`.

## Notes

Tokenizer artifacts are training dependencies. Record the tokenizer path and vocabulary configuration with model training metadata for reproducibility.
