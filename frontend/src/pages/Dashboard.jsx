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
} from "@mui/icons-material";
import StageConfig from "../components/StageConfig";
import PipelineVisualizer from "../components/PipelineVisualizer";
import { ExecutionMonitor } from "../components/ExecutionMonitor";
import { useWebSocketContext } from "../context/WebSocketContext";
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
    onClick={() => onLoad(item)}
  >
    <Box>
      <Typography variant="subtitle2">
        {item.name || `Pipeline ${new Date(item.createdAt).toLocaleString()}`}
      </Typography>
      <Typography variant="caption" color="text.secondary">
        {item.stages?.length || 0} stages • Created: {new Date(item.createdAt).toLocaleDateString()}
      </Typography>
    </Box>
    <IconButton
      size="small"
      onClick={(e) => {
        e.stopPropagation();
        onDelete(item.id);
      }}
    >
      <DeleteIcon fontSize="small" />
    </IconButton>
  </Paper>
);

const Dashboard = () => {
  const theme = useTheme();
  const { isConnected: wsConnected } = useWebSocketContext();
  
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
  
  // Snackbar State
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'info'
  });

  // Load pipeline history from localStorage
  useEffect(() => {
    const savedHistory = localStorage.getItem('pipelineHistory');
    if (savedHistory) {
      setPipelineHistory(JSON.parse(savedHistory));
    }
  }, []);

  // Save pipeline history to localStorage
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

  // Load pipeline from history
  const loadFromHistory = useCallback((historyItem) => {
    setPipeline(historyItem.stages);
    setSnackbar({
      open: true,
      message: `Loaded pipeline: ${historyItem.name}`,
      severity: 'success'
    });
    setCurrentTab(0);
  }, []);

  // Delete from history
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


  // Validate stage configuration
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

  // Add node to pipeline
  const handleAddNode = useCallback(() => {
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

  // Save current pipeline
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

  // Export pipeline as JSON
  const handleExportPipeline = useCallback(() => {
    const dataStr = JSON.stringify({
      pipeline,
      metadata: {
        version: '1.0',
        exportedAt: new Date().toISOString(),
        stageCount: pipeline.length
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

  // Import pipeline from JSON
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

  // Run pipeline
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
      const executionId = `exec_${Date.now()}`;
      setActiveExecutionId(executionId);
      
      setExecutionLogs(prev => [...prev, {
        timestamp: new Date(),
        level: 'info',
        message: 'Pipeline execution started'
      }]);
      
      for (let i = 0; i < pipeline.length; i++) {
        const stage = pipeline[i];
        
        setPipeline(prev => prev.map(s => 
          s.id === stage.id ? { ...s, status: 'running', progress: 0 } : s
        ));
        
        setExecutionLogs(prev => [...prev, {
          timestamp: new Date(),
          level: 'info',
          message: `Starting stage: ${stage.name}`
        }]);
        
        for (let progress = 0; progress <= 100; progress += 20) {
          await new Promise(resolve => setTimeout(resolve, 500));
          setPipeline(prev => prev.map(s =>
            s.id === stage.id ? { ...s, progress } : s
          ));
        }
        
        setPipeline(prev => prev.map(s =>
          s.id === stage.id ? { ...s, status: 'completed', progress: 100 } : s
        ));
        
        setExecutionLogs(prev => [...prev, {
          timestamp: new Date(),
          level: 'success',
          message: `Completed stage: ${stage.name}`
        }]);
      }
      
      setExecutionLogs(prev => [...prev, {
        timestamp: new Date(),
        level: 'success',
        message: 'Pipeline execution completed successfully!'
      }]);
      
      setSnackbar({
        open: true,
        message: 'Pipeline execution completed successfully!',
        severity: 'success'
      });
      
    } catch (error) {
      console.error('Pipeline execution failed:', error);
      setExecutionLogs(prev => [...prev, {
        timestamp: new Date(),
        level: 'error',
        message: `Execution failed: ${error.message}`
      }]);
      setSnackbar({
        open: true,
        message: 'Pipeline execution failed',
        severity: 'error'
      });
    } finally {
      setIsRunning(false);
      setActiveExecutionId(null);
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
                    />
                    <Button 
                      fullWidth 
                      variant="contained" 
                      startIcon={<AddIcon />}
                      onClick={handleAddNode}
                      disabled={isRunning}
                      sx={{ mt: 2, py: 1.5, borderRadius: 2 }}
                    >
                      Add to Pipeline
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
      
      {/* Active Execution Monitor */}
      {activeExecutionId && (
        <Zoom in={!!activeExecutionId}>
          <Box sx={{ position: 'fixed', bottom: 80, right: 24, width: 400, zIndex: 1000 }}>
            <ExecutionMonitor executionId={activeExecutionId} />
          </Box>
        </Zoom>
      )}
      
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
    </Container>
  );
};

export default Dashboard;