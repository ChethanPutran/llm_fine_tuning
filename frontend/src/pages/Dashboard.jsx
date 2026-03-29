import React, { useState, useEffect } from "react";
import { Container, Grid, Typography, Box } from "@mui/material";
import PipelineStage from "../components/PipelineStage";
import StatusMonitor from "../components/StatusMonitor";
import { apiService } from "../services/api.jsx";

const Dashboard = () => {
  // Store configuration for each stage separately
  const [stageConfigs, setStageConfigs] = useState({});
  const [stageStatus, setStageStatus] = useState({});

  const stages = [
    {
      id: "data_collection",
      name: "Data Collection",
      startApi: apiService.startDataCollection,
      statusApi: apiService.getCollectionStatus,
      options: [
        {
          key: "source",
          label: "Data Source",
          type: "select",
          values: ["web", "books", "upload"],
          default: "web",
          required: true,
        },
        {
          key: "topic",
          label: "Topic",
          type: "text",
          placeholder: "e.g., machine learning",
          required: true,
        },
        {
          key: "limit",
          label: "Documents Limit",
          type: "select",
          values: ["50", "100", "500", "1000"],
          default: "100",
        },
        {
          key: "max_depth",
          label: "Max Crawl Depth",
          type: "number",
          min: 1,
          max: 5,
          default: 2,
        },
        {
          key: "timeout",
          label: "Timeout (seconds)",
          type: "number",
          min: 5,
          max: 60,
          default: 10,
        },
      ],
    },
    {
      id: "preprocessing",
      name: "Preprocessing",
      startApi: apiService.startPreprocessing,
      statusApi: apiService.getPreprocessingStatus,
      options: [
        {
          key: "input_path",
          label: "Input Path",
          type: "text",
          placeholder: "e.g., /path/to/input",
          required: true,
        },
        {
          key: "clean_method",
          label: "Cleaning Method",
          type: "select",
          values: ["standard", "advanced"],
          default: "standard",
        },
        {
          key: "dedup_threshold",
          label: "Deduplication Threshold",
          type: "slider",
          min: 0,
          max: 1,
          step: 0.05,
          default: 0.9,
        },
        {
          key: "extract_entities",
          label: "Extract Named Entities",
          type: "checkbox",
          default: true,
        },
        {
          key: "normalize_text",
          label: "Normalize Text",
          type: "checkbox",
          default: true,
        },
        {
          key: "extract_keywords",
          label: "Extract Keywords",
          type: "checkbox",
          default: true,
        },
        {
          key: "min_doc_length",
          label: "Minimum Document Length",
          type: "number",
          min: 10,
          max: 500,
          default: 50,
        },
        {
          key: "remove_stopwords",
          label: "Remove Stopwords",
          type: "checkbox",
          default: true,
        },
        {
          key: "output_format",
          label: "Output Format",
          type: "select",
          values: ["parquet", "csv", "json"],
          default: "parquet",
        },
      ],
    },
    {
      id: "tokenization",
      name: "Tokenization",
      startApi: apiService.trainTokenizer,
      statusApi: apiService.getTokenizerStatus,
      options: [
        {
          key: "tokenizer_type",
          label: "Tokenizer Type",
          type: "select",
          values: ["bpe", "wordpiece", "sentencepiece"],
          default: "bpe",
        },
        {
          key: "vocab_size",
          label: "Vocabulary Size",
          type: "select",
          values: ["30000", "50000", "100000"],
          default: "50000",
        },
        {
          key: "corpus_path",
          label: "Corpus Path",
          type: "text",
          placeholder: "e.g., /path/to/corpus",
          required: true,
        },
        {
          key: "output_path",
          label: "Output Path",
          type: "text",
          placeholder: "e.g., /path/to/save/tokenizer",
          required: true,
        },
        {
          key: "field",
          label: "Field to Tokenize",
          type: "text",
          default: "content_clean",
          required: false,
        },
      ],
    },
    {
      id: "finetuning",
      name: "Fine-tuning",
      startApi: apiService.startFinetuning,
      statusApi: apiService.getFinetuningStatus,
      options: [
        {
          key: "model_type",
          label: "Model Type",
          type: "select",
          values: ["bert", "gpt", "bart"],
          default: "bert",
          required: true,
        },
        {
          key: "model_name",
          label: "Model Name",
          type: "text",
          placeholder: "bert-base-uncased",
          required: true,
        },
        {
          key: "strategy",
          label: "Fine-tuning Strategy",
          type: "select",
          values: ["full", "lora", "adapter"],
          default: "lora",
        },
        {
          key: "task",
          label: "Task",
          type: "select",
          values: ["classification", "summarization", "qa"],
          default: "classification",
        },
        {
          key: "learning_rate",
          label: "Learning Rate",
          type: "number",
          step: 0.00001,
          default: 0.00002,
        },
        {
          key: "num_epochs",
          label: "Number of Epochs",
          type: "number",
          min: 1,
          max: 20,
          default: 3,
        },
        {
          key: "dataset",
          label: "Dataset Name",
          type: "select",
          values: [
            "general_instruction_tuning",
            "mathematical_reasoning",
            "code_generation_and_understanding",
            "instruction_following",
            "multilingual_understanding",
            "agent_and_function_calling",
            "real_world_conversation",
            "preference_alignment",
          ],
          default: "general_instruction_tuning",
          required: true,
        },
        {
          key: "batch_size",
          label: "Batch Size",
          type: "select",
          values: ["8", "16", "32", "64"],
          default: "16",
        },
      ],
    },
    {
      id: "optimization",
      name: "Optimization",
      startApi: apiService.optimizeModel,
      statusApi: apiService.getOptimizationStatus,
      options: [
        {
          key: "optimization_type",
          label: "Optimization Type",
          type: "select",
          values: ["pruning", "distillation", "quantization"],
          default: "pruning",
        },
        {
          key: "target_sparsity",
          label: "Target Sparsity",
          type: "slider",
          min: 0,
          max: 0.9,
          step: 0.05,
          default: 0.5,
        },
      ],
    },
    {
      id: "deployment",
      name: "Deployment",
      startApi: apiService.deployModel,
      statusApi: apiService.getDeploymentStatus,
      options: [
        {
          key: "deployment_target",
          label: "Deployment Target",
          type: "select",
          values: ["local", "cloud", "edge"],
          default: "local",
        },
        {
          key: "serving_framework",
          label: "Serving Framework",
          type: "select",
          values: ["torchserve", "tensorflow-serving", "onnx"],
          default: "torchserve",
        },
      ],
    },
  ];

  // Load saved configs from localStorage on mount
  useEffect(() => {
    const savedConfigs = localStorage.getItem("stageConfigs");
    if (savedConfigs) {
      setStageConfigs(JSON.parse(savedConfigs));
    }
  }, []);

  // Save configs to localStorage when changed
  useEffect(() => {
    if (Object.keys(stageConfigs).length > 0) {
      localStorage.setItem("stageConfigs", JSON.stringify(stageConfigs));
    }
  }, [stageConfigs]);

  // Helper function to call the appropriate API based on stage
  const callStartApi = async (stage, config) => {
    switch (stage.id) {
      case "data_collection":
        return await stage.startApi(config.source, config.topic, config.limit, {
          max_depth: config.max_depth,
          timeout: config.timeout,
        });

      case "preprocessing":
        return await stage.startApi(
          config.input_path || "default_input", // input_path as separate param
          {
            clean_method: config.clean_method,
            dedup_threshold: parseFloat(config.dedup_threshold),
            extract_entities: config.extract_entities,
            extract_keywords: config.extract_keywords || true,
            normalize_text: config.normalize_text,
            remove_stopwords: config.remove_stopwords || true,
            min_doc_length: parseInt(config.min_doc_length),
            max_doc_length: 10000,
            language: "en",
            output_format: config.output_format,
          },
        );

      case "tokenization":
        return await stage.startApi(
          config.tokenizer_type,
          config.corpus_path || "default_corpus",
          parseInt(config.vocab_size),
          config.output_path || "default_output",
          config.field || "content_clean",
        );

      case "finetuning":
        return await stage.startApi(
          config.model_type,
          config.model_name,
          config.strategy,
          config.task,
          config.dataset_path || "default_dataset",
          {
            learning_rate: parseFloat(config.learning_rate),
            num_epochs: parseInt(config.num_epochs),
            batch_size: parseInt(config.batch_size),
          },
        );

      case "optimization":
        return await stage.startApi(
          config.model_path || "default_model",
          config.optimization_type,
          { target_sparsity: parseFloat(config.target_sparsity) },
        );

      case "deployment":
        return await stage.startApi(
          config.model_path || "default_model",
          config.deployment_target,
          config.serving_framework,
          {},
        );

      default:
        throw new Error(`Unknown stage: ${stage.id}`);
    }
  };

  const handleStageStart = async (stage, config) => {
    // Save config before starting
    setStageConfigs((prev) => ({ ...prev, [stage.id]: config }));

    // Update status
    setStageStatus((prev) => ({
      ...prev,
      [stage.id]: { status: "running", progress: 0 },
    }));

    try {
      const response = await callStartApi(stage, config);
      const jobId = response.job_id || response.deployment_id;

      // Only poll if there's a status API and job ID
      if (stage.statusApi && jobId) {
        // Poll for updates
        const interval = setInterval(async () => {
          try {
            const status = await stage.statusApi(jobId);
            setStageStatus((prev) => ({
              ...prev,
              [stage.id]: {
                status: status.status,
                progress: status.progress || 0,
                error: status.error,
                result: status.result,
              },
            }));

            if (status.status === "completed" || status.status === "failed") {
              clearInterval(interval);
            }
          } catch (error) {
            console.error("Error polling status:", error);
            clearInterval(interval);
          }
        }, 2000);

        // Store interval ID for cleanup if needed
        if (window.pollingIntervals) {
          window.pollingIntervals[stage.id] = interval;
        } else {
          window.pollingIntervals = { [stage.id]: interval };
        }
      } else {
        // No polling available, just mark as completed
        setStageStatus((prev) => ({
          ...prev,
          [stage.id]: { status: "completed", progress: 100, result: response },
        }));
      }
    } catch (error) {
      console.error(`Error starting ${stage.id}:`, error);
      setStageStatus((prev) => ({
        ...prev,
        [stage.id]: {
          status: "failed",
          error: error.message || "Failed to start stage",
        },
      }));
    }
  };

  const handleStageStop = async (stageId) => {
    // Clear polling interval if exists
    if (window.pollingIntervals && window.pollingIntervals[stageId]) {
      clearInterval(window.pollingIntervals[stageId]);
      delete window.pollingIntervals[stageId];
    }
    setStageStatus((prev) => ({ ...prev, [stageId]: { status: "stopped" } }));
  };

  // Cleanup polling intervals on unmount
  useEffect(() => {
    return () => {
      if (window.pollingIntervals) {
        Object.values(window.pollingIntervals).forEach((interval) =>
          clearInterval(interval),
        );
      }
    };
  }, []);

  return (
    <Container maxWidth="lg">
      <Box sx={{ my: 4 }}>
        <Typography variant="h3" component="h1" gutterBottom>
          LLM Fine-tuning Platform
        </Typography>

        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            {stages.map((stage) => (
              <PipelineStage
                key={stage.id}
                stage={stage}
                config={stageConfigs[stage.id] || {}}
                status={stageStatus[stage.id]?.status || "pending"}
                progress={stageStatus[stage.id]?.progress || 0}
                error={stageStatus[stage.id]?.error}
                result={stageStatus[stage.id]?.result}
                onStart={(config) => handleStageStart(stage, config)}
                onStop={() => handleStageStop(stage.id)}
              />
            ))}
          </Grid>

          <Grid item xs={12} md={4}>
            <StatusMonitor
              stages={stages.map((s) => ({
                ...s,
                status: stageStatus[s.id]?.status || "pending",
                progress: stageStatus[s.id]?.progress || 0,
              }))}
              stageStatus={stageStatus}
            />
          </Grid>
        </Grid>
      </Box>
    </Container>
  );
};

export default Dashboard;
