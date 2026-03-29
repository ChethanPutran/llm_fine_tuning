import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  TextField,
  Button,
  FormControlLabel,
  Switch,
  Box,
  Grid,
  Alert,
  CircularProgress,
  Slider,
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material';
import { apiService } from '../services/api';
import ResultsViewer from '../components/ResultsViewer';

const Preprocessing = () => {
  const [inputPath, setInputPath] = useState('');
  const [outputPath, setOutputPath] = useState('');
  const [deduplicate, setDeduplicate] = useState(true);
  const [extractKnowledge, setExtractKnowledge] = useState(true);
  const [cleanMethod, setCleanMethod] = useState('standard');
  const [dedupThreshold, setDedupThreshold] = useState(90);
  const [loading, setLoading] = useState(false);
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState(null);
  const [results, setResults] = useState(null);
  
  useEffect(() => {
    if (jobId) {
      const interval = setInterval(checkStatus, 2000);
      return () => clearInterval(interval);
    }
  }, [jobId]);
  
  const handleStart = async () => {
    if (!inputPath) {
      alert('Please enter input path');
      return;
    }
    
    setLoading(true);
    try {
      const response = await apiService.startPreprocessing(
        inputPath,
        {
          output_path: outputPath,
          deduplicate,
          extract_knowledge: extractKnowledge,
          clean_method: cleanMethod,
          dedup_threshold: dedupThreshold / 100
        }
      );
      setJobId(response.job_id);
      setStatus('started');
    } catch (error) {
      console.error('Error starting preprocessing:', error);
      alert('Failed to start preprocessing');
    } finally {
      setLoading(false);
    }
  };
  
  const checkStatus = async () => {
    if (!jobId) return;
    
    try {
      const data = await apiService.getPreprocessingStatus(jobId);
      setStatus(data.status);
      
      if (data.status === 'completed') {
        setResults(data.result);
        setJobId(null);
      } else if (data.status === 'failed') {
        console.error('Preprocessing failed:', data.error);
        setJobId(null);
      }
    } catch (error) {
      console.error('Error checking status:', error);
    }
  };
  
  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      <Typography variant="h4" gutterBottom>
        Data Preprocessing
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Preprocessing Configuration
            </Typography>
            
            <TextField
              fullWidth
              label="Input Path"
              value={inputPath}
              onChange={(e) => setInputPath(e.target.value)}
              placeholder="/path/to/raw/data"
              sx={{ mb: 2 }}
            />
            
            <TextField
              fullWidth
              label="Output Path (optional)"
              value={outputPath}
              onChange={(e) => setOutputPath(e.target.value)}
              placeholder="/path/to/processed/data"
              sx={{ mb: 2 }}
            />
            
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Cleaning Method</InputLabel>
              <Select
                value={cleanMethod}
                onChange={(e) => setCleanMethod(e.target.value)}
                label="Cleaning Method"
              >
                <MenuItem value="standard">Standard</MenuItem>
                <MenuItem value="advanced">Advanced</MenuItem>
              </Select>
            </FormControl>
            
            <FormControlLabel
              control={
                <Switch
                  checked={deduplicate}
                  onChange={(e) => setDeduplicate(e.target.checked)}
                />
              }
              label="Enable Deduplication"
              sx={{ mb: 2 }}
            />
            
            {deduplicate && (
              <Box sx={{ mb: 2 }}>
                <Typography gutterBottom>
                  Deduplication Threshold: {dedupThreshold}%
                </Typography>
                <Slider
                  value={dedupThreshold}
                  onChange={(e, val) => setDedupThreshold(val)}
                  min={50}
                  max={100}
                  step={1}
                />
              </Box>
            )}
            
            <FormControlLabel
              control={
                <Switch
                  checked={extractKnowledge}
                  onChange={(e) => setExtractKnowledge(e.target.checked)}
                />
              }
              label="Extract Knowledge Entities"
              sx={{ mb: 2 }}
            />
            
            <Button
              variant="contained"
              onClick={handleStart}
              disabled={loading || jobId !== null}
              fullWidth
            >
              {loading ? <CircularProgress size={24} /> : 'Start Preprocessing'}
            </Button>
            
            {status && (
              <Alert severity="info" sx={{ mt: 2 }}>
                Status: {status}
              </Alert>
            )}
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <ResultsViewer results={results} type="metrics" />
        </Grid>
      </Grid>
    </Container>
  );
};

export default Preprocessing;