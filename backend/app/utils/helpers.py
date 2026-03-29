import os
import json
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime
import yaml
import numpy as np


def save_json(data: Any, filepath: str) -> None:
    """Save data to JSON file"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_json(filepath: str) -> Any:
    """Load data from JSON file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_yaml(data: Any, filepath: str) -> None:
    """Save data to YAML file"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False)

def load_yaml(filepath: str) -> Any:
    """Load data from YAML file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def generate_id(data: Any) -> str:
    """Generate unique ID from data"""
    return hashlib.md5(str(data).encode()).hexdigest()

def format_size(bytes_size: int) -> str:
    """Format bytes to human readable size"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} TB"

def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """Split list into chunks"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def timestamp() -> str:
    """Get current timestamp string"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

class ProgressTracker:
    """Track progress for long-running operations"""
    
    def __init__(self, total: int, update_interval: int = 10):
        self.total = total
        self.current = 0
        self.update_interval = update_interval
        self.start_time = datetime.now()
        
    def update(self, step: int = 1) -> bool:
        """Update progress and return whether to log"""
        self.current += step
        return self.current % self.update_interval == 0 or self.current == self.total
    
    def get_progress(self) -> float:
        """Get progress percentage"""
        return (self.current / self.total) * 100 if self.total > 0 else 0
    
    def get_elapsed_time(self) -> float:
        """Get elapsed time in seconds"""
        return (datetime.now() - self.start_time).total_seconds()
    
    def get_estimated_remaining(self) -> float:
        """Get estimated remaining time in seconds"""
        if self.current == 0:
            return 0
        elapsed = self.get_elapsed_time()
        remaining = (elapsed / self.current) * (self.total - self.current)
        return remaining
    
    def format_time(self, seconds: float) -> str:
        """Format seconds to readable time"""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            return f"{seconds / 60:.0f}m"
        else:
            return f"{seconds / 3600:.1f}h"
