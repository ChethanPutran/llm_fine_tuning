# Tasks Module

This module lists supported task categories, task types, and helper lookups for datasets and models.

## Key Files

- `tasks.py`: Task category/type enums and lookup helpers.

## Responsibilities

- Provide task categories such as NLP, Computer Vision, Audio, and Multimodal.
- Map each category to supported task types.
- Suggest datasets and models for a task through Hugging Face Hub helpers.

## Notes

The task module is used by the frontend to populate dependent dropdowns. Return values should be JSON-serializable strings or simple objects, not raw SDK model objects.

## Extension Points

Add new task categories or task types in `tasks.py`, then update backend controller serialization and frontend stage definitions if the new task should be visible in the UI.
