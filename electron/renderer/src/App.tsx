import { HashRouter, Navigate, Route, Routes } from 'react-router-dom';
import MainLayout from './layout/MainLayout';
import DashboardPage from './pages/dashboard/DashboardPage';
import AboutPage from './pages/about/AboutPage';
import LiveConsolePage from './pages/dashboard/LiveConsolePage';
import ReportsPage from './pages/dashboard/ReportsPage';
import ToolsPage from './pages/settings/ToolsPage';
import AIGatewayPage from './pages/ai/AIGatewayPage';
import AIUsagePage from './pages/ai/AIUsagePage';
import useAuthGuard from './hooks/useAuthGuard';
import useAuthInterceptor from './hooks/useAuthInterceptor';
import FloatingWindowPage from './pages/FloatingWindowPage';

/**
 * 路由配置（简化版 - 本地桌面应用模式）
 *
 * 移除了登录/注册/订阅路由，直接进入主应用
 */
const AppRoutes = () => {
  const { requireAuth, requirePayment, isAuthenticated } = useAuthGuard();

  // 使用认证拦截器
  useAuthInterceptor();

  return (
    <Routes>
      {/* 悬浮窗路由（独立窗口） */}
      <Route path="/floating" element={<FloatingWindowPage />} />

      {/* 主应用路由（无需认证） */}
      <Route path="/" element={<MainLayout />}>
        <Route index element={<Navigate to="dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="live" element={<LiveConsolePage />} />
        <Route path="reports" element={<ReportsPage />} />
        <Route path="tools" element={<ToolsPage />} />
        <Route path="ai-gateway" element={<AIGatewayPage />} />
        <Route path="ai-usage" element={<AIUsagePage />} />
        <Route path="about" element={<AboutPage />} />
      </Route>

      {/* 兼容旧路由：重定向到主页面 */}
      <Route path="/auth/*" element={<Navigate to="/dashboard" replace />} />
      <Route path="/pay/*" element={<Navigate to="/dashboard" replace />} />

      {/* 未知路由：重定向到仪表板 */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
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
