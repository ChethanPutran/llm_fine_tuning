# End-to-End LLM Fine-Tuning & Post-Training Optimization

A comprehensive framework for architecting, training, and benchmarking Large Language Models (LLMs) using Parameter-Efficient Fine-Tuning (PEFT) and inference optimization techniques. This project explores the "Efficiency-Quality Frontier," balancing model performance with computational constraints.

## Project Overview
As LLMs grow in scale, full-parameter fine-tuning becomes computationally prohibitive. This project provides a modular pipeline to evaluate and deploy optimized models using **PEFT**, **Quantization**, and **Pruning**. It includes a full evaluation suite that measures both linguistic quality and system-level performance.

### Key Features
* **Multi-Strategy Training:** Support for LoRA, Adapter Tuning, Prefix Tuning, BitFit, and Full Fine-Tuning.
* **Optimization Engine:** Implementation of 4-bit/8-bit Quantization (bitsandbytes) and structural pruning.
* **Rigorous Benchmarking:** Dual-mode evaluation tracking NLP metrics (BLEU, ROUGE) and system metrics (latency, memory).
* **RAG Integration:** A Retrieval-Augmented Generation prototype using FAISS for dense vector search.

---

## Technical Architecture
The pipeline follows a modular design to ensure reproducibility and scalability across different model architectures (e.g., Llama, Mistral, T5).



### 1. Parameter-Efficient Fine-Tuning (PEFT)
By freezing the majority of the backbone LLM and only training small "adapter" layers, we significantly reduced the VRAM requirements.
* **LoRA:** Injected low-rank matrices into transformer attention layers.
* **Prefix Tuning:** Optimized a sequence of continuous prompts prefixed to each layer.
* **Adapter Tuning:** Inserted bottleneck layers between existing transformer blocks.

### 2. Model Compression & Inference
To prepare models for production, I implemented post-training optimization:
* **Quantization:** Utilized $NF4$ (4-bit NormalFloat) quantization to reduce memory footprint by ~70% with minimal perplexity degradation.
* **Pruning:** Applied magnitude-based pruning to remove redundant weights, increasing inference throughput.

---

## Evaluation & Metrics
The project features a comparative dashboard to visualize the trade-offs between different tuning methods.

| Metric Type | Indicators Tracked |
| :--- | :--- |
| **NLP Quality** | BLEU, ROUGE (1, 2, L), METEOR |
| **System Performance** | Latency (ms/token), Throughput (tokens/sec) |
| **Resource Efficiency** | VRAM Usage (GB), Model Size (MB) |

---

## Project Structure
```text
├── data/               # Preprocessing scripts and sample datasets
├── src/
│   ├── training/       # PEFT implementation (LoRA, Adapters)
│   ├── evaluation/     # NLP and System metric scripts
│   ├── optimization/   # Quantization and Pruning logic
│   └── rag/            # FAISS vector store and retrieval logic
├── notebooks/          # Experimental trials and visualizations
└── dashboard/          # Comparative results and trade-off plots
```

## Getting Started
1. **Install Dependencies:**
   ```bash
   pip install torch transformers peft accelerate bitsandbytes faiss-gpu
   ```
2. **Run Training:**
   ```bash
   python src/training/train.py --method lora --model_name_or_path "mistralai/Mistral-7B-v0.1"
   ```
3. **Evaluate:**
   ```bash
   python src/evaluation/benchmark.py --model_path "./output/lora-model"
   ```

---

## Future Work
* Integration of **QLoRA** for even more aggressive memory savings.
* Implementation of **RLHF** (Reinforcement Learning from Human Feedback) via PPO or DPO.
* Deployment of the inference engine via **vLLM** for continuous batching support.

