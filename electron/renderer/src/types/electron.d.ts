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
  
  // ========== 悬浮窗控制API ==========
  
  /**
   * 显示独立悬浮窗
   * 主窗口启动服务时调用
   */
  showFloatingWindow: () => Promise<{ success: boolean; error?: string }>;
  
  /**
   * 隐藏悬浮窗
   */
  hideFloatingWindow: () => Promise<{ success: boolean; error?: string }>;
  
  /**
   * 关闭悬浮窗
   */
  closeFloatingWindow: () => Promise<{ success: boolean; error?: string }>;
  
  /**
   * 检查悬浮窗是否可见
   */
  isFloatingWindowVisible: () => Promise<boolean>;
  
  /**
   * 🆕 切换悬浮窗置顶状态
   * @returns 返回新的置顶状态
   */
  toggleFloatingAlwaysOnTop: () => Promise<{ success: boolean; alwaysOnTop?: boolean; error?: string }>;
  
  /**
   * 🆕 获取悬浮窗置顶状态
   * @returns 当前是否置顶
   */
  getFloatingAlwaysOnTop: () => Promise<boolean>;
  
  /**
   * 推送数据到悬浮窗
   * @param data - 要推送的数据
   */
  sendFloatingData: (data: any) => void;
  
  /**
   * 监听来自主进程的数据（悬浮窗使用）
   * @param callback - 回调函数
   * @returns 清理函数
   */
  onFloatingData: (callback: (data: any) => void) => (() => void);
  
  /**
   * 移除悬浮窗数据监听
   */
  removeFloatingDataListener: () => void;
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
