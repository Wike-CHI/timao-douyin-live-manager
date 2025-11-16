const { contextBridge, ipcRenderer } = require('electron');

/**
 * 向渲染进程暴露 Electron IPC 通信接口
 * 用于监听主进程的清理信号和模型下载相关事件
 */
contextBridge.exposeInMainWorld('electron', {
  ipcRenderer: {
    // 调用主进程方法
    invoke: (channel, ...args) => {
      const validChannels = ['model:check', 'model:start-download', 'model:pause-download', 'model:resume-download', 'model:cancel-download'];
      if (validChannels.includes(channel)) {
        return ipcRenderer.invoke(channel, ...args);
      }
      return Promise.reject(new Error(`Invalid channel: ${channel}`));
    },
    // 监听来自主进程的消息
    on: (channel, callback) => {
      const validChannels = ['app-cleanup-request', 'model:download-progress', 'model:download-complete', 'model:download-error'];
      if (validChannels.includes(channel)) {
        ipcRenderer.on(channel, callback);
      }
    },
    // 移除监听器
    removeListener: (channel, callback) => {
      const validChannels = ['app-cleanup-request', 'model:download-progress', 'model:download-complete', 'model:download-error'];
      if (validChannels.includes(channel)) {
        ipcRenderer.removeListener(channel, callback);
      }
    },
    // 移除所有监听器
    removeAllListeners: (channel) => {
      const validChannels = ['app-cleanup-request', 'model:download-progress', 'model:download-complete', 'model:download-error'];
      if (validChannels.includes(channel)) {
        ipcRenderer.removeAllListeners(channel);
      }
    }
  }
});

/**
 * 向渲染进程暴露应用 API
 */
contextBridge.exposeInMainWorld('electronAPI', {
  // 应用操作
  openExternalLink: (url) => ipcRenderer.invoke('open-external-link', url),
  quitApp: () => ipcRenderer.invoke('app-quit'),
  openPath: (path) => ipcRenderer.invoke('open-path', path),
  openLogs: () => ipcRenderer.invoke('open-logs'),
  
  // 应用信息
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
  getAppPath: () => ipcRenderer.invoke('get-app-path'),
  getUserDataPath: () => ipcRenderer.invoke('get-user-data-path'),
  getLogsPath: () => ipcRenderer.invoke('get-logs-path'),
  getIsDev: () => ipcRenderer.invoke('get-is-dev'),
  getAppInfo: () => ipcRenderer.invoke('get-app-info'),
  
  // 系统信息
  platform: process.platform,
  version: process.versions,
  
  // ========== 🆕 悬浮窗控制API ==========
  
  /**
   * 获取 Python 本地服务状态
   */
  getPythonServiceStatus: () => ipcRenderer.invoke('get-python-service-status'),
  
  /**
   * 重启 Python 本地服务
   */
  restartPythonService: () => ipcRenderer.invoke('restart-python-service'),
  
  /**
   * 显示独立悬浮窗
   * 主窗口启动服务时调用
   */
  showFloatingWindow: () => ipcRenderer.invoke('show-floating-window'),
  
  /**
   * 隐藏悬浮窗
   */
  hideFloatingWindow: () => ipcRenderer.invoke('hide-floating-window'),
  
  /**
   * 关闭悬浮窗
   */
  closeFloatingWindow: () => ipcRenderer.invoke('close-floating-window'),
  
  /**
   * 检查悬浮窗是否可见
   */
  isFloatingWindowVisible: () => ipcRenderer.invoke('is-floating-window-visible'),
  
  /**
   * 🆕 切换悬浮窗置顶状态
   * @returns {Promise<{success: boolean, alwaysOnTop?: boolean, error?: string}>}
   */
  toggleFloatingAlwaysOnTop: () => ipcRenderer.invoke('toggle-floating-always-on-top'),
  
  /**
   * 🆕 获取悬浮窗置顶状态
   * @returns {Promise<boolean>}
   */
  getFloatingAlwaysOnTop: () => ipcRenderer.invoke('get-floating-always-on-top'),
  
  /**
   * 推送数据到悬浮窗
   * @param {object} data - 要推送的数据
   */
  sendFloatingData: (data) => ipcRenderer.send('floating-update-data', data),
  
  /**
   * 监听来自主进程的数据（悬浮窗使用）
   * @param {function} callback - 回调函数
   * @returns {function} 清理函数
   */
  onFloatingData: (callback) => {
    const handler = (event, data) => callback(data);
    ipcRenderer.on('floating-data', handler);
    // 返回清理函数
    return () => {
      ipcRenderer.removeListener('floating-data', handler);
    };
  },
  
  /**
   * 移除悬浮窗数据监听
   */
  removeFloatingDataListener: () => {
    ipcRenderer.removeAllListeners('floating-data');
  }
});

/**
 * 向渲染进程暴露工具函数
 */
contextBridge.exposeInMainWorld('utils', {
  // 格式化时间
  formatTime: (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  },
  
  // 格式化数字
  formatNumber: (num) => {
    if (num >= 10000) {
      return (num / 10000).toFixed(1) + 'w';
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'k';
    }
    return num.toString();
  },
  
  // 防抖函数
  debounce: (func, wait) => {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  },
  
  // 节流函数
  throttle: (func, limit) => {
    let inThrottle;
    return function executedFunction(...args) {
      if (!inThrottle) {
        func.apply(this, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  },
  
  // 生成UUID
  generateUUID: () => {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0;
      const v = c == 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  },
  
  // 复制到剪贴板
  copyToClipboard: async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch (err) {
      console.error('复制失败:', err);
      return false;
    }
  },
  
  // 下载文件
  downloadFile: (content, filename, type = 'text/plain') => {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }
});

// 控制台输出应用信息
console.log('提猫直播助手 - Preload脚本已加载');
console.log('Electron版本:', process.versions.electron);
console.log('Node版本:', process.versions.node);
console.log('Chrome版本:', process.versions.chrome);
