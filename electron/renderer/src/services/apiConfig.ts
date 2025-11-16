/**
 * 统一API配置管理
 * 支持前后端分离部署的服务发现和健康检查
 */

import { requestManager } from './requestManager';

export interface ServiceConfig {
  name: string;
  baseUrl: string;
  healthEndpoint: string;
  timeout: number;
  retryCount: number;
}

export interface ApiConfig {
  services: {
    main: ServiceConfig;
    streamcap: ServiceConfig;
    douyin: ServiceConfig;
  };
  healthCheck: {
    interval: number;
    timeout: number;
    maxRetries: number;
  };
}

// 默认服务配置
// 🔧 硬编码端口（演示测试）- 后端 11111，前端 10200
const DEFAULT_CONFIG: ApiConfig = {
  services: {
    main: {
      name: 'FastAPI主服务',
      baseUrl: 'http://127.0.0.1:11111', // 🔧 硬编码后端端口 11111
      healthEndpoint: '/health',
      timeout: 30000, // 30秒超时（本地开发可能较慢）
      retryCount: 3
    },
    streamcap: {
      name: 'StreamCap服务',
      baseUrl: 'http://127.0.0.1:11111', // 🔧 StreamCap 已集成到主服务
      healthEndpoint: '/health',
      timeout: 30000,
      retryCount: 3
    },
    douyin: {
      name: 'Douyin服务',
      baseUrl: 'http://127.0.0.1:11111', // 🔧 Douyin 已集成到主服务
      healthEndpoint: '/health',
      timeout: 30000,
      retryCount: 3
    }
  },
  healthCheck: {
    interval: 30000, // 30秒
    timeout: 5000,   // 5秒超时
    maxRetries: 3    // 最大重试次数
  }
};

class ApiConfigManager {
  private config: ApiConfig;
  private healthCheckInterval: NodeJS.Timeout | number | null = null;
  private serviceStatus: Map<string, boolean> = new Map();
  private listeners: Set<(status: Map<string, boolean>) => void> = new Set();

  constructor() {
    this.config = this.loadConfig();
    this.initializeServiceStatus();
    
    // 注册清理回调
    requestManager.registerCleanup(() => {
      this.stopHealthCheck();
    });
  }

  /**
   * 加载配置
   */
  private loadConfig(): ApiConfig {
    // 从环境变量获取配置
    const envConfig = {
      services: {
        main: {
          ...DEFAULT_CONFIG.services.main,
          baseUrl: import.meta.env?.VITE_FASTAPI_URL || DEFAULT_CONFIG.services.main.baseUrl
        },
        streamcap: {
          ...DEFAULT_CONFIG.services.streamcap,
          // 如果环境变量设置为6006，强制使用主服务端口
          baseUrl: import.meta.env?.VITE_STREAMCAP_URL === 'http://127.0.0.1:6006' 
            ? DEFAULT_CONFIG.services.streamcap.baseUrl
            : (import.meta.env?.VITE_STREAMCAP_URL || DEFAULT_CONFIG.services.streamcap.baseUrl)
        },
        douyin: {
          ...DEFAULT_CONFIG.services.douyin,
          baseUrl: import.meta.env?.VITE_DOUYIN_URL || import.meta.env?.VITE_FASTAPI_URL || DEFAULT_CONFIG.services.douyin.baseUrl
        }
      },
      healthCheck: DEFAULT_CONFIG.healthCheck
    };

    console.log('🔧 API配置已加载:', envConfig);
    return envConfig;
  }

  /**
   * 初始化服务状态
   */
  private initializeServiceStatus(): void {
    Object.keys(this.config.services).forEach(serviceName => {
      this.serviceStatus.set(serviceName, false);
    });
  }

  /**
   * 获取服务配置
   */
  getServiceConfig(serviceName: keyof ApiConfig['services']): ServiceConfig {
    return this.config.services[serviceName];
  }

  /**
   * 获取服务基础URL
   */
  getServiceUrl(serviceName: keyof ApiConfig['services']): string {
    return this.config.services[serviceName].baseUrl;
  }

  /**
   * 构建完整URL
   */
  buildUrl(serviceName: keyof ApiConfig['services'], path: string): string {
    const baseUrl = this.getServiceUrl(serviceName).replace(/\/$/, '');
    const cleanPath = path.startsWith('/') ? path : `/${path}`;
    return `${baseUrl}${cleanPath}`;
  }

  /**
   * 检查单个服务健康状态
   */
  async checkServiceHealth(serviceName: keyof ApiConfig['services']): Promise<boolean> {
    const service = this.config.services[serviceName];
    const healthUrl = this.buildUrl(serviceName, service.healthEndpoint);

    try {
      // 使用追踪的 AbortController
      const controller = requestManager.createAbortController();
      const timeoutId = requestManager.createTimeout(() => controller.abort(), service.timeout);

      const response = await fetch(healthUrl, {
        method: 'GET',
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json'
        }
      });

      requestManager.clearTimeout(timeoutId);

      const isHealthy = response.ok;
      this.serviceStatus.set(serviceName, isHealthy);
      
      if (isHealthy) {
        console.log(`✅ ${service.name} 健康检查通过`);
      } else {
        console.warn(`⚠️ ${service.name} 健康检查失败: ${response.status}`);
      }

      return isHealthy;
    } catch (error: any) {
      // 如果是超时错误，静默处理（不显示错误日志）
      if (error?.name === 'AbortError') {
        // 超时通常意味着服务暂时不可用，但不一定是错误
        this.serviceStatus.set(serviceName, false);
        return false;
      }
      
      // 其他错误才显示日志
      console.error(`❌ ${service.name} 健康检查异常:`, error);
      this.serviceStatus.set(serviceName, false);
      return false;
    }
  }

  /**
   * 检查所有服务健康状态
   */
  async checkAllServicesHealth(): Promise<Map<string, boolean>> {
    const promises = Object.keys(this.config.services).map(async (serviceName) => {
      const isHealthy = await this.checkServiceHealth(serviceName as keyof ApiConfig['services']);
      return [serviceName, isHealthy] as [string, boolean];
    });

    const results = await Promise.all(promises);
    const statusMap = new Map(results);

    // 通知监听器
    this.notifyListeners(statusMap);

    return statusMap;
  }

  /**
   * 启动健康检查
   */
  startHealthCheck(): void {
    if (this.healthCheckInterval) {
      return;
    }

    console.log('🔍 启动服务健康检查...');
    
    // 立即执行一次检查
    this.checkAllServicesHealth();

    // 使用追踪的 setInterval
    this.healthCheckInterval = requestManager.createInterval(() => {
      this.checkAllServicesHealth();
    }, this.config.healthCheck.interval);
  }

  /**
   * 停止健康检查
   */
  stopHealthCheck(): void {
    if (this.healthCheckInterval) {
      requestManager.clearInterval(this.healthCheckInterval);
      this.healthCheckInterval = null;
      console.log('🛑 服务健康检查已停止');
    }
  }

  /**
   * 获取服务状态
   */
  getServiceStatus(serviceName?: keyof ApiConfig['services']): boolean | Map<string, boolean> {
    if (serviceName) {
      return this.serviceStatus.get(serviceName) || false;
    }
    return new Map(this.serviceStatus);
  }

  /**
   * 添加状态监听器
   */
  addStatusListener(listener: (status: Map<string, boolean>) => void): void {
    this.listeners.add(listener);
  }

  /**
   * 移除状态监听器
   */
  removeStatusListener(listener: (status: Map<string, boolean>) => void): void {
    this.listeners.delete(listener);
  }

  /**
   * 通知监听器
   */
  private notifyListeners(status: Map<string, boolean>): void {
    this.listeners.forEach(listener => {
      try {
        listener(status);
      } catch (error) {
        console.error('状态监听器执行失败:', error);
      }
    });
  }

  /**
   * 带重试的请求方法
   */
  async requestWithRetry<T>(
    serviceName: keyof ApiConfig['services'],
    path: string,
    options: RequestInit = {},
    retryCount?: number
  ): Promise<T> {
    const service = this.config.services[serviceName];
    const maxRetries = retryCount || service.retryCount;
    const url = this.buildUrl(serviceName, path);

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        // 使用追踪的 AbortController 和 setTimeout
        const controller = requestManager.createAbortController();
        const timeoutId = requestManager.createTimeout(() => controller.abort(), service.timeout);

        const response = await fetch(url, {
          ...options,
          signal: controller.signal,
          headers: {
            'Content-Type': 'application/json',
            ...options.headers
          }
        });

        requestManager.clearTimeout(timeoutId);

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        
        // 请求成功，更新服务状态
        this.serviceStatus.set(serviceName, true);
        
        return data;
      } catch (error) {
        console.warn(`${service.name} 请求失败 (尝试 ${attempt}/${maxRetries}):`, error);
        
        // 更新服务状态
        this.serviceStatus.set(serviceName, false);
        
        if (attempt === maxRetries) {
          throw new Error(`${service.name} 请求失败: ${error}`);
        }
        
        // 使用追踪的 setTimeout 进行重试延迟
        await new Promise(resolve => {
          requestManager.createTimeout(() => resolve(undefined), 1000 * attempt);
        });
      }
    }

    throw new Error(`${service.name} 请求失败: 超过最大重试次数`);
  }

  /**
   * 获取配置信息
   */
  getConfig(): ApiConfig {
    return { ...this.config };
  }

  /**
   * 更新服务配置
   */
  updateServiceConfig(serviceName: keyof ApiConfig['services'], config: Partial<ServiceConfig>): void {
    this.config.services[serviceName] = {
      ...this.config.services[serviceName],
      ...config
    };
    console.log(`🔧 ${serviceName} 服务配置已更新:`, this.config.services[serviceName]);
  }
}

// 导出单例实例
export const apiConfig = new ApiConfigManager();

// 导出便捷方法
export const getServiceUrl = (serviceName: keyof ApiConfig['services']) => 
  apiConfig.getServiceUrl(serviceName);

export const buildApiUrl = (serviceName: keyof ApiConfig['services'], path: string) => 
  apiConfig.buildUrl(serviceName, path);

export const requestWithRetry = <T>(
  serviceName: keyof ApiConfig['services'],
  path: string,
  options?: RequestInit,
  retryCount?: number
) => apiConfig.requestWithRetry<T>(serviceName, path, options, retryCount);

export const buildServiceUrl = (
  serviceName: keyof ApiConfig['services'],
  path: string,
  overrideBaseUrl?: string
) => {
  const base = (overrideBaseUrl ?? apiConfig.getServiceUrl(serviceName)).replace(/\/$/, '');
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${base}${cleanPath}`;
};

// 自动启动健康检查
if (typeof window !== 'undefined') {
  // 页面加载完成后启动健康检查
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      apiConfig.startHealthCheck();
    });
  } else {
    apiConfig.startHealthCheck();
  }

  // 页面卸载时停止健康检查
  window.addEventListener('beforeunload', () => {
    apiConfig.stopHealthCheck();
  });
}