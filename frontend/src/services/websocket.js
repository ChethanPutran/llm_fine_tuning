// src/services/websocket.js
class WebSocketService {
  constructor() {
    this.socket = null;
    this.listeners = new Map();
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000;
    this.isConnecting = false;
    this.clientId = this.generateClientId();
    this.pingInterval = null;
  }

  generateClientId() {
    return `client_${Math.random().toString(36).substr(2, 9)}_${Date.now()}`;
  }

  connect(executionId = null, jobId = null) {
    if (this.socket?.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected');
      return Promise.resolve();
    }

    if (this.isConnecting) {
      console.log('WebSocket connection already in progress');
      return new Promise((resolve) => {
        const checkConnection = setInterval(() => {
          if (this.socket?.readyState === WebSocket.OPEN) {
            clearInterval(checkConnection);
            resolve();
          }
        }, 100);
      });
    }

    return new Promise((resolve, reject) => {
      this.isConnecting = true;
      const wsUrl = this.buildWebSocketUrl(executionId, jobId);
      
      try {
        this.socket = new WebSocket(wsUrl);
        
        this.socket.onopen = () => {
          console.log('WebSocket connected');
          this.reconnectAttempts = 0;
          this.isConnecting = false;
          this.startPingInterval();
          this.dispatchEvent('connected', { clientId: this.clientId });
          resolve();
        };
        
        this.socket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };
        
        this.socket.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.dispatchEvent('error', error);
          reject(error);
        };
        
        this.socket.onclose = (event) => {
          console.log('WebSocket disconnected:', event.code, event.reason);
          this.stopPingInterval();
          this.dispatchEvent('disconnected', { code: event.code, reason: event.reason });
          
          if (event.code !== 1000) { // Normal closure
            this.attemptReconnect(executionId, jobId);
          }
        };
      } catch (error) {
        this.isConnecting = false;
        reject(error);
      }
    });
  }

  buildWebSocketUrl(executionId, jobId) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.hostname;
    const port = window.location.port ? `:${window.location.port}` : '';
    
    let endpoint;
    if (executionId) {
      endpoint = `/ws/executions/${executionId}`;
    } else if (jobId) {
      endpoint = `/ws/jobs/${jobId}`;
    } else {
      endpoint = `/ws/client/${this.clientId}`;
    }
    
    return `${protocol}//${host}${port}${endpoint}`;
  }

  attemptReconnect(executionId, jobId) {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      this.dispatchEvent('reconnect_failed', { attempts: this.reconnectAttempts });
      return;
    }
    
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
    
    setTimeout(() => {
      this.connect(executionId, jobId).catch((error) => {
        console.error('Reconnection failed:', error);
      });
    }, delay);
  }

  startPingInterval() {
    this.pingInterval = setInterval(() => {
      if (this.isConnected()) {
        this.send({ type: 'ping' });
      }
    }, 30000); // Send ping every 30 seconds
  }

  stopPingInterval() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  handleMessage(data) {
    console.log('WebSocket message received:', data);
    
    switch (data.type) {
      case 'connected':
        this.dispatchEvent('connected', data);
        break;
      case 'execution_update':
        this.dispatchEvent('execution_update', data.data);
        this.dispatchEvent(`execution_${data.execution_id}_update`, data.data);
        break;
      case 'job_update':
        this.dispatchEvent('job_update', data.data);
        this.dispatchEvent(`job_${data.job_id}_update`, data.data);
        break;
      case 'pong':
        this.dispatchEvent('pong', data);
        break;
      case 'error':
        console.error('Server error:', data.message);
        this.dispatchEvent('error', data);
        break;
      case 'status':
        this.dispatchEvent('status', data.data);
        break;
      case 'cancelled':
        this.dispatchEvent('cancelled', data);
        break;
      case 'subscribed':
        this.dispatchEvent('subscribed', data);
        break;
      default:
        this.dispatchEvent('message', data);
    }
  }

  send(data) {
    if (this.isConnected()) {
      const message = typeof data === 'string' ? data : JSON.stringify(data);
      this.socket.send(message);
    } else {
      console.warn('WebSocket is not connected');
      this.dispatchEvent('send_failed', { data, reason: 'not_connected' });
    }
  }

  isConnected() {
    return this.socket && this.socket.readyState === WebSocket.OPEN;
  }

  disconnect() {
    this.stopPingInterval();
    if (this.socket) {
      this.socket.close(1000, 'Client disconnecting');
      this.socket = null;
    }
    this.listeners.clear();
  }

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event).add(callback);
    
    // Return unsubscribe function
    return () => this.off(event, callback);
  }

  off(event, callback) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).delete(callback);
    }
  }

  dispatchEvent(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in event handler for ${event}:`, error);
        }
      });
    }
  }

  // Convenience methods
  subscribeToExecution(executionId) {
    return this.send({
      type: 'subscribe',
      target_type: 'execution',
      target_id: executionId
    });
  }

  subscribeToJob(jobId) {
    return this.send({
      type: 'subscribe',
      target_type: 'job',
      target_id: jobId
    });
  }

  cancelExecution(executionId) {
    return this.send({
      type: 'cancel',
      execution_id: executionId
    });
  }

  cancelJob(jobId) {
    return this.send({
      type: 'cancel',
      job_id: jobId
    });
  }

  getExecutionStatus(executionId) {
    return this.send({
      type: 'status',
      execution_id: executionId
    });
  }

  getJobStatus(jobId) {
    return this.send({
      type: 'status',
      job_id: jobId
    });
  }
}

// Singleton instance
export const wsService = new WebSocketService();