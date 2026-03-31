// src/context/SettingsContext.jsx
import React, { createContext, useContext, useState, useEffect } from 'react';
import { settingsAPI } from '../services/settingsAPI';

const SettingsContext = createContext(null);

export const useSettings = () => {
  const context = useContext(SettingsContext);
  if (!context) {
    throw new Error('useSettings must be used within SettingsProvider');
  }
  return context;
};

export const SettingsProvider = ({ children }) => {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    setLoading(true);
    try {
      const response = await settingsAPI.getSettings();
      setSettings(response.data);
      setError(null);
    } catch (error) {
      console.error('Failed to load settings:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const updateSettings = async (newSettings) => {
    try {
      const response = await settingsAPI.saveSettings(newSettings);
      setSettings(response.data);
      return response.data;
    } catch (error) {
      console.error('Failed to update settings:', error);
      throw error;
    }
  };

  const resetSettings = async () => {
    try {
      const response = await settingsAPI.resetSettings();
      setSettings(response.data);
      return response.data;
    } catch (error) {
      console.error('Failed to reset settings:', error);
      throw error;
    }
  };

  const value = {
    settings,
    loading,
    error,
    updateSettings,
    resetSettings,
    reloadSettings: loadSettings,
  };

  return (
    <SettingsContext.Provider value={value}>
      {children}
    </SettingsContext.Provider>
  );
};