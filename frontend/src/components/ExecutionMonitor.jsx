// src/components/ExecutionMonitor.jsx
import React, { useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Box,
  Chip,
  IconButton,
  Button,
  Alert,
  Collapse,
  Paper
} from '@mui/material';
import {
  PlayArrow,
  Stop,
  CheckCircle,
  Error as ErrorIcon,
  Pending,
  ExpandMore,
  ExpandLess
} from '@mui/icons-material';
import { useExecutionWebSocket } from '../hooks/useWebSocket';

export const ExecutionMonitor = ({ executionId }) => {
  const [expanded, setExpanded] = useState(false);
  const {
    executionData,
    status,
    progress,
    error,
    cancelExecution,
    getStatus
  } = useExecutionWebSocket(executionId);

  const getStatusIcon = () => {
    switch (status?.toLowerCase()) {
      case 'completed':
        return <CheckCircle sx={{ color: 'success.main' }} />;
      case 'failed':
        return <ErrorIcon sx={{ color: 'error.main' }} />;
      case 'running':
        return <PlayArrow sx={{ color: 'info.main' }} />;
      case 'cancelled':
        return <Stop sx={{ color: 'warning.main' }} />;
      default:
        return <Pending sx={{ color: 'warning.main' }} />;
    }
  };

  const getStatusColor = () => {
    switch (status?.toLowerCase()) {
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      case 'running':
        return 'info';
      case 'cancelled':
        return 'warning';
      default:
        return 'default';
    }
  };

  if (!executionId) {
    return (
      <Card>
        <CardContent>
          <Alert severity="info">No execution ID provided</Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {getStatusIcon()}
            <Typography variant="h6">
              Execution: {executionId.substring(0, 8)}...
            </Typography>
            <Chip
              label={status || 'pending'}
              size="small"
              color={getStatusColor()}
            />
          </Box>
          <Box>
            <IconButton size="small" onClick={getStatus} title="Refresh status">
              <PlayArrow fontSize="small" />
            </IconButton>
            {status === 'running' && (
              <IconButton size="small" onClick={cancelExecution} color="error" title="Cancel execution">
                <Stop fontSize="small" />
              </IconButton>
            )}
            <IconButton size="small" onClick={() => setExpanded(!expanded)}>
              {expanded ? <ExpandLess /> : <ExpandMore />}
            </IconButton>
          </Box>
        </Box>

        {progress > 0 && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Progress: {progress}%
            </Typography>
            <LinearProgress
              variant="determinate"
              value={progress}
              sx={{ height: 8, borderRadius: 4 }}
            />
          </Box>
        )}

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Collapse in={expanded}>
          <Paper variant="outlined" sx={{ p: 2, mt: 2, bgcolor: 'grey.50' }}>
            <Typography variant="subtitle2" gutterBottom>
              Execution Details
            </Typography>
            {executionData && (
              <Box component="pre" sx={{ m: 0, fontSize: '12px', overflow: 'auto' }}>
                {JSON.stringify(executionData, null, 2)}
              </Box>
            )}
          </Paper>
        </Collapse>
      </CardContent>
    </Card>
  );
};