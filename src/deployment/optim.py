
class DeploymentOptimizer:
    """Optimize LLMs for deployment"""
    
    def __init__(self, model):
        self.model = model
        
    def quantization(self, quantization_type='dynamic'):
        """Apply quantization to reduce model size"""
        import torch.quantization
        
        if quantization_type == 'dynamic':
            # Dynamic quantization
            quantized_model = torch.quantization.quantize_dynamic(
                self.model,
                {torch.nn.Linear},  # Quantize linear layers
                dtype=torch.qint8
            )
            
        elif quantization_type == 'static':
            # Static quantization requires calibration
            self.model.eval()
            self.model.qconfig = torch.quantization.get_default_qconfig('fbgemm')
            
            # Prepare for quantization
            torch.quantization.prepare(self.model, inplace=True)
            
            # Calibrate (run inference on calibration dataset)
            # calibration_data = ...
            # for data in calibration_data:
            #     self.model(data)
            
            torch.quantization.convert(self.model, inplace=True)
            quantized_model = self.model
            
        elif quantization_type == 'float16':
            # Mixed precision
            quantized_model = self.model.half()
        
        # Calculate compression ratio
        original_size = sum(p.numel() for p in self.model.parameters()) * 4  # float32
        quantized_size = sum(p.numel() for p in quantized_model.parameters())
        
        if quantization_type == 'float16':
            quantized_size *= 2  # float16
        
        compression_ratio = original_size / quantized_size
        
        return {
            'model': quantized_model,
            'compression_ratio': compression_ratio,
            'original_size_mb': original_size / 1024 / 1024,
            'quantized_size_mb': quantized_size / 1024 / 1024,
            'type': quantization_type
        }
    
    def pruning(self, pruning_amount=0.3, method='magnitude'):
        """Apply pruning to remove unimportant weights"""
        import torch.nn.utils.prune as prune
        
        if method == 'magnitude':
            # Magnitude-based pruning
            parameters_to_prune = []
            for name, module in self.model.named_modules():
                if isinstance(module, torch.nn.Linear):
                    parameters_to_prune.append((module, 'weight'))
            
            prune.global_unstructured(
                parameters_to_prune,
                pruning_method=prune.L1Unstructured,
                amount=pruning_amount
            )
            
            # Remove pruning reparameterization
            for module, _ in parameters_to_prune:
                prune.remove(module, 'weight')
        
        # Calculate sparsity
        total_params = sum(p.numel() for p in self.model.parameters())
        zero_params = sum((p == 0).sum().item() for p in self.model.parameters())
        sparsity = zero_params / total_params
        
        return {
            'model': self.model,
            'sparsity': sparsity,
            'zero_params': zero_params,
            'total_params': total_params,
            'pruning_amount': pruning_amount
        }
    
    def knowledge_distillation(self, teacher_model, student_model, 
                             temperature=2.0, alpha=0.5):
        """Apply knowledge distillation"""
        class DistillationLoss(nn.Module):
            def __init__(self, temperature, alpha):
                super().__init__()
                self.temperature = temperature
                self.alpha = alpha
                self.kl_loss = nn.KLDivLoss(reduction='batchmean')
                self.ce_loss = nn.CrossEntropyLoss()
                
            def forward(self, student_logits, teacher_logits, labels):
                # Soft targets from teacher
                soft_targets = F.log_softmax(teacher_logits / self.temperature, dim=-1)
                soft_pred = F.log_softmax(student_logits / self.temperature, dim=-1)
                
                # KL divergence loss
                distillation_loss = self.kl_loss(soft_pred, soft_targets) * (self.temperature ** 2)
                
                # Hard targets (original task loss)
                student_loss = self.ce_loss(student_logits, labels)
                
                # Combined loss
                total_loss = self.alpha * distillation_loss + (1 - self.alpha) * student_loss
                
                return total_loss
        
        return DistillationLoss(temperature, alpha)
    
    def compare_optimizations(self, test_dataloader, optimizations):
        """Compare different optimization techniques"""
        import time
        
        results = {}
        
        for opt_name, opt_model in optimizations.items():
            print(f"Testing {opt_name}...")
            
            # Inference time
            start_time = time.time()
            correct = 0
            total = 0
            
            with torch.no_grad():
                for batch in test_dataloader:
                    outputs = opt_model(**batch)
                    predictions = torch.argmax(outputs.logits, dim=-1)
                    correct += (predictions == batch['labels']).sum().item()
                    total += len(batch['labels'])
            
            inference_time = time.time() - start_time
            
            # Memory usage
            import gc
            torch.cuda.empty_cache()
            gc.collect()
            
            if torch.cuda.is_available():
                memory_allocated = torch.cuda.memory_allocated() / 1024 / 1024  # MB
                memory_reserved = torch.cuda.memory_reserved() / 1024 / 1024  # MB
            else:
                memory_allocated = 0
                memory_reserved = 0
            
            # Model size
            param_count = sum(p.numel() for p in opt_model.parameters())
            model_size = param_count * 4 / 1024 / 1024  # MB (float32)
            
            # Accuracy
            accuracy = correct / total if total > 0 else 0
            
            results[opt_name] = {
                'inference_time': inference_time,
                'accuracy': accuracy,
                'model_size_mb': model_size,
                'parameter_count': param_count,
                'memory_allocated_mb': memory_allocated,
                'memory_reserved_mb': memory_reserved,
                'throughput_samples_per_sec': total / inference_time
            }
        
        # Create comparison visualization
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Accuracy vs Model Size', 'Inference Time',
                          'Memory Usage', 'Throughput'),
            specs=[[{'type': 'scatter'}, {'type': 'bar'}],
                  [{'type': 'bar'}, {'type': 'bar'}]]
        )
        
        # 1. Accuracy vs Model Size (scatter)
        sizes = [results[name]['model_size_mb'] for name in results.keys()]
        accuracies = [results[name]['accuracy'] for name in results.keys()]
        
        fig.add_trace(
            go.Scatter(
                x=sizes,
                y=accuracies,
                mode='markers+text',
                text=list(results.keys()),
                textposition='top center',
                marker=dict(size=20, color=accuracies, colorscale='Viridis',
                           showscale=True, colorbar=dict(title='Accuracy'))
            ),
            row=1, col=1
        )
        
        # 2. Inference Time
        times = [results[name]['inference_time'] for name in results.keys()]
        fig.add_trace(
            go.Bar(x=list(results.keys()), y=times, name='Inference Time'),
            row=1, col=2
        )
        
        # 3. Memory Usage
        memory = [results[name]['memory_allocated_mb'] for name in results.keys()]
        fig.add_trace(
            go.Bar(x=list(results.keys()), y=memory, name='Memory'),
            row=2, col=1
        )
        
        # 4. Throughput
        throughput = [results[name]['throughput_samples_per_sec'] for name in results.keys()]
        fig.add_trace(
            go.Bar(x=list(results.keys()), y=throughput, name='Throughput'),
            row=2, col=2
        )
        
        fig.update_layout(height=800, title_text="Optimization Techniques Comparison")
        
        return {
            'results': results,
            'comparison_plot': fig
        }
