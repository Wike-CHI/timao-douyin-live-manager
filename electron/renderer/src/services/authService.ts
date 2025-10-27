import useAuthStore from '../store/useAuthStore';

const API_BASE_URL = 'http://localhost:10090';

class AuthService {
  private refreshPromise: Promise<boolean> | null = null;

  /**
   * 检查token是否即将过期（5分钟内）
   */
  private isTokenExpiringSoon(token: string): boolean {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const exp = payload.exp * 1000; // 转换为毫秒
      const now = Date.now();
      const fiveMinutes = 5 * 60 * 1000;
      
      return exp - now < fiveMinutes;
    } catch (error) {
      console.error('Error parsing token:', error);
      return true; // 解析失败时认为需要刷新
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
    } catch (error) {
      console.error('Error parsing token:', error);
      return true;
    }
  }

  /**
   * 刷新访问令牌
   */
  private async refreshAccessToken(): Promise<boolean> {
    const { refreshToken, setAuth, clearAuth } = useAuthStore.getState();
    
    if (!refreshToken) {
      console.log('No refresh token available');
      return false;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (!response.ok) {
        console.log('Refresh token request failed:', response.status);
        clearAuth();
        return false;
      }

      const data = await response.json();
      
      // 更新认证状态
      const currentState = useAuthStore.getState();
      setAuth({
        user: currentState.user!,
        token: data.access_token,
        refreshToken: data.refresh_token,
        isPaid: currentState.isPaid
      });

      console.log('Token refreshed successfully');
      return true;
    } catch (error) {
      console.error('Error refreshing token:', error);
      clearAuth();
      return false;
    }
  }

  /**
   * 确保有效的访问令牌
   */
  async ensureValidToken(): Promise<string | null> {
    const { token, isAuthenticated } = useAuthStore.getState();
    
    if (!isAuthenticated || !token) {
      return null;
    }

    // 如果token已过期，立即刷新
    if (this.isTokenExpired(token)) {
      console.log('Token expired, refreshing...');
      if (this.refreshPromise) {
        await this.refreshPromise;
      } else {
        this.refreshPromise = this.refreshAccessToken();
        await this.refreshPromise;
        this.refreshPromise = null;
      }
      
      const newState = useAuthStore.getState();
      return newState.token;
    }

    // 如果token即将过期，预防性刷新
    if (this.isTokenExpiringSoon(token)) {
      console.log('Token expiring soon, refreshing preemptively...');
      if (!this.refreshPromise) {
        this.refreshPromise = this.refreshAccessToken();
        // 不等待刷新完成，继续使用当前token
        this.refreshPromise.finally(() => {
          this.refreshPromise = null;
        });
      }
    }

    return token;
  }

  /**
   * 获取认证头
   */
  async getAuthHeaders(): Promise<Record<string, string>> {
    const token = await this.ensureValidToken();
    
    if (!token) {
      return {};
    }

    return {
      'Authorization': `Bearer ${token}`,
    };
  }

  /**
   * 检查认证状态
   */
  async checkAuthStatus(): Promise<boolean> {
    const token = await this.ensureValidToken();
    return !!token;
  }

  /**
   * 登出
   */
  logout(): void {
    const { clearAuth } = useAuthStore.getState();
    clearAuth();
    
    // 清除可能存在的刷新Promise
    this.refreshPromise = null;
    
    console.log('User logged out');
  }
}

const authService = new AuthService();
export default authService;