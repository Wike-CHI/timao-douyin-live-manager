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
    
    // 未付费用户也可以访问页面，但会在页面中显示提示
    // 不再强制重定向到订阅页面（更友好的体验）
    return component;
  };

  return { requireAuth, requirePayment, isAuthenticated };
};

export default useAuthGuard;