import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Box,
  Grid,
  Alert,
  CircularProgress,
  Stepper,
  Step,
  StepLabel,
  Card,
  CardContent,
  Slider,
  FormControlLabel,
  Switch
} from '@mui/material';
import { apiService } from '../services/api.jsx';
import ResultsViewer from '../components/ResultsViewer.jsx';

const Training = () => {
  const [activeStep, setActiveStep] = useState(0);
  const [modelTypes, setModelTypes] = useState([]);
  const [strategies, setStrategies] = useState([]);
  const [tasks, setTasks] = useState([]);
  
  const [modelType, setModelType] = useState('bert');
  const [modelName, setModelName] = useState('bert-base-uncased');
  const [strategy, setStrategy] = useState('full');
  const [task, setTask] = useState('classification');
  const [datasetPath, setDatasetPath] = useState('');
  
  const [learningRate, setLearningRate] = useState(2e-5);
  const [numEpochs, setNumEpochs] = useState(3);
  const [batchSize, setBatchSize] = useState(16);
  const [loraR, setLoraR] = useState(8);
  const [useFP16, setUseFP16] = useState(false);
  
  const [loading, setLoading] = useState(false);
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState(null);
  const [results, setResults] = useState(null);
  
  useEffect(() => {
    loadOptions();
  }, []);
  
  useEffect(() => {
    if (jobId) {
      const interval = setInterval(checkStatus, 2000);
      return () => clearInterval(interval);
    }
  }, [jobId]);
  
  const loadOptions = async () => {
    try {
      const [modelTypesData, strategiesData, tasksData] = await Promise.all([
        apiService.getModelTypes(),
        apiService.getFinetuningStrategies(),
        apiService.getFinetuningTasks()
      ]);
      setModelTypes(modelTypesData);
      setStrategies(strategiesData);
      setTasks(tasksData);
    } catch (error) {
      console.error('Error loading options:', error);
    }
  };
  
  const handleStart = async () => {
    if (!datasetPath) {
      alert('Please enter dataset path');
      return;
    }
    
    setLoading(true);
    try {
      const config = {
        learning_rate: learningRate,
        num_epochs: numEpochs,
        batch_size: batchSize,
        fp16: useFP16
      };
      
      if (strategy === 'lora') {
        config.lora_r = loraR;
      }
      
      const response = await apiService.startFinetuning(
        modelType,
        modelName,
        strategy,
        task,
        datasetPath,
        config
      );
      setJobId(response.job_id);
      setStatus('started');
      setActiveStep(1);
    } catch (error) {
      console.error('Error starting training:', error);
      alert('Failed to start training');
    } finally {
      setLoading(false);
    }
  };
  
  const checkStatus = async () => {
    if (!jobId) return;
    
    try {
      const data = await apiService.getFinetuningStatus(jobId);
      setStatus(data.status);
      
      if (data.status === 'completed') {
        setResults(data.result);
        setJobId(null);
        setActiveStep(2);
      } else if (data.status === 'failed') {
        console.error('Training failed:', data.error);
        setJobId(null);
      }
    } catch (error) {
      console.error('Error checking status:', error);
    }
  };
  
  const steps = ['Configure Training', 'Training in Progress', 'Complete'];
  
  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      <Typography variant="h4" gutterBottom>
        Model Training & Fine-tuning
      </Typography>
      
      <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
        {steps.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>
      
      {activeStep === 0 && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Model Configuration
              </Typography>
              
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Model Type</InputLabel>
                <Select
                  value={modelType}
                  onChange={(e) => setModelType(e.target.value)}
                  label="Model Type"
                >
                  {modelTypes.map(type => (
                    <MenuItem key={type} value={type}>{type.toUpperCase()}</MenuItem>
                  ))}
                </Select>
              </FormControl>
              
              <TextField
                fullWidth
                label="Model Name"
                value={modelName}
                onChange={(e) => setModelName(e.target.value)}
                placeholder="bert-base-uncased"
                sx={{ mb: 2 }}
              />
              
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Fine-tuning Strategy</InputLabel>
                <Select
                  value={strategy}
                  onChange={(e) => setStrategy(e.target.value)}
                  label="Fine-tuning Strategy"
                >
                  {strategies.map(s => (
                    <MenuItem key={s} value={s}>{s}</MenuItem>
                  ))}
                </Select>
              </FormControl>
              
              {strategy === 'lora' && (
                <TextField
                  fullWidth
                  type="number"
                  label="LoRA Rank (r)"
                  value={loraR}
                  onChange={(e) => setLoraR(parseInt(e.target.value))}
                  sx={{ mb: 2 }}
                />
              )}
              
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Task Type</InputLabel>
                <Select
                  value={task}
                  onChange={(e) => setTask(e.target.value)}
                  label="Task Type"
                >
                  {tasks.map(t => (
                    <MenuItem key={t} value={t}>{t}</MenuItem>
                  ))}
                </Select>
              </FormControl>
              
              <TextField
                fullWidth
                label="Dataset Path"
                value={datasetPath}
                onChange={(e) => setDatasetPath(e.target.value)}
                placeholder="/path/to/dataset.csv"
                sx={{ mb: 2 }}
              />
            </Paper>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Training Parameters
              </Typography>
              
              <TextField
                fullWidth
                type="number"
                label="Learning Rate"
                value={learningRate}
                onChange={(e) => setLearningRate(parseFloat(e.target.value))}
                inputProps={{ step: 1e-5 }}
                sx={{ mb: 2 }}
              />
              
              <TextField
                fullWidth
                type="number"
                label="Number of Epochs"
                value={numEpochs}
                onChange={(e) => setNumEpochs(parseInt(e.target.value))}
                sx={{ mb: 2 }}
              />
              
              <TextField
                fullWidth
                type="number"
                label="Batch Size"
                value={batchSize}
                onChange={(e) => setBatchSize(parseInt(e.target.value))}
                sx={{ mb: 2 }}
              />
              
              <FormControlLabel
                control={
                  <Switch
                    checked={useFP16}
                    onChange={(e) => setUseFP16(e.target.checked)}
                  />
                }
                label="Use Mixed Precision (FP16)"
              />
              
              <Button
                variant="contained"
                onClick={handleStart}
                disabled={loading}
                fullWidth
                sx={{ mt: 2 }}
              >
                {loading ? <CircularProgress size={24} /> : 'Start Training'}
              </Button>
            </Paper>
          </Grid>
        </Grid>
      )}
      
      {activeStep === 1 && (
        <Paper sx={{ p: 3, textAlign: 'center' }}>
          <CircularProgress size={60} sx={{ mb: 2 }} />
          <Typography variant="h6">Training in Progress...</Typography>
          <Typography color="textSecondary">
            Job ID: {jobId}
          </Typography>
          {status && (
            <Alert severity="info" sx={{ mt: 2 }}>
              Status: {status}
            </Alert>
          )}
        </Paper>
      )}
      
      {activeStep === 2 && (
        <ResultsViewer results={results} type="training" />
      )}
    </Container>
  );
};

export default Training;