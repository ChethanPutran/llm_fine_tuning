# Pipeline Handlers

Handlers bridge pipeline nodes to domain modules. Each handler receives node/job configuration, invokes the relevant core module, and returns structured execution results.

## Key Files

- `base_handler.py`: Common handler interface.
- `data_collection_handler.py`: Runs data collection nodes.
- `preprocessing_handler.py`: Runs preprocessing nodes.
- `tokenization_handler.py`: Runs tokenizer training/use nodes.
- `training_handler.py`: Runs training nodes.
- `finetuning_handler.py`: Runs fine-tuning nodes.
- `evaluation_handler.py`: Runs evaluation nodes.
- `optimization_handler.py`: Runs optimization nodes.
- `deployment_handler.py`: Runs deployment nodes.

## Responsibilities

- Translate node config into core module calls.
- Report progress, metrics, artifacts, and errors.
- Keep orchestration concerns separate from domain implementation.

## Adding a Handler

Create a handler with the same execute signature as existing handlers, register it in `PipelineOrchestrator._register_all_handlers`, and make sure the corresponding node type is produced by the API/frontend pipeline definition.

## Notes

Handlers should be small. If a handler grows complex, move the logic into the relevant core module and keep the handler as a thin adapter.
