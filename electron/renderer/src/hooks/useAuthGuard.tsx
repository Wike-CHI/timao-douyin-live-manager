import { Navigate } from 'react-router-dom';
import useAuthStore from '../store/useAuthStore';

const useAuthGuard = () => {
  const { isAuthenticated, isPaid } = useAuthStore();

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
    // 检查是否已付费
    if (!isPaid) {
      return <Navigate to="/pay/subscription" replace />;
    }
    return component;
  };

  return { requireAuth, requirePayment, isAuthenticated };
};

export default useAuthGuard;
