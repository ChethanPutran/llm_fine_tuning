// src/services/settingsAPI.js
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';

class SettingsAPI {
  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  // Get all settings
  async getSettings() {
    try {
      const response = await this.client.get('/settings');
      return response.data;
    } catch (error) {
      console.error('Failed to get settings:', error);
      throw error;
    }
  }

  // Save settings
  async saveSettings(settings) {
    try {
      const response = await this.client.post('/settings', settings);
      return response.data;
    } catch (error) {
      console.error('Failed to save settings:', error);
      throw error;
    }
  }

  // Reset settings to defaults
  async resetSettings() {
    try {
      const response = await this.client.post('/settings/reset');
      return response.data;
    } catch (error) {
      console.error('Failed to reset settings:', error);
      throw error;
    }
  }

  // Export settings
  async exportSettings() {
    try {
      const response = await this.client.get('/settings/export');
      return response.data;
    } catch (error) {
      console.error('Failed to export settings:', error);
      throw error;
    }
  }

  // Import settings
  async importSettings(settings) {
    try {
      const response = await this.client.post('/settings/import', settings);
      return response.data;
    } catch (error) {
      console.error('Failed to import settings:', error);
      throw error;
    }
  }

  // Get backup list
  async getBackups() {
    try {
      const response = await this.client.get('/settings/backups');
      return response.data;
    } catch (error) {
      console.error('Failed to get backups:', error);
      throw error;
    }
  }

  // Create backup
  async createBackup() {
    try {
      const response = await this.client.post('/settings/backups');
      return response.data;
    } catch (error) {
      console.error('Failed to create backup:', error);
      throw error;
    }
  }

  // Restore backup
  async restoreBackup(backupId) {
    try {
      const response = await this.client.post(`/settings/backups/${backupId}/restore`);
      return response.data;
    } catch (error) {
      console.error('Failed to restore backup:', error);
      throw error;
    }
  }

  // Delete backup
  async deleteBackup(backupId) {
    try {
      const response = await this.client.delete(`/settings/backups/${backupId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to delete backup:', error);
      throw error;
    }
  }

  // Get environment variables
  async getEnvironmentVariables() {
    try {
      const response = await this.client.get('/settings/env');
      return response.data;
    } catch (error) {
      console.error('Failed to get environment variables:', error);
      throw error;
    }
  }

  // Update environment variable
  async updateEnvironmentVariable(key, value) {
    try {
      const response = await this.client.post('/settings/env', { key, value });
      return response.data;
    } catch (error) {
      console.error('Failed to update environment variable:', error);
      throw error;
    }
  }
}

export const settingsAPI = new SettingsAPI();