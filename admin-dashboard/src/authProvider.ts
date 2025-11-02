import { AuthProvider } from 'react-admin';

const API_BASE = import.meta.env.VITE_FASTAPI_URL || 'http://127.0.0.1:9019';

export const authProvider: AuthProvider = {
  // 登录
  login: async ({ username, password }) => {
    try {
      const response = await fetch(`${API_BASE}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username_or_email: username,
          password: password,
          remember_me: true,
        }),
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: '登录失败' }));
        throw new Error(error.detail || '登录失败');
      }

      const data = await response.json();
      
      // 保存token - 支持多种字段名
      const token = data.access_token || data.token || data.accessToken;
      if (token) {
        localStorage.setItem('token', token);
        const refreshToken = data.refresh_token || data.refreshToken;
        if (refreshToken) {
          localStorage.setItem('refresh_token', refreshToken);
        }
      } else {
        throw new Error('登录响应中未找到token');
      }

      return Promise.resolve();
    } catch (error) {
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

