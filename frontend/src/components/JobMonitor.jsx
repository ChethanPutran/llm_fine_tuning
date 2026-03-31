// src/components/JobMonitor.jsx
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
  Paper,
  Divider
} from '@mui/material';
import {
  PlayArrow,
  Stop,
  CheckCircle,
  Error as ErrorIcon,
  Pending,
  ExpandMore,
  ExpandLess,
  GetApp
} from '@mui/icons-material';
import { useJobWebSocket } from '../hooks/useWebSocket';

export const JobMonitor = ({ jobId }) => {
  const [expanded, setExpanded] = useState(false);
  const {
    jobData,
    status,
    progress,
    result,
    error,
    cancelJob,
    getStatus
  } = useJobWebSocket(jobId);

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

  if (!jobId) {
    return (
      <Card>
        <CardContent>
          <Alert severity="info">No job ID provided</Alert>
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
              Job: {jobId.substring(0, 8)}...
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
              <IconButton size="small" onClick={cancelJob} color="error" title="Cancel job">
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

        {result && (
          <Alert severity="success" sx={{ mb: 2 }}>
            Job completed successfully!
          </Alert>
        )}

        <Collapse in={expanded}>
          <Paper variant="outlined" sx={{ p: 2, mt: 2, bgcolor: 'grey.50' }}>
            <Typography variant="subtitle2" gutterBottom>
              Job Details
            </Typography>
            {jobData && (
              <Box component="pre" sx={{ m: 0, fontSize: '12px', overflow: 'auto' }}>
                {JSON.stringify(jobData, null, 2)}
              </Box>
            )}
            {result && (
              <>
                <Divider sx={{ my: 1 }} />
                <Typography variant="subtitle2" gutterBottom>
                  Result
                </Typography>
                <Box component="pre" sx={{ m: 0, fontSize: '12px', overflow: 'auto' }}>
                  {JSON.stringify(result, null, 2)}
                </Box>
              </>
            )}
          </Paper>
        </Collapse>
      </CardContent>
    </Card>
  );
};