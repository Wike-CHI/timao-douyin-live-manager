import { Outlet, Navigate, useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import ThemeToggle from '../components/ThemeToggle';
import useAuthStore from '../store/useAuthStore';

const PaymentLayout = () => {
  const { isAuthenticated } = useAuthStore();
  const navigate = useNavigate();

  if (!isAuthenticated) {
    return <Navigate to="/auth/login" replace />;
  }

  return (
    <div className="min-h-screen timao-surface flex flex-col">
      <header className="flex justify-between items-center px-6 py-4 border-b border-gray-200">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/dashboard')}
            className="flex items-center text-gray-600 hover:text-gray-900 transition-colors"
          >
            <ArrowLeft size={18} className="mr-2" />
            返回主界面
          </button>
          <div className="text-lg font-semibold text-gray-900">订阅管理</div>
        </div>
        <ThemeToggle />
      </header>
      <main className="flex-1 px-4 pb-10 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
};

export default PaymentLayout;
