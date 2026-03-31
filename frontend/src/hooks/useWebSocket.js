// src/hooks/useWebSocket.js
import { useState, useEffect, useCallback, useRef } from 'react';
import { wsService } from '../services/websocket';

export const useWebSocket = (executionId = null, jobId = null) => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const [error, setError] = useState(null);
  const reconnectAttempts = useRef(0);

  useEffect(() => {
    let mounted = true;

    const handleConnected = (data) => {
      if (mounted) {
        setIsConnected(true);
        setError(null);
        reconnectAttempts.current = 0;
        console.log('WebSocket connected:', data);
      }
    };

    const handleDisconnected = (data) => {
      if (mounted) {
        setIsConnected(false);
        console.log('WebSocket disconnected:', data);
      }
    };

    const handleError = (errorData) => {
      if (mounted) {
        setError(errorData);
        console.error('WebSocket error:', errorData);
      }
    };

    const handleMessage = (message) => {
      if (mounted) {
        setLastMessage(message);
      }
    };

    // Subscribe to events
    const unsubscribeConnected = wsService.on('connected', handleConnected);
    const unsubscribeDisconnected = wsService.on('disconnected', handleDisconnected);
    const unsubscribeError = wsService.on('error', handleError);
    const unsubscribeMessage = wsService.on('message', handleMessage);

    // Connect
    wsService.connect(executionId, jobId).catch((err) => {
      console.error('Failed to connect WebSocket:', err);
      if (mounted) setError(err);
    });

    return () => {
      mounted = false;
      unsubscribeConnected();
      unsubscribeDisconnected();
      unsubscribeError();
      unsubscribeMessage();
      // Don't disconnect globally, as other components might use the connection
    };
  }, [executionId, jobId]);

  const sendMessage = useCallback((data) => {
    wsService.send(data);
  }, []);

  const disconnect = useCallback(() => {
    wsService.disconnect();
  }, []);

  return {
    isConnected,
    lastMessage,
    error,
    sendMessage,
    disconnect
  };
};

// Hook for execution-specific updates
export const useExecutionWebSocket = (executionId) => {
  const [executionData, setExecutionData] = useState(null);
  const [status, setStatus] = useState(null);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!executionId) return;

    const handleUpdate = (data) => {
      setExecutionData(data);
      if (data.status) setStatus(data.status);
      if (data.progress !== undefined) setProgress(data.progress);
      if (data.error) setError(data.error);
    };

    const handleError = (errorData) => {
      setError(errorData.message || 'Unknown error');
    };

    // Subscribe to execution-specific updates
    const unsubscribeUpdate = wsService.on(`execution_${executionId}_update`, handleUpdate);
    const unsubscribeError = wsService.on('error', handleError);

    // Connect and subscribe
    wsService.connect(executionId).then(() => {
      wsService.subscribeToExecution(executionId);
    });

    return () => {
      unsubscribeUpdate();
      unsubscribeError();
    };
  }, [executionId]);

  const cancelExecution = useCallback(() => {
    wsService.cancelExecution(executionId);
  }, [executionId]);

  const getStatus = useCallback(() => {
    wsService.getExecutionStatus(executionId);
  }, [executionId]);

  return {
    executionData,
    status,
    progress,
    error,
    cancelExecution,
    getStatus
  };
};

// Hook for job-specific updates
export const useJobWebSocket = (jobId) => {
  const [jobData, setJobData] = useState(null);
  const [status, setStatus] = useState(null);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!jobId) return;

    const handleUpdate = (data) => {
      setJobData(data);
      if (data.status) setStatus(data.status);
      if (data.progress !== undefined) setProgress(data.progress);
      if (data.result) setResult(data.result);
      if (data.error) setError(data.error);
    };

    const handleError = (errorData) => {
      setError(errorData.message || 'Unknown error');
    };

    const unsubscribeUpdate = wsService.on(`job_${jobId}_update`, handleUpdate);
    const unsubscribeError = wsService.on('error', handleError);

    wsService.connect(null, jobId).then(() => {
      wsService.subscribeToJob(jobId);
    });

    return () => {
      unsubscribeUpdate();
      unsubscribeError();
    };
  }, [jobId]);

  const cancelJob = useCallback(() => {
    wsService.cancelJob(jobId);
  }, [jobId]);

  const getStatus = useCallback(() => {
    wsService.getJobStatus(jobId);
  }, [jobId]);

  return {
    jobData,
    status,
    progress,
    result,
    error,
    cancelJob,
    getStatus
  };
};