import { Navigate } from 'react-router-dom';
import useAuthStore from '../store/useAuthStore';

const useAuthGuard = () => {
  const { isAuthenticated, firstFreeUsed } = useAuthStore();

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
    // 积分策略：如果仍可享受首次免费（firstFreeUsed=false）即可进入主应用
    const canEnter = !firstFreeUsed;
    if (!canEnter) {
      return <Navigate to="/pay/subscription" replace />;
    }
    return component;
  };

  return { requireAuth, requirePayment, isAuthenticated };
};

export default useAuthGuard;
