def main():
    """Main pipeline for LLM fine-tuning project"""
    print("=== LLM Fine-Tuning & Optimization Project ===\n")
    
    # 1. Classical NLP
    print("1. Running Classical NLP Pipeline...")
    nlp = ClassicalNLP('ag_news')
    texts, labels = nlp.load_and_preprocess(n_samples=1000)
    
    # Classical ML pipeline
    classical_results = nlp.classical_ml_pipeline(texts, labels)
    classical_results['visualization'].write_html("classical_ml_comparison.html")
    print(f"✓ Best classical model accuracy: "
          f"{classical_results['comparison_df']['Accuracy'].max():.3f}")
    
    # 2. Transformer Analysis
    print("\n2. Analyzing Transformer Architecture...")
    from transformers import AutoModel, AutoTokenizer
    
    model_name = 'bert-base-uncased'
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name, output_attentions=True)
    
    analyzer = AttentionAnalyzer(model, tokenizer)
    
    # Analyze attention patterns
    sample_text = "The quick brown fox jumps over the lazy dog."
    attention_analysis = analyzer.analyze_attention_patterns(sample_text)
    attention_analysis['visualization'].write_html("attention_analysis.html")
    
    # Compare attention heads
    heads_comparison = analyzer.compare_attention_heads(sample_text, layer_idx=0)
    heads_comparison['visualization'].write_html("attention_heads_comparison.html")
    
    print("✓ Transformer analysis complete")
    
    # 3. Efficient Fine-Tuning Comparison
    print("\n3. Comparing Efficient Fine-Tuning Methods...")
    
    # For demo, create synthetic dataset
    from datasets import Dataset
    import torch
    
    # Create synthetic dataset
    train_data = {
        'text': texts[:800],
        'label': labels[:800]
    }
    val_data = {
        'text': texts[800:],
        'label': labels[800:]
    }
    
    # Tokenize
    def tokenize_function(examples):
        return tokenizer(examples['text'], padding='max_length', truncation=True)
    
    train_dataset = Dataset.from_dict(train_data)
    val_dataset = Dataset.from_dict(val_data)
    
    train_dataset = train_dataset.map(tokenize_function, batched=True)
    val_dataset = val_dataset.map(tokenize_function, batched=True)
    
    train_dataset.set_format(type='torch', columns=['input_ids', 'attention_mask', 'label'])
    val_dataset.set_format(type='torch', columns=['input_ids', 'attention_mask', 'label'])
    
    # Compare methods
    efficient_ft = EfficientFineTuning(model_name)
    ft_results = efficient_ft.compare_methods(
        train_dataset, val_dataset, n_epochs=2, batch_size=4
    )
    
    ft_results['comparison_plot'].write_html("fine_tuning_comparison.html")
    ft_results['tradeoff_plot'].write_html("efficiency_tradeoff.html")
    
    print("✓ Fine-tuning comparison complete")
    
    # 4. RAG System
    print("\n4. Building RAG System...")
    rag = RAGSystem()
    
    # Build knowledge base with sample documents
    sample_docs = [
        "Machine learning is a subset of artificial intelligence.",
        "Deep learning uses neural networks with multiple layers.",
        "Transformers are a type of neural network architecture.",
        "BERT is a popular transformer model for NLP tasks.",
        "Fine-tuning adapts pre-trained models to specific tasks."
    ]
    
    rag.build_knowledge_base(sample_docs)
    
    # Test retrieval
    query = "What is machine learning?"
    retrieved = rag.retrieve(query, k=2)
    print(f"Retrieved for '{query}':")
    for i, doc in enumerate(retrieved):
        print(f"  {i+1}. {doc['document'][:50]}... (similarity: {doc['similarity']:.3f})")
    
    # 5. Evaluation Framework
    print("\n5. Setting up Evaluation Framework...")
    evaluator = LLMEvaluation()
    
    # Sample predictions and references
    predictions = ["Machine learning is a field of AI.", "Deep learning uses neural networks."]
    references = ["Machine learning is a subset of artificial intelligence.", 
                 "Deep learning utilizes neural networks with multiple layers."]
    
    # Traditional metrics
    traditional_metrics = evaluator.traditional_metrics(predictions, references)
    
    # LLM-based evaluation (simulated)
    llm_metrics = evaluator.llm_based_evaluation(predictions, references)
    
    # Efficiency metrics
    efficiency_metrics = evaluator.efficiency_metrics(model, sample_text)
    
    # Create dashboard
    evaluation_results = {
        'traditional': traditional_metrics,
        'llm_based': llm_metrics,
        'efficiency': efficiency_metrics
    }
    
    dashboard = evaluator.create_evaluation_dashboard(evaluation_results)
    dashboard.write_html("evaluation_dashboard.html")
    
    print("✓ Evaluation framework setup complete")
    
    # 6. Deployment Optimization
    print("\n6. Testing Deployment Optimizations...")
    optimizer = DeploymentOptimizer(model)
    
    # Test different optimizations
    optimizations = {
        'original': model,
        'dynamic_quantized': optimizer.quantization('dynamic')['model'],
        'float16': optimizer.quantization('float16')['model'],
    }
    
    # Note: Actual comparison would require proper test dataloader
    print("✓ Deployment optimization methods defined")
    
    # Summary
    print("\n=== Project Summary ===")
    print(f"✓ Classical NLP: {len(texts)} documents processed")
    print(f"✓ Transformer Analysis: {model_name} analyzed")
    print(f"✓ Fine-Tuning Methods: 5 methods compared")
    print(f"✓ RAG System: {len(sample_docs)} documents indexed")
    print(f"✓ Evaluation: Comprehensive metrics implemented")
    print(f"✓ Deployment: {len(optimizations)} optimization techniques")
    
    print("\n✓ Project complete! Outputs saved as HTML files")
    
    return {
        'classical_nlp': nlp,
        'attention_analyzer': analyzer,
        'efficient_ft': efficient_ft,
        'rag_system': rag,
        'evaluator': evaluator,
        'optimizer': optimizer,
        'results': {
            'classical': classical_results,
            'fine_tuning': ft_results,
            'evaluation': evaluation_results
        }
    }

if __name__ == "__main__":
    results = main()