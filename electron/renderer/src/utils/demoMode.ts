/**
 * 演示模式工具函数
 */

/**
 * 检查是否启用演示模式
 * 通过检查后端API来确定演示模式状态
 */
export const isDemoMode = async (): Promise<boolean> => {
  try {
    const API_BASE_URL = import.meta.env?.VITE_FASTAPI_URL as string || 'http://127.0.0.1:9019';
    const response = await fetch(`${API_BASE_URL}/api/auth/demo-status`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (response.ok) {
      const data = await response.json();
      return data.demo_enabled === true;
    }
    
    return false;
  } catch (error) {
    console.log('检查演示模式状态失败:', error);
    return false;
  }
};

/**
 * 获取演示模式用户信息
 */
export const getDemoUserInfo = async () => {
  try {
    const API_BASE_URL = import.meta.env?.VITE_FASTAPI_URL as string || 'http://127.0.0.1:9019';
    const response = await fetch(`${API_BASE_URL}/api/auth/demo-login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (response.ok) {
      const data = await response.json();
      return data;
    }
    
    return null;
  } catch (error) {
    console.log('获取演示用户信息失败:', error);
    return null;
  }
};