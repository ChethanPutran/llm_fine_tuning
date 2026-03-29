import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'
import Dashboard from './pages/Dashboard.jsx'
import DataCollection from './pages/DataCollection.jsx'
import Preprocessing from './pages/Preprocessing.jsx'
import Training from './pages/Training.jsx'
import Deployment from './pages/Deployment.jsx'
import Navigation from './components/Navigation.jsx'
import './App.css'

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});


function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Navigation>
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/data-collection" element={<DataCollection />} />
            <Route path="/preprocessing" element={<Preprocessing />} />
            <Route path="/training" element={<Training />} />
            <Route path="/deployment" element={<Deployment />} />
          </Routes>
        </Navigation>
      </Router>
    </ThemeProvider>
  )
}

export default App
