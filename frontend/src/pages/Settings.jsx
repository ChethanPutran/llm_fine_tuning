import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  TextField,
  Button,
  Switch,
  FormControlLabel,
  Grid,
  Card,
  CardContent,
  Divider,
  Alert,
  Snackbar,
  Tabs,
  Tab,
  Box,
  Slider,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  CircularProgress
} from '@mui/material';
import { Save, Refresh, Settings as SettingsIcon, Security, Storage, Palette } from '@mui/icons-material';
import { api } from '../services/api';

const Settings = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [settings, setSettings] = useState({
    general: {
      appName: 'LLM Fine-tuning Platform',
      environment: 'development',
      debugMode: true,
      theme: 'light',
      language: 'en'
    },
    processing: {
      defaultBatchSize: 16,
      maxWorkers: 4,
      cacheEnabled: true,
      memoryLimit: 8192,
      timeoutSeconds: 3600,
      retryAttempts: 3
    },
    models: {
      defaultModel: 'bert-base-uncased',
      modelCachePath: './models/cache',
      downloadTimeout: 300,
      useGPU: true,
      precision: 'fp32'
    },
    data: {
      dataStoragePath: './data',
      maxFileSizeMB: 1024,
      supportedFormats: ['csv', 'json', 'parquet', 'txt'],
      autoCleanup: true,
      cleanupDays: 30
    },
    deployment: {
      defaultPort: 8080,
      workers: 4,
      maxBatchSize: 32,
      enableMetrics: true,
      enableTracing: false
    },
    security: {
      enableAuth: false,
      apiKeyRequired: false,
      rateLimitEnabled: true,
      rateLimitPerMinute: 60,
      allowedOrigins: ['http://localhost:3000']
    }
  });

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    setLoading(true);
    try {
      const response = await api.getSettings();
      setSettings(response.data);
    } catch (error) {
      console.error('Failed to load settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const saveSettings = async () => {
    setLoading(true);
    try {
      await api.saveSettings(settings);
      setSaveSuccess(true);
    } catch (error) {
      console.error('Failed to save settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleGeneralChange = (field, value) => {
    setSettings(prev => ({
      ...prev,
      general: { ...prev.general, [field]: value }
    }));
  };

  const handleProcessingChange = (field, value) => {
    setSettings(prev => ({
      ...prev,
      processing: { ...prev.processing, [field]: value }
    }));
  };

  const handleModelsChange = (field, value) => {
    setSettings(prev => ({
      ...prev,
      models: { ...prev.models, [field]: value }
    }));
  };

  const handleDataChange = (field, value) => {
    setSettings(prev => ({
      ...prev,
      data: { ...prev.data, [field]: value }
    }));
  };

  const handleDeploymentChange = (field, value) => {
    setSettings(prev => ({
      ...prev,
      deployment: { ...prev.deployment, [field]: value }
    }));
  };

  const handleSecurityChange = (field, value) => {
    setSettings(prev => ({
      ...prev,
      security: { ...prev.security, [field]: value }
    }));
  };

  const TabPanel = ({ children, value, index }) => (
    <div hidden={value !== index}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <SettingsIcon sx={{ fontSize: 32, mr: 2, color: 'primary.main' }} />
          <Typography variant="h4" component="h1">
            System Settings
          </Typography>
          <Box sx={{ flex: 1 }} />
          <Button
            variant="outlined"
            onClick={loadSettings}
            startIcon={<Refresh />}
            disabled={loading}
            sx={{ mr: 2 }}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            onClick={saveSettings}
            startIcon={<Save />}
            disabled={loading}
          >
            Save Changes
          </Button>
        </Box>

        <Divider sx={{ mb: 3 }} />

        <Tabs value={activeTab} onChange={(e, v) => setActiveTab(v)} sx={{ mb: 2 }}>
          <Tab label="General" />
          <Tab label="Processing" />
          <Tab label="Models" />
          <Tab label="Data" />
          <Tab label="Deployment" />
          <Tab label="Security" />
        </Tabs>

        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        )}

        <TabPanel value={activeTab} index={0}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Application Name"
                value={settings.general.appName}
                onChange={(e) => handleGeneralChange('appName', e.target.value)}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Environment</InputLabel>
                <Select
                  value={settings.general.environment}
                  onChange={(e) => handleGeneralChange('environment', e.target.value)}
                  label="Environment"
                >
                  <MenuItem value="development">Development</MenuItem>
                  <MenuItem value="staging">Staging</MenuItem>
                  <MenuItem value="production">Production</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.general.debugMode}
                    onChange={(e) => handleGeneralChange('debugMode', e.target.checked)}
                  />
                }
                label="Debug Mode"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Theme</InputLabel>
                <Select
                  value={settings.general.theme}
                  onChange={(e) => handleGeneralChange('theme', e.target.value)}
                  label="Theme"
                >
                  <MenuItem value="light">Light</MenuItem>
                  <MenuItem value="dark">Dark</MenuItem>
                  <MenuItem value="auto">Auto</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Language</InputLabel>
                <Select
                  value={settings.general.language}
                  onChange={(e) => handleGeneralChange('language', e.target.value)}
                  label="Language"
                >
                  <MenuItem value="en">English</MenuItem>
                  <MenuItem value="zh">Chinese</MenuItem>
                  <MenuItem value="es">Spanish</MenuItem>
                  <MenuItem value="fr">French</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={activeTab} index={1}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="number"
                label="Default Batch Size"
                value={settings.processing.defaultBatchSize}
                onChange={(e) => handleProcessingChange('defaultBatchSize', parseInt(e.target.value))}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="number"
                label="Maximum Workers"
                value={settings.processing.maxWorkers}
                onChange={(e) => handleProcessingChange('maxWorkers', parseInt(e.target.value))}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.processing.cacheEnabled}
                    onChange={(e) => handleProcessingChange('cacheEnabled', e.target.checked)}
                  />
                }
                label="Enable Cache"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="number"
                label="Memory Limit (MB)"
                value={settings.processing.memoryLimit}
                onChange={(e) => handleProcessingChange('memoryLimit', parseInt(e.target.value))}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="number"
                label="Timeout (seconds)"
                value={settings.processing.timeoutSeconds}
                onChange={(e) => handleProcessingChange('timeoutSeconds', parseInt(e.target.value))}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="number"
                label="Retry Attempts"
                value={settings.processing.retryAttempts}
                onChange={(e) => handleProcessingChange('retryAttempts', parseInt(e.target.value))}
              />
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={activeTab} index={2}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Default Model</InputLabel>
                <Select
                  value={settings.models.defaultModel}
                  onChange={(e) => handleModelsChange('defaultModel', e.target.value)}
                  label="Default Model"
                >
                  <MenuItem value="bert-base-uncased">BERT Base Uncased</MenuItem>
                  <MenuItem value="gpt2">GPT-2</MenuItem>
                  <MenuItem value="facebook/bart-base">BART Base</MenuItem>
                  <MenuItem value="t5-small">T5 Small</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Model Cache Path"
                value={settings.models.modelCachePath}
                onChange={(e) => handleModelsChange('modelCachePath', e.target.value)}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="number"
                label="Download Timeout (seconds)"
                value={settings.models.downloadTimeout}
                onChange={(e) => handleModelsChange('downloadTimeout', parseInt(e.target.value))}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.models.useGPU}
                    onChange={(e) => handleModelsChange('useGPU', e.target.checked)}
                  />
                }
                label="Use GPU"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Precision</InputLabel>
                <Select
                  value={settings.models.precision}
                  onChange={(e) => handleModelsChange('precision', e.target.value)}
                  label="Precision"
                >
                  <MenuItem value="fp32">FP32 (Full Precision)</MenuItem>
                  <MenuItem value="fp16">FP16 (Half Precision)</MenuItem>
                  <MenuItem value="int8">INT8 (Quantized)</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={activeTab} index={3}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Data Storage Path"
                value={settings.data.dataStoragePath}
                onChange={(e) => handleDataChange('dataStoragePath', e.target.value)}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="number"
                label="Max File Size (MB)"
                value={settings.data.maxFileSizeMB}
                onChange={(e) => handleDataChange('maxFileSizeMB', parseInt(e.target.value))}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.data.autoCleanup}
                    onChange={(e) => handleDataChange('autoCleanup', e.target.checked)}
                  />
                }
                label="Auto Cleanup"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="number"
                label="Cleanup After (days)"
                value={settings.data.cleanupDays}
                onChange={(e) => handleDataChange('cleanupDays', parseInt(e.target.value))}
              />
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={activeTab} index={4}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="number"
                label="Default Port"
                value={settings.deployment.defaultPort}
                onChange={(e) => handleDeploymentChange('defaultPort', parseInt(e.target.value))}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="number"
                label="Number of Workers"
                value={settings.deployment.workers}
                onChange={(e) => handleDeploymentChange('workers', parseInt(e.target.value))}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="number"
                label="Max Batch Size"
                value={settings.deployment.maxBatchSize}
                onChange={(e) => handleDeploymentChange('maxBatchSize', parseInt(e.target.value))}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.deployment.enableMetrics}
                    onChange={(e) => handleDeploymentChange('enableMetrics', e.target.checked)}
                  />
                }
                label="Enable Metrics"
              />
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={activeTab} index={5}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.security.enableAuth}
                    onChange={(e) => handleSecurityChange('enableAuth', e.target.checked)}
                  />
                }
                label="Enable Authentication"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.security.apiKeyRequired}
                    onChange={(e) => handleSecurityChange('apiKeyRequired', e.target.checked)}
                  />
                }
                label="Require API Key"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.security.rateLimitEnabled}
                    onChange={(e) => handleSecurityChange('rateLimitEnabled', e.target.checked)}
                  />
                }
                label="Enable Rate Limiting"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="number"
                label="Rate Limit (requests per minute)"
                value={settings.security.rateLimitPerMinute}
                onChange={(e) => handleSecurityChange('rateLimitPerMinute', parseInt(e.target.value))}
              />
            </Grid>
          </Grid>
        </TabPanel>
      </Paper>

      <Snackbar
        open={saveSuccess}
        autoHideDuration={6000}
        onClose={() => setSaveSuccess(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert severity="success" onClose={() => setSaveSuccess(false)}>
          Settings saved successfully!
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default Settings;