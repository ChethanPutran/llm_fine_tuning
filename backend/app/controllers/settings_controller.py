# app/controllers/settings_controller.py

from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
import logging
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import settings
from app.api.websocket import manager

logger = logging.getLogger(__name__)


class SettingsController:
    """Controller for application settings management"""

    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.settings_file = Path(settings.CONFIG_PATH) / "settings.json"
        self.backup_dir = Path(settings.BACKUP_DIR) 
        self._ensure_directories()
        self._load_settings()

    def _ensure_directories(self):
        """Ensure required directories exist"""
        self.settings_file.parent.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def _load_settings(self):
        """Load settings from file"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    self.settings = json.load(f)
            else:
                self.settings = self._get_default_settings()
                self._save_settings()
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            self.settings = self._get_default_settings()
            raise e

    def _save_settings(self):
        """Save settings to file"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2, default=str)
            logger.info("Settings saved successfully")
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            raise

    def _get_default_settings(self) -> Dict[str, Any]:
        """Get default settings configuration"""
        with open(Path(settings.DEFAULT_SETTINGS_FILE_PATH)) as f:
            return json.load(f)

    async def get_settings(self) -> Dict[str, Any]:
        """Get all settings"""
        return self.settings

    async def update_settings(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update settings"""
        try:
            # Deep merge updates
            self._deep_update(self.settings, updates)
            self._save_settings()
            
            # Notify about settings change
            await manager.broadcast_to_all_clients({
                "type": "settings_updated",
                "data": {"timestamp": datetime.now(timezone.utc).isoformat()}
            })
            
            logger.info("Settings updated successfully")
            return {"message": "Settings updated successfully", "settings": self.settings}
        except Exception as e:
            logger.error(f"Failed to update settings: {e}")
            raise

    def _deep_update(self, base: Dict, updates: Dict):
        """Deep update dictionary"""
        for key, value in updates.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value

    async def reset_settings(self) -> Dict[str, Any]:
        """Reset settings to defaults"""
        try:
            self.settings = self._get_default_settings()
            self._save_settings()
            
            logger.info("Settings reset to defaults")
            return {"message": "Settings reset to defaults", "settings": self.settings}
        except Exception as e:
            logger.error(f"Failed to reset settings: {e}")
            raise

    async def export_settings(self) -> Dict[str, Any]:
        """Export settings as JSON"""
        try:
            export_data = {
                "settings": self.settings,
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "version": "1.0"
            }
            return export_data
        except Exception as e:
            logger.error(f"Failed to export settings: {e}")
            raise

    async def import_settings(self, import_data: Dict[str, Any]) -> Dict[str, Any]:
        """Import settings from JSON"""
        try:
            if "settings" in import_data:
                self.settings = import_data["settings"]
            else:
                self.settings = import_data
            
            self._save_settings()
            
            logger.info("Settings imported successfully")
            return {"message": "Settings imported successfully", "settings": self.settings}
        except Exception as e:
            logger.error(f"Failed to import settings: {e}")
            raise

    async def create_backup(self) -> Dict[str, Any]:
        """Create a backup of current settings"""
        try:
            backup_id = f"backup_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
            backup_file = self.backup_dir / f"{backup_id}.json"
            
            backup_data = {
                "backup_id": backup_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "settings": self.settings,
                "version": "1.0"
            }
            
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2, default=str)
            
            # Clean old backups
            await self._clean_old_backups()
            
            logger.info(f"Backup created: {backup_id}")
            return {"message": "Backup created successfully", "backup_id": backup_id}
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise

    async def _clean_old_backups(self):
        """Clean old backups"""
        try:
            backups = sorted(self.backup_dir.glob("backup_*.json"))
            max_backups = self.settings.get("storage", {}).get("max_backups", 10)
            
            if len(backups) > max_backups:
                for backup in backups[:-max_backups]:
                    backup.unlink()
                    logger.info(f"Removed old backup: {backup.name}")
        except Exception as e:
            logger.error(f"Failed to clean old backups: {e}")

    async def list_backups(self) -> Dict[str, Any]:
        """List all available backups"""
        try:
            backups = []
            for backup_file in sorted(self.backup_dir.glob("backup_*.json"), reverse=True):
                try:
                    with open(backup_file, 'r') as f:
                        data = json.load(f)
                        backups.append({
                            "backup_id": data.get("backup_id", backup_file.stem),
                            "created_at": data.get("created_at"),
                            "file_name": backup_file.name,
                            "size_bytes": backup_file.stat().st_size
                        })
                except Exception as e:
                    logger.error(f"Failed to read backup {backup_file}: {e}")
                    continue
            
            return {"backups": backups, "total": len(backups)}
        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
            raise

    async def restore_backup(self, backup_id: str) -> Dict[str, Any]:
        """Restore settings from backup"""
        try:
            backup_file = self.backup_dir / f"{backup_id}.json"
            if not backup_file.exists():
                # Try with .json extension if not provided
                if not backup_id.endswith('.json'):
                    backup_file = self.backup_dir / f"{backup_id}.json"
                if not backup_file.exists():
                    raise ValueError(f"Backup {backup_id} not found")
            
            with open(backup_file, 'r') as f:
                backup_data = json.load(f)
            
            if "settings" in backup_data:
                self.settings = backup_data["settings"]
            else:
                self.settings = backup_data
            
            self._save_settings()
            
            logger.info(f"Restored backup: {backup_id}")
            return {"message": "Backup restored successfully", "settings": self.settings}
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            raise

    async def delete_backup(self, backup_id: str) -> Dict[str, Any]:
        """Delete a backup"""
        try:
            backup_file = self.backup_dir / f"{backup_id}.json"
            if not backup_file.exists():
                if not backup_id.endswith('.json'):
                    backup_file = self.backup_dir / f"{backup_id}.json"
                if not backup_file.exists():
                    raise ValueError(f"Backup {backup_id} not found")
            
            backup_file.unlink()
            
            logger.info(f"Deleted backup: {backup_id}")
            return {"message": f"Backup {backup_id} deleted successfully"}
        except Exception as e:
            logger.error(f"Failed to delete backup: {e}")
            raise

    async def get_environment_variables(self) -> Dict[str, Any]:
        """Get environment variables (masked)"""
        try:
            # Get relevant environment variables
            env_vars = {}
            sensitive_keys = ['KEY', 'SECRET', 'PASSWORD', 'TOKEN', 'API_KEY']
            
            for key, value in os.environ.items():
                # Filter to show only relevant app variables
                if key.startswith(('APP_', 'ML_', 'MODEL_', 'DATA_', 'API_', 'DB_', 'REDIS_')):
                    # Mask sensitive values
                    if any(sensitive in key.upper() for sensitive in sensitive_keys):
                        env_vars[key] = '***MASKED***'
                    else:
                        env_vars[key] = value
            
            return {"environment_variables": env_vars, "count": len(env_vars)}
        except Exception as e:
            logger.error(f"Failed to get environment variables: {e}")
            raise

    async def update_environment_variable(self, key: str, value: str) -> Dict[str, Any]:
        """Update an environment variable (runtime only)"""
        try:
            # Validate key
            if not key.startswith(('APP_', 'ML_', 'MODEL_', 'DATA_', 'API_', 'DB_', 'REDIS_')):
                raise ValueError("Cannot update system environment variables")
            
            os.environ[key] = value
            
            # Update in-memory settings if applicable
            if key in self.settings:
                self._update_settings_from_env(key, value)
            
            logger.info(f"Updated environment variable: {key}")
            return {"message": f"Environment variable {key} updated", "key": key}
        except Exception as e:
            logger.error(f"Failed to update environment variable: {e}")
            raise

    def _update_settings_from_env(self, key: str, value: str):
        """Update settings from environment variable"""
        # Map environment variables to settings paths
        mapping = {
            "APP_DEBUG": ("general", "debug_mode"),
            "APP_LOG_LEVEL": ("general", "log_level"),
            "ML_MAX_CONCURRENT_JOBS": ("general", "max_concurrent_jobs"),
            "DATA_STORAGE_PATH": ("storage", "data_path"),
            "MODEL_STORAGE_PATH": ("storage", "model_path"),
        }
        
        if key in mapping:
            path = mapping[key]
            if len(path) == 2:
                if path[0] in self.settings:
                    self.settings[path[0]][path[1]] = value
            self._save_settings()

    async def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        import psutil
        import platform
        
        try:
            system_info = {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "hostname": platform.node(),
                "cpu_count": psutil.cpu_count(),
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory": {
                    "total_gb": psutil.virtual_memory().total / (1024**3),
                    "available_gb": psutil.virtual_memory().available / (1024**3),
                    "percent": psutil.virtual_memory().percent
                },
                "disk": {
                    "total_gb": psutil.disk_usage('/').total / (1024**3),
                    "used_gb": psutil.disk_usage('/').used / (1024**3),
                    "free_gb": psutil.disk_usage('/').free / (1024**3),
                    "percent": psutil.disk_usage('/').percent
                },
                "app_version": self.settings.get("general", {}).get("version", "1.0.0"),
                "uptime_seconds": self._get_uptime()
            }
            
            return system_info
        except Exception as e:
            logger.error(f"Failed to get system info: {e}")
            raise

    def _get_uptime(self) -> float:
        """Get system uptime"""
        try:
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.readline().split()[0])
                return uptime_seconds
        except:
            return 0

    async def get_resource_usage(self) -> Dict[str, Any]:
        """Get current resource usage"""
        import psutil
        
        try:
            resource_usage = {
                "cpu": {
                    "percent": psutil.cpu_percent(interval=1),
                    "per_cpu": psutil.cpu_percent(interval=1, percpu=True)
                },
                "memory": {
                    "percent": psutil.virtual_memory().percent,
                    "used_gb": psutil.virtual_memory().used / (1024**3),
                    "available_gb": psutil.virtual_memory().available / (1024**3)
                },
                "disk": {
                    "percent": psutil.disk_usage('/').percent,
                    "used_gb": psutil.disk_usage('/').used / (1024**3),
                    "free_gb": psutil.disk_usage('/').free / (1024**3)
                },
                "active_jobs": len(self.orchestrator.get_active_jobs()) if hasattr(self.orchestrator, 'active_jobs') else 0,
                "queued_jobs": len(await self.orchestrator.get_queued_jobs()) if hasattr(self.orchestrator, 'job_queue') else 0
            }
            
            return resource_usage
        except Exception as e:
            logger.error(f"Failed to get resource usage: {e}")
            raise