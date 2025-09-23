import { ReactElement } from 'react';
import { Navigate } from 'react-router-dom';
import useAuthStore from '../store/useAuthStore';

const useAuthGuard = () => {
  const { isAuthenticated, balance, firstFreeUsed } = useAuthStore();

  const requireAuth = (element: ReactElement) =>
    isAuthenticated ? element : <Navigate to="/auth/login" replace />;

  const requirePayment = (element: ReactElement) => {
    if (!isAuthenticated) {
      return <Navigate to="/auth/login" replace />;
    }
    // 钱包策略：余额>0 或 仍可享受首次免费（firstFreeUsed=false）即可进入主应用
    const canEnter = (balance ?? 0) > 0 || !firstFreeUsed;
    if (!canEnter) {
      return <Navigate to="/pay/wallet" replace />;
    }
    return element;
  };

  return { requireAuth, requirePayment, isAuthenticated };
};

export default useAuthGuard;
