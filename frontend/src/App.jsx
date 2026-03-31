// src/App.jsx
import React, { useState } from 'react';
import { ThemeProvider } from '@mui/material/styles';
import { IconButton, Box } from '@mui/material';
import { Brightness4, Brightness7 } from '@mui/icons-material';
import CssBaseline from '@mui/material/CssBaseline';
import Dashboard from './pages/Dashboard.jsx';
import { lightTheme, darkTheme, globalStyles } from './components/Theme.jsx';
import { WebSocketProvider } from './context/WebSocketContext.jsx';
import { SettingsProvider } from './context/SettingsContext.jsx';
import { WebSocketStatus } from './components/WebSocketStatus.jsx';
import './App.css';

function App() {
  const [isDarkMode, setIsDarkMode] = useState(false);

  const toggleTheme = () => {
    setIsDarkMode(!isDarkMode);
  };

  // Inject global styles
  const styleSheet = document.createElement("style");
  styleSheet.textContent = `
    ${Object.entries(globalStyles).map(([key, value]) => `${key} ${value}`).join('\n')}
  `;
  document.head.appendChild(styleSheet);

  return (
    <ThemeProvider theme={isDarkMode ? darkTheme : lightTheme}>
      <CssBaseline />
      <SettingsProvider>
        <WebSocketProvider>
            <Box sx={{ position: 'fixed', bottom: 16, left: 16, zIndex: 2000, display: 'flex', gap: 1 }} title="Toggle Theme">
              {/* <WebSocketStatus /> */}
              <IconButton 
                onClick={toggleTheme} 
                sx={{
                  background: isDarkMode ? 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)' : 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
                  color: '#ffffff',
                  '&:hover': {
                    transform: 'scale(1.05)',
                  },
                }}
                
        
              >
                {isDarkMode ? <Brightness7 /> : <Brightness4 />}
              </IconButton>
            </Box>
              <Dashboard />
              {/* <Settings /> */}
        </WebSocketProvider>
      </SettingsProvider>
    </ThemeProvider>
  );
}

export default App;