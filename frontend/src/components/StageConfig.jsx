import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import {
  Card, CardContent, Typography, TextField, Select, MenuItem,
  FormControl, InputLabel, FormControlLabel, Switch,
  Box, IconButton, Chip, Divider, CircularProgress
} from '@mui/material';
import { Settings } from '@mui/icons-material';

const StageConfig = ({ stage, onConfigChange, config = {} }) => {
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [errors, setErrors] = useState({});
  const [asyncOptions, setAsyncOptions] = useState({});
  const [loadingFields, setLoadingFields] = useState({});
  
  const prevDepsRef = useRef({});

  const allFields = useMemo(() => [
    ...(stage.fields || []),
    ...(stage.advancedFields || [])
  ], [stage]);

  // 1. Fetch Dynamic Options
  useEffect(() => {
    let isMounted = true;

    const fetchNeededOptions = async () => {
      const dynamicFields = allFields.filter(f => f.fetch_endpoint);
      
      for (const field of dynamicFields) {
        const depKey = field.dependsOn;
        const depValue = depKey ? config[depKey] : 'root'; 

        // Fetch if the dependency value has changed
        if (prevDepsRef.current[field.key] !== depValue) {
          prevDepsRef.current[field.key] = depValue;

          // If a dependency is required but missing, clear options
          if (depKey && !depValue) {
            setAsyncOptions(prev => ({ ...prev, [field.key]: [] }));
            continue;
          }

          setLoadingFields(prev => ({ ...prev, [field.key]: true }));
          
          try {
            const data = await field.fetch_endpoint(config);
            if (isMounted) {
              setAsyncOptions(prev => ({ ...prev, [field.key]: data }));
            }
          } catch (err) {
            console.error(`Fetch error for ${field.key}:`, err);
          } finally {
            if (isMounted) setLoadingFields(prev => ({ ...prev, [field.key]: false }));
          }
        }
      }
    };

    fetchNeededOptions();
    return () => { isMounted = false; };
  }, [config, allFields]);

  // 2. Enhanced Change Handler (Handles Cascading Resets)
  const handleChange = useCallback((key, value, field) => {
    // Clear local errors
    setErrors(prev => ({ ...prev, [key]: null }));

    let newConfig = { ...config, [key]: value };

    // CASCADING RESET: Find all fields that depend on the field we just changed
    // and wipe their current values in the config.
    allFields.forEach(f => {
      if (f.dependsOn === key) {
        newConfig[f.key] = ""; // Clear the child
        
        // Recursively clear deeper children (e.g., if we changed Category, clear Task AND Model)
        allFields.forEach(subF => {
          if (subF.dependsOn === f.key) newConfig[subF.key] = "";
        });
      }
    });

    onConfigChange(newConfig);
  }, [config, onConfigChange, allFields]);

  const renderField = (field) => {
    const value = config[field.key] ?? '';
    const options = asyncOptions[field.key] || [];
    const isLoading = loadingFields[field.key];
    const isDisabled = field.dependsOn && !config[field.dependsOn];

    return (
      <Box key={field.key} sx={{ mb: 2 }}>
        {field.type === 'select' ? (
          <FormControl fullWidth disabled={isDisabled || isLoading}>
            <InputLabel>{field.label}</InputLabel>
            <Select
              value={value}
              label={field.label}
              onChange={(e) => handleChange(field.key, e.target.value, field)}
              endAdornment={isLoading ? <CircularProgress size={20} sx={{ mr: 4 }} /> : null}
            >
              {options.length > 0 ? (
                options.map(opt => (
                  <MenuItem key={opt} value={opt}>{opt}</MenuItem>
                ))
              ) : (
                <MenuItem disabled>
                  {isLoading ? "Loading..." : isDisabled ? `Select ${field.dependsOn} first` : "No options available"}
                </MenuItem>
              )}
            </Select>
          </FormControl>
        ) : (
          <TextField
            fullWidth
            type={field.type === 'number' ? 'number' : 'text'}
            label={field.label}
            value={value}
            onChange={(e) => handleChange(field.key, e.target.value, field)}
          />
        )}
      </Box>
    );
  };

  return (
    <Card variant="outlined" sx={{ borderRadius: 2, boxShadow: 'none', border: '1px solid #e0e0e0' }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2, alignItems: 'center' }}>
          <Typography variant="subtitle1" fontWeight="bold" color="text.secondary">
            {stage.name.toUpperCase()} CONFIGURATION
          </Typography>
          {stage.advancedFields?.length > 0 && (
            <IconButton onClick={() => setAdvancedOpen(!advancedOpen)} size="small">
              <Settings color={advancedOpen ? "primary" : "inherit"} />
            </IconButton>
          )}
        </Box>

        {stage.fields?.map(renderField)}

        {advancedOpen && (
          <>
            <Divider sx={{ my: 2 }}><Chip label="Advanced" size="small" /></Divider>
            {stage.advancedFields?.map(renderField)}
          </>
        )}
      </CardContent>
    </Card>
  );
};

export default StageConfig;