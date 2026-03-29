import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  TextField,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Box,
  Grid,
  Alert,
  CircularProgress
} from '@mui/material';
import { apiService } from '../services/api.jsx';
import PipelineStage from '../components/PipelineStage.jsx';
import ResultsViewer from '../components/ResultsViewer.jsx';

const DataCollection = () => {
  const [sources, setSources] = useState([]);
  const [selectedSource, setSelectedSource] = useState('web');
  const [topic, setTopic] = useState('');
  const [limit, setLimit] = useState(100);
  const [loading, setLoading] = useState(false);
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState(null);
  const [results, setResults] = useState(null);
  
  useEffect(() => {
    loadSources();
  }, []);
  
  useEffect(() => {
    if (jobId) {
      const interval = setInterval(checkStatus, 2000);
      return () => clearInterval(interval);
    }
  }, [jobId]);
  
  const loadSources = async () => {
    try {
      const data = await apiService.getDataSources();
      setSources(data);
    } catch (error) {
      console.error('Error loading sources:', error);
    }
  };
  
  const handleStart = async () => {
    if (!topic) {
      alert('Please enter a topic');
      return;
    }
    
    setLoading(true);
    try {
      const response = await apiService.startDataCollection(
        selectedSource,
        topic,
        limit,
        {}
      );
      setJobId(response.job_id);
      setStatus('started');
    } catch (error) {
      console.error('Error starting collection:', error);
      alert('Failed to start data collection');
    } finally {
      setLoading(false);
    }
  };
  
  const checkStatus = async () => {
    if (!jobId) return;
    
    try {
      const data = await apiService.getCollectionStatus(jobId);
      setStatus(data.status);
      
      if (data.status === 'completed') {
        setResults(data.result);
        setJobId(null);
      } else if (data.status === 'failed') {
        console.error('Collection failed:', data.error);
        setJobId(null);
      }
    } catch (error) {
      console.error('Error checking status:', error);
    }
  };
  
  const handleStop = () => {
    setJobId(null);
    setStatus(null);
  };
  
  const stage = {
    name: 'Data Collection',
    config: {
      source: selectedSource,
      topic,
      limit
    },
    fields: [
      {
        key: 'source',
        label: 'Data Source',
        type: 'select',
        options: sources.map(s => ({ value: s, label: s }))
      },
      {
        key: 'topic',
        label: 'Topic',
        type: 'text',
        helper: 'Enter the topic to search for'
      },
      {
        key: 'limit',
        label: 'Document Limit',
        type: 'number',
        helper: 'Maximum number of documents to collect'
      }
    ]
  };
  
  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      <Typography variant="h4" gutterBottom>
        Data Collection
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Collection Configuration
            </Typography>
            
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Data Source</InputLabel>
              <Select
                value={selectedSource}
                onChange={(e) => setSelectedSource(e.target.value)}
                label="Data Source"
              >
                {sources.map(source => (
                  <MenuItem key={source} value={source}>
                    {source.charAt(0).toUpperCase() + source.slice(1)}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            
            <TextField
              fullWidth
              label="Topic"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="e.g., machine learning, artificial intelligence"
              sx={{ mb: 2 }}
            />
            
            <TextField
              fullWidth
              type="number"
              label="Document Limit"
              value={limit}
              onChange={(e) => setLimit(parseInt(e.target.value))}
              sx={{ mb: 2 }}
            />
            
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button
                variant="contained"
                onClick={handleStart}
                disabled={loading || jobId !== null}
              >
                {loading ? <CircularProgress size={24} /> : 'Start Collection'}
              </Button>
              
              {jobId && (
                <Button
                  variant="outlined"
                  onClick={handleStop}
                  disabled={status === 'completed'}
                >
                  Stop
                </Button>
              )}
            </Box>
            
            {status && (
              <Alert severity="info" sx={{ mt: 2 }}>
                Status: {status}
              </Alert>
            )}
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <ResultsViewer results={results} type="documents" />
        </Grid>
      </Grid>
    </Container>
  );
};

export default DataCollection;