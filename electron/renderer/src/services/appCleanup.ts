/**
 * 应用清理服务
 * 监听来自 Electron 主进程的清理信号,并执行清理操作
 */

import { requestManager } from './requestManager';

class AppCleanupService {
  private static instance: AppCleanupService;
  private isInitialized: boolean = false;

  private constructor() {}

  public static getInstance(): AppCleanupService {
    if (!AppCleanupService.instance) {
      AppCleanupService.instance = new AppCleanupService();
    }
    return AppCleanupService.instance;
  }

  /**
   * 初始化清理服务
   * 设置 IPC 监听器来接收来自主进程的清理信号
   */
  public initialize(): void {
    if (this.isInitialized) {
      return;
    }

    console.log('🔧 初始化应用清理服务...');

    // 检查是否在 Electron 环境中
    if (typeof window !== 'undefined' && (window as any).electron) {
      const electron = (window as any).electron;
      
      // 监听来自主进程的清理信号
      if (electron.ipcRenderer) {
        electron.ipcRenderer.on('app-cleanup-request', () => {
          console.log('📡 收到主进程清理信号,开始清理资源...');
          this.cleanup();
        });
        
        console.log('✅ Electron IPC 清理监听器已设置');
      }
    }

    // 监听浏览器的 beforeunload 事件
    if (typeof window !== 'undefined') {
      window.addEventListener('beforeunload', () => {
        console.log('📡 页面即将卸载,开始清理资源...');
        this.cleanup();
      });
      
      console.log('✅ 浏览器 beforeunload 清理监听器已设置');
    }

    this.isInitialized = true;
    console.log('✅ 应用清理服务初始化完成');
  }

  /**
   * 执行清理操作
   */
  public cleanup(): void {
    console.log('🧹 开始执行应用资源清理...');
    
    try {
      // 调用请求管理器的清理方法
      requestManager.cleanup();
      
      console.log('✅ 应用资源清理完成');
    } catch (error) {
      console.error('❌ 应用资源清理失败:', error);
    }
  }

  /**
   * 手动触发清理
   */
  public manualCleanup(): void {
    console.log('🔧 手动触发清理...');
    this.cleanup();
  }
}

// 导出单例实例
export const appCleanupService = AppCleanupService.getInstance();

// 自动初始化
if (typeof window !== 'undefined') {
  // 页面加载完成后初始化
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      appCleanupService.initialize();
    });
  } else {
    appCleanupService.initialize();
  }
}

// 导出便捷方法
export const initializeAppCleanup = () => appCleanupService.initialize();
export const cleanupApp = () => appCleanupService.cleanup();
export const manualCleanup = () => appCleanupService.manualCleanup();

