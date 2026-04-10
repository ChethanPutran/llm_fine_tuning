import { apiService } from "../services/api.jsx";

export const STAGE_TYPES = {
  DATA_COLLECTION: 'data_collection',
  PREPROCESSING: 'preprocessing',
  TOKENIZATION: 'tokenization',
  FINETUNING: 'finetuning',
  OPTIMIZATION: 'optimization',
  DEPLOYMENT: 'deployment',
};

export const STAGE_DEFINITIONS = [
  {
    id: STAGE_TYPES.DATA_COLLECTION,
    name: "Data Collection",
    color: "#2563eb",
    startApi: apiService.startDataCollection,
    statusApi: apiService.getCollectionStatus,
    fields: [
      { key: "source", label: "Data Source", type: "select", options: ["web", "books", "upload"], default: "web", required: true },
      { key: "topic", label: "Topic", type: "text", placeholder: "e.g., machine learning", required: true },
      { key: "limit", label: "Documents Limit", type: "select", options: ["50", "100", "500", "1000"], default: "100" }
    ],
    advancedFields: [
      { key: "max_depth", label: "Max Crawl Depth", type: "number", min: 1, max: 5, default: 2 },
      { key: "timeout", label: "Timeout (seconds)", type: "number", min: 5, max: 60, default: 10 }
    ]
  },
  {
    id: STAGE_TYPES.PREPROCESSING,
    name: "Preprocessing",
    color: "#7c3aed",
    startApi: apiService.startPreprocessing,
    statusApi: apiService.getPreprocessingStatus,
    fields: [
      { key: "input_path", label: "Input Path", type: "text", placeholder: "e.g., /path/to/input", required: true },
      { key: "clean_method", label: "Cleaning Method", type: "select", options: ["standard", "advanced"], default: "standard" },
      { key: "output_format", label: "Output Format", type: "select", options: ["parquet", "csv", "json"], default: "parquet" }
    ],
    advancedFields: [
      { key: "dedup_threshold", label: "Deduplication Threshold", type: "slider", min: 0, max: 1, step: 0.05, default: 0.9 },
      { key: "extract_entities", label: "Extract Named Entities", type: "boolean", default: true },
      { key: "normalize_text", label: "Normalize Text", type: "boolean", default: true },
      { key: "min_doc_length", label: "Minimum Document Length", type: "number", min: 10, max: 500, default: 50 },
      { key: "remove_stopwords", label: "Remove Stopwords", type: "boolean", default: true }
    ]
  },
  {
    id: STAGE_TYPES.TOKENIZATION,
    name: "Tokenization",
    color: "#0ea5e9",
    startApi: apiService.trainTokenizer,
    statusApi: apiService.getTokenizerStatus,
    fields: [
      { key: "tokenizer_type", label: "Tokenizer Type", type: "select", options: ["bpe", "wordpiece", "sentencepiece"], default: "bpe" },
      { key: "vocab_size", label: "Vocabulary Size", type: "select", options: ["30000", "50000", "100000"], default: "50000" },
      { key: "corpus_path", label: "Corpus Path", type: "text", placeholder: "e.g., /path/to/corpus", required: true }
    ],
    advancedFields: [
      { key: "output_path", label: "Output Path", type: "text", placeholder: "e.g., /path/to/save/tokenizer", required: true },
      { key: "field", label: "Field to Tokenize", type: "text", default: "content_clean" }
    ]
  },
  {
    id: STAGE_TYPES.FINETUNING,
    name: "Fine-tuning",
    color: "#db2777",
    startApi: apiService.startFinetuning,
    statusApi: apiService.getFinetuningStatus,
    fields: [
      { 
  key: "task_category", 
  label: "Task Category", 
  type: "select", 
  // Explicitly bind the apiService context
  fetch_endpoint: (config) => apiService.getTaskCatergories(),
},
{ 
  key: "task", 
  label: "Task", 
  type: "select", 
  dependsOn: "task_category",
  // Pass the required dependency (task_category) to the API call
  fetch_endpoint: (config) => apiService.getTasksByCategory(config.task_category),
},
{ 
  key: "model_type", 
  label: "Model Type", 
  type: "select", 
  dependsOn: "task",
  fetch_endpoint: (config) => apiService.getTaskModels(config.task),
},
{ 
  key: "dataset", 
  label: "Dataset", 
  type: "select", 
  dependsOn: "task",
  fetch_endpoint: (config) => apiService.getTaskDatasets(config.task),
}

     
    ],
    advancedFields: [
      
      { key: "learning_rate", label: "Learning Rate", type: "number", step: 0.00001, default: 0.00002 },
      { key: "num_epochs", label: "Epochs", type: "number", min: 1, max: 20, default: 3 },
      { key: "batch_size", label: "Batch Size", type: "select", options: ["8", "16", "32", "64"], default: "16" }
    ]
  },
  {
    id: STAGE_TYPES.OPTIMIZATION,
    name: "Optimization",
    color: "#f59e0b",
    startApi: apiService.optimizeModel,
    statusApi: apiService.getOptimizationStatus,
    fields: [
      { key: "optimization_type", label: "Optimization Type", type: "select", options: ["pruning", "distillation", "quantization"], default: "pruning" }
    ],
    advancedFields: [
      { key: "target_sparsity", label: "Target Sparsity", type: "slider", min: 0, max: 0.9, step: 0.05, default: 0.5 }
    ]
  },
  {
    id: STAGE_TYPES.DEPLOYMENT,
    name: "Deployment",
    color: "#10b981",
    startApi: apiService.deployModel,
    statusApi: apiService.getDeploymentStatus,
    fields: [
      { key: "deployment_target", label: "Target", type: "select", options: ["local", "cloud", "edge"], default: "local" },
      { key: "serving_framework", label: "Framework", type: "select", options: ["torchserve", "tensorflow-serving", "onnx"], default: "torchserve" }
    ],
    advancedFields: [
      { key: "replicas", label: "Number of Replicas", type: "number", min: 1, max: 10, default: 1 },
      { key: "gpu_enabled", label: "Enable GPU", type: "boolean", default: false }
    ]
  }
];