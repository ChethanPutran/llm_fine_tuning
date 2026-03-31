// src/main.jsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import ErrorBoundary from './Error.jsx';
import { StyledEngineProvider } from '@mui/material/styles';
import App from './App.jsx';
import './index.css';

const rootElement = document.getElementById('root');

if (rootElement) {
  ReactDOM.createRoot(rootElement).render(
    <React.StrictMode>
      <StyledEngineProvider injectFirst>
        <ErrorBoundary>
          <App />
        </ErrorBoundary>
      </StyledEngineProvider>
    </React.StrictMode>
  );
}