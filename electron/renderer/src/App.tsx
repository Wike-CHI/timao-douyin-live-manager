import { HashRouter, Navigate, Route, Routes } from 'react-router-dom';
import AuthLayout from './layout/AuthLayout';
import PaymentLayout from './layout/PaymentLayout';
import MainLayout from './layout/MainLayout';
import LoginPage from './pages/auth/LoginPage';
import RegisterPage from './pages/auth/RegisterPage';
import SubscriptionPage from './pages/payment/SubscriptionPage';
import DashboardPage from './pages/dashboard/DashboardPage';
import AboutPage from './pages/about/AboutPage';
import LiveConsolePage from './pages/dashboard/LiveConsolePage';
import ReportsPage from './pages/dashboard/ReportsPage';
import ToolsPage from './pages/settings/ToolsPage';
import AIGatewayPage from './pages/ai/AIGatewayPage';
import AIUsagePage from './pages/ai/AIUsagePage';
import useAuthGuard from './hooks/useAuthGuard';
import useAuthInterceptor from './hooks/useAuthInterceptor';

// 内部路由组件，在Router上下文中使用hooks
const AppRoutes = () => {
  const { requireAuth, requirePayment, isAuthenticated } = useAuthGuard();
  
  // 使用认证拦截器（必须在Router上下文中）
  useAuthInterceptor();

  return (
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
        <Route index element={<Navigate to="subscription" replace />} />
        <Route path="subscription" element={<SubscriptionPage />} />
      </Route>

      <Route
        path="/"
        element={requireAuth(<MainLayout />)}
      >
        <Route index element={<Navigate to="dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="live" element={<LiveConsolePage />} />
        <Route path="reports" element={<ReportsPage />} />
        <Route path="tools" element={<ToolsPage />} />
        <Route path="ai-gateway" element={<AIGatewayPage />} />
        <Route path="ai-usage" element={<AIUsagePage />} />
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
  );
};

const App = () => {
  return (
    <HashRouter
      future={{
        v7_startTransition: true,
        v7_relativeSplatPath: true,
      }}
    >
      <AppRoutes />
    </HashRouter>
  );
};

export default App;
