// src/context/WebSocketContext.jsx
import React, { createContext, useContext, useEffect, useState } from 'react';
import { wsService } from '../services/websocket';

const WebSocketContext = createContext(null);

export const useWebSocketContext = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocketContext must be used within WebSocketProvider');
  }
  return context;
};

export const WebSocketProvider = ({ children }) => {
  const [isConnected, setIsConnected] = useState(false);
  const [clientId, setClientId] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const handleConnected = (data) => {
      setIsConnected(true);
      setClientId(data.clientId);
      setError(null);
    };

    const handleDisconnected = () => {
      setIsConnected(false);
    };

    const handleError = (errorData) => {
      setError(errorData);
    };

    const unsubscribeConnected = wsService.on('connected', handleConnected);
    const unsubscribeDisconnected = wsService.on('disconnected', handleDisconnected);
    const unsubscribeError = wsService.on('error', handleError);

    // Connect to client endpoint
    wsService.connect().catch(console.error);

    return () => {
      unsubscribeConnected();
      unsubscribeDisconnected();
      unsubscribeError();
      wsService.disconnect();
    };
  }, []);

  const value = {
    isConnected,
    clientId,
    error,
    wsService,
    sendMessage: wsService.send.bind(wsService),
    subscribeToExecution: wsService.subscribeToExecution.bind(wsService),
    subscribeToJob: wsService.subscribeToJob.bind(wsService),
    cancelExecution: wsService.cancelExecution.bind(wsService),
    cancelJob: wsService.cancelJob.bind(wsService),
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
};