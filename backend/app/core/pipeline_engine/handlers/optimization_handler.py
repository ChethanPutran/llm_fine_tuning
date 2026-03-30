# app/core/pipeline_engine/handlers/optimization_handler.py

"""
Handler for optimization jobs
"""

from typing import Dict, Any
import logging

from app.common.job_models import OptimizationJob
from app.core.pipeline_engine.handlers.base_handler import BaseHandler
from app.core.optimization.optimizer_factory import OptimizerFactory
from app.core.config import settings

logger = logging.getLogger(__name__)


class OptimizationHandler(BaseHandler):
    """Handler for optimization jobs"""
    
    async def execute(self, job: OptimizationJob) -> Dict[str, Any]:
        """Execute optimization"""
        
        await self._mark_started(job.job_id)
        
        try:
            await self._update_progress(job.job_id, 10, "Initializing optimizer")
            
            # Get optimizer
            optimizer = OptimizerFactory.get_optimizer(
                job.optimization_type,
                job.config
            )
            
            await self._update_progress(job.job_id, 30, "Loading model")
            
            # Load model
            model = optimizer.load_model(job.input_model_path)
            
            await self._update_progress(job.job_id, 50, f"Applying {job.optimization_type}")
            
            # Apply optimization
            optimized_model = optimizer.optimize(model)
            
            await self._update_progress(job.job_id, 80, "Saving optimized model")
            
            # Save optimized model
            output_path = f"{settings.MODEL_STORAGE_PATH}/optimized/{job.job_id}"
            optimizer.save_model(optimized_model, output_path)
            
            # Get metrics
            metrics = optimizer.get_metrics(optimized_model)
            
            result = {
                "success": True,
                "output_path": output_path,
                "optimization_type": job.optimization_type,
                "metrics": metrics,
                "original_size": optimizer.original_size,
                "optimized_size": optimizer.optimized_size,
                "compression_ratio": optimizer.original_size / optimizer.optimized_size if optimizer.optimized_size > 0 else 0
            }
            
            job.output_model_path = output_path
            job.metrics = metrics
            job.original_size = optimizer.original_size
            job.optimized_size = optimizer.optimized_size
            job.compression_ratio = result["compression_ratio"]
            job.result = result
            
            await self._mark_completed(job.job_id, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            await self._mark_failed(job.job_id, str(e))
            raise