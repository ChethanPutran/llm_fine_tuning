import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  TextField,
  Box,
  Grid,
  Alert,
  CircularProgress,
  Card,
  CardContent,
  Chip
} from '@mui/material';
import { apiService } from '../services/api.jsx';
import ResultsViewer from '../components/ResultsViewer.jsx';

const Deployment = () => {
  const [targets, setTargets] = useState([]);
  const [frameworks, setFrameworks] = useState([]);
  const [selectedTarget, setSelectedTarget] = useState('local');
  const [selectedFramework, setSelectedFramework] = useState('torchserve');
  const [modelPath, setModelPath] = useState('');
  const [loading, setLoading] = useState(false);
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState(null);
  const [results, setResults] = useState(null);
  const [deployments, setDeployments] = useState([]);
  
  useEffect(() => {
    loadOptions();
    loadDeployments();
  }, []);
  
  useEffect(() => {
    if (jobId) {
      const interval = setInterval(checkStatus, 2000);
      return () => clearInterval(interval);
    }
  }, [jobId]);
  
  const loadOptions = async () => {
    try {
      const [targetsData, frameworksData] = await Promise.all([
        apiService.getDeploymentTargets(),
        apiService.getServingFrameworks()
      ]);
      setTargets(targetsData);
      setFrameworks(frameworksData);
    } catch (error) {
      console.error('Error loading options:', error);
    }
  };
  
  const loadDeployments = async () => {
    try {
      const data = await apiService.getDeployments();
      setDeployments(data);
    } catch (error) {
      console.error('Error loading deployments:', error);
    }
  };
  
  const handleDeploy = async () => {
    if (!modelPath) {
      alert('Please enter model path');
      return;
    }
    
    setLoading(true);
    try {
      const response = await apiService.deployModel(
        modelPath,
        selectedTarget,
        selectedFramework,
        {}
      );
      setJobId(response.job_id);
      setStatus('started');
    } catch (error) {
      console.error('Error deploying model:', error);
      alert('Failed to deploy model');
    } finally {
      setLoading(false);
    }
  };
  
  const checkStatus = async () => {
    if (!jobId) return;
    
    try {
      const data = await apiService.getDeploymentStatus(jobId);
      setStatus(data.status);
      
      if (data.status === 'completed') {
        setResults(data.result);
        setJobId(null);
        loadDeployments();
      } else if (data.status === 'failed') {
        console.error('Deployment failed:', data.error);
        setJobId(null);
      }
    } catch (error) {
      console.error('Error checking status:', error);
    }
  };
  
  const handleUndeploy = async (deploymentId) => {
    try {
      await apiService.undeployModel(deploymentId);
      loadDeployments();
    } catch (error) {
      console.error('Error undeploying model:', error);
    }
  };
  
  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      <Typography variant="h4" gutterBottom>
        Model Deployment
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Deploy New Model
            </Typography>
            
            <TextField
              fullWidth
              label="Model Path"
              value={modelPath}
              onChange={(e) => setModelPath(e.target.value)}
              placeholder="/path/to/model"
              sx={{ mb: 2 }}
            />
            
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Deployment Target</InputLabel>
              <Select
                value={selectedTarget}
                onChange={(e) => setSelectedTarget(e.target.value)}
                label="Deployment Target"
              >
                {targets.map(target => (
                  <MenuItem key={target} value={target}>
                    {target.charAt(0).toUpperCase() + target.slice(1)}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Serving Framework</InputLabel>
              <Select
                value={selectedFramework}
                onChange={(e) => setSelectedFramework(e.target.value)}
                label="Serving Framework"
              >
                {frameworks.map(framework => (
                  <MenuItem key={framework} value={framework}>
                    {framework}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            
            <Button
              variant="contained"
              onClick={handleDeploy}
              disabled={loading || jobId !== null}
              fullWidth
            >
              {loading ? <CircularProgress size={24} /> : 'Deploy Model'}
            </Button>
            
            {status && (
              <Alert severity="info" sx={{ mt: 2 }}>
                Status: {status}
              </Alert>
            )}
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <ResultsViewer results={results} type="deployment" />
        </Grid>
        
        <Grid item xs={12}>
          <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
            Active Deployments
          </Typography>
          
          {deployments.map((deployment) => (
            <Card key={deployment.deployment_id} sx={{ mb: 2 }}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Box>
                    <Typography variant="h6">
                      {deployment.model_path.split('/').pop()}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Endpoint: {deployment.endpoint}
                    </Typography>
                    <Box sx={{ mt: 1 }}>
                      <Chip label={deployment.framework} size="small" sx={{ mr: 1 }} />
                      <Chip label={deployment.status} size="small" color="success" />
                    </Box>
                  </Box>
                  <Button
                    variant="outlined"
                    color="error"
                    onClick={() => handleUndeploy(deployment.deployment_id)}
                  >
                    Undeploy
                  </Button>
                </Box>
              </CardContent>
            </Card>
          ))}
        </Grid>
      </Grid>
    </Container>
  );
};

export default Deployment;