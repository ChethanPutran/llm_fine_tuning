// src/services/api.js
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

class APIService {
  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  // Generic request handler
  async request(endpoint, options = {}) {
    try {
      const response = await this.client({
        url: endpoint,
        ...options,
      });
      return response.data;
    } catch (error) {
      console.error(`API Error (${endpoint}):`, error.response?.data || error.message);
      throw error.response?.data || error;
    }
  }

  // ============= Data Collection APIs =============
  createDataCollectionJob(data) {
    return this.request('/data-collection/add', {
      method: 'POST',
      data: {
        source: data.source,
        topic: data.topic,
        search_engine: data.searchEngine || 'google',
        limit: data.limit || 100,
        config: data.config || {},
        auto_execute: data.autoExecute !== false,
        tags: data.tags || []
      }
    });
  }

  executeDataCollectionJob(jobId) {
    return this.request(`/data-collection/execute/${jobId}`, {
      method: 'POST'
    });
  }

  getDataCollectionStatus(jobId) {
    return this.request(`/data-collection/status/${jobId}`);
  }

  cancelDataCollectionJob(jobId) {
    return this.request(`/data-collection/cancel/${jobId}`, {
      method: 'POST'
    });
  }

  listDataCollectionJobs(params = {}) {
    return this.request('/data-collection/jobs', {
      params: {
        status: params.status,
        source: params.source,
        topic: params.topic,
        user_id: params.userId,
        limit: params.limit || 50,
        offset: params.offset || 0
      }
    });
  }

  getDataCollectionStatistics(params = {}) {
    return this.request('/data-collection/statistics', {
      params: {
        user_id: params.userId
      }
    });
  }

  getDataSources() {
    return this.request('/data-collection/sources');
  }

  // ============= Preprocessing APIs =============
  createPreprocessingJob(data) {
    return this.request('/preprocessing/add', {
      method: 'POST',
      data: {
        input_path: data.inputPath,
        config: data.config,
        output_path: data.outputPath,
        auto_execute: data.autoExecute !== false,
        tags: data.tags || []
      }
    });
  }

  executePreprocessingJob(jobId) {
    return this.request(`/preprocessing/execute/${jobId}`, {
      method: 'POST'
    });
  }

  uploadAndPreprocess(file, config, autoExecute = true) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('config', JSON.stringify(config));
    formData.append('auto_execute', autoExecute);
    
    return this.request('/preprocessing/upload', {
      method: 'POST',
      data: formData,
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  }

  getPreprocessingStatus(jobId) {
    return this.request(`/preprocessing/status/${jobId}`);
  }

  cancelPreprocessingJob(jobId) {
    return this.request(`/preprocessing/jobs/${jobId}`, {
      method: 'DELETE'
    });
  }

  listPreprocessingJobs(params = {}) {
    return this.request('/preprocessing/jobs', {
      params: {
        status: params.status,
        user_id: params.userId,
        limit: params.limit || 50,
        offset: params.offset || 0
      }
    });
  }

  getPreprocessingStatistics(params = {}) {
    return this.request('/preprocessing/statistics', {
      params: {
        user_id: params.userId
      }
    });
  }

  getPreprocessingMetrics(jobId) {
    return this.request(`/preprocessing/metrics/${jobId}`);
  }

  getSupportedFormats() {
    return this.request('/preprocessing/supported-formats');
  }

  // ============= Tokenization APIs =============
  createTokenizerJob(data) {
    return this.request('/tokenization/add', {
      method: 'POST',
      data: {
        tokenizer_type: data.tokenizerType,
        dataset_path: data.datasetPath,
        vocab_size: data.vocabSize || 32000,
        config: data.config || {},
        auto_execute: data.autoExecute !== false,
        tags: data.tags || []
      }
    });
  }

  executeTokenizerJob(jobId) {
    return this.request(`/tokenization/execute/${jobId}`, {
      method: 'POST'
    });
  }

  encodeText(tokenizerPath, text, maxLength = null) {
    return this.request('/tokenization/encode', {
      method: 'POST',
      data: {
        tokenizer_path: tokenizerPath,
        text: text,
        max_length: maxLength
      }
    });
  }

  decodeTokens(tokenizerPath, tokenIds) {
    return this.request('/tokenization/decode', {
      method: 'POST',
      data: {
        tokenizer_path: tokenizerPath,
        token_ids: tokenIds
      }
    });
  }

  getTokenizerStatus(jobId) {
    return this.request(`/tokenization/status/${jobId}`);
  }

  cancelTokenizerJob(jobId) {
    return this.request(`/tokenization/jobs/${jobId}`, {
      method: 'DELETE'
    });
  }

  listTokenizerJobs(params = {}) {
    return this.request('/tokenization/jobs', {
      params: {
        status: params.status,
        tokenizer_type: params.tokenizerType,
        user_id: params.userId,
        limit: params.limit || 50,
        offset: params.offset || 0
      }
    });
  }

  getTokenizerStatistics(params = {}) {
    return this.request('/tokenization/statistics', {
      params: {
        user_id: params.userId
      }
    });
  }

  getTokenizerTypes() {
    return this.request('/tokenization/types');
  }

  // ============= Training APIs =============
  createTrainingJob(data) {
    return this.request('/training/add', {
      method: 'POST',
      data: {
        model_type: data.modelType,
        model_name: data.modelName,
        dataset_path: data.datasetPath,
        config: data.config || {},
        auto_execute: data.autoExecute !== false,
        tags: data.tags || []
      }
    });
  }

  createFinetuningJob(data) {
    return this.request('/finetuning/add', {
      method: 'POST',
      data: {
        model_type: data.modelType,
        model_name: data.modelName,
        strategy_type: data.strategyType,
        task_type: data.taskType,
        dataset_path: data.datasetPath,
        config: data.config || {},
        auto_execute: data.autoExecute !== false,
        tags: data.tags || []
      }
    });
  }

  executeTrainingJob(jobId) {
    return this.request(`/training/execute/${jobId}`, {
      method: 'POST'
    });
  }

  getTrainingStatus(jobId) {
    return this.request(`/training/status/${jobId}`);
  }

  cancelTrainingJob(jobId) {
    return this.request(`/training/jobs/${jobId}`, {
      method: 'DELETE'
    });
  }

  listTrainingJobs(params = {}) {
    return this.request('/training/jobs', {
      params: {
        status: params.status,
        job_type: params.jobType,
        user_id: params.userId,
        limit: params.limit || 50,
        offset: params.offset || 0
      }
    });
  }

  getTrainingStatistics(params = {}) {
    return this.request('/training/statistics', {
      params: {
        user_id: params.userId
      }
    });
  }

  getTrainingMetrics(jobId) {
    return this.request(`/training/metrics/${jobId}`);
  }

  getTrainingLogs(jobId, tail = 100) {
    return this.request(`/training/logs/${jobId}`, {
      params: { tail }
    });
  }

  getTrainingStrategies() {
    return this.request('/training/strategies');
  }

  getTrainingTasks() {
    return this.request('/training/tasks');
  }

  getTrainingConfigs() {
    return this.request('/training/configs');
  }

  // ============= Optimization APIs =============
  createOptimizationJob(data) {
    return this.request('/optimization/add', {
      method: 'POST',
      data: {
        model_path: data.modelPath,
        optimization_type: data.optimizationType,
        config: data.config || {},
        auto_execute: data.autoExecute !== false,
        tags: data.tags || []
      }
    });
  }

  executeOptimizationJob(jobId) {
    return this.request(`/optimization/execute/${jobId}`, {
      method: 'POST'
    });
  }

  getOptimizationStatus(jobId) {
    return this.request(`/optimization/status/${jobId}`);
  }

  cancelOptimizationJob(jobId) {
    return this.request(`/optimization/jobs/${jobId}`, {
      method: 'DELETE'
    });
  }

  listOptimizationJobs(params = {}) {
    return this.request('/optimization/jobs', {
      params: {
        status: params.status,
        optimization_type: params.optimizationType,
        user_id: params.userId,
        limit: params.limit || 50,
        offset: params.offset || 0
      }
    });
  }

  getOptimizationStatistics(params = {}) {
    return this.request('/optimization/statistics', {
      params: {
        user_id: params.userId
      }
    });
  }

  getOptimizationMetrics(jobId) {
    return this.request(`/optimization/metrics/${jobId}`);
  }

  getOptimizationTypes() {
    return this.request('/optimization/types');
  }

  // ============= Deployment APIs =============
  createDeploymentJob(data) {
    return this.request('/deployment/add', {
      method: 'POST',
      data: {
        model_path: data.modelPath,
        serving_framework: data.servingFramework,
        deployment_target: data.deploymentTarget || 'local',
        config: data.config || {},
        auto_execute: data.autoExecute !== false,
        tags: data.tags || []
      }
    });
  }

  executeDeploymentJob(jobId) {
    return this.request(`/deployment/execute/${jobId}`, {
      method: 'POST'
    });
  }

  getDeploymentStatus(jobId) {
    return this.request(`/deployment/status/${jobId}`);
  }

  cancelDeploymentJob(jobId) {
    return this.request(`/deployment/jobs/${jobId}`, {
      method: 'DELETE'
    });
  }

  listDeploymentJobs(params = {}) {
    return this.request('/deployment/jobs', {
      params: {
        status: params.status,
        serving_framework: params.servingFramework,
        user_id: params.userId,
        limit: params.limit || 50,
        offset: params.offset || 0
      }
    });
  }

  listActiveDeployments() {
    return this.request('/deployment/active');
  }

  undeployModel(deploymentId) {
    return this.request(`/deployment/${deploymentId}`, {
      method: 'DELETE'
    });
  }

  getDeploymentStatistics(params = {}) {
    return this.request('/deployment/statistics', {
      params: {
        user_id: params.userId
      }
    });
  }

  getDeploymentTargets() {
    return this.request('/deployment/targets');
  }

  getServingFrameworks() {
    return this.request('/deployment/frameworks');
  }

  // ============= Pipeline APIs =============
  createPipelineJob(data) {
    return this.request('/pipelines/add', {
      method: 'POST',
      data: {
        pipeline_json: data.pipelineJson,
        priority: data.priority || 'NORMAL',
        auto_execute: data.autoExecute !== false,
        tags: data.tags || []
      }
    });
  }

  executePipelineJob(jobId) {
    return this.request(`/pipelines/execute/${jobId}`, {
      method: 'POST'
    });
  }

  executePipelineDirectly(data) {
    return this.request('/pipelines/execute', {
      method: 'POST',
      data: {
        pipeline_json: data.pipelineJson,
        user_id: data.userId,
        priority: data.priority || 'NORMAL',
        auto_register: data.autoRegister !== false
      }
    });
  }

  getPipelineStatus(jobId) {
    return this.request(`/pipelines/status/${jobId}`);
  }

  cancelPipelineJob(jobId) {
    return this.request(`/pipelines/jobs/${jobId}`, {
      method: 'DELETE'
    });
  }

  listPipelineJobs(params = {}) {
    return this.request('/pipelines/jobs', {
      params: {
        status: params.status,
        user_id: params.userId,
        limit: params.limit || 50,
        offset: params.offset || 0
      }
    });
  }

  getPipelineStatistics(params = {}) {
    return this.request('/pipelines/statistics', {
      params: {
        user_id: params.userId
      }
    });
  }

  getExecutionStatus(executionId) {
    return this.request(`/pipelines/executions/${executionId}/status`);
  }

  cancelExecution(executionId) {
    return this.request(`/pipelines/executions/${executionId}`, {
      method: 'DELETE'
    });
  }

  getExecutionLogs(executionId, nodeId = null, tail = 100) {
    const params = { tail };
    if (nodeId) params.node_id = nodeId;
    return this.request(`/pipelines/executions/${executionId}/logs`, { params });
  }

  getPipelineTemplates() {
    return this.request('/pipelines/templates');
  }

  getPipelineTemplate(templateName) {
    return this.request(`/pipelines/templates/${templateName}`);
  }

  instantiatePipelineTemplate(templateName, config = null) {
    return this.request(`/pipelines/templates/${templateName}/instantiate`, {
      method: 'POST',
      data: config || {}
    });
  }

  validatePipeline(pipelineJson) {
    return this.request('/pipelines/validate', {
      method: 'POST',
      data: pipelineJson
    });
  }

  // ============= Settings APIs =============
  getSettings() {
    return this.request('/settings/');
  }

  saveSettings(settings) {
    return this.request('/settings/', {
      method: 'POST',
      data: {
        settings}
    });
  }

  resetSettings() {
    return this.request('/settings/reset', {
      method: 'POST'
    });
  }

  exportSettings() {
    return this.request('/settings/export');
  }

  importSettings(settings) {
    return this.request('/settings/import', {
      method: 'POST',
      data: settings
    });
  }

  getBackups() {
    return this.request('/settings/backups');
  }

  createBackup() {
    return this.request('/settings/backups', {
      method: 'POST'
    });
  }

  restoreBackup(backupId) {
    return this.request(`/settings/backups/${backupId}/restore`, {
      method: 'POST'
    });
  }

  deleteBackup(backupId) {
    return this.request(`/settings/backups/${backupId}`, {
      method: 'DELETE'
    });
  }

  getEnvironmentVariables() {
    return this.request('/settings/env');
  }

  updateEnvironmentVariable(key, value) {
    return this.request('/settings/env', {
      method: 'POST',
      data: { key, value }
    });
  }


  // =========================== General routes ===========================
  getTaskCatergories() {
    return this.request('/tasks/categories');
  }
  getTasksByCategory(category) {
    return this.request('/tasks', {
      params: { category }
    });
  }
  getTaskDatasets(taskId) {
    return this.request(`/tasks/datasets/${taskId}`);
  }
  getTaskModels(taskId) {
    return this.request(`/tasks/models/${taskId}`);
  }
  getUserInfo() {
    return this.request('/user/info');
  }

  getSystemStatus() {
    return this.request('/system/status');
  }

  getSystemMetrics() {
    return this.request('/system/metrics');
  }

  getLogs(tail = 100) {
    return this.request('/system/logs', {
      params: { tail }
    });
  }
  getAvailableResources() {
    return this.request('/system/resources');
  }
  getResourceUsage() {
    return this.request('/system/resource-usage');
  }
}

export const apiService = new APIService();