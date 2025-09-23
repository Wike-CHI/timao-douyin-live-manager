import { Outlet, Navigate } from 'react-router-dom';
import ThemeToggle from '../components/ThemeToggle';
import useAuthStore from '../store/useAuthStore';

const PaymentLayout = () => {
  const { isAuthenticated, isPaid } = useAuthStore();

  if (!isAuthenticated) {
    return <Navigate to="/auth/login" replace />;
  }

  if (isPaid) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className="min-h-screen timao-surface flex flex-col">
      <header className="flex justify-between items-center px-6 py-4">
        <div className="text-xl font-semibold text-purple-500">🐾 支付验证</div>
        <ThemeToggle />
      </header>
      <main className="flex-1 flex items-center justify-center px-4 pb-10">
        <div className="w-full max-w-2xl">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default PaymentLayout;
