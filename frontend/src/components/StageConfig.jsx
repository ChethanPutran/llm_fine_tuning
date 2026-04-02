import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Card,
  CardContent,
  Typography,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  FormControlLabel,
  Switch,
  Slider,
  Box,
  IconButton,
  Tooltip,
  Alert,
  Chip,
  Divider
} from '@mui/material';
import { Settings, Info, HelpOutline } from '@mui/icons-material';

const StageConfig = ({ stage, onConfigChange, config = {} }) => {
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [errors, setErrors] = useState({});
  const [initialized, setInitialized] = useState(false);

  // Add a state for fetched options
  const [asyncOptions, setAsyncOptions] = useState({});

  // Memoize all fields to prevent recalculation
  const allFields = useMemo(() => {
    return [...(stage.fields || []), ...(stage.advancedFields || [])];
  }, [stage.fields, stage.advancedFields]);

  // Initialize defaults ONLY once when stage changes
  useEffect(() => {
    const missingDefaults = {};
    
    allFields.forEach(field => {
      if (field.default !== undefined && config[field.key] === undefined) {
        missingDefaults[field.key] = field.default;
      }
    });

    if (Object.keys(missingDefaults).length > 0 && !initialized) {
      onConfigChange({ ...config, ...missingDefaults });
      setInitialized(true);
    }
  }, [stage.id, allFields]); // Only when stage changes

    const validateField = useCallback((field, value) => {
    if (field.required && (value === undefined || value === null || value === '')) {
      return `${field.label} is required`;
    }
    if (field.type === 'number' && value !== undefined && value !== null) {
      const numValue = parseFloat(value);
      if (field.min !== undefined && numValue < field.min) {
        return `${field.label} must be at least ${field.min}`;
      }
      if (field.max !== undefined && numValue > field.max) {
        return `${field.label} must be at most ${field.max}`;
      }
    }
    if (field.type === 'select' && field.options && value) {
      if (!field.options.includes(value)) {
        return `${field.label} must be one of: ${field.options.join(', ')}`;
      }
    }
    return null;
  }, []);


  useEffect(() => {
  let isMounted = true;

  const updateDependentOptions = async () => {
    // 1. Identify fields that have a fetch_endpoint
    const dynamicFields = allFields.filter(f => f.fetch_endpoint);

    for (const field of dynamicFields) {
      // 2. Identify what this field depends on (e.g., field.dependsOn = 'previous_field_key')
      // If your schema doesn't have 'dependsOn', you might be using the whole config
      const dependencyValue = field.dependsOn ? config[field.dependsOn] : null;

      // 3. Only fetch if the dependency actually has a value (if required)
      if (field.dependsOn && !dependencyValue) {
        continue; 
      }

      try {
        console.log(`Fetching options for ${field.key} with dependency value:`, dependencyValue);
        console.log(`Current config passed to fetcher:`, config);
        // Pass the current config (or specific dependency) to the fetcher
        const data = await field.fetch_endpoint(config); 
        console.log(`Fetched options for ${field.key}:`, data);
        if (isMounted) {
          setAsyncOptions(prev => ({
            ...prev,
            [field.key]: data
          }));
        }
      } catch (err) {
        console.error(`Error fetching for ${field.key}:`, err);
      }
    }
  };

  updateDependentOptions();

  return () => { isMounted = false; };
  
  // CRITICAL: We only re-run this when the values in 'config' change
  // We use JSON.stringify(config) or specific keys to avoid reference-check loops
}, [JSON.stringify(config), allFields]);
  
  // Validate all fields when config changes
  useEffect(() => {
    const newErrors = {};
    allFields.forEach(field => {
      const value = config[field.key];
      const error = validateField(field, value);
      if (error) newErrors[field.key] = error;
    });
    setErrors(newErrors);
  }, [config, allFields]);


  const handleChange = useCallback((key, value, field) => {
    // Validate
    const error = validateField(field, value);
    setErrors(prev => ({ ...prev, [key]: error }));
    
    // Notify parent
    onConfigChange({ ...config, [key]: value });
  }, [config, onConfigChange, validateField]);

  const renderField = useCallback((field) => {
    const value = config[field.key];
    const error = errors[field.key];
    
    switch (field.type) {
      
      case 'select':
          const options = asyncOptions[field.key] || [];
          const isDisabled = field.dependsOn && !config[field.dependsOn];

          return (
            <FormControl fullWidth key={field.key} disabled={isDisabled}>
              <InputLabel>{field.label}</InputLabel>
              <Select
                value={config[field.key] || ''}
                onChange={(e) => handleChange(field.key, e.target.value, field)}
                label={field.label}
              >
                {options.length > 0 ? (
                  options.map(option => (
                    <MenuItem key={option} value={option}>{option}</MenuItem>
                  ))
                ) : (
                  <MenuItem disabled>
                    {isDisabled ? `Select ${field.dependsOn} first` : "Loading..."}
                  </MenuItem>
                )}
              </Select>
            </FormControl>
          );
        
      case 'text':
        return (
          <TextField
            key={field.key}
            fullWidth
            label={field.label}
            value={value !== undefined ? value : (field.default || '')}
            onChange={(e) => handleChange(field.key, e.target.value, field)}
            error={!!error}
            helperText={error || field.placeholder || field.helper}
            required={field.required}
            sx={{ mb: 2 }}
          />
        );
        
      case 'number':
        return (
          <TextField
            key={field.key}
            fullWidth
            type="number"
            label={field.label}
            value={value !== undefined ? value : (field.default || 0)}
            onChange={(e) => handleChange(field.key, parseFloat(e.target.value) || 0, field)}
            error={!!error}
            helperText={error || field.helper}
            inputProps={{ step: field.step || 1, min: field.min, max: field.max }}
            sx={{ mb: 2 }}
          />
        );
        
      case 'boolean':
        return (
          <FormControlLabel
            key={field.key}
            control={
              <Switch
                checked={value !== undefined ? value : (field.default || false)}
                onChange={(e) => handleChange(field.key, e.target.checked, field)}
              />
            }
            label={field.label}
            sx={{ mb: 2, display: 'block' }}
          />
        );
        
      case 'slider':
        return (
          <Box key={field.key} sx={{ mb: 2 }}>
            <Typography gutterBottom>{field.label}</Typography>
            <Slider
              value={value !== undefined ? value : (field.default || 0)}
              onChange={(_, newValue) => handleChange(field.key, newValue, field)}
              min={field.min || 0}
              max={field.max || 100}
              step={field.step || 1}
              valueLabelDisplay="auto"
            />
            {error && <Typography variant="caption" color="error">{error}</Typography>}
          </Box>
        );
        
      default:
        return null;
    }
  }, [config, errors, handleChange]);

  const hasRequiredFields = useCallback(() => {
    const requiredFields = allFields.filter(f => f.required);
    return requiredFields.every(field => {
      const value = config[field.key];
      return value !== undefined && value !== null && value !== '';
    });
  }, [allFields, config]);

  return (
    <Card variant="outlined">
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="h6">{stage.name} Configuration</Typography>
            {stage.description && (
              <Tooltip title={stage.description}>
                <HelpOutline fontSize="small" color="action" />
              </Tooltip>
            )}
          </Box>
          {stage.advancedFields?.length > 0 && (
            <Tooltip title={advancedOpen ? "Hide Advanced Settings" : "Show Advanced Settings"}>
              <IconButton size="small" onClick={() => setAdvancedOpen(prev => !prev)}>
                <Settings color={advancedOpen ? "primary" : "action"} />
              </IconButton>
            </Tooltip>
          )}
        </Box>
        
        {stage.fields?.map(field => renderField(field))}
        
        {advancedOpen && stage.advancedFields?.length > 0 && (
          <>
            <Divider sx={{ my: 2 }}>
              <Chip label="Advanced Settings" size="small" />
            </Divider>
            {stage.advancedFields.map(field => renderField(field))}
          </>
        )}
        
        {!hasRequiredFields() && (
          <Alert severity="info" sx={{ mt: 2 }}>
            Please fill in all required fields before proceeding.
          </Alert>
        )}
      </CardContent>
    </Card>
  );
};

export default StageConfig;