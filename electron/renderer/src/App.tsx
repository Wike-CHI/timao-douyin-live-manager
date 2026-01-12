import { HashRouter, Navigate, Route, Routes } from 'react-router-dom';
import MainLayout from './layout/MainLayout';
import DashboardPage from './pages/dashboard/DashboardPage';
import AboutPage from './pages/about/AboutPage';
import LiveConsolePage from './pages/dashboard/LiveConsolePage';
import ReportsPage from './pages/dashboard/ReportsPage';
import ToolsPage from './pages/settings/ToolsPage';
import AIGatewayPage from './pages/ai/AIGatewayPage';
import AIUsagePage from './pages/ai/AIUsagePage';
import SetupWizard from './pages/setup/SetupWizard';

// 本地化模式：简化路由，移除认证和付费检查
const AppRoutes = () => {
  return (
    <Routes>
      {/* 初次启动向导（独立路由，无Layout） */}
      <Route path="/setup" element={<SetupWizard />} />
      
      {/* 本地化模式：所有页面直接可访问，无需认证和付费检查 */}
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

      {/* 所有其他路径重定向到仪表板 */}
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
