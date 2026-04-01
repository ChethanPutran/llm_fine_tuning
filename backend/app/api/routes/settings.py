# app/api/routes/settings.py

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import logging

from app.dependencies.controller import get_settings_controller
from app.controllers.settings_controller import SettingsController

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["settings"])


# Request/Response Models
class UpdateSettingsRequest(BaseModel):
    """Request model for updating settings"""
    settings: Dict[str, Any] = Field(..., description="Settings to update")


class ImportSettingsRequest(BaseModel):
    """Request model for importing settings"""
    settings: Dict[str, Any] = Field(..., description="Settings to import")


class EnvironmentVariableRequest(BaseModel):
    """Request model for updating environment variable"""
    key: str = Field(..., description="Environment variable key")
    value: str = Field(..., description="Environment variable value")


class SettingsResponse(BaseModel):
    """Response model for settings"""
    settings: Dict[str, Any]
    message: Optional[str] = None


@router.get("/", response_model=SettingsResponse)
async def get_settings(
    controller: SettingsController = Depends(get_settings_controller)
):
    """
    Get all application settings
    
    Returns the complete settings configuration including:
    - General settings
    - Resource limits
    - Module-specific settings (data collection, training, etc.)
    - Storage and security settings
    """
    try:
        settings = await controller.get_settings()
        return SettingsResponse(settings=settings)
    except Exception as e:
        logger.error(f"Failed to get settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=SettingsResponse)
async def update_settings(
    request: UpdateSettingsRequest,
    controller: SettingsController = Depends(get_settings_controller)
):
    """
    Update application settings
    
    Allows partial or complete updates to the settings configuration.
    Updates are merged with existing settings.
    """
    try:
        result = await controller.update_settings(request.settings)
        return SettingsResponse(settings=result["settings"], message=result["message"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset", response_model=SettingsResponse)
async def reset_settings(
    controller: SettingsController = Depends(get_settings_controller)
):
    """
    Reset settings to default values
    
    Restores all settings to their original default configuration.
    """
    try:
        result = await controller.reset_settings()
        return SettingsResponse(settings=result["settings"], message=result["message"])
    except Exception as e:
        logger.error(f"Failed to reset settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export", response_model=Dict[str, Any])
async def export_settings(
    controller: SettingsController = Depends(get_settings_controller)
):
    """
    Export settings as JSON file
    
    Returns the complete settings configuration with metadata for backup.
    """
    try:
        result = await controller.export_settings()
        return result
    except Exception as e:
        logger.error(f"Failed to export settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import", response_model=SettingsResponse)
async def import_settings(
    request: ImportSettingsRequest,
    controller: SettingsController = Depends(get_settings_controller)
):
    """
    Import settings from JSON
    
    Replaces current settings with imported configuration.
    """
    try:
        result = await controller.import_settings(request.settings)
        return SettingsResponse(settings=result["settings"], message=result["message"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to import settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Backup Management
@router.get("/backups", response_model=Dict[str, Any])
async def list_backups(
    controller: SettingsController = Depends(get_settings_controller)
):
    """
    List all available settings backups
    
    Returns a list of backups with metadata (date, size, etc.)
    """
    try:
        result = await controller.list_backups()
        return result
    except Exception as e:
        logger.error(f"Failed to list backups: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backups", response_model=Dict[str, Any])
async def create_backup(
    controller: SettingsController = Depends(get_settings_controller)
):
    """
    Create a new settings backup
    
    Creates a timestamped backup of the current settings.
    """
    try:
        result = await controller.create_backup()
        return result
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backups/{backup_id}/restore", response_model=SettingsResponse)
async def restore_backup(
    backup_id: str,
    controller: SettingsController = Depends(get_settings_controller)
):
    """
    Restore settings from a backup
    
    Replaces current settings with the selected backup.
    """
    try:
        result = await controller.restore_backup(backup_id)
        return SettingsResponse(settings=result["settings"], message=result["message"])
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to restore backup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/backups/{backup_id}", response_model=Dict[str, Any])
async def delete_backup(
    backup_id: str,
    controller: SettingsController = Depends(get_settings_controller)
):
    """
    Delete a settings backup
    
    Removes the specified backup from storage.
    """
    try:
        result = await controller.delete_backup(backup_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete backup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Environment Variables
@router.get("/env", response_model=Dict[str, Any])
async def get_environment_variables(
    controller: SettingsController = Depends(get_settings_controller)
):
    """
    Get application environment variables
    
    Returns a list of environment variables with sensitive values masked.
    """
    try:
        result = await controller.get_environment_variables()
        return result
    except Exception as e:
        logger.error(f"Failed to get environment variables: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/env", response_model=Dict[str, Any])
async def update_environment_variable(
    request: EnvironmentVariableRequest,
    controller: SettingsController = Depends(get_settings_controller)
):
    """
    Update an environment variable (runtime only)
    
    Sets or updates an environment variable for the current session.
    """
    try:
        result = await controller.update_environment_variable(request.key, request.value)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update environment variable: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# System Information
@router.get("/system/info", response_model=Dict[str, Any])
async def get_system_info(
    controller: SettingsController = Depends(get_settings_controller)
):
    """
    Get system information
    
    Returns information about the system hardware and software.
    """
    try:
        result = await controller.get_system_info()
        return result
    except Exception as e:
        logger.error(f"Failed to get system info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system/resources", response_model=Dict[str, Any])
async def get_resource_usage(
    controller: SettingsController = Depends(get_settings_controller)
):
    """
    Get current resource usage
    
    Returns real-time CPU, memory, disk usage and job statistics.
    """
    try:
        result = await controller.get_resource_usage()
        return result
    except Exception as e:
        logger.error(f"Failed to get resource usage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Module-specific settings endpoints
@router.get("/modules/{module_name}", response_model=Dict[str, Any])
async def get_module_settings(
    module_name: str,
    controller: SettingsController = Depends(get_settings_controller)
):
    """
    Get settings for a specific module
    
    Available modules: general, resources, data_collection, preprocessing, 
    tokenization, training, finetuning, optimization, deployment, pipeline,
    storage, security, notifications
    """
    try:
        settings = await controller.get_settings()
        
        if module_name not in settings:
            raise HTTPException(status_code=404, detail=f"Module '{module_name}' not found")
        
        return {
            "module": module_name,
            "settings": settings[module_name]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get module settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/modules/{module_name}", response_model=Dict[str, Any])
async def update_module_settings(
    module_name: str,
    updates: Dict[str, Any],
    controller: SettingsController = Depends(get_settings_controller)
):
    """
    Update settings for a specific module
    
    Updates only the specified module's configuration.
    """
    try:
        # Validate module exists
        settings = await controller.get_settings()
        if module_name not in settings:
            raise HTTPException(status_code=404, detail=f"Module '{module_name}' not found")
        
        # Update only that module
        result = await controller.update_settings({module_name: updates})
        
        return {
            "module": module_name,
            "settings": result["settings"][module_name],
            "message": f"Module '{module_name}' settings updated"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update module settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Validation endpoint
@router.post("/validate", response_model=Dict[str, Any])
async def validate_settings(
    settings: Dict[str, Any],
    controller: SettingsController = Depends(get_settings_controller)
):
    """
    Validate settings without saving
    
    Checks if the provided settings configuration is valid.
    """
    try:
        # Basic validation
        errors = []
        
        # Check required top-level sections
        required_sections = ["general", "resources", "storage", "security"]
        for section in required_sections:
            if section not in settings:
                errors.append(f"Missing required section: {section}")
        
        # Validate resource limits
        if "resources" in settings:
            resources = settings["resources"]
            if resources.get("cpu_limit", 0) < 1:
                errors.append("cpu_limit must be at least 1")
            if resources.get("memory_limit_gb", 0) < 1:
                errors.append("memory_limit_gb must be at least 1")
        
        # Validate storage paths
        if "storage" in settings:
            storage = settings["storage"]
            if storage.get("backup_interval_days", 0) < 1:
                errors.append("backup_interval_days must be at least 1")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "message": "Settings are valid" if len(errors) == 0 else f"Found {len(errors)} validation errors"
        }
    except Exception as e:
        logger.error(f"Failed to validate settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))