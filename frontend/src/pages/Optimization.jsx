import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Slider,
  Switch,
  FormControlLabel,
  Chip,
  Box,
  LinearProgress,
  Alert,
  IconButton,
  Tooltip,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow
} from '@mui/material';
import {
  PlayArrow,
  Stop,
  Visibility,
  Speed,
  Memory,
  Storage,
  TrendingDown,
  Psychology,
  DataObject
} from '@mui/icons-material';
import { api } from '../services/api';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

const Optimization = () => {
  const [optimizationType, setOptimizationType] = useState('pruning');
  const [modelPath, setModelPath] = useState('');
  const [config, setConfig] = useState({
    pruning: {
      target_sparsity: 0.5,
      method: 'magnitude',
      remove_weights: true
    },
    distillation: {
      teacher_model: '',
      temperature: 4.0,
      alpha: 0.5,
      num_epochs: 10
    },
    quantization: {
      bits: 8,
      symmetric: true,
      per_channel: false,
      calibration_size: 100
    }
  });
  
  const [optimizationJob, setOptimizationJob] = useState(null);
  const [optimizationHistory, setOptimizationHistory] = useState([]);
  const [comparisonData, setComparisonData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadOptimizationHistory();
  }, []);

  const loadOptimizationHistory = async () => {
    try {
      const response = await api.getOptimizationHistory();
      setOptimizationHistory(response.data);
    } catch (error) {
      console.error('Failed to load optimization history:', error);
    }
  };

  const startOptimization = async () => {
    setLoading(true);
    try {
      const response = await api.startOptimization({
        type: optimizationType,
        model_path: modelPath,
        config: config[optimizationType]
      });
      setOptimizationJob(response.data);
      pollJobStatus(response.data.job_id);
    } catch (error) {
      console.error('Failed to start optimization:', error);
    } finally {
      setLoading(false);
    }
  };

  const pollJobStatus = (jobId) => {
    const interval = setInterval(async () => {
      try {
        const status = await api.getOptimizationStatus(jobId);
        setOptimizationJob(status.data);
        
        if (status.data.status === 'completed') {
          clearInterval(interval);
          loadComparisonData(jobId);
          loadOptimizationHistory();
        } else if (status.data.status === 'failed') {
          clearInterval(interval);
        }
      } catch (error) {
        console.error('Failed to get job status:', error);
        clearInterval(interval);
      }
    }, 2000);
  };

  const loadComparisonData = async (jobId) => {
    try {
      const response = await api.compareOptimization(jobId);
      setComparisonData(response.data);
    } catch (error) {
      console.error('Failed to load comparison data:', error);
    }
  };

  const getOptimizationIcon = (type) => {
    switch(type) {
      case 'pruning': return <Speed />;
      case 'distillation': return <Psychology />;
      case 'quantization': return <Storage />;
      default: return <DataObject />;
    }
  };

  const renderPruningConfig = () => (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <Typography variant="subtitle1" gutterBottom>
          Target Sparsity: {(config.pruning.target_sparsity * 100).toFixed(0)}%
        </Typography>
        <Slider
          value={config.pruning.target_sparsity}
          onChange={(e, val) => setConfig({
            ...config,
            pruning: { ...config.pruning, target_sparsity: val }
          })}
          min={0}
          max={0.9}
          step={0.05}
          marks={[
            { value: 0, label: '0%' },
            { value: 0.5, label: '50%' },
            { value: 0.9, label: '90%' }
          ]}
        />
      </Grid>
      <Grid item xs={12} md={6}>
        <FormControl fullWidth>
          <InputLabel>Pruning Method</InputLabel>
          <Select
            value={config.pruning.method}
            onChange={(e) => setConfig({
              ...config,
              pruning: { ...config.pruning, method: e.target.value }
            })}
            label="Pruning Method"
          >
            <MenuItem value="magnitude">Magnitude Pruning</MenuItem>
            <MenuItem value="random">Random Pruning</MenuItem>
            <MenuItem value="gradient">Gradient-based Pruning</MenuItem>
            <MenuItem value="movement">Movement Pruning</MenuItem>
          </Select>
        </FormControl>
      </Grid>
      <Grid item xs={12} md={6}>
        <FormControlLabel
          control={
            <Switch
              checked={config.pruning.remove_weights}
              onChange={(e) => setConfig({
                ...config,
                pruning: { ...config.pruning, remove_weights: e.target.checked }
              })}
            />
          }
          label="Remove Pruned Weights"
        />
      </Grid>
    </Grid>
  );

  const renderDistillationConfig = () => (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <TextField
          fullWidth
          label="Teacher Model Path"
          value={config.distillation.teacher_model}
          onChange={(e) => setConfig({
            ...config,
            distillation: { ...config.distillation, teacher_model: e.target.value }
          })}
          placeholder="/path/to/teacher/model"
        />
      </Grid>
      <Grid item xs={12} md={6}>
        <Typography variant="subtitle1" gutterBottom>
          Temperature: {config.distillation.temperature}
        </Typography>
        <Slider
          value={config.distillation.temperature}
          onChange={(e, val) => setConfig({
            ...config,
            distillation: { ...config.distillation, temperature: val }
          })}
          min={1}
          max={10}
          step={0.5}
        />
      </Grid>
      <Grid item xs={12} md={6}>
        <Typography variant="subtitle1" gutterBottom>
          Alpha (Distillation Weight): {config.distillation.alpha}
        </Typography>
        <Slider
          value={config.distillation.alpha}
          onChange={(e, val) => setConfig({
            ...config,
            distillation: { ...config.distillation, alpha: val }
          })}
          min={0}
          max={1}
          step={0.05}
        />
      </Grid>
      <Grid item xs={12} md={6}>
        <TextField
          fullWidth
          type="number"
          label="Number of Epochs"
          value={config.distillation.num_epochs}
          onChange={(e) => setConfig({
            ...config,
            distillation: { ...config.distillation, num_epochs: parseInt(e.target.value) }
          })}
        />
      </Grid>
    </Grid>
  );

  const renderQuantizationConfig = () => (
    <Grid container spacing={3}>
      <Grid item xs={12} md={6}>
        <FormControl fullWidth>
          <InputLabel>Bit Precision</InputLabel>
          <Select
            value={config.quantization.bits}
            onChange={(e) => setConfig({
              ...config,
              quantization: { ...config.quantization, bits: e.target.value }
            })}
            label="Bit Precision"
          >
            <MenuItem value={8}>8-bit</MenuItem>
            <MenuItem value={4}>4-bit</MenuItem>
            <MenuItem value={2}>2-bit</MenuItem>
          </Select>
        </FormControl>
      </Grid>
      <Grid item xs={12} md={6}>
        <FormControlLabel
          control={
            <Switch
              checked={config.quantization.symmetric}
              onChange={(e) => setConfig({
                ...config,
                quantization: { ...config.quantization, symmetric: e.target.checked }
              })}
            />
          }
          label="Symmetric Quantization"
        />
      </Grid>
      <Grid item xs={12} md={6}>
        <FormControlLabel
          control={
            <Switch
              checked={config.quantization.per_channel}
              onChange={(e) => setConfig({
                ...config,
                quantization: { ...config.quantization, per_channel: e.target.checked }
              })}
            />
          }
          label="Per-channel Quantization"
        />
      </Grid>
      <Grid item xs={12} md={6}>
        <TextField
          fullWidth
          type="number"
          label="Calibration Samples"
          value={config.quantization.calibration_size}
          onChange={(e) => setConfig({
            ...config,
            quantization: { ...config.quantization, calibration_size: parseInt(e.target.value) }
          })}
        />
      </Grid>
    </Grid>
  );

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Paper sx={{ p: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Model Optimization
        </Typography>
        <Typography variant="body2" color="textSecondary" paragraph>
          Optimize your models using pruning, distillation, or quantization techniques
        </Typography>

        <Grid container spacing={3}>
          {/* Configuration Panel */}
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Optimization Configuration
                </Typography>
                
                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel>Optimization Type</InputLabel>
                  <Select
                    value={optimizationType}
                    onChange={(e) => setOptimizationType(e.target.value)}
                    label="Optimization Type"
                  >
                    <MenuItem value="pruning">Pruning</MenuItem>
                    <MenuItem value="distillation">Knowledge Distillation</MenuItem>
                    <MenuItem value="quantization">Quantization</MenuItem>
                  </Select>
                </FormControl>

                <TextField
                  fullWidth
                  label="Model Path"
                  value={modelPath}
                  onChange={(e) => setModelPath(e.target.value)}
                  placeholder="/path/to/model"
                  sx={{ mb: 2 }}
                />

                {optimizationType === 'pruning' && renderPruningConfig()}
                {optimizationType === 'distillation' && renderDistillationConfig()}
                {optimizationType === 'quantization' && renderQuantizationConfig()}

                <Button
                  fullWidth
                  variant="contained"
                  onClick={startOptimization}
                  disabled={loading || !modelPath}
                  startIcon={<PlayArrow />}
                  sx={{ mt: 2 }}
                >
                  Start Optimization
                </Button>
              </CardContent>
            </Card>
          </Grid>

          {/* Status and Results */}
          <Grid item xs={12} md={8}>
            {optimizationJob && optimizationJob.status === 'running' && (
              <Card sx={{ mb: 3 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Optimization in Progress
                  </Typography>
                  <LinearProgress variant="determinate" value={optimizationJob.progress} />
                  <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                    {optimizationJob.progress}% complete
                  </Typography>
                  {optimizationJob.message && (
                    <Alert severity="info" sx={{ mt: 2 }}>
                      {optimizationJob.message}
                    </Alert>
                  )}
                </CardContent>
              </Card>
            )}

            {comparisonData && (
              <Card sx={{ mb: 3 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Optimization Results
                  </Typography>
                  
                  <Grid container spacing={2} sx={{ mb: 3 }}>
                    <Grid item xs={6} md={3}>
                      <Card variant="outlined">
                        <CardContent sx={{ textAlign: 'center' }}>
                          <TrendingDown color="primary" />
                          <Typography variant="h4">
                            {(comparisonData.size_reduction * 100).toFixed(1)}%
                          </Typography>
                          <Typography variant="body2">Size Reduction</Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                    <Grid item xs={6} md={3}>
                      <Card variant="outlined">
                        <CardContent sx={{ textAlign: 'center' }}>
                          <Speed color="primary" />
                          <Typography variant="h4">
                            {comparisonData.speedup.toFixed(2)}x
                          </Typography>
                          <Typography variant="body2">Speedup</Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                    <Grid item xs={6} md={3}>
                      <Card variant="outlined">
                        <CardContent sx={{ textAlign: 'center' }}>
                          <Memory color="primary" />
                          <Typography variant="h4">
                            {(comparisonData.memory_reduction * 100).toFixed(1)}%
                          </Typography>
                          <Typography variant="body2">Memory Reduction</Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                    <Grid item xs={6} md={3}>
                      <Card variant="outlined">
                        <CardContent sx={{ textAlign: 'center' }}>
                          <Psychology color={comparisonData.accuracy_change >= 0 ? 'success' : 'error'} />
                          <Typography variant="h4" color={comparisonData.accuracy_change >= 0 ? 'success.main' : 'error.main'}>
                            {comparisonData.accuracy_change >= 0 ? '+' : ''}{(comparisonData.accuracy_change * 100).toFixed(1)}%
                          </Typography>
                          <Typography variant="body2">Accuracy Change</Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                  </Grid>

                  <Typography variant="subtitle1" gutterBottom>
                    Performance Comparison
                  </Typography>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={comparisonData.metrics_comparison}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="metric" />
                      <YAxis />
                      <RechartsTooltip />
                      <Legend />
                      <Bar dataKey="original" fill="#8884d8" name="Original Model" />
                      <Bar dataKey="optimized" fill="#82ca9d" name="Optimized Model" />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            )}

            {/* Optimization History */}
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Optimization History
                </Typography>
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Date</TableCell>
                        <TableCell>Type</TableCell>
                        <TableCell>Model</TableCell>
                        <TableCell>Size Reduction</TableCell>
                        <TableCell>Speedup</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {optimizationHistory.map((job) => (
                        <TableRow key={job.job_id}>
                          <TableCell>{new Date(job.timestamp).toLocaleString()}</TableCell>
                          <TableCell>
                            <Chip
                              icon={getOptimizationIcon(job.type)}
                              label={job.type}
                              size="small"
                            />
                          </TableCell>
                          <TableCell>{job.model_name}</TableCell>
                          <TableCell>
                            {job.size_reduction ? `${(job.size_reduction * 100).toFixed(1)}%` : '-'}
                          </TableCell>
                          <TableCell>
                            {job.speedup ? `${job.speedup.toFixed(2)}x` : '-'}
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={job.status}
                              color={job.status === 'completed' ? 'success' : job.status === 'failed' ? 'error' : 'warning'}
                              size="small"
                            />
                          </TableCell>
                          <TableCell>
                            <Tooltip title="View Details">
                              <IconButton size="small" onClick={() => loadComparisonData(job.job_id)}>
                                <Visibility />
                              </IconButton>
                            </Tooltip>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>
    </Container>
  );
};

export default Optimization;