import numpy as np
import torch
import torch.nn as nn
from torch.optim import Adam
from torch.distributions.uniform import Uniform
from torch.utils.data import TensorDataset, DataLoader
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import math


# seaborn==0.13.2
# matplotlib==3.10.1
# pandas==2.2.3
# torch==2.6.0
# Positinal Encding with Sine and Cosine signals
class PositionalEncoding(nn.Module):
    def __init__(self, emb_size, max_len=100):
        pos = torch.arange(0, max_len).reshape(
            max_len, 1)  # Position of the word in sentence
        # 1000^(-2i/d_max) = e^(-2i*ln(1000)/d_max) 2i = arange(emb_size/2,2)
        dim = torch.exp(-torch.arange(0, emb_size, 2)*math.log(1000)/emb_size)

        self.pos_encodings = torch.zeros(
            (max_len, emb_size))  # Initialize pos encoding mat
        # Altername sin signals sin(k),sin(2k),...
        self.pos_encodings[:, 0::2] = torch.sin(pos*dim)
        # Altername cos signals cos(k),cos(2k),...
        self.pos_encodings[:, 1::2] = torch.cos(pos*dim)
        self.pos_encodings.unsqueeze(-2),  # Format 1*emb_size vector

    def forward(self, token_embedding: torch.Tensor):
        return token_embedding + self.pos_encodings


class DataGen:
    vocabulary = {}
    vocab_size = 0

    def __init__(self, vocabulary, data):
        self.data = data
        self.i = -1

    def __len__(self):
        return self.size

    def __call__(self):
        self.i += 1
        return self.data[self.i].split()


class Embedding(nn.Module):
    def __init__(self, emd_size, vocab_size):
        super().__init__()

        self.W1 = nn.Parameter(torch.randn((emd_size, vocab_size)))
        self.W2 = nn.Parameter(torch.randn((vocab_size, emd_size)))

    def forward(self, x):
        out = self.W1 @ x
        out = self.W2 @ out
        out = torch.nn.functional.softmax(out.squeeze(-1), dim=1)
        return out


def get_vocab_indices(vocab: dict):
    return list(vocab.values())


def test_positional_encoding(vocab_size, emd_size):
    # Create word embedding
    embedding = nn.Embedding(vocab_size, emd_size)
    test_embedding = embedding(torch.tensor(get_vocab_indices(vocab)))

    # Create positional encoding
    pos_encoding = PositionalEncoding(emd_size)

    # Add positional encoding
    encoded_tokens = pos_encoding(test_embedding)

    print(encoded_tokens)


def generate_vocaculary(data_):
    data = data_.replace("!", "")
    sentences = list(map(str.strip, data.split("\n")))
    vocabulary_set = set(word.lower()
                         for sentence in sentences for word in sentence.split())
    vocabulary = {item: i for i, item in enumerate(vocabulary_set)}
    n = len(vocabulary)
    vocabulary['<sos>'] = n
    vocabulary['<eos>'] = n+1
    vocabulary['<unk>'] = n+2
    vocabulary['<pad>'] = n+3
    return vocabulary


def get_one_hot(token, vocab_size, vocabulary={}):
    one_hot = torch.tensor([0 for _ in range(vocab_size)])
    idx = token if isinstance(token, int) else vocabulary.get(token)
    one_hot[idx] = 1
    return one_hot


def train(data, vocabulary, epochs=10):
    gen = DataGen(vocabulary, data)

    training_set = gen.get_training_data()

    X = []
    y = []

    for i in range(len(training_set)-1):
        token = training_set[i]
        X.append(get_one_hot(token, len(vocabulary), vocabulary))
        y.append(get_one_hot(training_set[i+1], len(vocabulary), vocabulary).squeeze())

    loss_func = nn.CrossEntropyLoss()
    optimizer = Adam(emdr.parameters(), lr=0.01)
    X_tensor = torch.stack(X)
    y_tensor = torch.stack(y)

    for epoch in range(epochs):
        # Shape: (batch_size, vocab_size)
        pred = emdr(X_tensor)
        # Compare to next word one-hot
        loss = loss_func(pred, y_tensor)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        if epoch % 1 == 0:
            print(f"Epoch {epoch}, Loss: {loss.item():.4f}")

    


if __name__ == "__main__":

    data = """Troll2 is great!
            Gymkata is great!"""

    vocab = generate_vocaculary(data)

    VOCAB_SIZE = len(vocab)
    EMBEDDING_SIZE = 10

    emdr = Embedding(EMBEDDING_SIZE, VOCAB_SIZE)
