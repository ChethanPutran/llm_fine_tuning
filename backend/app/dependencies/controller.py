# app/dependencies/controller.py

from fastapi import Depends
from app.core.pipeline_engine.orchestrator import PipelineOrchestrator
from app.controllers.data_collection_controller import DataCollectionController
from app.controllers.preprocessing_controller import PreprocessingController
from app.controllers.training_controller import TrainingController
from app.controllers.optimization_controller import OptimizationController
from app.controllers.deployment_controller import DeploymentController
from app.controllers.tokenization_controller import TokenizationController

# Global orchestrator instance
_orchestrator = None


def get_orchestrator() -> PipelineOrchestrator:
    """Get or create orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = PipelineOrchestrator(num_workers=4)
    return _orchestrator


def get_data_collection_controller(
    orchestrator: PipelineOrchestrator = Depends(get_orchestrator)
) -> DataCollectionController:
    """Get data collection controller instance"""
    return DataCollectionController(orchestrator)


def get_preprocessing_controller(
    orchestrator: PipelineOrchestrator = Depends(get_orchestrator)
) -> PreprocessingController:
    """Get preprocessing controller instance"""
    return PreprocessingController(orchestrator)


def get_training_controller(
    orchestrator: PipelineOrchestrator = Depends(get_orchestrator)
) -> TrainingController:
    """Get training controller instance"""
    return TrainingController(orchestrator)


def get_optimization_controller(
    orchestrator: PipelineOrchestrator = Depends(get_orchestrator)
) -> OptimizationController:
    """Get optimization controller instance"""
    return OptimizationController(orchestrator)


def get_deployment_controller(
    orchestrator: PipelineOrchestrator = Depends(get_orchestrator)
) -> DeploymentController:
    """Get deployment controller instance"""
    return DeploymentController(orchestrator)


def get_tokenization_controller(
    orchestrator: PipelineOrchestrator = Depends(get_orchestrator)
) -> TokenizationController:
    """Get tokenization controller instance"""
    return TokenizationController(orchestrator)