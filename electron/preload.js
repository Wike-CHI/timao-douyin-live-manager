const { contextBridge, ipcRenderer } = require('electron');

/**
 * 向渲染进程暴露安全的API
 */
contextBridge.exposeInMainWorld('electronAPI', {
  // Flask服务相关
  checkFlaskHealth: () => ipcRenderer.invoke('flask-health-check'),
  getFlaskUrl: () => ipcRenderer.invoke('get-flask-url'),
  openPath: (p) => ipcRenderer.invoke('open-path', p),
  quitApp: () => ipcRenderer.invoke('app-quit'),
  openLogs: () => ipcRenderer.invoke('open-logs'),
  bootstrapRetry: () => ipcRenderer.invoke('bootstrap-retry'),
  toggleSplashPin: () => ipcRenderer.invoke('toggle-splash-pin'),
  
  // 系统信息
  platform: process.platform,
  version: process.versions,
  
  // 应用信息
  appVersion: require('../package.json').version,
  appName: require('../package.json').name
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

/**
 * 向渲染进程暴露常量
 */
contextBridge.exposeInMainWorld('constants', {
  // API端点
  API_ENDPOINTS: {
    HEALTH: '/api/health',
    COMMENTS_STREAM: '/api/comments/stream',
    HOT_WORDS: '/api/analysis/hot-words',
    LATEST_SCRIPT: '/api/ai/latest-script',
    MARK_SCRIPT_USED: '/api/ai/mark-used',
    CONFIG: '/api/config'
  },
  
  // 事件类型
  EVENT_TYPES: {
    COMMENT_RECEIVED: 'comment_received',
    HOT_WORDS_UPDATED: 'hot_words_updated',
    SCRIPT_GENERATED: 'script_generated',
    ERROR_OCCURRED: 'error_occurred'
  },
  
  // 状态码
  STATUS_CODES: {
    SUCCESS: 200,
    CREATED: 201,
    BAD_REQUEST: 400,
    UNAUTHORIZED: 401,
    NOT_FOUND: 404,
    INTERNAL_ERROR: 500
  },
  
  // 配置默认值
  DEFAULT_CONFIG: {
    MAX_COMMENTS_DISPLAY: 100,
    HOT_WORDS_LIMIT: 20,
    SCRIPT_REFRESH_INTERVAL: 30000,
    COMMENT_FETCH_INTERVAL: 1000,
    AUTO_SCROLL: true,
    SOUND_ENABLED: true
  }
});

// 控制台输出应用信息
console.log('提猫直播助手 - Preload脚本已加载');
console.log('Electron版本:', process.versions.electron);
console.log('Node版本:', process.versions.node);
console.log('Chrome版本:', process.versions.chrome);
