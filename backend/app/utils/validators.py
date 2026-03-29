import os
import re
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

class Validator:
    """Validation utilities"""
    
    @staticmethod
    def validate_path(path: str, must_exist: bool = True, 
                      must_be_dir: bool = False) -> bool:
        """Validate file or directory path"""
        if not path:
            return False
        
        path_obj = Path(path)
        
        if must_exist and not path_obj.exists():
            return False
        
        if must_be_dir and not path_obj.is_dir():
            return False
        
        if not must_be_dir and path_obj.is_dir():
            return False
        
        return True
    
    @staticmethod
    def validate_topic(topic: str) -> bool:
        """Validate search topic"""
        if not topic or len(topic) < 2:
            return False
        
        # Check for valid characters
        pattern = r'^[a-zA-Z0-9\s\-_]+$'
        return bool(re.match(pattern, topic))
    
    @staticmethod
    def validate_model_name(model_name: str) -> bool:
        """Validate model name"""
        if not model_name:
            return False
        
        # Check if it's a valid HuggingFace model name or local path
        if '/' in model_name:
            parts = model_name.split('/')
            if len(parts) != 2 or not parts[0] or not parts[1]:
                return False
        
        return True
    
    @staticmethod
    def validate_dataset_format(dataset: Any) -> bool:
        """Validate dataset format"""
        # Check if dataset has required columns
        if hasattr(dataset, 'columns'):
            required_columns = ['text', 'label']
            return all(col in dataset.columns for col in required_columns)
        
        return False
    
    @staticmethod
    def validate_hyperparameters(config: Dict[str, Any]) -> Dict[str, List[str]]:
        """Validate hyperparameters and return errors"""
        errors = {}
        
        # Learning rate validation
        if 'learning_rate' in config:
            lr = config['learning_rate']
            if lr <= 0 or lr > 1:
                errors['learning_rate'] = ['Must be between 0 and 1']
        
        # Batch size validation
        if 'batch_size' in config:
            bs = config['batch_size']
            if bs <= 0 or bs > 1024:
                errors['batch_size'] = ['Must be between 1 and 1024']
        
        # Epochs validation
        if 'num_epochs' in config:
            epochs = config['num_epochs']
            if epochs <= 0 or epochs > 1000:
                errors['num_epochs'] = ['Must be between 1 and 1000']
        
        return errors
    
    @staticmethod
    def validate_tokenizer_type(tokenizer_type: str) -> bool:
        """Validate tokenizer type"""
        valid_types = ['bpe', 'wordpiece', 'sentencepiece']
        return tokenizer_type.lower() in valid_types
    
    @staticmethod
    def validate_optimization_type(opt_type: str) -> bool:
        """Validate optimization type"""
        valid_types = ['pruning', 'distillation', 'quantization']
        return opt_type.lower() in valid_types
    
    @staticmethod
    def validate_deployment_target(target: str) -> bool:
        """Validate deployment target"""
        valid_targets = ['local', 'cloud', 'edge']
        return target.lower() in valid_targets
    
    @staticmethod
    def validate_serving_framework(framework: str) -> bool:
        """Validate serving framework"""
        valid_frameworks = ['torchserve', 'tensorflow-serving', 'onnx']
        return framework.lower() in valid_frameworks
    
    @staticmethod
    def validate_json_schema(data: Dict, schema: Dict) -> List[str]:
        """Validate JSON against schema"""
        errors = []
        
        for required_field in schema.get('required', []):
            if required_field not in data:
                errors.append(f"Missing required field: {required_field}")
        
        for field, field_schema in schema.get('properties', {}).items():
            if field in data:
                field_value = data[field]
                field_type = field_schema.get('type')
                
                if field_type == 'string' and not isinstance(field_value, str):
                    errors.append(f"Field {field} must be string")
                elif field_type == 'integer' and not isinstance(field_value, int):
                    errors.append(f"Field {field} must be integer")
                elif field_type == 'number' and not isinstance(field_value, (int, float)):
                    errors.append(f"Field {field} must be number")
                elif field_type == 'boolean' and not isinstance(field_value, bool):
                    errors.append(f"Field {field} must be boolean")
        
        return errors

class DataValidator:
    """Data validation utilities"""
    
    @staticmethod
    def validate_text_quality(text: str, min_length: int = 50) -> bool:
        """Validate text quality"""
        if not text or len(text) < min_length:
            return False
        
        # Check for too many special characters
        special_chars = sum(1 for c in text if not c.isalnum() and not c.isspace())
        if special_chars / len(text) > 0.5:
            return False
        
        # Check for repetitive content
        words = text.split()
        unique_words = set(words)
        if len(unique_words) / len(words) < 0.1:
            return False
        
        return True
    
    @staticmethod
    def validate_image(image_path: str) -> bool:
        """Validate image file"""
        try:
            from PIL import Image
            img = Image.open(image_path)
            img.verify()
            return True
        except:
            return False
    
    @staticmethod
    def validate_csv_structure(filepath: str, expected_columns: List[str]) -> bool:
        """Validate CSV file structure"""
        import pandas as pd
        
        try:
            df = pd.read_csv(filepath, nrows=1)
            return all(col in df.columns for col in expected_columns)
        except:
            return False

class ConfigValidator:
    """Configuration validation utilities"""
    
    @staticmethod
    def validate_training_config(config: Dict[str, Any]) -> bool:
        """Validate training configuration"""
        required_keys = ['learning_rate', 'batch_size', 'num_epochs']
        
        for key in required_keys:
            if key not in config:
                return False
        
        # Validate values
        if config['learning_rate'] <= 0 or config['learning_rate'] > 1:
            return False
        
        if config['batch_size'] <= 0:
            return False
        
        if config['num_epochs'] <= 0:
            return False
        
        return True
    
    @staticmethod
    def validate_finetuning_config(config: Dict[str, Any]) -> bool:
        """Validate fine-tuning configuration"""
        if not ConfigValidator.validate_training_config(config):
            return False
        
        # Validate strategy-specific configs
        strategy = config.get('strategy', 'full')
        
        if strategy == 'lora':
            if 'lora_r' in config:
                if config['lora_r'] <= 0 or config['lora_r'] > 64:
                    return False
        
        return True