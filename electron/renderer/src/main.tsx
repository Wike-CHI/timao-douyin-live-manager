import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './theme/global.css';
import useAuthStore from './store/useAuthStore';
import './services/appCleanup'; // 初始化应用清理服务
import apiClient from './services/apiClient';

// 本地化模式：启动时自动写入本地用户登录态与订阅状态
// 完全绕过认证和订阅机制
(() => {
  const { setAuth, setPaid } = useAuthStore.getState();
  
  // 本地用户令牌（长期有效）
  const localUserToken =
    // header: { alg: "HS256", typ: "JWT" }
    // payload: { exp: 4102444800 (UTC 2100-01-01), sub: "local" }
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjQxMDI0NDQ4MDAsInN1YiI6ImxvY2FsIn0.local';

  setAuth({
    user: {
      id: 1,
      username: 'local_user',
      email: 'local@localhost',
      nickname: '本地用户',
      avatar_url: '',
      role: 'super_admin',
      status: 'active',
      email_verified: true,
      phone_verified: true,
      created_at: '2025-01-01T00:00:00Z',
    },
    token: localUserToken,
    refreshToken: localUserToken,
    isPaid: true,  // 本地化模式：始终已付费
  });
  setPaid(true);  // 确保订阅状态为已付费
  
  console.log('🏠 本地化模式已启用：认证和订阅检查已绕过');
})();

// 初始化API客户端
apiClient.initApiClient();

// 启动时检查后端连接和初始化状态
(async () => {
  try {
    // 测试后端连接
    const connectionTest = await apiClient.testBackendConnection();
    
    if (!connectionTest.success) {
      console.warn('⚠️ 后端服务未连接:', connectionTest.message);
      // 尝试自动检测端口
      const detectedPort = await apiClient.autoDetectBackendPort();
      if (detectedPort) {
        console.log(`✅ 自动检测到后端服务: ${detectedPort}`);
        apiClient.savePortConfig({ 
          backend: detectedPort, 
          frontend: apiClient.getPortConfig().frontend 
        });
      } else {
        console.error('❌ 无法连接到后端服务，跳转到配置向导');
        window.location.hash = '#/setup';
        return;
      }
    }
    
    // 检查初始化状态
    const baseUrl = apiClient.getBackendBaseUrl();
    const response = await fetch(`${baseUrl}/api/bootstrap/status`);
    const data = await response.json();
    
    if (!data?.is_initialized) {
      console.log('⚙️ 首次启动，跳转到配置向导');
      window.location.hash = '#/setup';
    }
  } catch (error) {
    console.warn('⚠️ 检查初始化状态失败:', error);
    window.location.hash = '#/setup';
  }
})();

type RootElement = HTMLElement & { _reactRootContainer?: unknown };

const rootElement = document.getElementById('root') as RootElement;

const root = ReactDOM.createRoot(rootElement);
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
