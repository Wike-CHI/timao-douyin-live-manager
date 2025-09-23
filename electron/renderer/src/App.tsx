import { HashRouter, Navigate, Route, Routes } from 'react-router-dom';
import AuthLayout from './layout/AuthLayout';
import PaymentLayout from './layout/PaymentLayout';
import MainLayout from './layout/MainLayout';
import LoginPage from './pages/auth/LoginPage';
import RegisterPage from './pages/auth/RegisterPage';
import PaymentVerifyPage from './pages/payment/PaymentVerifyPage';
import DashboardPage from './pages/dashboard/DashboardPage';
import AboutPage from './pages/about/AboutPage';
import LiveConsolePage from './pages/dashboard/LiveConsolePage';
import ReportsPlaceholder from './pages/dashboard/ReportsPlaceholder';
import useAuthGuard from './hooks/useAuthGuard';
import WalletPage from '@/pages/payment/WalletPage';

const App = () => {
  const { requireAuth, requirePayment, isAuthenticated } = useAuthGuard();

  return (
    <HashRouter>
      <Routes>
        <Route path="/auth" element={<AuthLayout />}> 
          <Route index element={<Navigate to="login" replace />} />
          <Route path="login" element={<LoginPage />} />
          <Route path="register" element={<RegisterPage />} />
        </Route>

        <Route
          path="/pay"
          element={requireAuth(<PaymentLayout />)}
        >
          <Route index element={<Navigate to="wallet" replace />} />
          <Route path="verify" element={<PaymentVerifyPage />} />
          <Route path="wallet" element={<WalletPage />} />
        </Route>

        <Route
          path="/"
          element={requirePayment(<MainLayout />)}
        >
          <Route index element={<Navigate to="dashboard" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="live" element={<LiveConsolePage />} />
          <Route path="reports" element={<ReportsPlaceholder />} />
          <Route path="about" element={<AboutPage />} />
        </Route>

        <Route
          path="*"
          element={
            isAuthenticated
              ? <Navigate to="/dashboard" replace />
              : <Navigate to="/auth/login" replace />
          }
        />
      </Routes>
    </HashRouter>
  );
};

export default App;
