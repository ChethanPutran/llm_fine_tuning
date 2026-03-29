import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Box,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  CheckCircle,
  Error,
  Pending,
  PlayArrow,
  Stop,
  Refresh
} from '@mui/icons-material';

const StatusMonitor = ({ stages, selectedJob, onRefresh }) => {
  const [expanded, setExpanded] = useState(false);
  
  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle sx={{ color: 'success.main' }} />;
      case 'failed':
        return <Error sx={{ color: 'error.main' }} />;
      case 'running':
        return <PlayArrow sx={{ color: 'info.main' }} />;
      default:
        return <Pending sx={{ color: 'warning.main' }} />;
    }
  };
  
  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      case 'running':
        return 'info';
      default:
        return 'default';
    }
  };
  
  const overallProgress = stages.reduce((acc, stage) => {
    if (stage.status === 'completed') return acc + 100;
    if (stage.status === 'running') return acc + stage.progress;
    return acc;
  }, 0) / stages.length;
  
  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">
            Pipeline Status
          </Typography>
          <Tooltip title="Refresh">
            <IconButton size="small" onClick={onRefresh}>
              <Refresh />
            </IconButton>
          </Tooltip>
        </Box>
        
        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" color="textSecondary" gutterBottom>
            Overall Progress
          </Typography>
          <LinearProgress 
            variant="determinate" 
            value={overallProgress} 
            sx={{ height: 8, borderRadius: 4 }}
          />
          <Typography variant="caption" color="textSecondary">
            {Math.round(overallProgress)}% Complete
          </Typography>
        </Box>
        
        <Divider sx={{ my: 2 }} />
        
        <List dense>
          {stages.map((stage, index) => (
            <ListItem key={stage.name} sx={{ px: 0 }}>
              <ListItemIcon>
                {getStatusIcon(stage.status)}
              </ListItemIcon>
              <ListItemText
                primary={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="body2">{stage.name}</Typography>
                    <Chip 
                      label={stage.status} 
                      size="small" 
                      color={getStatusColor(stage.status)}
                      variant="outlined"
                    />
                  </Box>
                }
                secondary={
                  stage.status === 'running' && (
                    <LinearProgress 
                      variant="determinate" 
                      value={stage.progress} 
                      sx={{ mt: 0.5, height: 4 }}
                    />
                  )
                }
              />
              {stage.progress > 0 && stage.status === 'running' && (
                <Typography variant="caption" color="textSecondary">
                  {stage.progress}%
                </Typography>
              )}
            </ListItem>
          ))}
        </List>
        
        {selectedJob && (
          <>
            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle2" gutterBottom>
              Current Job: {selectedJob}
            </Typography>
          </>
        )}
      </CardContent>
    </Card>
  );
};

export default StatusMonitor;