# Models Module

This module wraps supported model families and provides factory-based creation.

## Key Files

- `base.py`: Base model wrapper contract.
- `config.py`: Model configuration, including name, tokenizer, type, path, and extra parameters.
- `model_factory.py`: Instantiates model wrappers by type.
- `bert_model.py`: BERT model wrapper.
- `bart_model.py`: BART model wrapper.
- `gpt_model.py`: GPT-style causal language model wrapper.
- `vit_model.py`: Vision Transformer wrapper.
- `vlm_model.py`: Vision-language model wrapper.
- `main.py`: High-level model listing/helper functions.

## Responsibilities

- Hide model-family differences from training and fine-tuning pipelines.
- Centralize model creation and forward-pass wrappers.
- Provide a single place to add new architecture support.

## Extension Points

Add a new architecture by creating a wrapper that follows `base.py`, adding config support if needed, and registering it in `model_factory.py`.

## Notes

Model wrappers should keep heavyweight framework logic inside the core layer. API routes should only pass model config and return structured status or artifact metadata.
