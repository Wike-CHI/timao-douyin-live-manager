import { ReactElement } from 'react';
import { Navigate } from 'react-router-dom';
import useAuthStore from '../store/useAuthStore';

const useAuthGuard = () => {
  const { isAuthenticated, isPaid } = useAuthStore();

  const requireAuth = (element: ReactElement) =>
    isAuthenticated ? element : <Navigate to="/auth/login" replace />;

  const requirePayment = (element: ReactElement) => {
    if (!isAuthenticated) {
      return <Navigate to="/auth/login" replace />;
    }
    if (!isPaid) {
      return <Navigate to="/pay/verify" replace />;
    }
    return element;
  };

  return { requireAuth, requirePayment, isAuthenticated, isPaid };
};

export default useAuthGuard;
