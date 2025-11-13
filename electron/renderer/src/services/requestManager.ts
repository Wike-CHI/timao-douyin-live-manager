/**
 * 全局请求管理器
 * 用于追踪和取消所有正在进行的HTTP请求和定时器
 * 当应用关闭时,确保所有资源都被正确清理
 */

export class RequestManager {
  private static instance: RequestManager;
  private abortControllers: Set<AbortController> = new Set();
  private timers: Set<NodeJS.Timeout | number> = new Set();
  private intervals: Set<NodeJS.Timeout | number> = new Set();
  private cleanupCallbacks: Set<() => void> = new Set();
  private isShuttingDown: boolean = false;

  private constructor() {
    // 监听页面卸载事件
    if (typeof window !== 'undefined') {
      window.addEventListener('beforeunload', () => {
        this.cleanup();
      });

      // 监听来自 Electron 主进程的清理信号
      window.addEventListener('app-cleanup', () => {
        console.log('📡 收到应用清理信号,开始清理资源...');
        this.cleanup();
      });
    }
  }

  public static getInstance(): RequestManager {
    if (!RequestManager.instance) {
      RequestManager.instance = new RequestManager();
    }
    return RequestManager.instance;
  }

  /**
   * 创建一个被追踪的 AbortController
   * 当应用关闭时,会自动 abort 这个 controller
   */
  public createAbortController(): AbortController {
    const controller = new AbortController();
    this.abortControllers.add(controller);

    // 当请求完成时,自动从追踪列表中移除
    controller.signal.addEventListener('abort', () => {
      this.abortControllers.delete(controller);
    });

    return controller;
  }

  /**
   * 创建一个被追踪的 setTimeout
   * 当应用关闭时,会自动清除这个定时器
   */
  public createTimeout(callback: () => void, delay: number): NodeJS.Timeout | number {
    if (this.isShuttingDown) {
      console.warn('⚠️ 应用正在关闭,忽略新的定时器创建');
      return -1;
    }

    const wrappedCallback = () => {
      callback();
      this.timers.delete(timer);
    };

    const timer = setTimeout(wrappedCallback, delay);
    this.timers.add(timer);
    return timer;
  }

  /**
   * 创建一个被追踪的 setInterval
   * 当应用关闭时,会自动清除这个定时器
   */
  public createInterval(callback: () => void, delay: number): NodeJS.Timeout | number {
    if (this.isShuttingDown) {
      console.warn('⚠️ 应用正在关闭,忽略新的定时器创建');
      return -1;
    }

    const interval = setInterval(callback, delay);
    this.intervals.add(interval);
    return interval;
  }

  /**
   * 手动移除定时器
   */
  public clearTimeout(timer: NodeJS.Timeout | number): void {
    clearTimeout(timer);
    this.timers.delete(timer);
  }

  /**
   * 手动移除轮询定时器
   */
  public clearInterval(interval: NodeJS.Timeout | number): void {
    clearInterval(interval);
    this.intervals.delete(interval);
  }

  /**
   * 注册清理回调
   * 当应用关闭时,会执行这些回调
   */
  public registerCleanup(callback: () => void): void {
    this.cleanupCallbacks.add(callback);
  }

  /**
   * 移除清理回调
   */
  public unregisterCleanup(callback: () => void): void {
    this.cleanupCallbacks.delete(callback);
  }

  /**
   * 检查是否正在关闭
   */
  public isCleaningUp(): boolean {
    return this.isShuttingDown;
  }

  /**
   * 清理所有资源
   */
  public cleanup(): void {
    if (this.isShuttingDown) {
      return; // 防止重复清理
    }

    this.isShuttingDown = true;
    console.log('🧹 开始清理所有资源...');

    // 1. 取消所有正在进行的请求
    console.log(`📡 取消 ${this.abortControllers.size} 个正在进行的请求...`);
    this.abortControllers.forEach((controller) => {
      try {
        controller.abort();
      } catch (error) {
        console.error('取消请求失败:', error);
      }
    });
    this.abortControllers.clear();

    // 2. 清除所有定时器
    console.log(`⏱️  清除 ${this.timers.size} 个定时器...`);
    this.timers.forEach((timer) => {
      clearTimeout(timer);
    });
    this.timers.clear();

    // 3. 清除所有轮询定时器
    console.log(`🔄 清除 ${this.intervals.size} 个轮询定时器...`);
    this.intervals.forEach((interval) => {
      clearInterval(interval);
    });
    this.intervals.clear();

    // 4. 执行所有注册的清理回调
    console.log(`🔧 执行 ${this.cleanupCallbacks.size} 个清理回调...`);
    this.cleanupCallbacks.forEach((callback) => {
      try {
        callback();
      } catch (error) {
        console.error('清理回调执行失败:', error);
      }
    });
    this.cleanupCallbacks.clear();

    console.log('✅ 资源清理完成');
  }

  /**
   * 重置状态 (主要用于测试)
   */
  public reset(): void {
    this.cleanup();
    this.isShuttingDown = false;
  }
}

// 导出单例实例
export const requestManager = RequestManager.getInstance();

// 导出便捷方法
export const createTrackedAbortController = () => 
  requestManager.createAbortController();

export const createTrackedTimeout = (callback: () => void, delay: number) => 
  requestManager.createTimeout(callback, delay);

export const createTrackedInterval = (callback: () => void, delay: number) => 
  requestManager.createInterval(callback, delay);

export const clearTrackedTimeout = (timer: NodeJS.Timeout | number) => 
  requestManager.clearTimeout(timer);

export const clearTrackedInterval = (interval: NodeJS.Timeout | number) => 
  requestManager.clearInterval(interval);

export const registerCleanupCallback = (callback: () => void) => 
  requestManager.registerCleanup(callback);

export const cleanupAllResources = () => 
  requestManager.cleanup();

