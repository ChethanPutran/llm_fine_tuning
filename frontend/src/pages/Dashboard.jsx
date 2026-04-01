import React, { useState, useCallback, useEffect, useMemo } from "react";
import {
  Container,
  Grid,
  Typography,
  Box,
  Button,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Card,
  CardContent,
  Divider,
  Alert,
  Snackbar,
  Chip,
  IconButton,
  Paper,
  LinearProgress,
  Tabs,
  Tab,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Fab,
  Zoom,
  useTheme,
  alpha,
  Drawer,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Badge,
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Switch,
  FormControlLabel,
  RadioGroup,
  Radio,
  FormLabel,
} from "@mui/material";
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Save as SaveIcon,
  PlayArrow as PlayArrowIcon,
  Clear as ClearIcon,
  Settings as SettingsIcon,
  Timeline as TimelineIcon,
  Assessment as AssessmentIcon,
  History as HistoryIcon,
  Close as CloseIcon,
  Download as DownloadIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Refresh as RefreshIcon,
   ExpandMore as ExpandMoreIcon,
  DataUsage as DataIcon,
  CleaningServices as PreprocessIcon,
  Code as TokenizerIcon,
  ModelTraining as TrainingIcon,
  Tune as OptimizationIcon,
  CloudUpload as DeployIcon,
  AccountTree as PipelineIcon,
  Visibility as VisibilityIcon,
  Pause as PauseIcon,
  Stop as StopIcon,
  TrendingUp as StatsIcon,
  Info as InfoIcon,
} from "@mui/icons-material";
import StageConfig from "../components/StageConfig";
import PipelineVisualizer from "../components/PipelineVisualizer";
import { ExecutionMonitor } from "../components/ExecutionMonitor";
import { useWebSocketContext } from "../context/WebSocketContext";
import { apiService } from '../services/api';
import { wsService } from '../services/websocket';
import { STAGE_DEFINITIONS } from "../constants/pipelineStages";
import Settings from "./Settings"; // Import Settings component

// Tab Panel Component
const TabPanel = ({ children, value, index, ...other }) => (
  <div
    role="tabpanel"
    hidden={value !== index}
    id={`dashboard-tabpanel-${index}`}
    aria-labelledby={`dashboard-tab-${index}`}
    {...other}
  >
    {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
  </div>
);

// Pipeline History Item Component
const HistoryItem = ({ item, onLoad, onDelete }) => (
  <Paper
    sx={{
      p: 2,
      mb: 1,
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      cursor: 'pointer',
      transition: 'all 0.2s',
      '&:hover': {
        bgcolor: 'action.hover',
        transform: 'translateX(4px)'
      }
    }}
  >
   <Box sx={{ flex: 1 }} onClick={() => onLoad(item)}>
         <Typography variant="subtitle2">
           {item.name || `Pipeline ${new Date(item.createdAt).toLocaleString()}`}
         </Typography>
         <Typography variant="caption" color="text.secondary">
           {item.stages?.length || 0} stages • Created: {new Date(item.createdAt).toLocaleDateString()}
         </Typography>
       </Box>
       <Box>
         <IconButton size="small" onClick={(e) => { e.stopPropagation(); onViewDetails(item); }}>
           <InfoIcon fontSize="small" />
         </IconButton>
         <IconButton size="small" onClick={(e) => { e.stopPropagation(); onDelete(item.id); }}>
           <DeleteIcon fontSize="small" />
         </IconButton>
       </Box>
  </Paper>
);

// Job Status Card Component
const JobStatusCard = ({ job, onCancel, onViewDetails }) => (
  <Card sx={{ mb: 1, position: 'relative' }}>
    <CardContent>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <Box>
          <Typography variant="subtitle2">
            {job.name || `${job.type} Job`}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            ID: {job.id}
          </Typography>
        </Box>
        <Chip 
          size="small"
          label={job.status}
          color={
            job.status === 'completed' ? 'success' :
            job.status === 'running' ? 'info' :
            job.status === 'failed' ? 'error' :
            job.status === 'cancelled' ? 'warning' : 'default'
          }
        />
      </Box>
      
      {job.progress !== undefined && (
        <Box sx={{ mt: 1 }}>
          <LinearProgress 
            variant="determinate" 
            value={job.progress} 
            sx={{ height: 4, borderRadius: 2 }}
          />
          <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
            {job.progress}% complete
          </Typography>
        </Box>
      )}
      
      {job.error && (
        <Alert severity="error" sx={{ mt: 1, py: 0 }}>
          {job.error}
        </Alert>
      )}
      
      <Box sx={{ mt: 1, display: 'flex', gap: 1 }}>
        <Button size="small" onClick={() => onViewDetails(job)}>
          Details
        </Button>
        {job.status === 'running' && (
          <Button size="small" color="error" onClick={() => onCancel(job.id)}>
            Cancel
          </Button>
        )}
      </Box>
    </CardContent>
  </Card>
);


const Dashboard = () => {
  const theme = useTheme();
  const { isConnected: wsContextConnected } = useWebSocketContext();
  
  // State Management
  const [selectedType, setSelectedType] = useState("");
  const [currentConfig, setCurrentConfig] = useState({});
  const [pipeline, setPipeline] = useState([]);
  const [selectedStage, setSelectedStage] = useState(null);
  const [activeExecutionId, setActiveExecutionId] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [currentTab, setCurrentTab] = useState(0);
  const [pipelineHistory, setPipelineHistory] = useState([]);
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const [pipelineName, setPipelineName] = useState("");
  const [validationErrors, setValidationErrors] = useState({});
  const [executionLogs, setExecutionLogs] = useState([]);
  const [settingsOpen, setSettingsOpen] = useState(false); // Settings drawer state

    // WebSocket State
    const [executionId, setExecutionId] = useState(null);
    const [currentJobId, setCurrentJobId] = useState(null);
    const [wsConnected, setWsConnected] = useState(false);
    

  // Job Management State
    const [activeJobs, setActiveJobs] = useState([]);
    const [jobHistory, setJobHistory] = useState([]);
    const [selectedJob, setSelectedJob] = useState(null);
    const [jobDetailsDialog, setJobDetailsDialog] = useState(false);
    const [jobMetrics, setJobMetrics] = useState(null);
    
    // Statistics State
    const [statistics, setStatistics] = useState({
      totalJobs: 0,
      byStatus: {},
      byType: {},
      completedJobs: 0,
      failedJobs: 0,
      runningJobs: 0
    });
  // UI State
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'info'
  });
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  

   // ============= WebSocket Connection =============
  useEffect(() => {
    // Connect WebSocket
    wsService.connect().then(() => {
      setWsConnected(true);
    }).catch((error) => {
      console.error('WebSocket connection failed:', error);
    });

    // Listen for WebSocket events
    const unsubscribeConnected = wsService.on('connected', () => {
      setWsConnected(true);
    });

    const unsubscribeDisconnected = wsService.on('disconnected', () => {
      setWsConnected(false);
    });

    const unsubscribeExecutionUpdate = wsService.on('execution_update', (data) => {
      console.log('Execution update received:', data);
      updatePipelineStatus(data);
    });

    const unsubscribeJobUpdate = wsService.on('job_update', (data) => {
      console.log('Job update received:', data);
      updateJobStatus(data);
    });

    return () => {
      unsubscribeConnected();
      unsubscribeDisconnected();
      unsubscribeExecutionUpdate();
      unsubscribeJobUpdate();
      wsService.disconnect();
    };
  }, []);


    // ============= Load Statistics =============
    const loadStatistics = useCallback(async () => {
      try {
        const [dataStats, trainingStats, deploymentStats] = await Promise.all([
          apiService.getDataCollectionStatistics(),
          apiService.getTrainingStatistics(),
          apiService.getDeploymentStatistics()
        ]);
        
        setStatistics({
          totalJobs: (dataStats.total_jobs || 0) + (trainingStats.total_jobs || 0) + (deploymentStats.total_jobs || 0),
          byStatus: {
            ...dataStats.by_status,
            ...trainingStats.by_status,
            ...deploymentStats.by_status
          },
          byType: {
            dataCollection: dataStats.total_jobs || 0,
            training: trainingStats.total_jobs || 0,
            deployment: deploymentStats.total_jobs || 0
          },
          completedJobs: (dataStats.completed_jobs || 0) + (trainingStats.completed_jobs || 0) + (deploymentStats.completed_jobs || 0),
          failedJobs: (dataStats.failed_jobs || 0) + (trainingStats.failed_jobs || 0) + (deploymentStats.failed_jobs || 0),
          runningJobs: (dataStats.running_jobs || 0) + (trainingStats.running_jobs || 0) + (deploymentStats.running_jobs || 0)
        });
      } catch (error) {
        console.error('Failed to load statistics:', error);
      }
    }, []);
  
    useEffect(() => {
      if (autoRefresh) {
        loadStatistics();
        const interval = setInterval(loadStatistics, 30000);
        return () => clearInterval(interval);
      }
    }, [autoRefresh, loadStatistics]);


  // ============= Pipeline History Management =============
  useEffect(() => {
    const savedHistory = localStorage.getItem('pipelineHistory');
    if (savedHistory) {
      setPipelineHistory(JSON.parse(savedHistory));
    }
  }, []);

    const saveToHistory = useCallback((pipelineData, name = null) => {
      const historyItem = {
        id: Date.now().toString(),
        name: name || `Pipeline ${new Date().toLocaleString()}`,
        stages: pipelineData,
        createdAt: new Date().toISOString(),
        stageCount: pipelineData.length
      };
          const updatedHistory = [historyItem, ...pipelineHistory.slice(0, 9)];
    setPipelineHistory(updatedHistory);
    localStorage.setItem('pipelineHistory', JSON.stringify(updatedHistory));
    return historyItem;
  }, [pipelineHistory]);

    const loadFromHistory = useCallback((historyItem) => {
      setPipeline(historyItem.stages);
      setSnackbar({
        open: true,
        message: `Loaded pipeline: ${historyItem.name}`,
        severity: 'success'
      });
      setCurrentTab(0);
    }, []);
const deleteFromHistory = useCallback((id) => {
    const updatedHistory = pipelineHistory.filter(item => item.id !== id);
    setPipelineHistory(updatedHistory);
    localStorage.setItem('pipelineHistory', JSON.stringify(updatedHistory));
    setSnackbar({
      open: true,
      message: 'Pipeline deleted from history',
      severity: 'info'
    });
  }, [pipelineHistory]);



    // ============= Stage Configuration =============
    const validateStageConfig = useCallback((stageDef, config) => {
      const errors = {};
      const allFields = [...(stageDef.fields || []), ...(stageDef.advancedFields || [])];
      
      allFields.forEach(field => {
        if (field.required && (!config[field.key] || config[field.key] === '')) {
          errors[field.key] = `${field.label} is required`;
        }
        if (field.type === 'number' && config[field.key]) {
          const value = parseFloat(config[field.key]);
          if (field.min !== undefined && value < field.min) {
            errors[field.key] = `${field.label} must be at least ${field.min}`;
          }
          if (field.max !== undefined && value > field.max) {
            errors[field.key] = `${field.label} must be at most ${field.max}`;
          }
        }
      });
      
      return errors;
    }, []);

 // ============= Pipeline Execution =============
    // Update handleRunPipeline to use real API
  const handleRunPipeline = useCallback(async () => {
    if (pipeline.length === 0) {
      setSnackbar({
        open: true,
        message: 'Please add stages to the pipeline first',
        severity: 'warning'
      });
      return;
    }
    
    setIsRunning(true);
    setExecutionLogs([]);
    
    try {
         // First, execute each stage's job if not already executed
              for (let i = 0; i < pipeline.length; i++) {
                const stage = pipeline[i];
                
                if (stage.jobId) {
                  setExecutionLogs(prev => [...prev, {
                    timestamp: new Date(),
                    level: 'info',
                    message: `Executing ${stage.name} (Job: ${stage.jobId})...`
                  }]);
                  
                  // Execute the job
                  let result;
                  switch(stage.type) {
                    case 'data_collection':
                      result = await apiService.executeDataCollectionJob(stage.jobId);
                      break;
                    case 'preprocessing':
                      result = await apiService.executePreprocessingJob(stage.jobId);
                      break;
                    case 'tokenization':
                      result = await apiService.executeTokenizerJob(stage.jobId);
                      break;
                    case 'training':
                    case 'finetuning':
                      result = await apiService.executeTrainingJob(stage.jobId);
                      break;
                    case 'optimization':
                      result = await apiService.executeOptimizationJob(stage.jobId);
                      break;
                    case 'deployment':
                      result = await apiService.executeDeploymentJob(stage.jobId);
                      break;
                    default:
                      continue;
                  }
                  
                  const newExecutionId = result.execution_id;
                  setExecutionId(newExecutionId);
                  setCurrentJobId(stage.jobId);
                  
                  // Subscribe to execution updates
                  wsService.subscribeToExecution(newExecutionId);
                  
                  setExecutionLogs(prev => [...prev, {
                    timestamp: new Date(),
                    level: 'info',
                    message: `${stage.name} execution started: ${newExecutionId}`
                  }]);
                }
              }

      // Convert pipeline to JSON format
      const pipelineJson = {
        nodes: pipeline.map(stage => ({
          id: stage.id,
          type: stage.type,
          name: stage.name,
          config: stage.config
        })),
        edges: pipeline.slice(1).map((_, idx) => ({
          source: pipeline[idx].id,
          target: pipeline[idx + 1].id
        }))
      };
      
      // Execute pipeline
      const result = await apiService.executePipelineDirectly({
        pipelineJson,
        priority: 'HIGH'
      });
      
      const newExecutionId = result.execution_id;
      setExecutionId(newExecutionId);
      setCurrentJobId(result.job_id);
      
      // Subscribe to execution updates via WebSocket
      wsService.subscribeToExecution(newExecutionId);
      
      setExecutionLogs(prev => [...prev, {
        timestamp: new Date(),
        level: 'info',
        message: `Pipeline execution started: ${result.execution_id}`
      }]);
      
      setSnackbar({
        open: true,
        message: 'Pipeline execution started successfully!',
        severity: 'success'
      });
      
    } catch (error) {
      console.error('Pipeline execution failed:', error);
      setExecutionLogs(prev => [...prev, {
        timestamp: new Date(),
        level: 'error',
        message: `Execution failed: ${error.message || 'Unknown error'}`
      }]);
      setSnackbar({
        open: true,
        message: 'Pipeline execution failed',
        severity: 'error'
      });
    } finally {
      setIsRunning(false);
    }
  }, [pipeline]);

// Add function to update pipeline status from WebSocket
const updatePipelineStatus = useCallback((data) => {
  if (data.node_status) {
    setPipeline(prev => prev.map(stage => {
      if (stage.id === data.node_id) {
        return {
          ...stage,
          status: data.node_status,
          progress: data.progress || (data.node_status === 'completed' ? 100 : stage.progress)
        };
      }
      return stage;
    }));
  }
  
  // Add log entries
  if (data.message) {
    setExecutionLogs(prev => [...prev, {
      timestamp: new Date(data.timestamp || Date.now()),
      level: data.level || 'info',
      message: data.message
    }]);
  }
  // Update active jobs
    if (data.job_status) {
      setActiveJobs(prev => {
        const existing = prev.find(j => j.id === data.job_id);
        if (existing) {
          return prev.map(j => j.id === data.job_id ? { ...j, ...data.job_status } : j);
        } else {
          return [...prev, { id: data.job_id, ...data.job_status }];
        }
      });
    }

}, []);

  const updateJobStatus = useCallback((data) => {
    setExecutionLogs(prev => [...prev, {
      timestamp: new Date(),
      level: data.status === 'failed' ? 'error' : 'info',
      message: `Job ${data.job_id}: ${data.status} - ${data.message || ''}`
    }]);
    
    setActiveJobs(prev => prev.filter(j => j.id !== data.job_id));
    setJobHistory(prev => [data, ...prev.slice(0, 19)]);
  }, []);

 // ============= Job Management =============
   const handleCancelJob = useCallback(async (jobId) => {
     try {
       await apiService.cancelTrainingJob(jobId);
       setSnackbar({
         open: true,
         message: 'Job cancelled successfully',
         severity: 'success'
       });
     } catch (error) {
       console.error('Failed to cancel job:', error);
       setSnackbar({
         open: true,
         message: 'Failed to cancel job',
         severity: 'error'
       });
     }
   }, []);
 
// ============= Pipeline Export/Import =============
  const handleSavePipeline = useCallback(() => {
    setSaveDialogOpen(true);
    setPipelineName(`Pipeline ${new Date().toLocaleString()}`);
  }, []);

  const confirmSavePipeline = useCallback(() => {
    const name = pipelineName.trim() || `Pipeline ${new Date().toLocaleString()}`;
    saveToHistory(pipeline, name);
    setSaveDialogOpen(false);
    setPipelineName("");
    setSnackbar({
      open: true,
      message: 'Pipeline saved successfully!',
      severity: 'success'
    });
  }, [pipeline, pipelineName, saveToHistory]);



    const handleExportPipeline = useCallback(() => {
      const dataStr = JSON.stringify({
        pipeline,
        metadata: {
          version: '1.0',
          exportedAt: new Date().toISOString(),
          stageCount: pipeline.length,
          jobIds: pipeline.map(s => s.jobId).filter(Boolean)
        }
      }, null, 2);
      
      const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
      const exportFileDefaultName = `pipeline_${Date.now()}.json`;
      
      const linkElement = document.createElement('a');
      linkElement.setAttribute('href', dataUri);
      linkElement.setAttribute('download', exportFileDefaultName);
      linkElement.click();
      
      setSnackbar({
        open: true,
        message: 'Pipeline exported successfully',
        severity: 'success'
      });
    }, [pipeline]);

     const handleImportPipeline = useCallback(() => {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.json';
        
        input.onchange = (e) => {
          const file = e.target.files[0];
          const reader = new FileReader();
          
          reader.onload = (event) => {
            try {
              const imported = JSON.parse(event.target.result);
              const importedPipeline = imported.pipeline || imported;
              
              if (Array.isArray(importedPipeline)) {
                setPipeline(importedPipeline);
                setSnackbar({
                  open: true,
                  message: `Imported ${importedPipeline.length} stages`,
                  severity: 'success'
                });
              } else {
                throw new Error('Invalid pipeline format');
              }
            } catch (error) {
              setSnackbar({
                open: true,
                message: 'Failed to import pipeline: Invalid format',
                severity: 'error'
              });
            }
          };
          
          reader.readAsText(file);
        };
        
        input.click();
      }, []);

  // Load pipeline history from localStorage
  useEffect(() => {
    const savedHistory = localStorage.getItem('pipelineHistory');
    if (savedHistory) {
      setPipelineHistory(JSON.parse(savedHistory));
    }
  }, []);

  // Add node to pipeline
  const handleAddNode =  useCallback(async () => {
    if (!selectedType) {
      setSnackbar({
        open: true,
        message: 'Please select a stage type',
        severity: 'warning'
      });
      return;
    }

    const stageDef = STAGE_DEFINITIONS.find(s => s.id === selectedType);
    const errors = validateStageConfig(stageDef, currentConfig);
    
    if (Object.keys(errors).length > 0) {
      setValidationErrors(errors);
      setSnackbar({
        open: true,
        message: `Please fix validation errors: ${Object.values(errors).join(', ')}`,
        severity: 'error'
      });
      return;
    }

     // Create the job based on stage type
    let jobResult = null;
    setLoading(true);

    try {
          switch(selectedType) {
            case 'data_collection':
              jobResult = await apiService.createDataCollectionJob({
                source: currentConfig.source,
                topic: currentConfig.topic,
                limit: currentConfig.limit || 100,
                searchEngine: currentConfig.searchEngine || 'google',
                config: currentConfig,
                autoExecute: false
              });
              break;
            case 'preprocessing':
              jobResult = await apiService.createPreprocessingJob({
                inputPath: currentConfig.inputPath,
                config: currentConfig,
                autoExecute: false
              });
              break;
            case 'tokenization':
              jobResult = await apiService.createTokenizerJob({
                tokenizerType: currentConfig.tokenizerType,
                datasetPath: currentConfig.datasetPath,
                vocabSize: currentConfig.vocabSize || 32000,
                config: currentConfig,
                autoExecute: false
              });
              break;
            case 'training':
              jobResult = await apiService.createTrainingJob({
                modelType: currentConfig.modelType,
                modelName: currentConfig.modelName,
                datasetPath: currentConfig.datasetPath,
                config: currentConfig,
                autoExecute: false
              });
              break;
            case 'finetuning':
              jobResult = await apiService.createFinetuningJob({
                modelType: currentConfig.modelType,
                modelName: currentConfig.modelName,
                strategyType: currentConfig.strategyType,
                taskType: currentConfig.taskType,
                datasetPath: currentConfig.datasetPath,
                config: currentConfig,
                autoExecute: false
              });
              break;
            case 'optimization':
              jobResult = await apiService.createOptimizationJob({
                modelPath: currentConfig.modelPath,
                optimizationType: currentConfig.optimizationType,
                config: currentConfig,
                autoExecute: false
              });
              break;
            case 'deployment':
              jobResult = await apiService.createDeploymentJob({
                modelPath: currentConfig.modelPath,
                servingFramework: currentConfig.servingFramework,
                deploymentTarget: currentConfig.deploymentTarget || 'local',
                config: currentConfig,
                autoExecute: false
              });
              break;
            default:
              break;
          }

    const newNode = {
      id: `${selectedType}-${Date.now()}`,
      type: selectedType,
      name: stageDef.name,
      description: `${stageDef.name} stage`,
      config: currentConfig,
      color: stageDef.color,
      status: 'pending',
      progress: 0,
      createdAt: new Date().toISOString(),
      jobId: jobResult?.job_id,
    };

    setPipeline(prev => [...prev, newNode]);
    setSelectedType("");
    setCurrentConfig({});
    setValidationErrors({});
    
    setSnackbar({
      open: true,
      message: `${stageDef.name} added to pipeline`,
      severity: 'success'
    });

    } catch (error) {
      console.error('Failed to create stage job:', error);
      setSnackbar({
        open: true,
        message: `Failed to create ${stageDef.name} job: ${error.message}`,
        severity: 'error'
      });
    } finally {
      setLoading(false);
    }
  }, [selectedType, currentConfig, validateStageConfig]);

  // Remove node from pipeline
  const handleRemoveNode = useCallback((nodeId) => {
    setPipeline(prev => prev.filter(node => node.id !== nodeId));
    if (selectedStage?.id === nodeId) {
      setSelectedStage(null);
    }
    setSnackbar({
      open: true,
      message: 'Stage removed from pipeline',
      severity: 'info'
    });
  }, [selectedStage]);

  // Clear all nodes
  const handleClearAll = useCallback(() => {
    if (pipeline.length === 0) return;
    
    if (window.confirm('Are you sure you want to clear the entire pipeline? This action cannot be undone.')) {
      setPipeline([]);
      setSelectedStage(null);
      setSnackbar({
        open: true,
        message: 'Pipeline cleared',
        severity: 'info'
      });
    }
  }, [pipeline]);

  // Handle node click in visualizer
  const handleNodeClick = useCallback((node) => {
    const originalNode = pipeline.find(n => n.id === node.id);
    setSelectedStage(originalNode);
  }, [pipeline]);

  // Calculate pipeline statistics
  const pipelineStats = useMemo(() => {
    const completed = pipeline.filter(s => s.status === 'completed').length;
    const running = pipeline.filter(s => s.status === 'running').length;
    const failed = pipeline.filter(s => s.status === 'failed').length;
    const pending = pipeline.filter(s => s.status === 'pending' || !s.status).length;
    
    return { completed, running, failed, pending, total: pipeline.length };
  }, [pipeline]);

  return (
    <Container maxWidth="xl" sx={{ py: 4, position: 'relative' }}>
      {/* Header Section with Settings Button */}
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Box>
            <Typography variant="h4" fontWeight="700" gutterBottom>
              ML Pipeline Builder
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Design, visualize, and execute machine learning pipelines with real-time monitoring
            </Typography>
          </Box>
          
          {/* Settings Button - RIGHT HERE */}
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title="Statistics">
                <IconButton onClick={loadStatistics} color="primary">
                <StatsIcon />
                </IconButton>
             </Tooltip>
            <Tooltip title="Settings">
              <IconButton 
                onClick={() => {
                  setSettingsOpen(true)
                }} 
                color="primary"
                sx={{ 
                  bgcolor: alpha(theme.palette.primary.main, 0.1),
                  '&:hover': {
                    bgcolor: alpha(theme.palette.primary.main, 0.2),
                  }
                }}
              >
                <SettingsIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Connection Status">
              <Chip
                icon={wsConnected ? <CheckCircleIcon /> : <ErrorIcon />}
                label={wsConnected ? "Connected" : "Disconnected"}
                color={wsConnected ? "success" : "error"}
                variant="outlined"
                size="small"
              />
            </Tooltip>
          </Box>
        </Box>

        {/* Statistics Cards */}
                <Grid container spacing={2} sx={{ mb: 2 }}>
                  <Grid item xs={12} sm={6} md={3}>
                    <Paper sx={{ p: 2, bgcolor: alpha(theme.palette.primary.main, 0.05) }}>
                      <Typography variant="caption" color="text.secondary">Total Jobs</Typography>
                      <Typography variant="h5">{statistics.totalJobs}</Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <Paper sx={{ p: 2, bgcolor: alpha(theme.palette.success.main, 0.05) }}>
                      <Typography variant="caption" color="text.secondary">Completed</Typography>
                      <Typography variant="h5" color="success.main">{statistics.completedJobs}</Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <Paper sx={{ p: 2, bgcolor: alpha(theme.palette.info.main, 0.05) }}>
                      <Typography variant="caption" color="text.secondary">Running</Typography>
                      <Typography variant="h5" color="info.main">{statistics.runningJobs}</Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <Paper sx={{ p: 2, bgcolor: alpha(theme.palette.error.main, 0.05) }}>
                      <Typography variant="caption" color="text.secondary">Failed</Typography>
                      <Typography variant="h5" color="error.main">{statistics.failedJobs}</Typography>
                    </Paper>
                  </Grid>
                </Grid>
        
        {/* Pipeline Statistics */}
        {pipeline.length > 0 && (
          <Paper sx={{ p: 2, bgcolor: alpha(theme.palette.primary.main, 0.05), mb: 2 }}>
            <Grid container spacing={2} alignItems="center">
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="caption" color="text.secondary">Total Stages</Typography>
                <Typography variant="h6">{pipelineStats.total}</Typography>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="caption" color="text.secondary">Completed</Typography>
                <Typography variant="h6" color="success.main">{pipelineStats.completed}</Typography>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="caption" color="text.secondary">In Progress</Typography>
                <Typography variant="h6" color="info.main">{pipelineStats.running}</Typography>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="caption" color="text.secondary">Pending</Typography>
                <Typography variant="h6" color="warning.main">{pipelineStats.pending}</Typography>
              </Grid>
            </Grid>
          </Paper>
        )}
        
        {/* Tabs */}
        <Tabs
          value={currentTab}
          onChange={(_, v) => setCurrentTab(v)}
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab label="Pipeline Builder" icon={<TimelineIcon />} iconPosition="start" />
          <Tab label="History" icon={<HistoryIcon />} iconPosition="start" />
          <Tab label="Execution Logs" icon={<AssessmentIcon />} iconPosition="start" />
        </Tabs>
      </Box>
      
      {/* Pipeline Builder Tab */}
      <TabPanel value={currentTab} index={0}>
        <Grid container spacing={4}>
          {/* Left Side: Configuration Panel */}
          <Grid item xs={12} md={4}>
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>Add New Stage</Typography>
                
                <FormControl fullWidth sx={{ mb: 3 }}>
                  <InputLabel>Select Stage Type</InputLabel>
                  <Select 
                    value={selectedType} 
                    onChange={(e) => {
                      setSelectedType(e.target.value);
                      setValidationErrors({});
                    }}
                    label="Select Stage Type"
                  >
                    {STAGE_DEFINITIONS.map(s => (
                      <MenuItem key={s.id} value={s.id}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Box sx={{ 
                            width: 12, 
                            height: 12, 
                            borderRadius: '50%', 
                            bgcolor: s.color 
                          }} />
                          {s.name}
                        </Box>
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
  
                {selectedType && (
                  <Box>
                    <StageConfig 
                      stage={STAGE_DEFINITIONS.find(s => s.id === selectedType)} 
                      onConfigChange={(args)=>{
                        console.log('Received config change from StageConfig:', args);
                        setCurrentConfig(args);
                      }
                      }
                      config={currentConfig}
                      errors={validationErrors}
                    />
                    <Button 
                      fullWidth 
                      variant="contained" 
                      startIcon={<AddIcon />}
                      onClick={handleAddNode}
                      disabled={isRunning}
                      sx={{ mt: 2, py: 1.5, borderRadius: 2 }}
                    >
                      {loading ? 'Creating...' : 'Add to Pipeline'}
                    </Button>
                  </Box>
                )}
              </CardContent>
            </Card>
  
            {/* Pipeline Controls */}
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>Pipeline Controls</Typography>
                <Grid container spacing={1}>
                  <Grid item xs={6}>
                    <Button 
                      fullWidth 
                      variant="outlined" 
                      startIcon={<SaveIcon />}
                      onClick={handleSavePipeline}
                      disabled={pipeline.length === 0}
                      size="small"
                    >
                      Save
                    </Button>
                  </Grid>
                  <Grid item xs={6}>
                    <Button 
                      fullWidth 
                      variant="outlined" 
                      startIcon={<DownloadIcon />}
                      onClick={handleExportPipeline}
                      disabled={pipeline.length === 0}
                      size="small"
                    >
                      Export
                    </Button>
                  </Grid>
                  <Grid item xs={6}>
                    <Button 
                      fullWidth 
                      variant="outlined" 
                      startIcon={<RefreshIcon />}
                      onClick={handleImportPipeline}
                      size="small"
                    >
                      Import
                    </Button>
                  </Grid>
                  <Grid item xs={6}>
                    <Button 
                      fullWidth 
                      variant="outlined" 
                      color="error"
                      startIcon={<ClearIcon />}
                      onClick={handleClearAll}
                      disabled={pipeline.length === 0 || isRunning}
                      size="small"
                    >
                      Clear All
                    </Button>
                  </Grid>
                  <Grid item xs={12}>
                    <Button 
                      fullWidth 
                      variant="contained" 
                      color="success"
                      startIcon={<PlayArrowIcon />}
                      onClick={handleRunPipeline}
                      disabled={pipeline.length === 0 || isRunning}
                      size="large"
                      sx={{ mt: 1 }}
                    >
                      {isRunning ? 'Executing Pipeline...' : 'Run Pipeline'}
                    </Button>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>
  
          {/* Right Side: Graph Visualizer */}
          <Grid item xs={12} md={8}>
            <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Typography variant="h6" color="text.secondary">
                Pipeline Visualization
                {pipeline.length > 0 && (
                  <Chip 
                    label={`${pipeline.length} stage${pipeline.length !== 1 ? 's' : ''}`} 
                    size="small" 
                    sx={{ ml: 1 }}
                  />
                )}
              </Typography>

              <FormControlLabel
                              control={
                                <Switch
                                  checked={autoRefresh}
                                  onChange={(e) => setAutoRefresh(e.target.checked)}
                                  size="small"
                                />
                              }
                              label="Auto Refresh"
                            />
            </Box>
            
            <PipelineVisualizer 
              pipelineNodes={pipeline} 
              onNodeClick={handleNodeClick}
            />
            
            {/* Selected Stage Details */}
            {selectedStage && (
              <Card sx={{ mt: 2 }}>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <Box>
                      <Typography variant="subtitle1" fontWeight="bold">
                        {selectedStage.name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary" display="block">
                        Type: {selectedStage.type}
                      </Typography>
                    </Box>
                    <IconButton size="small" onClick={() => setSelectedStage(null)}>
                      <CloseIcon fontSize="small" />
                    </IconButton>
                  </Box>
                  
                  {selectedStage.config && Object.keys(selectedStage.config).length > 0 && (
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="subtitle2" gutterBottom>
                        Configuration
                      </Typography>
                      <Paper variant="outlined" sx={{ p: 1, bgcolor: 'grey.50' }}>
                        <Box component="pre" sx={{ m: 0, fontSize: '12px', overflow: 'auto' }}>
                          {JSON.stringify(selectedStage.config, null, 2)}
                        </Box>
                      </Paper>
                    </Box>
                  )}
                </CardContent>
              </Card>
            )}
 
          </Grid>
        </Grid>
      </TabPanel>

                 
            {/* Pipeline Summary */}
            <Box sx={{ mt: 4 }}>
              <Typography variant="h6" gutterBottom>Pipeline Summary</Typography>
              <Card variant="outlined">
                <CardContent>
                  {pipeline.length === 0 ? (
                    <Typography color="text.disabled" textAlign="center" py={4}>
                      No stages added yet. Use the left panel to begin building your pipeline.
                    </Typography>
                  ) : (
                    <Box>
                      {pipeline.map((node, i) => (
                        <Box key={node.id}>
                          <Box sx={{ 
                            display: 'flex', 
                            justifyContent: 'space-between', 
                            alignItems: 'center', 
                            py: 1.5,
                            '&:hover': { bgcolor: 'action.hover' }
                          }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                              <Chip 
                                label={i + 1} 
                                size="small" 
                                sx={{ 
                                  bgcolor: node.color, 
                                  color: 'white',
                                  minWidth: 32
                                }} 
                              />
                              <Box>
                                <Typography variant="body2">
                                  <strong>{node.name}</strong>
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                  {node.type}
                                </Typography>
                              </Box>
                            </Box>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              {node.status === 'running' && (
                                <LinearProgress 
                                  variant="determinate" 
                                  value={node.progress} 
                                  sx={{ width: 60, height: 4 }}
                                />
                              )}
                              {node.status === 'completed' && (
                                <CheckCircleIcon color="success" fontSize="small" />
                              )}
                              {node.status === 'failed' && (
                                <ErrorIcon color="error" fontSize="small" />
                              )}
                              <IconButton 
                                size="small" 
                                onClick={() => handleRemoveNode(node.id)}
                                disabled={isRunning}
                              >
                                <DeleteIcon fontSize="small" />
                              </IconButton>
                            </Box>
                          </Box>
                          {i < pipeline.length - 1 && <Divider />}
                        </Box>
                      ))}
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Box>
      {/* Active Jobs Tab */}
            <TabPanel value={currentTab} index={1}>
              <Grid container spacing={3}>
                <Grid item xs={12} md={8}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Active Jobs
                      </Typography>
                      {activeJobs.length === 0 ? (
                        <Typography color="text.disabled" textAlign="center" py={4}>
                          No active jobs running.
                        </Typography>
                      ) : (
                        <Box>
                          {activeJobs.map(job => (
                            <JobStatusCard
                              key={job.id}
                              job={job}
                              onCancel={handleCancelJob}
                              onViewDetails={handleViewJobDetails}
                            />
                          ))}
                        </Box>
                      )}
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid item xs={12} md={4}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Job Statistics
                      </Typography>
                      <List dense>
                        <ListItem>
                          <ListItemIcon><PlayArrowIcon color="info" /></ListItemIcon>
                          <ListItemText primary="Running" secondary={statistics.runningJobs} />
                        </ListItem>
                        <ListItem>
                          <ListItemIcon><CheckCircleIcon color="success" /></ListItemIcon>
                          <ListItemText primary="Completed" secondary={statistics.completedJobs} />
                        </ListItem>
                        <ListItem>
                          <ListItemIcon><ErrorIcon color="error" /></ListItemIcon>
                          <ListItemText primary="Failed" secondary={statistics.failedJobs} />
                        </ListItem>
                      </List>
                      <Divider sx={{ my: 2 }} />
                      <Typography variant="subtitle2" gutterBottom>
                        By Type
                      </Typography>
                      <List dense>
                        <ListItem>
                          <ListItemIcon><DataIcon /></ListItemIcon>
                          <ListItemText primary="Data Collection" secondary={statistics.byType?.dataCollection || 0} />
                        </ListItem>
                        <ListItem>
                          <ListItemIcon><TrainingIcon /></ListItemIcon>
                          <ListItemText primary="Training" secondary={statistics.byType?.training || 0} />
                        </ListItem>
                        <ListItem>
                          <ListItemIcon><DeployIcon /></ListItemIcon>
                          <ListItemText primary="Deployment" secondary={statistics.byType?.deployment || 0} />
                        </ListItem>
                      </List>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </TabPanel>

      {/* History Tab */}
      <TabPanel value={currentTab} index={1}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Saved Pipelines
                </Typography>
                {pipelineHistory.length === 0 ? (
                  <Typography color="text.disabled" textAlign="center" py={4}>
                    No saved pipelines yet. Build and save a pipeline to see it here.
                  </Typography>
                ) : (
                  <Box>
                    {pipelineHistory.map(item => (
                      <HistoryItem
                        key={item.id}
                        item={item}
                        onLoad={loadFromHistory}
                        onDelete={deleteFromHistory}
                        onViewDetails={(item) => {
                          setSelectedStage(null);
                          setPipeline(item.stages);
                          setCurrentTab(0);
                          setSnackbar({
                            open: true,
                            message: `Loaded pipeline: ${item.name}`,
                            severity: 'info'
                          });
                        }}
                      />
                    ))}
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>

           <Grid item xs={12} md={4}>
                      <Card>
                        <CardContent>
                          <Typography variant="h6" gutterBottom>
                            Recent Jobs
                          </Typography>
                          {jobHistory.length === 0 ? (
                            <Typography color="text.disabled" textAlign="center" py={2}>
                              No recent jobs
                            </Typography>
                          ) : (
                            <Box sx={{ maxHeight: 400, overflow: 'auto' }}>
                              {jobHistory.slice(0, 10).map((job, idx) => (
                                <Paper key={idx} sx={{ p: 1, mb: 1, cursor: 'pointer' }} onClick={() => handleViewJobDetails(job)}>
                                  <Typography variant="caption" display="block">
                                    {job.job_id}
                                  </Typography>
                                  <Typography variant="caption" color="text.secondary">
                                    Status: {job.status}
                                  </Typography>
                                </Paper>
                              ))}
                            </Box>
                          )}
                        </CardContent>
                      </Card>
                    </Grid>
          
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Pipeline Tips
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  • Save your pipelines to reuse them later
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  • Export pipelines to share with team members
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  • Import JSON files to load existing pipelines
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  • Click on any saved pipeline to load it
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>
      
      {/* Execution Logs Tab */}
      <TabPanel value={currentTab} index={2}>
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">Execution Logs</Typography>
              {executionLogs.length > 0 && (
                <Button
                  size="small"
                  onClick={() => setExecutionLogs([])}
                  startIcon={<ClearIcon />}
                >
                  Clear
                </Button>
              )}
              <Button
                                size="small"
                                onClick={async () => {
                                  if (executionId) {
                                    const logs = await apiService.getExecutionLogs(executionId);
                                    if (logs.logs) {
                                      setExecutionLogs(logs.logs.map(log => ({
                                        timestamp: new Date(),
                                        level: 'info',
                                        message: log
                                      })));
                                    }
                                  }
                                }}
                                startIcon={<RefreshIcon />}
                                disabled={!executionId}
                              >
                                Refresh
                              </Button>
            </Box>
            
            {executionLogs.length === 0 ? (
              <Typography color="text.disabled" textAlign="center" py={4}>
                No execution logs yet. Run a pipeline to see logs here.
              </Typography>
            ) : (
              <Box
                sx={{
                  maxHeight: 500,
                  overflow: 'auto',
                  bgcolor: 'grey.900',
                  color: 'grey.100',
                  p: 2,
                  borderRadius: 1,
                  fontFamily: 'monospace',
                  fontSize: '12px'
                }}
              >
                {executionLogs.map((log, idx) => (
                  <Box
                    key={idx}
                    sx={{
                      mb: 1,
                      color: log.level === 'error' ? 'error.light' :
                             log.level === 'success' ? 'success.light' : 'grey.100'
                    }}
                  >
                    <span style={{ color: 'grey.500' }}>
                      [{new Date(log.timestamp).toLocaleTimeString()}]
                    </span>{' '}
                    {log.message}
                  </Box>
                ))}
              </Box>
            )}
          </CardContent>
        </Card>
      </TabPanel>

       {/* Job Details Dialog */}
            <Dialog open={jobDetailsDialog} onClose={() => setJobDetailsDialog(false)} maxWidth="md" fullWidth>
              <DialogTitle>
                Job Details
                <IconButton sx={{ position: 'absolute', right: 8, top: 8 }} onClick={() => setJobDetailsDialog(false)}>
                  <CloseIcon />
                </IconButton>
              </DialogTitle>
              <DialogContent>
                {selectedJob && (
                  <Box>
                    <Typography variant="subtitle2">Job ID</Typography>
                    <Typography variant="body2" color="text.secondary" paragraph>
                      {selectedJob.id}
                    </Typography>
                    
                    <Typography variant="subtitle2">Status</Typography>
                    <Chip 
                      label={selectedJob.status}
                      color={
                        selectedJob.status === 'completed' ? 'success' :
                        selectedJob.status === 'running' ? 'info' :
                        selectedJob.status === 'failed' ? 'error' : 'default'
                      }
                      size="small"
                      sx={{ mb: 2 }}
                    />
                    
                    {jobMetrics && Object.keys(jobMetrics).length > 0 && (
                      <>
                        <Typography variant="subtitle2" gutterBottom>Metrics</Typography>
                        <Paper variant="outlined" sx={{ p: 2, mb: 2, bgcolor: 'grey.50' }}>
                          <Box component="pre" sx={{ m: 0, fontSize: '12px', overflow: 'auto' }}>
                            {JSON.stringify(jobMetrics, null, 2)}
                          </Box>
                        </Paper>
                      </>
                    )}
                  </Box>
                )}
              </DialogContent>
              <DialogActions>
                <Button onClick={() => setJobDetailsDialog(false)}>Close</Button>
              </DialogActions>
            </Dialog>
      
     
      {/* Save Pipeline Dialog */}
      <Dialog open={saveDialogOpen} onClose={() => setSaveDialogOpen(false)}>
        <DialogTitle>Save Pipeline</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Pipeline Name"
            fullWidth
            variant="outlined"
            value={pipelineName}
            onChange={(e) => setPipelineName(e.target.value)}
            placeholder="Enter a name for this pipeline"
          />
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
            {pipeline.length} stage{pipeline.length !== 1 ? 's' : ''} will be saved
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSaveDialogOpen(false)}>Cancel</Button>
          <Button onClick={confirmSavePipeline} variant="contained">Save</Button>
        </DialogActions>
      </Dialog>

      
      {/* Settings Drawer */}
      <Drawer
        anchor="right"
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        sx={{
          '& .MuiDrawer-paper': {
            width: { xs: '100%', sm: 600, md: 800 },
            boxSizing: 'border-box',
          },
        }}
      >
        <Settings onClose={() => setSettingsOpen(false)} />
      </Drawer>
      
      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={() => setSnackbar(prev => ({ ...prev, open: false }))}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert 
          severity={snackbar.severity} 
          onClose={() => setSnackbar(prev => ({ ...prev, open: false }))}
          variant="filled"
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
      
      {/* Floating Action Button for quick actions */}
      {pipeline.length > 0 && !isRunning && (
        <Zoom in={pipeline.length > 0 && !isRunning}>
          <Fab
            color="primary"
            sx={{ position: 'fixed', bottom: 24, right: 24 }}
            onClick={handleRunPipeline}
            title='Execute Piplines'
          >
            <PlayArrowIcon />
          </Fab>
        </Zoom>
      )}

       {/* Active Execution Monitor */}
      {activeExecutionId && (
        <Zoom in={!!activeExecutionId}>
          <Box sx={{ position: 'fixed', bottom: 80, right: 24, width: 400, zIndex: 1000 }}>
            <ExecutionMonitor executionId={activeExecutionId} />
          </Box>
        </Zoom>
      )}
      
    </Container>
  );
};

export default Dashboard; 