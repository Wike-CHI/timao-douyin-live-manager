import { AuthProvider } from 'react-admin';

const API_BASE = import.meta.env.VITE_FASTAPI_URL || 'http://127.0.0.1:9019';

export const authProvider: AuthProvider = {
  // 登录
  login: async ({ username, password }) => {
    try {
      console.log('🔐 开始登录请求...', { username, apiBase: API_BASE });
      
      const response = await fetch(`${API_BASE}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include', // 允许发送cookies
        body: JSON.stringify({
          username_or_email: username,
          password: password,
          remember_me: true,
        }),
      });

      console.log('📡 登录响应状态:', response.status, response.statusText);
      console.log('📡 响应头:', Object.fromEntries(response.headers.entries()));

      if (!response.ok) {
        let errorDetail = '登录失败';
        try {
          const errorData = await response.json();
          errorDetail = errorData.detail || errorData.message || `HTTP ${response.status}: ${response.statusText}`;
          console.error('❌ 登录失败:', errorData);
        } catch (e) {
          errorDetail = `HTTP ${response.status}: ${response.statusText}`;
          const errorText = await response.text();
          console.error('❌ 登录失败（无法解析JSON）:', errorText);
        }
        
        // 如果是CORS错误，提供更详细的错误信息
        if (response.status === 0 || response.type === 'opaque') {
          errorDetail = 'CORS错误：无法连接到后端服务。请检查后端服务是否运行，以及CORS配置是否正确。';
          console.error('❌ CORS错误:', {
            origin: window.location.origin,
            target: `${API_BASE}/api/auth/login`,
          });
        }
        
        throw new Error(errorDetail);
      }

      const data = await response.json();
      console.log('✅ 登录成功，响应数据:', { hasToken: !!(data.access_token || data.token), hasRefreshToken: !!(data.refresh_token) });
      
      // 保存token - 支持多种字段名
      const token = data.access_token || data.token || data.accessToken;
      if (token) {
        localStorage.setItem('token', token);
        const refreshToken = data.refresh_token || data.refreshToken;
        if (refreshToken) {
          localStorage.setItem('refresh_token', refreshToken);
        }
        console.log('✅ Token已保存到localStorage');
      } else {
        console.error('❌ 登录响应中未找到token:', data);
        throw new Error('登录响应中未找到token');
      }

      return Promise.resolve();
    } catch (error: any) {
      console.error('❌ 登录异常:', error);
      // 提供更详细的错误信息
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        return Promise.reject(new Error(`网络错误：无法连接到后端服务 ${API_BASE}。请检查后端服务是否运行。`));
      }
      return Promise.reject(error);
    }
  },

  // 登出
  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    return Promise.resolve();
  },

  // 检查认证状态
  checkAuth: () => {
    const token = localStorage.getItem('token');
    if (token) {
      return Promise.resolve();
    }
    return Promise.reject({ redirectTo: '/login' });
  },

  // 检查错误
  checkError: (error) => {
    const status = error.status;
    if (status === 401 || status === 403) {
      localStorage.removeItem('token');
      localStorage.removeItem('refresh_token');
      return Promise.reject({ redirectTo: '/login', logoutUser: true });
    }
    return Promise.resolve();
  },

  // 获取权限
  getPermissions: async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        return Promise.resolve();
      }

      const response = await fetch(`${API_BASE}/api/auth/me`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        return Promise.resolve();
      }

      const user = await response.json();
      
      // 只有管理员可以访问
      if (user.role === 'admin' || user.role === 'super_admin') {
        return Promise.resolve(user.role);
      }
      
      return Promise.reject({ message: '权限不足' });
    } catch (error) {
      return Promise.resolve();
    }
  },

  // 获取用户身份
  getIdentity: async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('未登录');
      }

      const response = await fetch(`${API_BASE}/api/auth/me`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('获取用户信息失败');
      }

      const user = await response.json();
      
      return Promise.resolve({
        id: user.id,
        fullName: user.nickname || user.username || user.email,
        avatar: user.avatar_url,
      });
    } catch (error) {
      return Promise.reject(error);
    }
  },
};

