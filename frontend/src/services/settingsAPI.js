// src/services/settingsAPI.js
import { apiService } from './api';

class SettingsAPI {
  // Get all settings
  async getSettings() {
    return apiService.getSettings();
  }

  // Save settings
  async saveSettings(settings) {
    return apiService.saveSettings(settings);
  }

  // Reset settings to defaults
  async resetSettings() {
    return apiService.resetSettings();
  }

  // Export settings
  async exportSettings() {
    return apiService.exportSettings();
  }

  // Import settings
  async importSettings(settings) {
    return apiService.importSettings(settings);
  }

  // Get backup list
  async getBackups() {
    return apiService.getBackups();
  }

  // Create backup
  async createBackup() {
    return apiService.createBackup();
  }

  // Restore backup
  async restoreBackup(backupId) {
    return apiService.restoreBackup(backupId);
  }

  // Delete backup
  async deleteBackup(backupId) {
    return apiService.deleteBackup(backupId);
  }

  // Get environment variables
  async getEnvironmentVariables() {
    return apiService.getEnvironmentVariables();
  }

  // Update environment variable
  async updateEnvironmentVariable(key, value) {
    return apiService.updateEnvironmentVariable(key, value);
  }

  // Get system info
  async getSystemInfo() {
    try {
      const response = await apiService.request('/system/info');
      return response;
    } catch (error) {
      console.error('Failed to get system info:', error);
      throw error;
    }
  }

  // Get resource usage
  async getResourceUsage() {
    try {
      const response = await apiService.request('/system/resources');
      return response;
    } catch (error) {
      console.error('Failed to get resource usage:', error);
      throw error;
    }
  }
}

export const settingsAPI = new SettingsAPI();