import { HashRouter, Navigate, Route, Routes } from 'react-router-dom';
import { useEffect, useState } from 'react';
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
import useAuthStore from './store/useAuthStore';
import { isDemoMode, getDemoUserInfo } from './utils/demoMode';

// 内部路由组件，在Router上下文中使用hooks
const AppRoutes = () => {
  const { requireAuth, requirePayment, isAuthenticated } = useAuthGuard();
  const { setAuth } = useAuthStore();
  const [demoModeChecked, setDemoModeChecked] = useState(false);
  
  // 使用认证拦截器（必须在Router上下文中）
  useAuthInterceptor();

  // 检查演示模式并自动登录
  useEffect(() => {
    const checkDemoMode = async () => {
      try {
        const isDemoEnabled = await isDemoMode();
        
        if (isDemoEnabled && !isAuthenticated) {
          console.log('演示模式已启用，自动登录演示用户');
          const demoUserInfo = await getDemoUserInfo();
          
          if (demoUserInfo) {
            setAuth({
              user: demoUserInfo.user,
              token: demoUserInfo.token,
              refreshToken: demoUserInfo.refresh_token,
              isPaid: demoUserInfo.isPaid
            });
            console.log('演示用户自动登录成功');
          }
        }
      } catch (error) {
        console.log('检查演示模式失败:', error);
      } finally {
        setDemoModeChecked(true);
      }
    };

    if (!demoModeChecked) {
      checkDemoMode();
    }
  }, [isAuthenticated, setAuth, demoModeChecked]);

  // 在演示模式检查完成前显示加载状态
  if (!demoModeChecked) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        fontSize: '18px',
        color: '#666'
      }}>
        正在初始化...
      </div>
    );
  }

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
