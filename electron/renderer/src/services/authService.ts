import useAuthStore from '../store/useAuthStore';

const DEFAULT_BASE_URL = (import.meta.env?.VITE_FASTAPI_URL as string | undefined) || 'http://127.0.0.1:10090';

interface RefreshTokenResponse {
  success: boolean;
  token: string;
  access_token: string;
  refresh_token: string;
  expires_in: number;
  user: any;
  isPaid: boolean;
}

class AuthService {
  private refreshPromise: Promise<boolean> | null = null;

  /**
   * 检查token是否即将过期（提前5分钟刷新）
   */
  private isTokenExpiringSoon(token: string): boolean {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const exp = payload.exp * 1000; // 转换为毫秒
      const now = Date.now();
      const fiveMinutes = 5 * 60 * 1000;
      
      return exp - now < fiveMinutes;
    } catch {
      return true; // 如果解析失败，认为需要刷新
    }
  }

  /**
   * 检查token是否已过期
   */
  private isTokenExpired(token: string): boolean {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const exp = payload.exp * 1000;
      return Date.now() >= exp;
    } catch {
      return true;
    }
  }

  /**
   * 刷新访问令牌
   */
  private async refreshAccessToken(): Promise<boolean> {
    const { token: currentToken } = useAuthStore.getState();
    
    // 从localStorage获取refresh token
    const authData = localStorage.getItem('timao-auth');
    if (!authData) {
      return false;
    }

    try {
      const parsedData = JSON.parse(authData);
      const refreshToken = parsedData.state?.refreshToken;
      
      if (!refreshToken) {
        console.warn('No refresh token available');
        return false;
      }

      const response = await fetch(`${DEFAULT_BASE_URL}/api/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          refresh_token: refreshToken
        })
      });

      if (!response.ok) {
        throw new Error('Token refresh failed');
      }

      const data: RefreshTokenResponse = await response.json();
      
      // 更新认证状态
      const { setAuth } = useAuthStore.getState();
      setAuth({
        user: data.user,
        token: data.access_token,
        isPaid: data.isPaid
      });

      // 更新localStorage中的refresh token
      const updatedAuthData = {
        ...parsedData,
        state: {
          ...parsedData.state,
          token: data.access_token,
          refreshToken: data.refresh_token,
          user: data.user,
          isPaid: data.isPaid
        }
      };
      localStorage.setItem('timao-auth', JSON.stringify(updatedAuthData));

      console.log('Token refreshed successfully');
      return true;
    } catch (error) {
      console.error('Token refresh failed:', error);
      // 刷新失败，清除认证状态
      this.logout();
      return false;
    }
  }

  /**
   * 确保token有效（自动刷新）
   */
  async ensureValidToken(): Promise<boolean> {
    const { token, isAuthenticated } = useAuthStore.getState();
    
    if (!isAuthenticated || !token) {
      return false;
    }

    // 如果token已过期，尝试刷新
    if (this.isTokenExpired(token)) {
      console.log('Token expired, attempting refresh...');
      return await this.performRefresh();
    }

    // 如果token即将过期，预先刷新
    if (this.isTokenExpiringSoon(token)) {
      console.log('Token expiring soon, preemptive refresh...');
      // 异步刷新，不阻塞当前请求
      this.performRefresh().catch(console.error);
    }

    return true;
  }

  /**
   * 执行token刷新（防止并发刷新）
   */
  private async performRefresh(): Promise<boolean> {
    // 如果已经有刷新请求在进行中，等待它完成
    if (this.refreshPromise) {
      return await this.refreshPromise;
    }

    // 创建新的刷新请求
    this.refreshPromise = this.refreshAccessToken();
    
    try {
      const result = await this.refreshPromise;
      return result;
    } finally {
      this.refreshPromise = null;
    }
  }

  /**
   * 获取有效的认证头
   */
  async getAuthHeaders(): Promise<Record<string, string>> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json'
    };

    const isValid = await this.ensureValidToken();
    if (isValid) {
      const { token } = useAuthStore.getState();
      if (token) {
        headers.Authorization = `Bearer ${token}`;
      }
    }

    return headers;
  }

  /**
   * 登出
   */
  logout(): void {
    const { logout } = useAuthStore.getState();
    logout();
    // 清除localStorage中的refresh token
    localStorage.removeItem('timao-auth');
  }

  /**
   * 检查认证状态
   */
  async checkAuthStatus(): Promise<boolean> {
    return await this.ensureValidToken();
  }
}

// 导出单例实例
export const authService = new AuthService();
export default authService;