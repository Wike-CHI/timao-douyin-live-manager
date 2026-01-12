/**
 * 统一API客户端
 * 提供动态端口配置和连接管理
 */

import { message } from 'antd';
import { apiConfig } from './apiConfig';

// 动态端口配置
interface PortConfig {
  backend: number;
  frontend: number;
}

// 从环境变量或localStorage获取端口配置
const getPortConfig = (): PortConfig => {
  // 优先从localStorage读取（用户自定义配置）
  const savedConfig = localStorage.getItem('port_config');
  if (savedConfig) {
    try {
      return JSON.parse(savedConfig);
    } catch (e) {
      console.error('解析端口配置失败:', e);
    }
  }

  // 默认端口配置
  return {
    backend: parseInt(import.meta.env.VITE_BACKEND_PORT || '11111'),
    frontend: parseInt(import.meta.env.VITE_FRONTEND_PORT || '10065')
  };
};

// 保存端口配置
export const savePortConfig = (config: PortConfig): void => {
  localStorage.setItem('port_config', JSON.stringify(config));
  // 重新初始化API客户端
  initApiClient();
};

// 获取后端基础URL
export const getBackendBaseUrl = (): string => {
  const config = getPortConfig();
  return `http://127.0.0.1:${config.backend}`;
};

// 初始化API客户端
export const initApiClient = (): void => {
  const baseURL = getBackendBaseUrl();
  console.log('🔧 初始化API客户端:', baseURL);
  
  // 更新 apiConfig 服务配置
  apiConfig.updateServiceConfig('main', { baseUrl: baseURL });
  apiConfig.updateServiceConfig('backend', { baseUrl: baseURL });
};

// 测试后端连接
export const testBackendConnection = async (): Promise<{
  success: boolean;
  message: string;
  latency?: number;
}> => {
  const start = Date.now();
  const baseURL = getBackendBaseUrl();
  
  try {
    const response = await fetch(`${baseURL}/health`, {
      method: 'GET',
      signal: AbortSignal.timeout(5000)
    });
    const latency = Date.now() - start;
    
    if (response.ok) {
      return {
        success: true,
        message: '连接成功',
        latency
      };
    } else {
      return {
        success: false,
        message: `HTTP ${response.status}`
      };
    }
  } catch (error: unknown) {
    console.error('后端连接测试失败:', error);
    
    const err = error as { code?: string; message?: string };
    
    if (err.code === 'ECONNREFUSED') {
      return {
        success: false,
        message: '连接被拒绝，请检查后端服务是否启动'
      };
    } else if (err.code === 'ETIMEDOUT' || (error instanceof DOMException && error.name === 'TimeoutError')) {
      return {
        success: false,
        message: '连接超时'
      };
    } else {
      return {
        success: false,
        message: err.message || '未知错误'
      };
    }
  }
};

// 自动检测可用端口
export const autoDetectBackendPort = async (): Promise<number | null> => {
  const portsToTry = [11111, 5001, 8000, 8080, 9000];
  
  for (const port of portsToTry) {
    try {
      const testUrl = `http://127.0.0.1:${port}/health`;
      const response = await fetch(testUrl, { 
        method: 'GET',
        signal: AbortSignal.timeout(2000)
      });
      
      if (response.ok) {
        console.log(`✅ 检测到后端服务: ${port}`);
        return port;
      }
    } catch {
      // 继续尝试下一个端口
    }
  }
  
  return null;
};

// 端口配置钩子
export const usePortConfig = () => {
  const config = getPortConfig();
  
  const updateConfig = (newConfig: Partial<PortConfig>) => {
    const updated = { ...config, ...newConfig };
    savePortConfig(updated);
    message.success('端口配置已更新');
  };
  
  return {
    config,
    updateConfig,
    testConnection: testBackendConnection,
    autoDetect: autoDetectBackendPort
  };
};

// 导出单例
const apiClient = {
  getPortConfig,
  savePortConfig,
  getBackendBaseUrl,
  initApiClient,
  testBackendConnection,
  autoDetectBackendPort,
  usePortConfig
};

// 启动时自动初始化
initApiClient();

export default apiClient;
