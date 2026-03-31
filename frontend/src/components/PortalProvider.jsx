import React from 'react';
import ReactDOM from 'react-dom/client';
import ErrorBoundary from './Error.jsx';
import { StyledEngineProvider } from '@mui/material/styles';
import App from './App.jsx';
import './index.css';

// Create portal root for modals
const rootElement = document.getElementById('root');
const modalRoot = document.createElement('div');
modalRoot.id = 'modal-root';
document.body.appendChild(modalRoot);

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