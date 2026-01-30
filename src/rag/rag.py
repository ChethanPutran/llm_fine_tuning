import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any

class RAGSystem:
    """Retrieval-Augmented Generation System"""
    
    def __init__(self, embedding_model='all-MiniLM-L6-v2'):
        self.embedding_model = SentenceTransformer(embedding_model)
        self.index = None
        self.documents = []
        self.metadata = []
        
    def build_knowledge_base(self, documents: List[str], metadatas: List[Dict] = None):
        """Build FAISS index from documents"""
        print("Building knowledge base...")
        
        self.documents = documents
        self.metadata = metadatas if metadatas else [{} for _ in documents]
        
        # Create embeddings
        embeddings = self.embedding_model.encode(
            documents,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        # Create FAISS index
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)  # L2 distance
        self.index.add(embeddings.astype('float32'))
        
        print(f"Index built with {len(documents)} documents")
        
        return {
            'num_documents': len(documents),
            'embedding_dimension': dimension,
            'index_type': 'FlatL2'
        }
    
    def retrieve(self, query: str, k: int = 5):
        """Retrieve relevant documents for query"""
        if self.index is None:
            raise ValueError("Knowledge base not built. Call build_knowledge_base first.")
        
        # Encode query
        query_embedding = self.embedding_model.encode([query])
        
        # Search
        distances, indices = self.index.search(
            query_embedding.astype('float32'), 
            k
        )
        
        # Get retrieved documents
        retrieved_docs = []
        for idx, dist in zip(indices[0], distances[0]):
            if idx < len(self.documents):  # Valid index
                retrieved_docs.append({
                    'document': self.documents[idx],
                    'metadata': self.metadata[idx],
                    'distance': float(dist),
                    'similarity': 1 / (1 + dist)  # Convert distance to similarity
                })
        
        return retrieved_docs
    
    def generate_with_rag(self, query: str, generator_model, k: int = 3):
        """Generate answer using RAG"""
        # Retrieve relevant documents
        retrieved_docs = self.retrieve(query, k=k)
        
        # Create context
        context = "\n\n".join([
            f"Document {i+1}: {doc['document']}"
            for i, doc in enumerate(retrieved_docs)
        ])
        
        # Create prompt
        prompt = f"""Based on the following context, answer the question.

Context:
{context}

Question: {query}

Answer: """
        
        # Generate answer
        inputs = generator_model.tokenizer(prompt, return_tensors='pt')
        with torch.no_grad():
            outputs = generator_model.model.generate(
                **inputs,
                max_length=200,
                num_beams=3,
                temperature=0.7,
                do_sample=True
            )
        
        answer = generator_model.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract only the answer part (after "Answer: ")
        answer = answer.split("Answer: ")[-1] if "Answer: " in answer else answer
        
        return {
            'answer': answer,
            'context': context,
            'retrieved_docs': retrieved_docs,
            'prompt': prompt
        }
    
    def evaluate_retrieval(self, queries: List[str], ground_truths: List[List[int]]):
        """Evaluate retrieval performance"""
        metrics = {
            'precision@k': [],
            'recall@k': [],
            'mrr': []  # Mean Reciprocal Rank
        }
        
        k_values = [1, 3, 5, 10]
        
        for query, gt_indices in zip(queries, ground_truths):
            # Retrieve documents
            retrieved_docs = self.retrieve(query, k=max(k_values))
            retrieved_indices = [i for i in range(len(retrieved_docs))]
            
            # Calculate metrics for each k
            for k in k_values:
                retrieved_at_k = retrieved_indices[:k]
                
                # Precision@k
                relevant_retrieved = len(set(retrieved_at_k) & set(gt_indices))
                precision = relevant_retrieved / k if k > 0 else 0
                
                # Recall@k
                recall = relevant_retrieved / len(gt_indices) if gt_indices else 0
                
                # Store
                if k not in metrics:
                    metrics[f'precision@{k}'] = []
                    metrics[f'recall@{k}'] = []
                
                metrics[f'precision@{k}'].append(precision)
                metrics[f'recall@{k}'].append(recall)
            
            # MRR
            for rank, idx in enumerate(retrieved_indices, 1):
                if idx in gt_indices:
                    metrics['mrr'].append(1.0 / rank)
                    break
            else:
                metrics['mrr'].append(0.0)
        
        # Average metrics
        avg_metrics = {}
        for key, values in metrics.items():
            avg_metrics[key] = np.mean(values) if values else 0
        
        # Create visualization
        fig = go.Figure()
        
        # Precision@k curve
        precision_values = [avg_metrics.get(f'precision@{k}', 0) for k in k_values]
        fig.add_trace(go.Scatter(
            x=k_values, y=precision_values,
            mode='lines+markers',
            name='Precision@k',
            line=dict(color='blue', width=2)
        ))
        
        # Recall@k curve
        recall_values = [avg_metrics.get(f'recall@{k}', 0) for k in k_values]
        fig.add_trace(go.Scatter(
            x=k_values, y=recall_values,
            mode='lines+markers',
            name='Recall@k',
            line=dict(color='red', width=2)
        ))
        
        fig.update_layout(
            title='Retrieval Performance',
            xaxis_title='k (number of retrieved documents)',
            yaxis_title='Score',
            height=500
        )
        
        return {
            'metrics': avg_metrics,
            'visualization': fig
        }
    
    def hybrid_retrieval(self, query: str, k: int = 5, 
                        sparse_weight: float = 0.3, dense_weight: float = 0.7):
        """Hybrid retrieval combining dense and sparse methods"""
        from sklearn.feature_extraction.text import TfidfVectorizer
        
        # Dense retrieval (already implemented)
        dense_results = self.retrieve(query, k=k*2)  # Get more for reranking
        
        # Sparse retrieval (TF-IDF)
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(self.documents)
        
        # Transform query
        query_vec = vectorizer.transform([query])
        
        # Calculate cosine similarities
        from sklearn.metrics.pairwise import cosine_similarity
        sparse_similarities = cosine_similarity(query_vec, tfidf_matrix).flatten()
        
        # Combine scores
        combined_scores = {}
        for i, doc in enumerate(dense_results):
            doc_idx = self.documents.index(doc['document'])
            
            dense_score = doc['similarity']
            sparse_score = sparse_similarities[doc_idx] if doc_idx < len(sparse_similarities) else 0
            
            # Normalize scores
            combined_score = (dense_weight * dense_score + 
                            sparse_weight * sparse_score)
            
            combined_scores[doc_idx] = {
                'combined_score': combined_score,
                'dense_score': dense_score,
                'sparse_score': sparse_score,
                'document': self.documents[doc_idx]
            }
        
        # Sort by combined score
        sorted_docs = sorted(combined_scores.items(), 
                           key=lambda x: x[1]['combined_score'], 
                           reverse=True)[:k]
        
        return [doc_info for _, doc_info in sorted_docs]

