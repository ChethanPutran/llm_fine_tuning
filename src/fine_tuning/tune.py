import torch
import torch.nn as nn
from transformers import AutoModel, AutoConfig, AutoTokenizer
from peft import LoraConfig, get_peft_model, TaskType
from collections import OrderedDict

class EfficientFineTuning:
    """Compare different efficient fine-tuning methods"""
    
    def __init__(self, model_name='bert-base-uncased'):
        self.model_name = model_name
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.config = AutoConfig.from_pretrained(model_name)


        
class EfficientFineTuning:
    """Compare different efficient fine-tuning methods"""
    
    def __init__(self, model_name='bert-base-uncased'):
        self.model_name = model_name
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.config = AutoConfig.from_pretrained(model_name)
        
    def create_base_model(self):
        """Create base model for fine-tuning"""
        model = AutoModel.from_pretrained(self.model_name)
        return model
    
    def full_fine_tuning(self, model, trainable_layers=None):
        """Full fine-tuning (baseline)"""
        # Freeze all layers first
        for param in model.parameters():
            param.requires_grad = False
        
        if trainable_layers is None:
            # Train all layers
            for param in model.parameters():
                param.requires_grad = True
        else:
            # Train only specified layers
            for name, param in model.named_parameters():
                if any(layer in name for layer in trainable_layers):
                    param.requires_grad = True
        
        trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
        total_params = sum(p.numel() for p in model.parameters())
        
        return {
            'model': model,
            'trainable_params': trainable_params,
            'total_params': total_params,
            'trainable_percentage': trainable_params / total_params * 100
        }
    
    def adapter_tuning(self, model, adapter_dim=64):
        """Adapter-based fine-tuning"""
        # Freeze base model
        for param in model.parameters():
            param.requires_grad = False
        
        # Add adapter layers to each transformer block
        class Adapter(nn.Module):
            def __init__(self, hidden_size, adapter_dim):
                super().__init__()
                self.down_proj = nn.Linear(hidden_size, adapter_dim)
                self.up_proj = nn.Linear(adapter_dim, hidden_size)
                self.activation = nn.GELU()
                self.layer_norm = nn.LayerNorm(hidden_size)
                
            def forward(self, x):
                residual = x
                x = self.layer_norm(x)
                x = self.down_proj(x)
                x = self.activation(x)
                x = self.up_proj(x)
                return residual + x
        
        # Find transformer layers and add adapters
        adapters_added = 0
        for name, module in model.named_children():
            if 'layer' in name.lower() or isinstance(module, nn.ModuleList):
                # This is likely a transformer layer
                for i, submodule in enumerate(module):
                    if hasattr(submodule, 'output'):
                        # Add adapter after output layer
                        hidden_size = submodule.output.dense.out_features
                        adapter = Adapter(hidden_size, adapter_dim)
                        submodule.output.adapter = adapter
                        adapters_added += 1
        
        # Only train adapters
        trainable_params = sum(p.numel() for p in model.parameters() 
                              if 'adapter' in (''.join(p.keys()) if hasattr(p, 'keys') else ''))
        total_params = sum(p.numel() for p in model.parameters())
        
        return {
            'model': model,
            'trainable_params': trainable_params,
            'total_params': total_params,
            'trainable_percentage': trainable_params / total_params * 100,
            'adapters_added': adapters_added
        }
    
    def lora_tuning(self, model, r=8, lora_alpha=32, lora_dropout=0.1):
        """LoRA (Low-Rank Adaptation) fine-tuning"""
        # Using PEFT library for LoRA
        from peft import LoraConfig, get_peft_model
        
        peft_config = LoraConfig(
            task_type=TaskType.SEQ_CLS,
            inference_mode=False,
            r=r,
            lora_alpha=lora_alpha,
            lora_dropout=lora_dropout,
            target_modules=["query", "value"]  # Apply to attention layers
        )
        
        model = get_peft_model(model, peft_config)
        
        trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
        total_params = sum(p.numel() for p in model.parameters())
        
        return {
            'model': model,
            'trainable_params': trainable_params,
            'total_params': total_params,
            'trainable_percentage': trainable_params / total_params * 100,
            'peft_config': peft_config
        }
    
    def prefix_tuning(self, model, prefix_length=10):
        """Prefix tuning"""
        hidden_size = self.config.hidden_size
        num_heads = self.config.num_attention_heads
        head_dim = hidden_size // num_heads
        
        # Create learnable prefix embeddings
        prefix_embeddings = nn.Parameter(
            torch.randn(prefix_length, hidden_size) * 0.02
        )
        
        # Create attention biases for prefix
        prefix_attention_biases = nn.Parameter(
            torch.zeros(num_heads, prefix_length)
        )
        
        # Wrap model to incorporate prefix
        class PrefixTunedModel(nn.Module):
            def __init__(self, base_model, prefix_embeddings, prefix_attention_biases):
                super().__init__()
                self.base_model = base_model
                self.prefix_embeddings = prefix_embeddings
                self.prefix_attention_biases = prefix_attention_biases
                
            def forward(self, input_ids, attention_mask=None, **kwargs):
                batch_size = input_ids.shape[0]
                
                # Get base embeddings
                embeddings = self.base_model.embeddings(input_ids)
                
                # Add prefix embeddings
                prefix_expanded = self.prefix_embeddings.unsqueeze(0).expand(
                    batch_size, -1, -1
                )
                embeddings_with_prefix = torch.cat([prefix_expanded, embeddings], dim=1)
                
                # Adjust attention mask
                if attention_mask is not None:
                    prefix_mask = torch.ones(
                        batch_size, prefix_length, 
                        device=attention_mask.device
                    )
                    attention_mask_with_prefix = torch.cat(
                        [prefix_mask, attention_mask], dim=1
                    )
                else:
                    attention_mask_with_prefix = None
                
                # Forward through base model
                outputs = self.base_model(
                    inputs_embeds=embeddings_with_prefix,
                    attention_mask=attention_mask_with_prefix,
                    **kwargs
                )
                
                return outputs
        
        model = PrefixTunedModel(model, prefix_embeddings, prefix_attention_biases)
        
        # Freeze base model, only train prefix parameters
        for name, param in model.named_parameters():
            if 'base_model' in name:
                param.requires_grad = False
        
        trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
        total_params = sum(p.numel() for p in model.parameters())
        
        return {
            'model': model,
            'trainable_params': trainable_params,
            'total_params': total_params,
            'trainable_percentage': trainable_params / total_params * 100
        }
    
    def bitfit_tuning(self, model):
        """BitFit: Bias-term only fine-tuning"""
        # Freeze all parameters
        for param in model.parameters():
            param.requires_grad = False
        
        # Only unfreeze bias terms
        for name, param in model.named_parameters():
            if 'bias' in name:
                param.requires_grad = True
        
        trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
        total_params = sum(p.numel() for p in model.parameters())
        
        return {
            'model': model,
            'trainable_params': trainable_params,
            'total_params': total_params,
            'trainable_percentage': trainable_params / total_params * 100
        }
    
    def compare_methods(self, train_dataset, val_dataset, n_epochs=3, batch_size=8):
        """Compare all fine-tuning methods"""
        from torch.utils.data import DataLoader
        from transformers import AdamW, get_linear_schedule_with_warmup
        import time
        
        methods = {
            'Full Fine-Tuning': self.full_fine_tuning,
            'Adapter Tuning': lambda m: self.adapter_tuning(m, adapter_dim=64),
            'LoRA Tuning': lambda m: self.lora_tuning(m, r=8),
            'Prefix Tuning': lambda m: self.prefix_tuning(m, prefix_length=10),
            'BitFit': self.bitfit_tuning
        }
        
        results = {}
        
        for method_name, method_func in methods.items():
            print(f"\n=== Testing {method_name} ===")
            
            # Create fresh model
            model = self.create_base_model()
            
            # Apply fine-tuning method
            method_result = method_func(model)
            model = method_result['model']
            
            print(f"Trainable parameters: {method_result['trainable_params']:,}")
            print(f"Trainable percentage: {method_result['trainable_percentage']:.2f}%")
            
            # Create dataloaders
            train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
            val_loader = DataLoader(val_dataset, batch_size=batch_size)
            
            # Setup training
            optimizer = AdamW(
                [p for p in model.parameters() if p.requires_grad],
                lr=2e-5,
                weight_decay=0.01
            )
            
            total_steps = len(train_loader) * n_epochs
            scheduler = get_linear_schedule_with_warmup(
                optimizer,
                num_warmup_steps=int(0.1 * total_steps),
                num_training_steps=total_steps
            )
            
            # Training loop
            train_losses = []
            val_accuracies = []
            training_times = []
            
            for epoch in range(n_epochs):
                print(f"Epoch {epoch + 1}/{n_epochs}")
                
                # Training
                model.train()
                epoch_loss = 0
                start_time = time.time()
                
                for batch in train_loader:
                    optimizer.zero_grad()
                    
                    # Forward pass
                    outputs = model(**batch)
                    loss = outputs.loss
                    
                    # Backward pass
                    loss.backward()
                    optimizer.step()
                    scheduler.step()
                    
                    epoch_loss += loss.item()
                
                train_losses.append(epoch_loss / len(train_loader))
                epoch_time = time.time() - start_time
                training_times.append(epoch_time)
                
                # Validation
                model.eval()
                correct = 0
                total = 0
                
                with torch.no_grad():
                    for batch in val_loader:
                        outputs = model(**batch)
                        predictions = torch.argmax(outputs.logits, dim=-1)
                        correct += (predictions == batch['labels']).sum().item()
                        total += len(batch['labels'])
                
                val_accuracy = correct / total
                val_accuracies.append(val_accuracy)
                
                print(f"  Loss: {train_losses[-1]:.4f}, "
                      f"Accuracy: {val_accuracy:.4f}, "
                      f"Time: {epoch_time:.2f}s")
            
            # Store results
            results[method_name] = {
                'method_result': method_result,
                'train_losses': train_losses,
                'val_accuracies': val_accuracies,
                'training_times': training_times,
                'final_accuracy': val_accuracies[-1],
                'total_training_time': sum(training_times),
                'avg_epoch_time': np.mean(training_times)
            }
        
        # Create comparison visualization
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Final Accuracy', 'Training Time per Epoch',
                          'Trainable Parameters', 'Training Loss Progression')
        )
        
        # 1. Final Accuracy
        accuracies = [results[m]['final_accuracy'] for m in methods.keys()]
        fig.add_trace(
            go.Bar(x=list(methods.keys()), y=accuracies, name='Accuracy'),
            row=1, col=1
        )
        
        # 2. Training Time
        avg_times = [results[m]['avg_epoch_time'] for m in methods.keys()]
        fig.add_trace(
            go.Bar(x=list(methods.keys()), y=avg_times, name='Time'),
            row=1, col=2
        )
        
        # 3. Trainable Parameters
        trainable_params = [results[m]['method_result']['trainable_params'] 
                           for m in methods.keys()]
        fig.add_trace(
            go.Bar(x=list(methods.keys()), y=trainable_params, name='Params'),
            row=2, col=1
        )
        
        # 4. Training Loss Progression
        for method_name in methods.keys():
            losses = results[method_name]['train_losses']
            fig.add_trace(
                go.Scatter(x=list(range(len(losses))), y=losses,
                          name=method_name, mode='lines+markers'),
                row=2, col=2
            )
        
        fig.update_layout(height=800, title_text="Fine-Tuning Methods Comparison")
        
        # Create efficiency-accuracy tradeoff plot
        fig2 = go.Figure()
        
        for method_name in methods.keys():
            efficiency = 1 - (results[method_name]['method_result']['trainable_percentage'] / 100)
            accuracy = results[method_name]['final_accuracy']
            trainable_pct = results[method_name]['method_result']['trainable_percentage']
            
            fig2.add_trace(go.Scatter(
                x=[efficiency],
                y=[accuracy],
                mode='markers+text',
                name=method_name,
                text=[method_name],
                textposition='top center',
                marker=dict(
                    size=20,
                    color=trainable_pct,
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title='Trainable %')
                )
            ))
        
        fig2.update_layout(
            title='Efficiency vs Accuracy Tradeoff',
            xaxis_title='Efficiency (1 - trainable %)',
            yaxis_title='Validation Accuracy',
            height=600
        )
        
        return {
            'results': results,
            'comparison_plot': fig,
            'tradeoff_plot': fig2
        }