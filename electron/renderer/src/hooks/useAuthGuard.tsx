import { Navigate } from 'react-router-dom';
import useAuthStore from '../store/useAuthStore';

const useAuthGuard = () => {
  const { isAuthenticated, isPaid, user } = useAuthStore();

  const requireAuth = (component: React.ReactElement) => {
    if (!isAuthenticated) {
      return <Navigate to="/auth/login" replace />;
    }
    return component;
  };

  const requirePayment = (component: React.ReactElement) => {
    if (!isAuthenticated) {
      return <Navigate to="/auth/login" replace />;
    }
    
    // 检查用户是否为超级管理员，如果是则跳过订阅检查
    if (user?.role === 'super_admin') {
      return component;
    }
    
    // 强制检查是否已付费，未付费用户必须停留在订阅页面
    if (!isPaid) {
      // 如果当前不在订阅页面，强制跳转
      const currentPath = window.location.hash.replace('#', '');
      if (currentPath !== '/pay/subscription') {
        return <Navigate to="/pay/subscription" replace />;
      }
      // 如果在订阅页面，仍然允许访问（避免无限重定向）
      return component;
    }
    return component;
  };

  return { requireAuth, requirePayment, isAuthenticated };
};

export default useAuthGuard;