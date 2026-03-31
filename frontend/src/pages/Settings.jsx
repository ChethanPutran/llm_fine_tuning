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
  CircularProgress,
  IconButton,
  Tooltip,
  Chip,
  Stack,
  LinearProgress,
  Avatar,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  RadioGroup,
  Radio,
  FormLabel,
  InputAdornment
} from '@mui/material';
import {
  Save,
  Refresh,
  Settings as SettingsIcon,
  Security,
  Storage,
  Palette,
  Speed,
  Memory,
  Cloud,
  Api,
  VpnKey,
  Notifications,
  Language,
  DarkMode,
  LightMode,
  AutoMode,
  CheckCircle,
  Warning,
  Info,
  Delete,
  Science,
  BugReport,
  RestartAlt,
  Download,
  Upload,
  Close as CloseIcon,
  ExpandMore,
  Computer,
  Phone,
  Tablet,
  Webhook,
  DataObject,
  Timeline,
  BarChart,
  MonitorHeart,
  Lock,
  Public,
  Visibility,
  VisibilityOff,
  AccountCircle
} from '@mui/icons-material';
import { settingsAPI } from '../services/settingsAPI';

// Tab Panel Component
const TabPanel = ({ children, value, index, ...other }) => (
  <div
    role="tabpanel"
    hidden={value !== index}
    id={`settings-tabpanel-${index}`}
    aria-labelledby={`settings-tab-${index}`}
    {...other}
  >
    {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
  </div>
);

// Setting Card Component
const SettingCard = ({ title, icon, children, description }) => (
  <Card sx={{ mb: 3 }}>
    <CardContent>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
          {icon}
        </Avatar>
        <Box>
          <Typography variant="h6">{title}</Typography>
          {description && (
            <Typography variant="caption" color="text.secondary">
              {description}
            </Typography>
          )}
        </Box>
      </Box>
      <Divider sx={{ mb: 2 }} />
      {children}
    </CardContent>
  </Card>
);

// Color Picker Component
const ColorPicker = ({ value, onChange, label }) => (
  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
    <Box
      sx={{
        width: 40,
        height: 40,
        borderRadius: 1,
        bgcolor: value,
        border: '1px solid #ddd',
        cursor: 'pointer'
      }}
      onClick={() => {
        const input = document.createElement('input');
        input.type = 'color';
        input.value = value;
        input.onchange = (e) => onChange(e.target.value);
        input.click();
      }}
    />
    <TextField
      label={label}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      size="small"
    />
  </Box>
);

const Settings = ({ onClose }) => {
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState(null);
  const [resetDialogOpen, setResetDialogOpen] = useState(false);
  const [exportDialogOpen, setExportDialogOpen] = useState(false);
  const [importDialogOpen, setImportDialogOpen] = useState(false);
  const [importData, setImportData] = useState(null);
  const [backupList, setBackupList] = useState([]);
  const [showPassword, setShowPassword] = useState(false);
  
  const [settings, setSettings] = useState({
    // General Settings
    general: {
      appName: 'LLM Fine-tuning Platform',
      appVersion: '1.0.0',
      environment: 'development',
      debugMode: true,
      theme: 'light',
      language: 'en',
      timezone: 'UTC',
      dateFormat: 'YYYY-MM-DD',
      notificationsEnabled: true,
      emailNotifications: false,
      desktopNotifications: true,
      soundEnabled: false,
      autoSave: true,
      autoSaveInterval: 30,
      compactMode: false,
      animationsEnabled: true,
      tooltipsEnabled: true
    },
    
    // UI Customization
    ui: {
      primaryColor: '#1976d2',
      secondaryColor: '#dc004e',
      backgroundColor: '#f5f5f5',
      paperColor: '#ffffff',
      borderRadius: 8,
      fontSize: 14,
      density: 'comfortable',
      sidebarCollapsed: false,
      showBreadcrumbs: true,
      showRecentActivities: true,
      maxRecentItems: 10
    },
    
    // Processing Settings
    processing: {
      defaultBatchSize: 16,
      maxWorkers: 4,
      cacheEnabled: true,
      memoryLimit: 8192,
      timeoutSeconds: 3600,
      retryAttempts: 3,
      retryDelay: 1000,
      maxQueueSize: 100,
      priorityQueue: true,
      parallelProcessing: true,
      gpuMemoryFraction: 0.8,
      cpuThreads: 4,
      enableProfiling: false,
      logLevel: 'info'
    },
    
    // Model Settings
    models: {
      defaultModel: 'bert-base-uncased',
      modelCachePath: './models/cache',
      downloadTimeout: 300,
      useGPU: true,
      precision: 'fp32',
      maxSequenceLength: 512,
      modelParallelism: false,
      gradientCheckpointing: true,
      mixedPrecision: false,
      optimizer: 'adamw',
      learningRateScheduler: 'linear',
      warmupSteps: 0,
      weightDecay: 0.01,
      dropoutRate: 0.1,
      attentionProbsDropout: 0.1,
      hiddenDropout: 0.1
    },
    
    // Data Settings
    data: {
      dataStoragePath: './data',
      maxFileSizeMB: 1024,
      supportedFormats: ['csv', 'json', 'parquet', 'txt'],
      autoCleanup: true,
      cleanupDays: 30,
      compressionEnabled: true,
      compressionLevel: 6,
      encryptionEnabled: false,
      encryptionKey: '',
      backupEnabled: true,
      backupInterval: 24,
      maxBackups: 10,
      dataValidation: true,
      deduplicationEnabled: true,
      samplingRate: 1.0,
      shuffleData: true,
      seed: 42
    },
    
    // Deployment Settings
    deployment: {
      defaultPort: 8080,
      workers: 4,
      maxBatchSize: 32,
      enableMetrics: true,
      enableTracing: false,
      metricsPort: 9090,
      healthCheckEnabled: true,
      healthCheckInterval: 30,
      rateLimitEnabled: true,
      rateLimitPerMinute: 60,
      corsEnabled: true,
      allowedOrigins: ['http://localhost:3000'],
      sslEnabled: false,
      sslCertPath: '',
      sslKeyPath: '',
      loadBalancing: 'round_robin',
      autoScaling: false,
      minReplicas: 1,
      maxReplicas: 10,
      targetCPUUtilization: 70
    },
    
    // Security Settings
    security: {
      enableAuth: false,
      authProvider: 'jwt',
      jwtSecret: '',
      jwtExpiration: 3600,
      apiKeyRequired: false,
      apiKeyHeader: 'X-API-Key',
      rateLimitEnabled: true,
      rateLimitPerMinute: 60,
      allowedOrigins: ['http://localhost:3000'],
      sessionTimeout: 3600,
      passwordPolicy: 'strong',
      twoFactorEnabled: false,
      ipWhitelist: [],
      blacklistEnabled: false,
      blacklistedIPs: [],
      auditLogging: true,
      auditLogRetention: 90,
      dataRetentionDays: 365,
      encryptionAlgorithm: 'AES-256-GCM'
    },
    
    // Integration Settings
    integrations: {
      slackWebhook: '',
      discordWebhook: '',
      teamsWebhook: '',
      emailSmtp: '',
      emailPort: 587,
      emailUser: '',
      emailPassword: '',
      emailFrom: '',
      webhookEnabled: false,
      webhookUrl: '',
      webhookEvents: ['start', 'complete', 'failed'],
      prometheusEnabled: true,
      prometheusUrl: 'http://localhost:9090',
      grafanaEnabled: false,
      grafanaUrl: '',
      sentryEnabled: false,
      sentryDsn: ''
    },
    
    // Advanced Settings
    advanced: {
      experimentalFeatures: false,
      telemetryEnabled: true,
      crashReporting: true,
      debugTools: false,
      customPlugins: [],
      customScripts: [],
      environmentVariables: {},
      customHeaders: {},
      proxyEnabled: false,
      proxyUrl: '',
      proxyUsername: '',
      proxyPassword: '',
      customCA: '',
      verboseLogging: false,
      traceLogging: false,
      performanceMode: false
    }
  });

  useEffect(() => {
    loadSettings();
    loadBackups();
  }, []);

  const loadSettings = async () => {
    setLoading(true);
    try {
      const response = await settingsAPI.getSettings();
      if (response.data) {
        setSettings(prev => ({ ...prev, ...response.data }));
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
      // Use default settings if API fails
    } finally {
      setLoading(false);
    }
  };

  const loadBackups = async () => {
    try {
      const response = await settingsAPI.getBackups();
      setBackupList(response.data || []);
    } catch (error) {
      console.error('Failed to load backups:', error);
    }
  };

  const saveSettings = async () => {
    setLoading(true);
    setSaveError(null);
    try {
      await settingsAPI.saveSettings(settings);
      setSaveSuccess(true);
      
      // Apply theme change immediately
      if (settings.general.theme === 'dark') {
        document.body.classList.add('dark-mode');
      } else {
        document.body.classList.remove('dark-mode');
      }
      
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (error) {
      console.error('Failed to save settings:', error);
      setSaveError(error.message || 'Failed to save settings');
    } finally {
      setLoading(false);
    }
  };

  const resetSettings = async () => {
    setLoading(true);
    try {
      await settingsAPI.resetSettings();
      await loadSettings();
      setResetDialogOpen(false);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (error) {
      console.error('Failed to reset settings:', error);
      setSaveError('Failed to reset settings');
    } finally {
      setLoading(false);
    }
  };

  const exportSettings = async () => {
    try {
      const data = await settingsAPI.exportSettings();
      const dataStr = JSON.stringify(data, null, 2);
      const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);
      const exportFileDefaultName = `settings_backup_${new Date().toISOString()}.json`;
      
      const linkElement = document.createElement('a');
      linkElement.setAttribute('href', dataUri);
      linkElement.setAttribute('download', exportFileDefaultName);
      linkElement.click();
      
      setExportDialogOpen(false);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (error) {
      console.error('Failed to export settings:', error);
      setSaveError('Failed to export settings');
    }
  };

  const importSettings = async () => {
    if (!importData) return;
    
    setLoading(true);
    try {
      await settingsAPI.importSettings(importData);
      await loadSettings();
      setImportDialogOpen(false);
      setImportData(null);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (error) {
      console.error('Failed to import settings:', error);
      setSaveError('Failed to import settings');
    } finally {
      setLoading(false);
    }
  };

  const handleFileImport = (event) => {
    const file = event.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const data = JSON.parse(e.target.result);
        setImportData(data);
        setImportDialogOpen(true);
      } catch (error) {
        setSaveError('Invalid JSON file');
      }
    };
    reader.readAsText(file);
  };

  const createBackup = async () => {
    try {
      await settingsAPI.createBackup();
      loadBackups();
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (error) {
      console.error('Failed to create backup:', error);
      setSaveError('Failed to create backup');
    }
  };

  const restoreBackup = async (backupId) => {
    if (window.confirm('Restoring a backup will overwrite current settings. Continue?')) {
      setLoading(true);
      try {
        await settingsAPI.restoreBackup(backupId);
        await loadSettings();
        setSaveSuccess(true);
        setTimeout(() => setSaveSuccess(false), 3000);
      } catch (error) {
        console.error('Failed to restore backup:', error);
        setSaveError('Failed to restore backup');
      } finally {
        setLoading(false);
      }
    }
  };

  const deleteBackup = async (backupId) => {
    try {
      await settingsAPI.deleteBackup(backupId);
      loadBackups();
    } catch (error) {
      console.error('Failed to delete backup:', error);
      setSaveError('Failed to delete backup');
    }
  };

  // Handle change functions
  const handleGeneralChange = (field, value) => {
    setSettings(prev => ({
      ...prev,
      general: { ...prev.general, [field]: value }
    }));
  };

  const handleUIChange = (field, value) => {
    setSettings(prev => ({
      ...prev,
      ui: { ...prev.ui, [field]: value }
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

  const handleIntegrationsChange = (field, value) => {
    setSettings(prev => ({
      ...prev,
      integrations: { ...prev.integrations, [field]: value }
    }));
  };

  const handleAdvancedChange = (field, value) => {
    setSettings(prev => ({
      ...prev,
      advanced: { ...prev.advanced, [field]: value }
    }));
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Paper sx={{ p: 3 }}>
        {/* Header */}
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3, flexWrap: 'wrap', gap: 2 }}>
          <SettingsIcon sx={{ fontSize: 32, mr: 2, color: 'primary.main' }} />
          <Typography variant="h4" component="h1">
            System Settings
          </Typography>
          <Box sx={{ flex: 1 }} />
          
          {onClose && (
            <IconButton onClick={onClose} sx={{ mr: 1 }}>
              <CloseIcon />
            </IconButton>
          )}
          
          <Button
            variant="outlined"
            onClick={() => setResetDialogOpen(true)}
            startIcon={<RestartAlt />}
            disabled={loading}
            sx={{ mr: 1 }}
          >
            Reset
          </Button>
          
          <Button
            variant="outlined"
            onClick={exportSettings}
            startIcon={<Download />}
            disabled={loading}
            sx={{ mr: 1 }}
          >
            Export
          </Button>
          
          <Button
            variant="outlined"
            component="label"
            startIcon={<Upload />}
            disabled={loading}
            sx={{ mr: 1 }}
          >
            Import
            <input
              type="file"
              hidden
              accept=".json"
              onChange={handleFileImport}
            />
          </Button>
          
          <Button
            variant="outlined"
            onClick={loadSettings}
            startIcon={<Refresh />}
            disabled={loading}
            sx={{ mr: 1 }}
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

        {saveError && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setSaveError(null)}>
            {saveError}
          </Alert>
        )}

        {loading && <LinearProgress sx={{ mb: 2 }} />}

        <Divider sx={{ mb: 3 }} />

        {/* Tabs */}
        <Tabs 
          value={activeTab} 
          onChange={(e, v) => setActiveTab(v)} 
          sx={{ mb: 2 }}
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab icon={<SettingsIcon />} label="General" />
          <Tab icon={<Palette />} label="UI" />
          <Tab icon={<Speed />} label="Processing" />
          <Tab icon={<Memory />} label="Models" />
          <Tab icon={<Storage />} label="Data" />
          <Tab icon={<Cloud />} label="Deployment" />
          <Tab icon={<Security />} label="Security" />
          <Tab icon={<Api />} label="Integrations" />
          <Tab icon={<DataObject />} label="Advanced" />
        </Tabs>

        {/* General Settings Tab */}
        <TabPanel value={activeTab} index={0}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <SettingCard title="Application" icon={<SettingsIcon />}>
                <TextField
                  fullWidth
                  label="Application Name"
                  value={settings.general.appName}
                  onChange={(e) => handleGeneralChange('appName', e.target.value)}
                  sx={{ mb: 2 }}
                />
                
                <FormControl fullWidth sx={{ mb: 2 }}>
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
                
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.general.debugMode}
                      onChange={(e) => handleGeneralChange('debugMode', e.target.checked)}
                    />
                  }
                  label="Debug Mode"
                  sx={{ mb: 2, display: 'block' }}
                />
              </SettingCard>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <SettingCard title="Preferences" icon={<Language />}>
                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel>Theme</InputLabel>
                  <Select
                    value={settings.general.theme}
                    onChange={(e) => handleGeneralChange('theme', e.target.value)}
                    label="Theme"
                  >
                    <MenuItem value="light"><LightMode /> Light</MenuItem>
                    <MenuItem value="dark"><DarkMode /> Dark</MenuItem>
                    <MenuItem value="auto"><AutoMode /> Auto</MenuItem>
                  </Select>
                </FormControl>
                
                <FormControl fullWidth sx={{ mb: 2 }}>
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
                    <MenuItem value="de">German</MenuItem>
                    <MenuItem value="ja">Japanese</MenuItem>
                  </Select>
                </FormControl>
                
                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel>Timezone</InputLabel>
                  <Select
                    value={settings.general.timezone}
                    onChange={(e) => handleGeneralChange('timezone', e.target.value)}
                    label="Timezone"
                  >
                    <MenuItem value="UTC">UTC</MenuItem>
                    <MenuItem value="America/New_York">America/New_York</MenuItem>
                    <MenuItem value="Europe/London">Europe/London</MenuItem>
                    <MenuItem value="Asia/Tokyo">Asia/Tokyo</MenuItem>
                  </Select>
                </FormControl>
              </SettingCard>
            </Grid>
            
            <Grid item xs={12}>
              <SettingCard title="Notifications" icon={<Notifications />}>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={4}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.general.notificationsEnabled}
                          onChange={(e) => handleGeneralChange('notificationsEnabled', e.target.checked)}
                        />
                      }
                      label="Enable Notifications"
                    />
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.general.emailNotifications}
                          onChange={(e) => handleGeneralChange('emailNotifications', e.target.checked)}
                          disabled={!settings.general.notificationsEnabled}
                        />
                      }
                      label="Email Notifications"
                    />
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.general.desktopNotifications}
                          onChange={(e) => handleGeneralChange('desktopNotifications', e.target.checked)}
                          disabled={!settings.general.notificationsEnabled}
                        />
                      }
                      label="Desktop Notifications"
                    />
                  </Grid>
                </Grid>
              </SettingCard>
            </Grid>
          </Grid>
        </TabPanel>

        {/* UI Settings Tab */}
        <TabPanel value={activeTab} index={1}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <SettingCard title="Colors" icon={<Palette />}>
                <ColorPicker
                  value={settings.ui.primaryColor}
                  onChange={(color) => handleUIChange('primaryColor', color)}
                  label="Primary Color"
                />
                
                <ColorPicker
                  value={settings.ui.secondaryColor}
                  onChange={(color) => handleUIChange('secondaryColor', color)}
                  label="Secondary Color"
                  sx={{ mt: 2 }}
                />
                
                <ColorPicker
                  value={settings.ui.backgroundColor}
                  onChange={(color) => handleUIChange('backgroundColor', color)}
                  label="Background Color"
                  sx={{ mt: 2 }}
                />
              </SettingCard>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <SettingCard title="Layout" icon={<Tablet />}>
                <Typography gutterBottom>Border Radius</Typography>
                <Slider
                  value={settings.ui.borderRadius}
                  onChange={(e, val) => handleUIChange('borderRadius', val)}
                  min={0}
                  max={24}
                  step={1}
                  marks={[
                    { value: 0, label: '0' },
                    { value: 8, label: '8' },
                    { value: 16, label: '16' },
                    { value: 24, label: '24' }
                  ]}
                  sx={{ mb: 2 }}
                />
                
                <Typography gutterBottom>Font Size (px)</Typography>
                <Slider
                  value={settings.ui.fontSize}
                  onChange={(e, val) => handleUIChange('fontSize', val)}
                  min={12}
                  max={18}
                  step={1}
                  marks={[
                    { value: 12, label: '12' },
                    { value: 14, label: '14' },
                    { value: 16, label: '16' },
                    { value: 18, label: '18' }
                  ]}
                  sx={{ mb: 2 }}
                />
                
                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel>Density</InputLabel>
                  <Select
                    value={settings.ui.density}
                    onChange={(e) => handleUIChange('density', e.target.value)}
                    label="Density"
                  >
                    <MenuItem value="compact">Compact</MenuItem>
                    <MenuItem value="comfortable">Comfortable</MenuItem>
                    <MenuItem value="spacious">Spacious</MenuItem>
                  </Select>
                </FormControl>
              </SettingCard>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Processing Settings Tab */}
        <TabPanel value={activeTab} index={2}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <SettingCard title="Performance" icon={<Speed />}>
                <TextField
                  fullWidth
                  type="number"
                  label="Default Batch Size"
                  value={settings.processing.defaultBatchSize}
                  onChange={(e) => handleProcessingChange('defaultBatchSize', parseInt(e.target.value))}
                  sx={{ mb: 2 }}
                />
                
                <TextField
                  fullWidth
                  type="number"
                  label="Maximum Workers"
                  value={settings.processing.maxWorkers}
                  onChange={(e) => handleProcessingChange('maxWorkers', parseInt(e.target.value))}
                  sx={{ mb: 2 }}
                />
                
                <TextField
                  fullWidth
                  type="number"
                  label="Memory Limit (MB)"
                  value={settings.processing.memoryLimit}
                  onChange={(e) => handleProcessingChange('memoryLimit', parseInt(e.target.value))}
                  sx={{ mb: 2 }}
                />
                
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.processing.cacheEnabled}
                      onChange={(e) => handleProcessingChange('cacheEnabled', e.target.checked)}
                    />
                  }
                  label="Enable Cache"
                  sx={{ mb: 2, display: 'block' }}
                />
                
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.processing.parallelProcessing}
                      onChange={(e) => handleProcessingChange('parallelProcessing', e.target.checked)}
                    />
                  }
                  label="Parallel Processing"
                  sx={{ display: 'block' }}
                />
              </SettingCard>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <SettingCard title="Retry & Queue" icon={<Timeline />}>
                <TextField
                  fullWidth
                  type="number"
                  label="Retry Attempts"
                  value={settings.processing.retryAttempts}
                  onChange={(e) => handleProcessingChange('retryAttempts', parseInt(e.target.value))}
                  sx={{ mb: 2 }}
                />
                
                <TextField
                  fullWidth
                  type="number"
                  label="Retry Delay (ms)"
                  value={settings.processing.retryDelay}
                  onChange={(e) => handleProcessingChange('retryDelay', parseInt(e.target.value))}
                  sx={{ mb: 2 }}
                />
                
                <TextField
                  fullWidth
                  type="number"
                  label="Max Queue Size"
                  value={settings.processing.maxQueueSize}
                  onChange={(e) => handleProcessingChange('maxQueueSize', parseInt(e.target.value))}
                  sx={{ mb: 2 }}
                />
                
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.processing.priorityQueue}
                      onChange={(e) => handleProcessingChange('priorityQueue', e.target.checked)}
                    />
                  }
                  label="Priority Queue"
                />
              </SettingCard>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Model Settings Tab */}
        <TabPanel value={activeTab} index={3}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <SettingCard title="Model Configuration" icon={<Memory />}>
                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel>Default Model</InputLabel>
                  <Select
                    value={settings.models.defaultModel}
                    onChange={(e) => handleModelsChange('defaultModel', e.target.value)}
                    label="Default Model"
                  >
                    <MenuItem value="bert-base-uncased">BERT Base Uncased</MenuItem>
                    <MenuItem value="bert-large-uncased">BERT Large Uncased</MenuItem>
                    <MenuItem value="gpt2">GPT-2</MenuItem>
                    <MenuItem value="gpt2-medium">GPT-2 Medium</MenuItem>
                    <MenuItem value="facebook/bart-base">BART Base</MenuItem>
                    <MenuItem value="t5-small">T5 Small</MenuItem>
                    <MenuItem value="roberta-base">RoBERTa Base</MenuItem>
                    <MenuItem value="distilbert-base-uncased">DistilBERT Base</MenuItem>
                  </Select>
                </FormControl>
                
                <TextField
                  fullWidth
                  label="Model Cache Path"
                  value={settings.models.modelCachePath}
                  onChange={(e) => handleModelsChange('modelCachePath', e.target.value)}
                  sx={{ mb: 2 }}
                />
                
                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel>Precision</InputLabel>
                  <Select
                    value={settings.models.precision}
                    onChange={(e) => handleModelsChange('precision', e.target.value)}
                    label="Precision"
                  >
                    <MenuItem value="fp32">FP32 (Full Precision)</MenuItem>
                    <MenuItem value="fp16">FP16 (Half Precision)</MenuItem>
                    <MenuItem value="int8">INT8 (Quantized)</MenuItem>
                    <MenuItem value="bf16">BF16 (Brain Float)</MenuItem>
                  </Select>
                </FormControl>
                
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.models.useGPU}
                      onChange={(e) => handleModelsChange('useGPU', e.target.checked)}
                    />
                  }
                  label="Use GPU"
                  sx={{ mb: 2, display: 'block' }}
                />
                
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.models.gradientCheckpointing}
                      onChange={(e) => handleModelsChange('gradientCheckpointing', e.target.checked)}
                    />
                  }
                  label="Gradient Checkpointing"
                />
              </SettingCard>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <SettingCard title="Training Parameters" icon={<MonitorHeart />}>
                <TextField
                  fullWidth
                  type="number"
                  label="Max Sequence Length"
                  value={settings.models.maxSequenceLength}
                  onChange={(e) => handleModelsChange('maxSequenceLength', parseInt(e.target.value))}
                  sx={{ mb: 2 }}
                />
                
                <TextField
                  fullWidth
                  type="number"
                  label="Dropout Rate"
                  value={settings.models.dropoutRate}
                  onChange={(e) => handleModelsChange('dropoutRate', parseFloat(e.target.value))}
                  inputProps={{ step: 0.01 }}
                  sx={{ mb: 2 }}
                />
                
                <TextField
                  fullWidth
                  type="number"
                  label="Weight Decay"
                  value={settings.models.weightDecay}
                  onChange={(e) => handleModelsChange('weightDecay', parseFloat(e.target.value))}
                  inputProps={{ step: 0.001 }}
                  sx={{ mb: 2 }}
                />
                
                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel>Optimizer</InputLabel>
                  <Select
                    value={settings.models.optimizer}
                    onChange={(e) => handleModelsChange('optimizer', e.target.value)}
                    label="Optimizer"
                  >
                    <MenuItem value="adamw">AdamW</MenuItem>
                    <MenuItem value="adam">Adam</MenuItem>
                    <MenuItem value="sgd">SGD</MenuItem>
                    <MenuItem value="adafactor">Adafactor</MenuItem>
                  </Select>
                </FormControl>
                
                <FormControl fullWidth>
                  <InputLabel>Learning Rate Scheduler</InputLabel>
                  <Select
                    value={settings.models.learningRateScheduler}
                    onChange={(e) => handleModelsChange('learningRateScheduler', e.target.value)}
                    label="Learning Rate Scheduler"
                  >
                    <MenuItem value="linear">Linear</MenuItem>
                    <MenuItem value="cosine">Cosine</MenuItem>
                    <MenuItem value="constant">Constant</MenuItem>
                    <MenuItem value="exponential">Exponential</MenuItem>
                  </Select>
                </FormControl>
              </SettingCard>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Data Settings Tab */}
        <TabPanel value={activeTab} index={4}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <SettingCard title="Storage" icon={<Storage />}>
                <TextField
                  fullWidth
                  label="Data Storage Path"
                  value={settings.data.dataStoragePath}
                  onChange={(e) => handleDataChange('dataStoragePath', e.target.value)}
                  sx={{ mb: 2 }}
                />
                
                <TextField
                  fullWidth
                  type="number"
                  label="Max File Size (MB)"
                  value={settings.data.maxFileSizeMB}
                  onChange={(e) => handleDataChange('maxFileSizeMB', parseInt(e.target.value))}
                  sx={{ mb: 2 }}
                />
                
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.data.compressionEnabled}
                      onChange={(e) => handleDataChange('compressionEnabled', e.target.checked)}
                    />
                  }
                  label="Enable Compression"
                  sx={{ mb: 2, display: 'block' }}
                />
                
                {settings.data.compressionEnabled && (
                  <TextField
                    fullWidth
                    type="number"
                    label="Compression Level"
                    value={settings.data.compressionLevel}
                    onChange={(e) => handleDataChange('compressionLevel', parseInt(e.target.value))}
                    inputProps={{ min: 1, max: 9 }}
                    sx={{ mb: 2 }}
                  />
                )}
              </SettingCard>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <SettingCard title="Backup & Cleanup" icon={<Save />}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.data.autoCleanup}
                      onChange={(e) => handleDataChange('autoCleanup', e.target.checked)}
                    />
                  }
                  label="Auto Cleanup"
                  sx={{ mb: 2, display: 'block' }}
                />
                
                {settings.data.autoCleanup && (
                  <TextField
                    fullWidth
                    type="number"
                    label="Cleanup After (days)"
                    value={settings.data.cleanupDays}
                    onChange={(e) => handleDataChange('cleanupDays', parseInt(e.target.value))}
                    sx={{ mb: 2 }}
                  />
                )}
                
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.data.backupEnabled}
                      onChange={(e) => handleDataChange('backupEnabled', e.target.checked)}
                    />
                  }
                  label="Enable Automatic Backups"
                  sx={{ mb: 2, display: 'block' }}
                />
                
                {settings.data.backupEnabled && (
                  <>
                    <TextField
                      fullWidth
                      type="number"
                      label="Backup Interval (hours)"
                      value={settings.data.backupInterval}
                      onChange={(e) => handleDataChange('backupInterval', parseInt(e.target.value))}
                      sx={{ mb: 2 }}
                    />
                    
                    <TextField
                      fullWidth
                      type="number"
                      label="Max Backups"
                      value={settings.data.maxBackups}
                      onChange={(e) => handleDataChange('maxBackups', parseInt(e.target.value))}
                      sx={{ mb: 2 }}
                    />
                  </>
                )}
                
                <Button
                  variant="outlined"
                  onClick={createBackup}
                  startIcon={<Save />}
                  fullWidth
                >
                  Create Backup Now
                </Button>
              </SettingCard>
            </Grid>
          </Grid>
          
          {/* Backup List */}
          {backupList.length > 0 && (
            <SettingCard title="Backup History" icon={<HistoryIcon />}>
              <List>
                {backupList.map((backup) => (
                  <ListItem key={backup.id}>
                    <ListItemIcon>
                      <Save />
                    </ListItemIcon>
                    <ListItemText
                      primary={backup.name}
                      secondary={`Created: ${new Date(backup.createdAt).toLocaleString()} • Size: ${(backup.size / 1024).toFixed(2)} KB`}
                    />
                    <ListItemSecondaryAction>
                      <Tooltip title="Restore">
                        <IconButton onClick={() => restoreBackup(backup.id)}>
                          <RestartAlt />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Delete">
                        <IconButton onClick={() => deleteBackup(backup.id)}>
                          <Delete />
                        </IconButton>
                      </Tooltip>
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>
            </SettingCard>
          )}
        </TabPanel>

        {/* Deployment Settings Tab */}
        <TabPanel value={activeTab} index={5}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <SettingCard title="Server Configuration" icon={<Cloud />}>
                <TextField
                  fullWidth
                  type="number"
                  label="Default Port"
                  value={settings.deployment.defaultPort}
                  onChange={(e) => handleDeploymentChange('defaultPort', parseInt(e.target.value))}
                  sx={{ mb: 2 }}
                />
                
                <TextField
                  fullWidth
                  type="number"
                  label="Number of Workers"
                  value={settings.deployment.workers}
                  onChange={(e) => handleDeploymentChange('workers', parseInt(e.target.value))}
                  sx={{ mb: 2 }}
                />
                
                <TextField
                  fullWidth
                  type="number"
                  label="Max Batch Size"
                  value={settings.deployment.maxBatchSize}
                  onChange={(e) => handleDeploymentChange('maxBatchSize', parseInt(e.target.value))}
                  sx={{ mb: 2 }}
                />
                
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.deployment.enableMetrics}
                      onChange={(e) => handleDeploymentChange('enableMetrics', e.target.checked)}
                    />
                  }
                  label="Enable Metrics"
                  sx={{ mb: 2, display: 'block' }}
                />
                
                {settings.deployment.enableMetrics && (
                  <TextField
                    fullWidth
                    type="number"
                    label="Metrics Port"
                    value={settings.deployment.metricsPort}
                    onChange={(e) => handleDeploymentChange('metricsPort', parseInt(e.target.value))}
                    sx={{ mb: 2 }}
                  />
                )}
              </SettingCard>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <SettingCard title="Auto-scaling" icon={<BarChart />}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.deployment.autoScaling}
                      onChange={(e) => handleDeploymentChange('autoScaling', e.target.checked)}
                    />
                  }
                  label="Enable Auto-scaling"
                  sx={{ mb: 2, display: 'block' }}
                />
                
                {settings.deployment.autoScaling && (
                  <>
                    <TextField
                      fullWidth
                      type="number"
                      label="Min Replicas"
                      value={settings.deployment.minReplicas}
                      onChange={(e) => handleDeploymentChange('minReplicas', parseInt(e.target.value))}
                      sx={{ mb: 2 }}
                    />
                    
                    <TextField
                      fullWidth
                      type="number"
                      label="Max Replicas"
                      value={settings.deployment.maxReplicas}
                      onChange={(e) => handleDeploymentChange('maxReplicas', parseInt(e.target.value))}
                      sx={{ mb: 2 }}
                    />
                    
                    <TextField
                      fullWidth
                      type="number"
                      label="Target CPU Utilization (%)"
                      value={settings.deployment.targetCPUUtilization}
                      onChange={(e) => handleDeploymentChange('targetCPUUtilization', parseInt(e.target.value))}
                      sx={{ mb: 2 }}
                    />
                  </>
                )}
                
                <FormControl fullWidth>
                  <InputLabel>Load Balancing Strategy</InputLabel>
                  <Select
                    value={settings.deployment.loadBalancing}
                    onChange={(e) => handleDeploymentChange('loadBalancing', e.target.value)}
                    label="Load Balancing Strategy"
                  >
                    <MenuItem value="round_robin">Round Robin</MenuItem>
                    <MenuItem value="least_connections">Least Connections</MenuItem>
                    <MenuItem value="ip_hash">IP Hash</MenuItem>
                    <MenuItem value="random">Random</MenuItem>
                  </Select>
                </FormControl>
              </SettingCard>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Security Settings Tab */}
        <TabPanel value={activeTab} index={6}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <SettingCard title="Authentication" icon={<Lock />}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.security.enableAuth}
                      onChange={(e) => handleSecurityChange('enableAuth', e.target.checked)}
                    />
                  }
                  label="Enable Authentication"
                  sx={{ mb: 2, display: 'block' }}
                />
                
                {settings.security.enableAuth && (
                  <>
                    <FormControl fullWidth sx={{ mb: 2 }}>
                      <InputLabel>Auth Provider</InputLabel>
                      <Select
                        value={settings.security.authProvider}
                        onChange={(e) => handleSecurityChange('authProvider', e.target.value)}
                        label="Auth Provider"
                      >
                        <MenuItem value="jwt">JWT</MenuItem>
                        <MenuItem value="oauth2">OAuth2</MenuItem>
                        <MenuItem value="ldap">LDAP</MenuItem>
                        <MenuItem value="saml">SAML</MenuItem>
                      </Select>
                    </FormControl>
                    
                    <TextField
                      fullWidth
                      label="JWT Secret"
                      value={settings.security.jwtSecret}
                      onChange={(e) => handleSecurityChange('jwtSecret', e.target.value)}
                      type={showPassword ? 'text' : 'password'}
                      InputProps={{
                        endAdornment: (
                          <InputAdornment position="end">
                            <IconButton onClick={() => setShowPassword(!showPassword)}>
                              {showPassword ? <VisibilityOff /> : <Visibility />}
                            </IconButton>
                          </InputAdornment>
                        )
                      }}
                      sx={{ mb: 2 }}
                    />
                    
                    <TextField
                      fullWidth
                      type="number"
                      label="Session Timeout (seconds)"
                      value={settings.security.sessionTimeout}
                      onChange={(e) => handleSecurityChange('sessionTimeout', parseInt(e.target.value))}
                      sx={{ mb: 2 }}
                    />
                  </>
                )}
                
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.security.twoFactorEnabled}
                      onChange={(e) => handleSecurityChange('twoFactorEnabled', e.target.checked)}
                    />
                  }
                  label="Enable Two-Factor Authentication"
                />
              </SettingCard>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <SettingCard title="API Security" icon={<VpnKey />}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.security.apiKeyRequired}
                      onChange={(e) => handleSecurityChange('apiKeyRequired', e.target.checked)}
                    />
                  }
                  label="Require API Key"
                  sx={{ mb: 2, display: 'block' }}
                />
                
                {settings.security.apiKeyRequired && (
                  <TextField
                    fullWidth
                    label="API Key Header"
                    value={settings.security.apiKeyHeader}
                    onChange={(e) => handleSecurityChange('apiKeyHeader', e.target.value)}
                    sx={{ mb: 2 }}
                  />
                )}
                
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.security.rateLimitEnabled}
                      onChange={(e) => handleSecurityChange('rateLimitEnabled', e.target.checked)}
                    />
                  }
                  label="Enable Rate Limiting"
                  sx={{ mb: 2, display: 'block' }}
                />
                
                {settings.security.rateLimitEnabled && (
                  <TextField
                    fullWidth
                    type="number"
                    label="Rate Limit (requests per minute)"
                    value={settings.security.rateLimitPerMinute}
                    onChange={(e) => handleSecurityChange('rateLimitPerMinute', parseInt(e.target.value))}
                    sx={{ mb: 2 }}
                  />
                )}
                
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.security.auditLogging}
                      onChange={(e) => handleSecurityChange('auditLogging', e.target.checked)}
                    />
                  }
                  label="Enable Audit Logging"
                  sx={{ mb: 2, display: 'block' }}
                />
                
                {settings.security.auditLogging && (
                  <TextField
                    fullWidth
                    type="number"
                    label="Audit Log Retention (days)"
                    value={settings.security.auditLogRetention}
                    onChange={(e) => handleSecurityChange('auditLogRetention', parseInt(e.target.value))}
                  />
                )}
              </SettingCard>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Integrations Tab */}
        <TabPanel value={activeTab} index={7}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <SettingCard title="Webhooks" icon={<Webhook />}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.integrations.webhookEnabled}
                      onChange={(e) => handleIntegrationsChange('webhookEnabled', e.target.checked)}
                    />
                  }
                  label="Enable Webhooks"
                  sx={{ mb: 2, display: 'block' }}
                />
                
                {settings.integrations.webhookEnabled && (
                  <>
                    <TextField
                      fullWidth
                      label="Webhook URL"
                      value={settings.integrations.webhookUrl}
                      onChange={(e) => handleIntegrationsChange('webhookUrl', e.target.value)}
                      sx={{ mb: 2 }}
                    />
                    
                    <FormControl fullWidth>
                      <InputLabel>Webhook Events</InputLabel>
                      <Select
                        multiple
                        value={settings.integrations.webhookEvents}
                        onChange={(e) => handleIntegrationsChange('webhookEvents', e.target.value)}
                        label="Webhook Events"
                        renderValue={(selected) => (
                          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                            {selected.map((value) => (
                              <Chip key={value} label={value} size="small" />
                            ))}
                          </Box>
                        )}
                      >
                        <MenuItem value="start">Pipeline Start</MenuItem>
                        <MenuItem value="complete">Pipeline Complete</MenuItem>
                        <MenuItem value="failed">Pipeline Failed</MenuItem>
                        <MenuItem value="stage_complete">Stage Complete</MenuItem>
                      </Select>
                    </FormControl>
                  </>
                )}
              </SettingCard>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <SettingCard title="Monitoring" icon={<BarChart />}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.integrations.prometheusEnabled}
                      onChange={(e) => handleIntegrationsChange('prometheusEnabled', e.target.checked)}
                    />
                  }
                  label="Enable Prometheus"
                  sx={{ mb: 2, display: 'block' }}
                />
                
                {settings.integrations.prometheusEnabled && (
                  <TextField
                    fullWidth
                    label="Prometheus URL"
                    value={settings.integrations.prometheusUrl}
                    onChange={(e) => handleIntegrationsChange('prometheusUrl', e.target.value)}
                    sx={{ mb: 2 }}
                  />
                )}
                
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.integrations.grafanaEnabled}
                      onChange={(e) => handleIntegrationsChange('grafanaEnabled', e.target.checked)}
                    />
                  }
                  label="Enable Grafana"
                  sx={{ mb: 2, display: 'block' }}
                />
                
                {settings.integrations.grafanaEnabled && (
                  <TextField
                    fullWidth
                    label="Grafana URL"
                    value={settings.integrations.grafanaUrl}
                    onChange={(e) => handleIntegrationsChange('grafanaUrl', e.target.value)}
                  />
                )}
              </SettingCard>
            </Grid>
            
            <Grid item xs={12}>
              <SettingCard title="Messaging" icon={<Notifications />}>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={4}>
                    <TextField
                      fullWidth
                      label="Slack Webhook"
                      value={settings.integrations.slackWebhook}
                      onChange={(e) => handleIntegrationsChange('slackWebhook', e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <TextField
                      fullWidth
                      label="Discord Webhook"
                      value={settings.integrations.discordWebhook}
                      onChange={(e) => handleIntegrationsChange('discordWebhook', e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <TextField
                      fullWidth
                      label="Teams Webhook"
                      value={settings.integrations.teamsWebhook}
                      onChange={(e) => handleIntegrationsChange('teamsWebhook', e.target.value)}
                    />
                  </Grid>
                </Grid>
              </SettingCard>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Advanced Settings Tab */}
        <TabPanel value={activeTab} index={8}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <SettingCard title="Experimental" icon={<Science />}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.advanced.experimentalFeatures}
                      onChange={(e) => handleAdvancedChange('experimentalFeatures', e.target.checked)}
                    />
                  }
                  label="Enable Experimental Features"
                  sx={{ mb: 2, display: 'block' }}
                />
                
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.advanced.telemetryEnabled}
                      onChange={(e) => handleAdvancedChange('telemetryEnabled', e.target.checked)}
                    />
                  }
                  label="Enable Telemetry"
                  sx={{ mb: 2, display: 'block' }}
                />
                
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.advanced.crashReporting}
                      onChange={(e) => handleAdvancedChange('crashReporting', e.target.checked)}
                    />
                  }
                  label="Enable Crash Reporting"
                  sx={{ mb: 2, display: 'block' }}
                />
                
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.advanced.performanceMode}
                      onChange={(e) => handleAdvancedChange('performanceMode', e.target.checked)}
                    />
                  }
                  label="Performance Mode"
                />
              </SettingCard>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <SettingCard title="Debugging" icon={<BugReport />}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.advanced.debugTools}
                      onChange={(e) => handleAdvancedChange('debugTools', e.target.checked)}
                    />
                  }
                  label="Show Debug Tools"
                  sx={{ mb: 2, display: 'block' }}
                />
                
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.advanced.verboseLogging}
                      onChange={(e) => handleAdvancedChange('verboseLogging', e.target.checked)}
                    />
                  }
                  label="Verbose Logging"
                  sx={{ mb: 2, display: 'block' }}
                />
                
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.advanced.traceLogging}
                      onChange={(e) => handleAdvancedChange('traceLogging', e.target.checked)}
                    />
                  }
                  label="Trace Logging"
                />
              </SettingCard>
            </Grid>
            
            <Grid item xs={12}>
              <SettingCard title="Proxy Configuration" icon={<Public />}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.advanced.proxyEnabled}
                      onChange={(e) => handleAdvancedChange('proxyEnabled', e.target.checked)}
                    />
                  }
                  label="Enable Proxy"
                  sx={{ mb: 2, display: 'block' }}
                />
                
                {settings.advanced.proxyEnabled && (
                  <Grid container spacing={2}>
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        label="Proxy URL"
                        value={settings.advanced.proxyUrl}
                        onChange={(e) => handleAdvancedChange('proxyUrl', e.target.value)}
                      />
                    </Grid>
                    <Grid item xs={6}>
                      <TextField
                        fullWidth
                        label="Username"
                        value={settings.advanced.proxyUsername}
                        onChange={(e) => handleAdvancedChange('proxyUsername', e.target.value)}
                      />
                    </Grid>
                    <Grid item xs={6}>
                      <TextField
                        fullWidth
                        label="Password"
                        type="password"
                        value={settings.advanced.proxyPassword}
                        onChange={(e) => handleAdvancedChange('proxyPassword', e.target.value)}
                      />
                    </Grid>
                  </Grid>
                )}
              </SettingCard>
            </Grid>
          </Grid>
        </TabPanel>
      </Paper>

      {/* Reset Confirmation Dialog */}
      <Dialog open={resetDialogOpen} onClose={() => setResetDialogOpen(false)}>
        <DialogTitle>Reset Settings</DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            This will reset all settings to their default values. This action cannot be undone.
          </Alert>
          <Typography>Are you sure you want to reset all settings?</Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setResetDialogOpen(false)}>Cancel</Button>
          <Button onClick={resetSettings} variant="contained" color="error">
            Reset
          </Button>
        </DialogActions>
      </Dialog>

      {/* Import Confirmation Dialog */}
      <Dialog open={importDialogOpen} onClose={() => setImportDialogOpen(false)}>
        <DialogTitle>Import Settings</DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 2 }}>
            Importing settings will overwrite your current configuration.
          </Alert>
          <Typography>Do you want to proceed with the import?</Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setImportDialogOpen(false)}>Cancel</Button>
          <Button onClick={importSettings} variant="contained">
            Import
          </Button>
        </DialogActions>
      </Dialog>

      {/* Success Snackbar */}
      <Snackbar
        open={saveSuccess}
        autoHideDuration={3000}
        onClose={() => setSaveSuccess(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert severity="success" onClose={() => setSaveSuccess(false)}>
          Settings saved successfully!
        </Alert>
      </Snackbar>

      {/* Error Snackbar */}
      <Snackbar
        open={!!saveError}
        autoHideDuration={6000}
        onClose={() => setSaveError(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert severity="error" onClose={() => setSaveError(null)}>
          {saveError}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default Settings;