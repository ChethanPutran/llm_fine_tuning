from app.core.config import settings
from datetime import datetime
import pandas as pd
import os
import torch
from torch.utils.data import Dataset, DataLoader


class TextDataset(Dataset):
    """Simple text dataset for training"""
    
    def __init__(self, texts, labels, tokenizer, max_length=512):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length
    
    def __len__(self):
        return len(self.texts)
    
    def __getitem__(self, idx):
        text = self.texts[idx]
        label = self.labels[idx]
        
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding='max_length',
            max_length=self.max_length,
            return_tensors='pt'
        )
        
        return {
            'input_ids': encoding['input_ids'].squeeze(),
            'attention_mask': encoding['attention_mask'].squeeze(),
            'labels': torch.tensor(label)
        }


class Datasets:
    @staticmethod
    def get_datasets():
        """Get all available datasets"""
        import os
        from pathlib import Path
        
        data_path = Path(settings.DATA_STORAGE_PATH)
        datasets = []
        
        if data_path.exists():
            for dataset_dir in data_path.glob("*"):
                if dataset_dir.is_dir():
                    datasets.append({
                        "name": dataset_dir.name,
                        "path": str(dataset_dir),
                        "size": sum(f.stat().st_size for f in dataset_dir.rglob('*')) if dataset_dir.exists() else 0,
                        "modified": datetime.fromtimestamp(dataset_dir.stat().st_mtime).isoformat()
                    })

        task = "classification"  # For simplicity, we assume all datasets are for classification. In a real implementation, you would determine this based on the dataset content or metadata.
        # Prepare dataset based on task
        df = pd.read_csv("path_to_your_dataset.csv")  # Replace with actual dataset path

        if task == "classification":
            texts = df['text'].tolist()
            labels = df['label'].tolist()
            
            split_idx = int(len(texts) * 0.8)
            from app.core.pipeline_engine.handlers.training_handler import TextDataset
            train_dataset = TextDataset(
                texts[:split_idx],
                labels[:split_idx],
                model.tokenizer,
                tuning_config.max_length
            )
            eval_dataset = TextDataset(
                texts[split_idx:],
                labels[split_idx:],
                model.tokenizer,
                tuning_config.max_length
            )
        else:
            # For other tasks, implement similar dataset preparation
            train_dataset = None
            eval_dataset = None
        
        return datasets
    
    @staticmethod
    def get_finetuning_datasets(dataset_config):
        """Get datasets suitable for fine-tuning"""
        # For simplicity, we return the same datasets. In a real implementation,
        # you might want to filter or categorize datasets based on their suitability for fine-tuning.
        # Load dataset
        df = pd.read_csv(dataset_config.dataset_path)
        return Datasets.get_datasets()