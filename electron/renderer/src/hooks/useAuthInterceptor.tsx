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
    // 应用启动时检查认证状态
    const checkInitialAuth = async () => {
      if (isAuthenticated && token) {
        const isValid = await authService.checkAuthStatus();
        if (!isValid) {
          console.log('Initial auth check failed, redirecting to login');
          clearAuth();
          navigate('/auth/login');
        }
      }
    };

    checkInitialAuth();

    // 设置定期检查token状态（每5分钟）
    const interval = setInterval(async () => {
      if (isAuthenticated && token) {
        const isValid = await authService.checkAuthStatus();
        if (!isValid) {
          console.log('Periodic auth check failed, redirecting to login');
          clearAuth();
          navigate('/auth/login');
        }
      }
    }, 5 * 60 * 1000); // 5分钟

    return () => clearInterval(interval);
  }, [isAuthenticated, token, clearAuth, navigate]);

  // 监听页面可见性变化，页面重新获得焦点时检查认证状态
  useEffect(() => {
    const handleVisibilityChange = async () => {
      if (document.visibilityState === 'visible' && isAuthenticated && token) {
        const isValid = await authService.checkAuthStatus();
        if (!isValid) {
          console.log('Visibility change auth check failed, redirecting to login');
          clearAuth();
          navigate('/auth/login');
        }
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [isAuthenticated, token, clearAuth, navigate]);
};

export default useAuthInterceptor;