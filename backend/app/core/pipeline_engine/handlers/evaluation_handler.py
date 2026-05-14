"""
Handler for evaluation nodes.
"""

from typing import Any, Dict

from app.core.evaluation.eval import LLMEvaluation
from app.core.pipeline_engine.handlers.base_handler import BaseHandler


class EvaluationHandler(BaseHandler):
    """Execute lightweight evaluation from node/job configuration."""

    async def execute(self, job) -> Dict[str, Any]:
        await self._mark_started(job)

        try:
            config = getattr(job, "config", {}) or {}
            if hasattr(config, "model_dump"):
                config = config.model_dump()

            node_config = getattr(job, "metadata", {}).get("node_config", {})
            if isinstance(node_config, dict):
                config = {**config, **node_config}

            predictions = config.get("predictions", [])
            references = config.get("references", [])
            evaluator = LLMEvaluation()

            metrics: Dict[str, Any] = {}
            if predictions and references:
                metrics = evaluator.traditional_metrics(predictions, references)

            result = {
                "success": True,
                "metrics": metrics,
                "message": "Evaluation completed" if metrics else "Evaluation node completed without prediction/reference inputs",
            }

            await self._mark_completed(job, result)
            return result
        except Exception as exc:
            await self._mark_failed(job, str(exc))
            raise
