import torch
import torch.nn as nn
import torch.functional as F
from torch.optim import Adam
from torch.utils.data import TensorDataset,DataLoader
from NLP.pre_processing import PositionalEncoding, Embedding, generate_vocaculary, get_one_hot