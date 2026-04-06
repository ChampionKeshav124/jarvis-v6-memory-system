// ═══════════════════════════════════════════════════════════════
//  JARVIS V2 — Preload Script
//  Secure contextBridge API for the renderer process
// ═══════════════════════════════════════════════════════════════

const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('jarvis', {
  /** Send a command to the Python AI backend — returns { response, action, audio_base64 } */
  sendCommand: (payload) => ipcRenderer.invoke('send-command', payload),

  /** Get real CPU/RAM stats from the OS — returns { cpu, ram } */
  getSystemStats: () => ipcRenderer.invoke('get-system-stats'),

  /** Get config variables from the main process */
  getConfig: () => ipcRenderer.invoke('get-config'),
  onWakeJarvis: (callback) => ipcRenderer.on('wake-jarvis', callback),

  /** Frameless window controls */
  minimize: () => ipcRenderer.send('win-minimize'),
  maximize: () => ipcRenderer.send('win-maximize'),
  close:    () => ipcRenderer.send('win-close'),
  openMicSettings: () => ipcRenderer.send('open-mic-settings'),

  /** Get full conversation history for UI startup display */
  getChatHistory: () => ipcRenderer.invoke('get-chat-history'),
});
