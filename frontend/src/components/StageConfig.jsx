import React, { useState, useEffect } from 'react';
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
  Box,
  IconButton,
  Tooltip
} from '@mui/material';
import { Add, Delete, Settings } from '@mui/icons-material';

const StageConfig = ({ stage, onConfigChange }) => {
  const [config, setConfig] = useState(stage.config || {});
  const [advancedOpen, setAdvancedOpen] = useState(false);
  
  useEffect(() => {
    onConfigChange(config);
  }, [config]);
  
  const handleChange = (key, value) => {
    setConfig(prev => ({ ...prev, [key]: value }));
  };
  
  const handleNestedChange = (parent, key, value) => {
    setConfig(prev => ({
      ...prev,
      [parent]: {
        ...prev[parent],
        [key]: value
      }
    }));
  };
  
  const renderField = (field) => {
    switch (field.type) {
      case 'select':
        return (
          <FormControl fullWidth key={field.key}>
            <InputLabel>{field.label}</InputLabel>
            <Select
              value={config[field.key] || field.default || ''}
              onChange={(e) => handleChange(field.key, e.target.value)}
              label={field.label}
            >
              {field.options.map(option => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        );
        
      case 'text':
        return (
          <TextField
            key={field.key}
            fullWidth
            label={field.label}
            value={config[field.key] || field.default || ''}
            onChange={(e) => handleChange(field.key, e.target.value)}
            helperText={field.helper}
          />
        );
        
      case 'number':
        return (
          <TextField
            key={field.key}
            fullWidth
            type="number"
            label={field.label}
            value={config[field.key] || field.default || 0}
            onChange={(e) => handleChange(field.key, parseFloat(e.target.value))}
            helperText={field.helper}
          />
        );
        
      case 'boolean':
        return (
          <FormControlLabel
            key={field.key}
            control={
              <Switch
                checked={config[field.key] || field.default || false}
                onChange={(e) => handleChange(field.key, e.target.checked)}
              />
            }
            label={field.label}
          />
        );
        
      default:
        return null;
    }
  };
  
  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">{stage.name} Configuration</Typography>
          <Tooltip title="Advanced Settings">
            <IconButton onClick={() => setAdvancedOpen(!advancedOpen)}>
              <Settings />
            </IconButton>
          </Tooltip>
        </Box>
        
        {stage.fields && stage.fields.map(field => renderField(field))}
        
        {advancedOpen && stage.advancedFields && (
          <Box sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: 'grey.200' }}>
            <Typography variant="subtitle1" gutterBottom>
              Advanced Settings
            </Typography>
            {stage.advancedFields.map(field => renderField(field))}
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default StageConfig;