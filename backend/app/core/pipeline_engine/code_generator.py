from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent
from typing import Any, Dict, List
from uuid import UUID

from app.common.job_models import JobPriority

from .models import Pipeline


class PipelineCodeGenerator:
    """Generate Python code that executes a pipeline through the engine."""

    def __init__(self, output_dir: str | Path = "data/generated_pipelines"):
        self.output_dir = Path(output_dir)

    def generate(
        self,
        pipeline: Pipeline,
        execution_plan: List[List[str]],
        optimization_summary: Dict[str, Any],
        execution_id: UUID,
        user_id: str | None = None,
        priority: JobPriority = JobPriority.NORMAL,
    ) -> Dict[str, str]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        filename = f"pipeline_{execution_id}.py"
        path = self.output_dir / filename
        code = self.render(
            pipeline=pipeline,
            execution_plan=execution_plan,
            optimization_summary=optimization_summary,
            user_id=user_id,
            priority=priority,
        )
        path.write_text(code)
        return {
            "path": str(path),
            "code": code,
        }

    def render(
        self,
        pipeline: Pipeline,
        execution_plan: List[List[str]],
        optimization_summary: Dict[str, Any],
        user_id: str | None = None,
        priority: JobPriority = JobPriority.NORMAL,
    ) -> str:
        pipeline_dict = self._pipeline_to_dict(pipeline)
        payload = json.dumps(pipeline_dict, indent=2, default=str)
        plan = json.dumps(execution_plan, indent=2)
        summary = json.dumps(optimization_summary, indent=2, default=str)
        priority_name = priority.name if hasattr(priority, "name") else JobPriority(priority).name

        return dedent(f"""\
            \"\"\"
            Auto-generated pipeline execution script.

            This script reconstructs the optimized pipeline graph and executes it
            using the backend pipeline engine.
            \"\"\"

            import asyncio

            from app.common.job_models import JobPriority
            from app.core.pipeline_engine.models import Pipeline
            from app.core.pipeline_engine.orchestrator import PipelineOrchestrator


            PIPELINE = {payload}

            EXECUTION_PLAN = {plan}

            OPTIMIZATION_SUMMARY = {summary}


            async def main():
                orchestrator = PipelineOrchestrator()
                await orchestrator.start()
                try:
                    pipeline = Pipeline.from_dict(PIPELINE)
                    result = await orchestrator._execute_pipeline(
                        pipeline=pipeline,
                        user_id={user_id!r},
                        priority=JobPriority.{priority_name},
                    )
                    print(result)
                    return result
                finally:
                    await orchestrator.stop()


            if __name__ == "__main__":
                asyncio.run(main())
            """)

    def _pipeline_to_dict(self, pipeline: Pipeline) -> Dict[str, Any]:
        return {
            "id": str(pipeline.id),
            "name": pipeline.name,
            "description": pipeline.description,
            "version": pipeline.version,
            "created_at": pipeline.created_at.isoformat(),
            "updated_at": pipeline.updated_at.isoformat(),
            "tags": pipeline.tags,
            "nodes": [
                {
                    "id": node.id,
                    "name": node.name,
                    "type": node.type.value,
                    "config": node.config.model_dump(),
                    "status": node.status.value,
                    "metadata": node.metadata,
                }
                for node in pipeline.nodes.values()
            ],
            "edges": [
                edge.model_dump()
                for edge in pipeline.edges
            ],
        }
