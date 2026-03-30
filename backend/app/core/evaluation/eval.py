from nltk.translate.bleu_score import sentence_bleu, corpus_bleu
from nltk.translate.meteor_score import meteor_score
from rouge import Rouge
import nltk
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from transformers import AutoTokenizer
import time
import psutil
import torch


class LLMEvaluation:
    """Comprehensive evaluation framework for LLMs"""
    
    def __init__(self):
        self.metrics = {}
        
    def traditional_metrics(self, predictions, references):
        """Calculate traditional NLP metrics"""
        
        
        # Ensure nltk data is available
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
        
        results = {}
        
        # BLEU scores
        try:
            # Tokenize
            pred_tokens = [nltk.word_tokenize(pred.lower()) for pred in predictions]
            ref_tokens = [[nltk.word_tokenize(ref.lower())] for ref in references]
            
            # Calculate BLEU
            bleu1 = corpus_bleu(ref_tokens, pred_tokens, weights=(1, 0, 0, 0))
            bleu2 = corpus_bleu(ref_tokens, pred_tokens, weights=(0.5, 0.5, 0, 0))
            bleu3 = corpus_bleu(ref_tokens, pred_tokens, weights=(0.33, 0.33, 0.33, 0))
            bleu4 = corpus_bleu(ref_tokens, pred_tokens, weights=(0.25, 0.25, 0.25, 0.25))
            
            results['bleu1'] = bleu1
            results['bleu2'] = bleu2
            results['bleu3'] = bleu3
            results['bleu4'] = bleu4
        except Exception as e:
            print(f"BLEU calculation failed: {e}")
        
        # ROUGE scores
        try:
            rouge = Rouge()
            rouge_scores = rouge.get_scores(predictions, references, avg=True)
            results['rouge'] = rouge_scores
        except Exception as e:
            print(f"ROUGE calculation failed: {e}")
        
        # METEOR
        try:
            meteor_scores = []
            for pred, ref in zip(predictions, references):
                score = meteor_score([nltk.word_tokenize(ref)], nltk.word_tokenize(pred))
                meteor_scores.append(score)
            results['meteor'] = np.mean(meteor_scores)
        except Exception as e:
            print(f"METEOR calculation failed: {e}")
        
        # Perplexity (simplified)
        try:
            # This would require a proper language model
            # For demo, return placeholder
            results['perplexity'] = None
        except:
            results['perplexity'] = None
        
        return results
    
    def llm_based_evaluation(self, predictions, references, 
                           questions=None, evaluator_model='gpt-3.5-turbo'):
        """Use LLM as evaluator"""
        
        
        # This requires OpenAI API key
        # For demo, return simulated results
        
        simulated_results = {
            'factual_accuracy': np.random.uniform(0.7, 0.95),
            'coherence': np.random.uniform(0.6, 0.9),
            'relevance': np.random.uniform(0.8, 0.98),
            'fluency': np.random.uniform(0.7, 0.95),
            'overall_quality': np.random.uniform(0.7, 0.9)
        }
        
        # In practice, you would call OpenAI API like:
        prompt = f"""
        Evaluate the following answer:
        
        Questions: {questions}
        Reference Answers: {references}
        Model Answers: {predictions}
        
        Please rate on a scale of 1-5:
        1. Factual Accuracy
        2. Coherence
        3. Relevance
        4. Fluency
        5. Overall Quality
        
        Return as JSON.
        """
        
        # response = openai.ChatCompletion.create(...)
        
        return simulated_results
    
    def efficiency_metrics(self, model, input_text, device='cuda'):
        """Measure model efficiency"""
        
        
        metrics = {}
        
        # Memory usage before
        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Tokenize
        tokenizer = AutoTokenizer.from_pretrained('bert-base-uncased')
        inputs = tokenizer(input_text, return_tensors='pt').to(device)
        
        # Warmup
        with torch.no_grad():
            _ = model(**inputs)
        
        # Inference time
        start_time = time.time()
        with torch.no_grad():
            outputs = model(**inputs)
        inference_time = (time.time() - start_time) * 1000  # ms
        
        # Memory after
        memory_after = process.memory_info().rss / 1024 / 1024
        memory_increase = memory_after - memory_before
        
        # Throughput
        num_tokens = inputs['input_ids'].shape[1]
        throughput = num_tokens / (inference_time / 1000)  # tokens per second
        
        # Model size
        param_count = sum(p.numel() for p in model.parameters())
        
        metrics.update({
            'inference_time_ms': inference_time,
            'memory_increase_mb': memory_increase,
            'throughput_tokens_per_sec': throughput,
            'parameter_count': param_count,
            'model_size_mb': param_count * 4 / 1024 / 1024,  # Assuming float32
            'sequence_length': num_tokens
        })
        
        return metrics
    
    def create_evaluation_dashboard(self, evaluation_results):
        """Create comprehensive evaluation dashboard"""
        fig = make_subplots(
            rows=2, cols=3,
            subplot_titles=('BLEU Scores', 'ROUGE Scores', 'LLM-based Evaluation',
                          'Efficiency Metrics', 'Throughput Comparison', 'Memory Usage'),
            specs=[[{'type': 'bar'}, {'type': 'bar'}, {'type': 'radar'}],
                  [{'type': 'bar'}, {'type': 'bar'}, {'type': 'bar'}]]
        )
        
        # 1. BLEU Scores
        if 'traditional' in evaluation_results:
            bleu_scores = evaluation_results['traditional'].get('bleu', {})
            if bleu_scores:
                fig.add_trace(
                    go.Bar(
                        x=list(bleu_scores.keys()),
                        y=list(bleu_scores.values()),
                        name='BLEU'
                    ),
                    row=1, col=1
                )
        
        # 2. ROUGE Scores
        if 'traditional' in evaluation_results:
            rouge_scores = evaluation_results['traditional'].get('rouge', {})
            if rouge_scores:
                for rouge_type in ['rouge-1', 'rouge-2', 'rouge-l']:
                    if rouge_type in rouge_scores:
                        fig.add_trace(
                            go.Bar(
                                x=['f', 'p', 'r'],
                                y=[rouge_scores[rouge_type]['f'],
                                  rouge_scores[rouge_type]['p'],
                                  rouge_scores[rouge_type]['r']],
                                name=rouge_type
                            ),
                            row=1, col=2
                        )
        
        # 3. LLM-based Evaluation (Radar chart)
        if 'llm_based' in evaluation_results:
            llm_metrics = evaluation_results['llm_based']
            categories = list(llm_metrics.keys())
            values = list(llm_metrics.values())
            
            # Close the radar chart
            categories = categories + [categories[0]]
            values = values + [values[0]]
            
            fig.add_trace(
                go.Scatterpolar(
                    r=values,
                    theta=categories,
                    fill='toself',
                    name='LLM Evaluation'
                ),
                row=1, col=3
            )
        
        # 4. Efficiency Metrics
        if 'efficiency' in evaluation_results:
            eff_metrics = evaluation_results['efficiency']
            metrics_to_plot = ['inference_time_ms', 'memory_increase_mb', 
                             'throughput_tokens_per_sec']
            
            for i, metric in enumerate(metrics_to_plot):
                if metric in eff_metrics:
                    fig.add_trace(
                        go.Bar(
                            x=[metric],
                            y=[eff_metrics[metric]],
                            name=metric
                        ),
                        row=2, col=1
                    )
        
        fig.update_layout(height=800, showlegend=True, title_text="LLM Evaluation Dashboard")
        
        return fig
