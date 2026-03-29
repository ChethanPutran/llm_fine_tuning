import axios from 'axios';

// Use Vite's import.meta.env instead of process.env
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// WebSocket connection
let ws = null;

export const connectWebSocket = (clientId, onMessage) => {
  ws = new WebSocket(`ws://localhost:8000/ws/${clientId}`);
  
  ws.onopen = () => {
    console.log('WebSocket connected');
  };
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    onMessage(data);
  };
  
  ws.onclose = () => {
    console.log('WebSocket disconnected');
  };
  
  return ws;
};

export const subscribeToJob = (jobId) => {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({
      type: 'subscribe',
      job_id: jobId
    }));
  }
};

export const apiService = {
  // Data Collection
  startDataCollection: async (source, topic, limit, config) => {
    const response = await api.post('/data-collection/start', null, {
      params: { source, topic, limit, ...config }
    });
    return response.data;
  },
  
  getCollectionStatus: async (jobId) => {
    const response = await api.get(`/data-collection/status/${jobId}`);
    return response.data;
  },
  
  getDataSources: async () => {
    const response = await api.get('/data-collection/sources');
    return response.data;
  },
  
  // Preprocessing
 startPreprocessing: async (inputPath, config) => {
  // Send input_path as query parameter, config as body
  const response = await api.post('/preprocessing/start', 
    config,  // Send config directly as body
    { params: { input_path: inputPath } }  // input_path as query param
  );
  return response.data;
},
  
  getPreprocessingStatus: async (jobId) => {
    const response = await api.get(`/preprocessing/status/${jobId}`);
    return response.data;
  },
  
  // Tokenization
  trainTokenizer: async (tokenizerType, corpusPath, vocabSize, outputPath, field) => {
    const response = await api.post('/tokenization/train', {
      tokenizer_type: tokenizerType,
      corpus_path: corpusPath,
      vocab_size: vocabSize,
      output_path: outputPath,
      field: field
    });
    return response.data;
  },
  // Tokenization status
  getTokenizerStatus: async (jobId) => {
    const response = await api.post(`/tokenization/status/${jobId}`);
    return response.data;
  },
  
  getTokenizerTypes: async () => {
    const response = await api.get('/tokenization/types');
    return response.data;
  },
  
  // Training
  startTraining: async (modelType, modelName, datasetPath, config) => {
    const response = await api.post('/training/start', {
      model_type: modelType,
      model_name: modelName,
      dataset_path: datasetPath,
      config
    });
    return response.data;
  },
  
  getTrainingStatus: async (jobId) => {
    const response = await api.get(`/training/status/${jobId}`);
    return response.data;
  },
  
  // Fine-tuning
  startFinetuning: async (modelType, modelName, strategy, task, datasetPath, config) => {
    const response = await api.post('/finetuning/start', {
      model_type: modelType,
      model_name: modelName,
      strategy,
      task,
      dataset_path: datasetPath,
      config
    });
    return response.data;
  },
  
  getFinetuningStatus: async (jobId) => {
    const response = await api.get(`/finetuning/status/${jobId}`);
    return response.data;
  },
  
  getFinetuningStrategies: async () => {
    const response = await api.get('/finetuning/strategies');
    return response.data;
  },
  
  getFinetuningTasks: async () => {
    const response = await api.get('/finetuning/tasks');
    return response.data;
  },
  
  // Optimization
  optimizeModel: async (modelPath, optimizationType, config) => {
    const response = await api.post('/optimization/optimize', {
      model_path: modelPath,
      optimization_type: optimizationType,
      config
    });
    return response.data;
  },
  
  getOptimizationStatus: async (jobId) => {
    const response = await api.get(`/optimization/status/${jobId}`);
    return response.data;
  },
  
  getOptimizationTypes: async () => {
    const response = await api.get('/optimization/types');
    return response.data;
  },
  
  // Deployment
  deployModel: async (modelPath, target, framework, config) => {
    const response = await api.post('/deployment/deploy', {
      model_path: modelPath,
      deployment_target: target,
      serving_framework: framework,
      config
    });
    return response.data;
  },
  
  getDeploymentStatus: async (deploymentId) => {
    const response = await api.get(`/deployment/status/${deploymentId}`);
    return response.data;
  },
  
  getDeploymentTargets: async () => {
    const response = await api.get('/deployment/targets');
    return response.data;
  },
  
  getServingFrameworks: async () => {
    const response = await api.get('/deployment/frameworks');
    return response.data;
  }
};

export default apiService;