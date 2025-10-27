import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './theme/global.css';
import useAuthStore from './store/useAuthStore';

// 演示模式：启动时自动写入“超级管理员”登录态与订阅状态
(() => {
  const DEMO = (import.meta.env?.VITE_DEMO_MODE as string | undefined) === 'true';
  if (!DEMO) return;

  const { setAuth, setPaid } = useAuthStore.getState();
  const farFutureToken =
    // header: { alg: "HS256", typ: "JWT" }
    // payload: { exp: 4102444800 (UTC 2100-01-01), sub: "demo" }
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjQxMDI0NDQ4MDAsInN1YiI6ImRlbW8ifQ.demo';

  setAuth({
    user: {
      id: 1,
      username: 'demo',
      email: 'demo@example.com',
      nickname: '演示账号',
      avatar_url: '',
      role: 'super_admin',
      status: 'active',
      email_verified: true,
      phone_verified: true,
      created_at: '2025-01-01T00:00:00Z',
    },
    token: farFutureToken,
    refreshToken: farFutureToken,
    isPaid: true,
  });
  setPaid(true);
})();

type RootElement = HTMLElement & { _reactRootContainer?: unknown };

const rootElement = document.getElementById('root') as RootElement;

const root = ReactDOM.createRoot(rootElement);
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
