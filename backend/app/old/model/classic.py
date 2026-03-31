import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation, NMF, TruncatedSVD
from sklearn.manifold import TSNE
from sklearn.cluster import KMeans, DBSCAN
import gensim
from gensim.models import Word2Vec, Doc2Vec
from gensim.models.phrases import Phrases, Phraser
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

class ClassicalNLP:
    def __init__(self, dataset='ag_news'):
        self.dataset = dataset
        self.stop_words = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()
        
    def load_and_preprocess(self, n_samples=5000):
        """Load and preprocess text data"""
        if self.dataset == 'ag_news':
            from datasets import load_dataset
            dataset = load_dataset('ag_news')
            texts = dataset['train']['text'][:n_samples]
            labels = dataset['train']['label'][:n_samples]
        else:
            # Load custom dataset
            df = pd.read_csv('text_data.csv')
            texts = df['text'].tolist()[:n_samples]
            labels = df.get('label', [0]*len(texts))[:n_samples]
        
        # Preprocess
        print("Preprocessing texts...")
        processed_texts = []
        for text in texts:
            processed = self._preprocess_text(text)
            processed_texts.append(processed)
        
        return processed_texts, labels
    
    def _preprocess_text(self, text):
        """Basic text preprocessing"""
        # Lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        
        # Remove user mentions and hashtags
        text = re.sub(r'@\w+|\#\w+', '', text)
        
        # Remove punctuation and numbers
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\d+', ' ', text)
        
        # Tokenize
        tokens = word_tokenize(text)
        
        # Remove stopwords and lemmatize
        tokens = [self.lemmatizer.lemmatize(token) for token in tokens 
                 if token not in self.stop_words and len(token) > 2]
        
        return ' '.join(tokens)
    
    def create_tfidf_features(self, texts, max_features=5000):
        """Create TF-IDF features"""
        print("Creating TF-IDF features...")
        vectorizer = TfidfVectorizer(
            max_features=max_features,
            min_df=5,
            max_df=0.7,
            ngram_range=(1, 2)  # Unigrams and bigrams
        )
        
        tfidf_matrix = vectorizer.fit_transform(texts)
        feature_names = vectorizer.get_feature_names_out()
        
        # Get most important words per document
        important_words = []
        for i in range(min(10, len(texts))):
            feature_index = tfidf_matrix[i, :].nonzero()[1]
            tfidf_scores = zip(feature_index, [tfidf_matrix[i, x] for x in feature_index])
            sorted_words = sorted(tfidf_scores, key=lambda x: x[1], reverse=True)[:10]
            words = [feature_names[i] for i, _ in sorted_words]
            important_words.append(words)
        
        return {
            'matrix': tfidf_matrix,
            'features': feature_names,
            'vectorizer': vectorizer,
            'important_words': important_words
        }
    
    def topic_modeling(self, texts, n_topics=10, method='lda'):
        """Topic modeling using LDA or NMF"""
        print(f"Running {method.upper()} topic modeling...")
        
        # Create document-term matrix
        vectorizer = CountVectorizer(
            max_features=2000,
            min_df=5,
            max_df=0.7,
            stop_words='english'
        )
        dtm = vectorizer.fit_transform(texts)
        feature_names = vectorizer.get_feature_names_out()
        
        if method == 'lda':
            model = LatentDirichletAllocation(
                n_components=n_topics,
                random_state=42,
                learning_method='online',
                max_iter=10
            )
        else:  # NMF
            from sklearn.decomposition import NMF
            model = NMF(
                n_components=n_topics,
                random_state=42,
                max_iter=1000
            )
        
        # Fit model
        model.fit(dtm)
        
        # Get topics
        topics = []
        for topic_idx, topic in enumerate(model.components_):
            top_words_idx = topic.argsort()[:-11:-1]
            top_words = [feature_names[i] for i in top_words_idx]
            topics.append({
                'topic_id': topic_idx,
                'top_words': top_words,
                'word_weights': topic[top_words_idx]
            })
        
        # Get document-topic distributions
        doc_topic_dist = model.transform(dtm)
        
        # Assign dominant topic to each document
        dominant_topics = doc_topic_dist.argmax(axis=1)
        
        return {
            'model': model,
            'topics': topics,
            'doc_topic_dist': doc_topic_dist,
            'dominant_topics': dominant_topics,
            'dtm': dtm,
            'feature_names': feature_names
        }
    
    def word_embeddings(self, texts, method='word2vec'):
        """Create word embeddings using classical methods"""
        print(f"Training {method} embeddings...")
        
        # Tokenize texts
        tokenized_texts = [text.split() for text in texts]
        
        if method == 'word2vec':
            # Train Word2Vec
            model = Word2Vec(
                sentences=tokenized_texts,
                vector_size=100,
                window=5,
                min_count=2,
                workers=4,
                epochs=10
            )
            
            # Get vocabulary
            vocab = list(model.wv.key_to_index.keys())
            
            # Get document vectors by averaging word vectors
            doc_vectors = []
            for tokens in tokenized_texts:
                valid_tokens = [t for t in tokens if t in model.wv]
                if valid_tokens:
                    doc_vector = np.mean([model.wv[t] for t in valid_tokens], axis=0)
                else:
                    doc_vector = np.zeros(model.vector_size)
                doc_vectors.append(doc_vector)
            
            doc_vectors = np.array(doc_vectors)
            
            return {
                'model': model,
                'vocab': vocab,
                'doc_vectors': doc_vectors,
                'embeddings': model.wv
            }
        
        elif method == 'doc2vec':
            # Prepare tagged documents
            tagged_data = [gensim.models.doc2vec.TaggedDocument(
                words=text.split(), tags=[i]
            ) for i, text in enumerate(texts)]
            
            # Train Doc2Vec
            model = Doc2Vec(
                documents=tagged_data,
                vector_size=100,
                window=5,
                min_count=2,
                workers=4,
                epochs=20
            )
            
            # Get document vectors
            doc_vectors = np.array([model.dv[i] for i in range(len(texts))])
            
            return {
                'model': model,
                'doc_vectors': doc_vectors
            }
    
    def classical_ml_pipeline(self, texts, labels):
        """Complete classical ML pipeline for text classification"""
        from sklearn.model_selection import train_test_split
        from sklearn.linear_model import LogisticRegression
        from sklearn.svm import SVC
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.naive_bayes import MultinomialNB
        from sklearn.metrics import classification_report, accuracy_score
        
        # Create different feature representations
        print("Creating multiple feature representations...")
        
        # 1. TF-IDF
        tfidf_result = self.create_tfidf_features(texts, max_features=2000)
        X_tfidf = tfidf_result['matrix']
        
        # 2. Word2Vec document vectors
        w2v_result = self.word_embeddings(texts, 'word2vec')
        X_w2v = w2v_result['doc_vectors']
        
        # 3. Topic features
        lda_result = self.topic_modeling(texts, n_topics=20, method='lda')
        X_topics = lda_result['doc_topic_dist']
        
        # Combine features
        X_combined = np.hstack([X_tfidf.toarray(), X_w2v, X_topics])
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_combined, labels, test_size=0.2, random_state=42, stratify=labels
        )
        
        # Train different models
        models = {
            'Logistic Regression': LogisticRegression(max_iter=1000),
            'SVM': SVC(kernel='linear', probability=True),
            'Random Forest': RandomForestClassifier(n_estimators=100),
            'Naive Bayes': MultinomialNB()
        }
        
        results = {}
        for name, model in models.items():
            print(f"Training {name}...")
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            y_pred_proba = model.predict_proba(X_test) if hasattr(model, 'predict_proba') else None
            
            accuracy = accuracy_score(y_test, y_pred)
            report = classification_report(y_test, y_pred, output_dict=True)
            
            results[name] = {
                'model': model,
                'accuracy': accuracy,
                'report': report,
                'predictions': y_pred,
                'probabilities': y_pred_proba
            }
        
        # Compare results
        comparison_df = pd.DataFrame({
            name: {
                'Accuracy': results[name]['accuracy'],
                'Precision': results[name]['report']['weighted avg']['precision'],
                'Recall': results[name]['report']['weighted avg']['recall'],
                'F1-Score': results[name]['report']['weighted avg']['f1-score']
            }
            for name in results.keys()
        }).T
        
        # Create visualization
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Accuracy', 'Precision', 'Recall', 'F1-Score')
        )
        
        metrics = ['Accuracy', 'Precision', 'Recall', 'F1-Score']
        for i, metric in enumerate(metrics):
            row = i // 2 + 1
            col = i % 2 + 1
            
            fig.add_trace(
                go.Bar(
                    x=comparison_df.index,
                    y=comparison_df[metric],
                    name=metric,
                    text=[f'{v:.3f}' for v in comparison_df[metric]],
                    textposition='auto'
                ),
                row=row, col=col
            )
        
        fig.update_layout(height=600, showlegend=False, title_text="Classical ML Model Comparison")
        
        return {
            'results': results,
            'comparison_df': comparison_df,
            'visualization': fig,
            'features': {
                'tfidf': tfidf_result,
                'word2vec': w2v_result,
                'topics': lda_result
            }
        }
    
    def visualize_embeddings(self, embeddings, words=None, n_words=100):
        """Visualize word embeddings in 2D/3D"""
        if words is None:
            words = list(embeddings.key_to_index.keys())[:n_words]
        
        # Get vectors for selected words
        vectors = np.array([embeddings[word] for word in words])
        
        # Reduce dimensions
        tsne = TSNE(n_components=2, random_state=42, perplexity=30)
        vectors_2d = tsne.fit_transform(vectors)
        
        # Create visualization
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=vectors_2d[:, 0],
            y=vectors_2d[:, 1],
            mode='markers+text',
            text=words,
            textposition='top center',
            marker=dict(size=10, color='blue', opacity=0.7),
            hoverinfo='text'
        ))
        
        fig.update_layout(
            title='Word Embeddings Visualization (t-SNE)',
            xaxis_title='Dimension 1',
            yaxis_title='Dimension 2',
            hovermode='closest'
        )
        
        # Add clustering
        if len(words) > 20:
            # Cluster words
            kmeans = KMeans(n_clusters=min(5, len(words)//10), random_state=42)
            clusters = kmeans.fit_predict(vectors)
            
            # Update plot with colors by cluster
            fig.data = []  # Clear previous traces
            
            for cluster_id in range(max(clusters) + 1):
                mask = clusters == cluster_id
                cluster_words = [words[i] for i in np.where(mask)[0]]
                cluster_vectors = vectors_2d[mask]
                
                fig.add_trace(go.Scatter(
                    x=cluster_vectors[:, 0],
                    y=cluster_vectors[:, 1],
                    mode='markers+text',
                    text=cluster_words,
                    name=f'Cluster {cluster_id}',
                    marker=dict(size=12),
                    textposition='top center'
                ))
        
        return fig