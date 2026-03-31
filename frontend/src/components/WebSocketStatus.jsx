// src/components/WebSocketStatus.jsx
import React from 'react';
import { Chip, Tooltip, Box } from '@mui/material';
import { Wifi, WifiOff, Refresh } from '@mui/icons-material';
import { useWebSocketContext } from '../context/WebSocketContext';

export const WebSocketStatus = () => {
  const { isConnected, error } = useWebSocketContext();

  const getStatusColor = () => {
    if (error) return 'error';
    if (isConnected) return 'success';
    return 'warning';
  };

  const getStatusText = () => {
    if (error) return 'Connection Error';
    if (isConnected) return 'Connected';
    return 'Connecting...';
  };

  const getStatusIcon = () => {
    if (error) return <Refresh fontSize="small" />;
    if (isConnected) return <Wifi fontSize="small" />;
    return <WifiOff fontSize="small" />;
  };

  return (
    <Tooltip title={error ? error.message : 'Real-time connection status'}>
      <Chip
        icon={getStatusIcon()}
        label={getStatusText()}
        color={getStatusColor()}
        size="small"
        variant="outlined"
        sx={{ ml: 2 }}
      />
    </Tooltip>
  );
};