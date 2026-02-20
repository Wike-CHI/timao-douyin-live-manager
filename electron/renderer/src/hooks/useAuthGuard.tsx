import { Navigate } from 'react-router-dom';
import useAuthStore from '../store/useAuthStore';

/**
 * 认证守卫（简化版 - 本地桌面应用模式）
 *
 * 不再进行认证检查，直接允许访问
 */
const useAuthGuard = () => {
  const { isAuthenticated, isPaid, user } = useAuthStore();

  // 本地模式：直接返回组件，不进行认证检查
  const requireAuth = (component: React.ReactElement) => {
    return component;
  };

  // 本地模式：直接返回组件，不进行付费检查
  const requirePayment = (component: React.ReactElement) => {
    return component;
  };

  return { requireAuth, requirePayment, isAuthenticated: true };
};

export default useAuthGuard;
