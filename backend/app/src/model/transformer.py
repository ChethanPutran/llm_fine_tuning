import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

import plotly.graph_objects as go
from plotly.subplots import make_subplots

class BERT:
    """BERT model with attention analysis capabilities"""
    
    def __init__(self, model_name='bert-base-uncased'):
        from transformers import BertModel, BertTokenizer
        self.tokenizer = BertTokenizer.from_pretrained(model_name)
        self.model = BertModel.from_pretrained(model_name, output_attentions=True)
        self.model.eval()

    def analyze_attention(self, text):
        """Analyze attention patterns for given text"""
        inputs = self.tokenizer(text, return_tensors='pt', truncation=True, padding=True)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
        
        attentions = outputs.attentions  # List of [batch, heads, seq_len, seq_len]
        tokens = self.tokenizer.convert_ids_to_tokens(inputs['input_ids'][0])
        
        return {
            'attentions': attentions,
            'tokens': tokens
        }
    def visualize_attention(self, attentions, tokens, layer_idx=-1, head_idx=0):
        """Visualize attention patterns for specific layer and head"""
        if layer_idx < 0:
            layer_idx = len(attentions) + layer_idx
        
        attention = attentions[layer_idx][0, head_idx].cpu().numpy()  # [seq_len, seq_len]
        
        fig = go.Figure(data=go.Heatmap(
            z=attention,
            x=tokens,
            y=tokens,
            colorscale='Viridis',
            colorbar=dict(title="Attention Weight")
        ))
        
        fig.update_layout(
            title=f'Attention Pattern - Layer {layer_idx}, Head {head_idx}',
            xaxis_title='Key Tokens',
            yaxis_title='Query Tokens',
            height=600
        )
        
        return fig

class GPT2:
    """GPT-2 model with attention analysis capabilities"""
    
    def __init__(self, model_name='gpt2'):
        from transformers import GPT2Model, GPT2Tokenizer
        self.tokenizer = GPT2Tokenizer.from_pretrained(model_name)
        self.model = GPT2Model.from_pretrained(model_name, output_attentions=True)
        self.model.eval()

    def analyze_attention(self, text):
        """Analyze attention patterns for given text"""
        inputs = self.tokenizer(text, return_tensors='pt', truncation=True, padding=True)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
        
        attentions = outputs.attentions  # List of [batch, heads, seq_len, seq_len]
        tokens = self.tokenizer.convert_ids_to_tokens(inputs['input_ids'][0])
        
        return {
            'attentions': attentions,
            'tokens': tokens
        }
    
    def visualize_attention(self, attentions, tokens, layer_idx=-1, head_idx=0):
        """Visualize attention patterns for specific layer and head"""
        if layer_idx < 0:
            layer_idx = len(attentions) + layer_idx
        
        attention = attentions[layer_idx][0, head_idx].cpu().numpy()  # [seq_len, seq_len]
        
        fig = go.Figure(data=go.Heatmap(
            z=attention,
            x=tokens,
            y=tokens,
            colorscale='Viridis',
            colorbar=dict(title="Attention Weight")
        ))
        
        fig.update_layout(
            title=f'Attention Pattern - Layer {layer_idx}, Head {head_idx}',
            xaxis_title='Key Tokens',
            yaxis_title='Query Tokens',
            height=600
        )
        
        return fig

class MiniTransformer(nn.Module):
    """
    Simplified Transformer implementation for educational purposes
    """
    def __init__(self, vocab_size=30522, d_model=512, nhead=8, 
                 num_layers=6, dim_feedforward=2048, max_seq_len=512):
        super().__init__()
        
        self.d_model = d_model
        self.max_seq_len = max_seq_len
        
        # Embeddings
        self.token_embedding = nn.Embedding(vocab_size, d_model)
        self.position_embedding = nn.Embedding(max_seq_len, d_model)
        
        # Transformer encoder layers
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=0.1,
            activation='gelu',
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers)
        
        # Output layer
        self.lm_head = nn.Linear(d_model, vocab_size)
        
        # Initialize weights
        self._init_weights()
        
    def _init_weights(self):
        """Initialize weights like in original Transformer paper"""
        for p in self.parameters():
            if p.dim() > 1:
                nn.init.xavier_uniform_(p)
    
    def create_position_ids(self, seq_len, device):
        """Create position ids for positional encoding"""
        position_ids = torch.arange(seq_len, dtype=torch.long, device=device)
        position_ids = position_ids.unsqueeze(0).expand(1, -1)
        return position_ids
    
    def forward(self, input_ids, attention_mask=None, return_attentions=False):
        """
        Forward pass through mini-transformer
        
        Args:
            input_ids: [batch_size, seq_len]
            attention_mask: [batch_size, seq_len]
            return_attentions: Whether to return attention weights
        """
        batch_size, seq_len = input_ids.shape
        
        # Create token embeddings
        token_embeds = self.token_embedding(input_ids)  # [batch, seq_len, d_model]
        
        # Create position embeddings
        position_ids = self.create_position_ids(seq_len, input_ids.device)
        position_embeds = self.position_embedding(position_ids)  # [1, seq_len, d_model]
        
        # Combine embeddings
        embeddings = token_embeds + position_embeds
        
        # Create padding mask if not provided
        if attention_mask is None:
            attention_mask = torch.ones(batch_size, seq_len, device=input_ids.device)
        
        # Transformer expects mask where 0 means attend, 1 means ignore
        # Convert from 1=attend, 0=ignore to opposite
        key_padding_mask = (1 - attention_mask).bool()

        
        
        # Pass through transformer
        if return_attentions:
            # Use custom forward to get attention weights
            outputs = []
            attentions = []
            x = embeddings

            causal_mask = torch.triu(
            torch.ones(seq_len, seq_len, device=x.device), diagonal=1).bool()
            
            # Manually pass through each layer to capture attentions
            for layer in self.transformer.layers:
                # Self-attention
                attn_output, attn_weights = layer.self_attn(
                    x, x, x,
                    attn_mask=causal_mask,
                    key_padding_mask=key_padding_mask)
                # Dropout after attention
                attn_output = layer.dropout1(attn_output)

                # Residual connection
                x = x + attn_output

                # Layer norm
                x = layer.norm1(x)
                
                # Feedforward
                ff_output = layer.linear2(
                    layer.dropout(layer.activation(layer.linear1(x)))
                )

                # Dropout after feedforward
                ff_output = layer.dropout2(ff_output)

                # Residual connection
                x = x + ff_output

                # Layer norm
                x = layer.norm2(x)
                
                outputs.append(x)
                attentions.append(attn_weights)
            
            hidden_states = outputs[-1]
        else:
            hidden_states = self.transformer(
                embeddings, 
                src_key_padding_mask=key_padding_mask
            )
            attentions = None
        
        # Language modeling head
        logits = self.lm_head(hidden_states)
        
        return {
            'logits': logits,
            'hidden_states': hidden_states,
            'attentions': attentions
        }

class AttentionAnalyzer:
    """Analyze attention patterns in Transformers"""
    
    def __init__(self, model, tokenizer):
        self.model = model
        self.tokenizer = tokenizer
        
    def analyze_attention_patterns(self, text, layer_idx=-1, head_idx=0):
        """Analyze attention patterns for given text"""
        # Tokenize
        inputs = self.tokenizer(text, return_tensors='pt', truncation=True, padding=True)
        
        # Forward pass with attention
        with torch.no_grad():
            outputs = self.model(**inputs, output_attentions=True)
        
        # Get attention weights
        attentions = outputs.attentions  # List of [batch, heads, seq_len, seq_len]
        
        if layer_idx < 0:
            layer_idx = len(attentions) + layer_idx
        
        # Get attention for specific layer and head
        attention = attentions[layer_idx][0, head_idx].cpu().numpy()  # [seq_len, seq_len]
        
        # Get tokens
        tokens = self.tokenizer.convert_ids_to_tokens(inputs['input_ids'][0])
        
        # Create attention visualization
        fig = go.Figure(data=go.Heatmap(
            z=attention,
            x=tokens,
            y=tokens,
            colorscale='Viridis',
            colorbar=dict(title="Attention Weight")
        ))
        
        fig.update_layout(
            title=f'Attention Pattern - Layer {layer_idx}, Head {head_idx}',
            xaxis_title='Key Tokens',
            yaxis_title='Query Tokens',
            height=600
        )
        
        # Analyze attention patterns
        analysis = self._analyze_attention_matrix(attention, tokens)
        
        return {
            'attention_matrix': attention,
            'tokens': tokens,
            'visualization': fig,
            'analysis': analysis
        }
    
    def _analyze_attention_matrix(self, attention, tokens):
        """Analyze attention matrix for patterns"""
        analysis = {}
        
        # 1. Self-attention (diagonal)
        diagonal = np.diag(attention)
        analysis['self_attention_mean'] = np.mean(diagonal)
        analysis['self_attention_std'] = np.std(diagonal)
        
        # 2. Most attended-to tokens for each token
        top_attentions = []
        for i in range(len(tokens)):
            # Exclude self
            attn_scores = attention[i].copy()
            attn_scores[i] = 0
            
            top_idx = np.argsort(attn_scores)[-3:][::-1]
            top_tokens = [(tokens[idx], attn_scores[idx]) for idx in top_idx]
            top_attentions.append({
                'token': tokens[i],
                'top_attended': top_tokens
            })
        
        analysis['top_attentions'] = top_attentions
        
        # 3. Attention entropy (diversity of attention)
        entropies = []
        for i in range(len(tokens)):
            # Add small epsilon to avoid log(0)
            probs = attention[i] + 1e-10
            probs = probs / probs.sum()
            entropy = -np.sum(probs * np.log(probs))
            entropies.append(entropy)
        
        analysis['attention_entropy_mean'] = np.mean(entropies)
        analysis['attention_entropy_std'] = np.std(entropies)
        
        # 4. Identify special patterns
        analysis['patterns'] = self._identify_patterns(attention, tokens)
        
        return analysis
    
    def _identify_patterns(self, attention, tokens):
        """Identify common attention patterns"""
        patterns = {}
        
        # Look for [CLS] token attention
        if '[CLS]' in tokens:
            cls_idx = tokens.index('[CLS]')
            cls_attention = attention[cls_idx]
            patterns['cls_attends_to'] = [
                (tokens[i], cls_attention[i]) 
                for i in np.argsort(cls_attention)[-5:][::-1]
            ]
        
        # Look for [SEP] token attention
        if '[SEP]' in tokens:
            sep_indices = [i for i, t in enumerate(tokens) if t == '[SEP]']
            for sep_idx in sep_indices:
                sep_attention = attention[sep_idx]
                patterns[f'sep_{sep_idx}_attends_to'] = [
                    (tokens[i], sep_attention[i])
                    for i in np.argsort(sep_attention)[-5:][::-1]
                ]
        
        # Check for local attention (attending to nearby tokens)
        local_attention_scores = []
        for i in range(len(tokens)):
            window_size = 3
            start = max(0, i - window_size)
            end = min(len(tokens), i + window_size + 1)
            local_score = np.sum(attention[i, start:end]) - attention[i, i]
            local_attention_scores.append(local_score)
        
        patterns['local_attention_mean'] = np.mean(local_attention_scores)
        
        return patterns
    
    def compare_attention_heads(self, text, layer_idx=-1):
        """Compare all attention heads in a layer"""
        inputs = self.tokenizer(text, return_tensors='pt')
        
        with torch.no_grad():
            outputs = self.model(**inputs, output_attentions=True)
        
        attentions = outputs.attentions[layer_idx][0]  # [heads, seq_len, seq_len]
        tokens = self.tokenizer.convert_ids_to_tokens(inputs['input_ids'][0])
        n_heads = attentions.shape[0]
        
        # Create subplot for each head
        fig = make_subplots(
            rows=int(np.ceil(n_heads / 4)),
            cols=min(4, n_heads),
            subplot_titles=[f'Head {i}' for i in range(n_heads)]
        )
        
        for head_idx in range(n_heads):
            row = head_idx // 4 + 1
            col = head_idx % 4 + 1
            
            fig.add_trace(
                go.Heatmap(
                    z=attentions[head_idx].cpu().numpy(),
                    x=tokens,
                    y=tokens,
                    colorscale='Viridis',
                    showscale=False
                ),
                row=row, col=col
            )
        
        fig.update_layout(height=300 * int(np.ceil(n_heads / 4)), 
                         title_text=f'Attention Heads - Layer {layer_idx}')
        
        # Analyze head diversity
        head_diversity = []
        for head_idx in range(n_heads):
            attention = attentions[head_idx].cpu().numpy()
            # Calculate entropy of attention distributions
            entropies = []
            for i in range(len(tokens)):
                probs = attention[i] + 1e-10
                probs = probs / probs.sum()
                entropy = -np.sum(probs * np.log(probs))
                entropies.append(entropy)
            head_diversity.append(np.mean(entropies))
        
        return {
            'visualization': fig,
            'head_diversity': head_diversity,
            'tokens': tokens
        }
