/**
 * Electron API 类型定义
 * 定义通过 contextBridge 暴露给渲染进程的 API
 */

export interface ElectronAPI {
  // 应用操作
  openExternalLink: (url: string) => Promise<void>;
  quitApp: () => Promise<void>;
  openPath: (path: string) => Promise<{ success: boolean; error?: string }>;
  openLogs: () => Promise<{ success: boolean; path?: string; error?: string }>;
  
  // 应用信息
  getAppVersion: () => Promise<string>;
  getAppPath: () => Promise<string>;
  getUserDataPath: () => Promise<string>;
  getLogsPath: () => Promise<string>;
  getIsDev: () => Promise<boolean>;
  getAppInfo: () => Promise<{
    version: string;
    name: string;
    path: string;
    userDataPath: string;
    logsPath: string;
    isDev: boolean;
    platform: string;
  }>;
  
  // 系统信息
  platform: NodeJS.Platform;
  version: NodeJS.ProcessVersions;
}

export interface ElectronIpcRenderer {
  on: (channel: string, callback: (...args: any[]) => void) => void;
  removeListener: (channel: string, callback: (...args: any[]) => void) => void;
}

export interface Electron {
  ipcRenderer: ElectronIpcRenderer;
}

export interface Utils {
  formatTime: (timestamp: number) => string;
  formatNumber: (num: number) => string;
  debounce: (func: Function, wait: number) => Function;
  throttle: (func: Function, limit: number) => Function;
  generateUUID: () => string;
  copyToClipboard: (text: string) => Promise<boolean>;
  downloadFile: (content: string, filename: string, type?: string) => void;
}

declare global {
  interface Window {
    electron?: Electron;
    electronAPI?: ElectronAPI;
    utils?: Utils;
  }
}

export {};
