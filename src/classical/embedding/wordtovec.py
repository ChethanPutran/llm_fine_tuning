import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
from collections import Counter
import random

class Word2VecDataset(Dataset):
    def __init__(self, text, window_size=5):
        self.text = text
        self.window_size = window_size
        self.vocab, self.word_to_idx, self.idx_to_word = self.build_vocab(text)
        self.data = self.generate_training_data()
    
    def build_vocab(self, text, min_freq=5):
        words = text.split()
        word_counts = Counter(words)
        vocab = [word for word, count in word_counts.items() if count >= min_freq]
        word_to_idx = {word: idx for idx, word in enumerate(vocab)}
        idx_to_word = {idx: word for idx, word in enumerate(vocab)}
        return vocab, word_to_idx, idx_to_word
    
    def generate_training_data(self):
        data = []
        words = self.text.split()
        
        for i, target_word in enumerate(words):
            if target_word not in self.word_to_idx:
                continue
            
            # Get context words
            start = max(0, i - self.window_size)
            end = min(len(words), i + self.window_size + 1)
            
            context_words = words[start:i] + words[i+1:end]
            
            for context_word in context_words:
                if context_word in self.word_to_idx:
                    data.append((self.word_to_idx[target_word], 
                                self.word_to_idx[context_word]))
        
        return data
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        return torch.tensor(self.data[idx][0]), torch.tensor(self.data[idx][1])

class SkipGramModel(nn.Module):
    def __init__(self, vocab_size, embedding_dim):
        super(SkipGramModel, self).__init__()
        self.input_embeddings = nn.Embedding(vocab_size, embedding_dim)
        self.output_embeddings = nn.Embedding(vocab_size, embedding_dim)
        
        # Initialize weights
        self.input_embeddings.weight.data.uniform_(-0.5/embedding_dim, 0.5/embedding_dim)
        self.output_embeddings.weight.data.uniform_(-0.5/embedding_dim, 0.5/embedding_dim)
    
    def forward(self, target_word):
        # Get input embedding
        input_embedding = self.input_embeddings(target_word)
        
        # Get output embeddings for all words
        output_embeddings = self.output_embeddings.weight
        
        # Calculate scores (dot product)
        scores = torch.matmul(input_embedding, output_embeddings.t())
        
        return scores
    
    def get_embeddings(self):
        return self.input_embeddings.weight.data.cpu().numpy()

def train_word2vec(text, embedding_dim=100, window_size=5, 
                   batch_size=32, epochs=10, learning_rate=0.001):
    
    # Create dataset
    dataset = Word2VecDataset(text, window_size=window_size)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    
    # Initialize model
    vocab_size = len(dataset.vocab)
    model = SkipGramModel(vocab_size, embedding_dim)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    
    # Training loop
    losses = []
    for epoch in range(epochs):
        epoch_loss = 0
        for target, context in dataloader:
            optimizer.zero_grad()
            
            # Forward pass
            scores = model(target)
            
            # Calculate loss
            loss = criterion(scores, context)
            
            # Backward pass
            loss.backward()
            optimizer.step()
            
            epoch_loss += loss.item()
        
        avg_loss = epoch_loss / len(dataloader)
        losses.append(avg_loss)
        print(f"Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.4f}")
    
    return model, dataset

# Example usage
if __name__ == "__main__":
    # Sample text (in practice, use larger corpus like wikiText2)
    sample_text = """
    natural language processing is a field of artificial intelligence 
    that focuses on the interaction between computers and human language 
    machine learning algorithms are used to process and analyze large 
    amounts of natural language data deep learning models have achieved 
    state of the art results in many natural language processing tasks
    """
    
    # Train model
    model, dataset = train_word2vec(
        sample_text,
        embedding_dim=50,
        window_size=3,
        batch_size=16,
        epochs=20,
        learning_rate=0.01
    )
    
    # Get embeddings
    embeddings = model.get_embeddings()
    word_to_idx = dataset.word_to_idx
    
    # Example: Find similar words
    def get_similar_words(word, top_n=5):
        if word not in word_to_idx:
            return []
        
        word_idx = word_to_idx[word]
        word_embedding = embeddings[word_idx]
        
        # Calculate cosine similarities
        similarities = np.dot(embeddings, word_embedding) / (
            np.linalg.norm(embeddings, axis=1) * np.linalg.norm(word_embedding)
        )
        
        # Get top similar words (excluding the word itself)
        similar_indices = np.argsort(similarities)[::-1][1:top_n+1]
        similar_words = [(dataset.idx_to_word[idx], similarities[idx]) 
                        for idx in similar_indices]
        
        return similar_words
    
    # Test
    test_word = "language"
    similar_words = get_similar_words(test_word, top_n=5)
    print(f"\nWords similar to '{test_word}':")
    for word, similarity in similar_words:
        print(f"  {word}: {similarity:.3f}")
    
    # Visualize embeddings (2D projection using PCA)
    from sklearn.decomposition import PCA
    import matplotlib.pyplot as plt
    
    # Reduce dimensions
    pca = PCA(n_components=2)
    embeddings_2d = pca.fit_transform(embeddings)
    
    # Plot
    plt.figure(figsize=(10, 8))
    for word, idx in word_to_idx.items():
        x, y = embeddings_2d[idx]
        plt.scatter(x, y)
        plt.text(x, y, word, fontsize=9)
    
    plt.title("Word Embeddings Visualization (PCA)")
    plt.xlabel("PC1")
    plt.ylabel("PC2")
    plt.grid(alpha=0.3)
    plt.show()
