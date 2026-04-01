from abc import abstractmethod

from app.core.config import settings
from datetime import datetime
import pandas as pd
import os
import torch
from torch.utils.data import Dataset, DataLoader


class BaseDataset(Dataset):
    """Base class for datasets"""
    
    @abstractmethod
    def load_data(self):
        """Load data from source"""
        raise NotImplementedError("Must implement load_data method")
    @abstractmethod
    def get_train_data(self):
        """Get training data"""
        pass
    
    @abstractmethod
    def get_eval_data(self):
        """Get evaluation data"""
        pass