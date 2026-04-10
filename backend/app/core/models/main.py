
from transformers import generation
from transformers.pipelines import SUPPORTED_TASKS


# data = get_task_resources("text-classification")

# print(data)

    

class Models:
    @staticmethod
    def get_available_models():
        # This is a placeholder implementation. In a real application, this might query a database or an external API.

        return {
            "bert": [
                {
                    "name": "bert-base-uncased",
                    "version": "1.0",
                    "description": "BERT base model, uncased."
                },
                {
                    "name": "bert-large-uncased",
                    "version": "1.0",
                    "description": "BERT large model, uncased."
                },
                {
                    "name": "bert-base-cased",
                    "version": "1.0",
                    "description": "BERT base model, cased."
                },
                {
                    "name": "bert-large-cased",
                    "version": "1.0",
                    "description": "BERT large model, cased."
                },
                {
                    "name": "bert-base-multilingual-cased",
                    "version": "1.0",
                    "description": "BERT base model, multilingual and cased."
                }

            ],
            "gpt": [
                {
                    "name": "gpt2",
                    "version": "1.0",
                    "description": "GPT-2 model by OpenAI."
                },
                {
                    "name": "gpt2-medium",
                    "version": "1.0",
                    "description": "GPT-2 medium model by OpenAI."
                },
                {
                    "name": "gpt2-large",
                    "version": "1.0",
                    "description": "GPT-2 large model by OpenAI."
                },
                {
                    "name": "gpt2-xl",
                    "version": "1.0",
                    "description": "GPT-2 XL model by OpenAI."
                }
            ],
            "llama": [
                {
                    "name": "Llama-2-7b-hf",
                    "version": "1.0",
                    "description": "LLaMA 2 7B model by Meta AI."
                },
                {
                    "name": "Llama-2-13b-hf",
                    "version": "1.0",
                    "description": "LLaMA 2 13B model by Meta AI."
                },
                {
                    "name": "Llama-2-70b-hf",
                    "version": "1.0",
                    "description": "LLaMA 2 70B model by Meta AI."
                }
            ],
            "bart": [
                {
                    "name": "facebook/bart-base",
                    "version": "1.0",
                    "description": "BART base model by Facebook."
                },
                {
                    "name": "facebook/bart-large",
                    "version": "1.0",
                    "description": "BART large model by Facebook."
                }
            ],
            "vit": [
                {
                    "name": "google/vit-base-patch16-224",
                    "version": "1.0",
                    "description": "Vision Transformer base model by Google."
                },
                {
                    "name": "google/vit-large-patch16-224",
                    "version": "1.0",
                    "description": "Vision Transformer large model by Google."
                }
            ],
            "vlm": [
                {
                    "name": "openai/clip-vit-base-patch32",
                    "version": "1.0",
                    "description": "CLIP model by OpenAI for vision-language tasks."
                },
                {
                    "name": "openai/clip-vit-large-patch14",
                    "version": "1.0",
                    "description": "CLIP large model by OpenAI for vision-language tasks."
                }
            ]
        }


# if __name__ == "__main__":
#     print("Available Tasks:")
#     print(Tasks.get_available_tasks())
    
#     print("\nAvailable Models:")
#     print(Models.get_available_models())