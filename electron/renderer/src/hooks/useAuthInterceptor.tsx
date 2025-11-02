import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import useAuthStore from '../store/useAuthStore';
import authService from '../services/authService';

/**
 * 认证拦截器Hook
 * 在应用启动时检查认证状态，并设置定期检查
 */
const useAuthInterceptor = () => {
  const navigate = useNavigate();
  const { isAuthenticated, token, clearAuth } = useAuthStore();

  useEffect(() => {
    // 应用启动时检查认证状态，优先尝试刷新 token
    const checkInitialAuth = async () => {
      if (isAuthenticated && token) {
        // 使用 ensureValidToken 自动刷新过期的 token
        const newToken = await authService.ensureValidToken();
        if (!newToken) {
          console.log('Initial auth check failed after refresh attempt, redirecting to login');
          clearAuth();
          navigate('/auth/login');
        }
      }
    };

    checkInitialAuth();

    // 设置定期检查token状态（每10分钟，给刷新机制更多时间）
    const interval = setInterval(async () => {
      if (isAuthenticated && token) {
        // 使用 ensureValidToken 自动刷新即将过期或已过期的 token
        const newToken = await authService.ensureValidToken();
        if (!newToken) {
          console.log('Periodic auth check failed, redirecting to login');
          clearAuth();
          navigate('/auth/login');
        }
      }
    }, 10 * 60 * 1000); // 10分钟（从5分钟延长，与后端8小时token配合）

    return () => clearInterval(interval);
  }, [isAuthenticated, token, clearAuth, navigate]);

  // 监听页面可见性变化，页面重新获得焦点时先尝试刷新 token
  useEffect(() => {
    const handleVisibilityChange = async () => {
      if (document.visibilityState === 'visible' && isAuthenticated && token) {
        // 先尝试刷新 token，而不是直接检查是否有效
        const newToken = await authService.ensureValidToken();
        if (!newToken) {
          console.log('Visibility change auth check failed after refresh attempt, redirecting to login');
          clearAuth();
          navigate('/auth/login');
        } else {
          console.log('Token validated/refreshed after visibility change');
        }
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [isAuthenticated, token, clearAuth, navigate]);
};

export default useAuthInterceptor;