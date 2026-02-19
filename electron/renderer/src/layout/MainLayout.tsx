import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import {
  LayoutDashboard,
  Radio,
  FileText,
  Settings,
  Info,
  Loader2,
  LogOut
} from 'lucide-react';
import ThemeToggle from '../components/ThemeToggle';
import useAuthStore from '../store/useAuthStore';
import logoUrl from '../assets/logo.jpg';

const navItems = [
  { to: '/dashboard', label: '总览', icon: LayoutDashboard },
  { to: '/live', label: '直播控制台', icon: Radio },
  { to: '/reports', label: '直播报告', icon: FileText },
  { to: '/tools', label: '工具', icon: Settings },
  { to: '/about', label: '关于', icon: Info },
];

const MainLayout = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const [bootstrap, setBootstrap] = useState<any>(null);
  const [showBoot, setShowBoot] = useState<boolean>(true);
  const [wsOk, setWsOk] = useState<boolean | null>(null);
  const defaultApiBase = import.meta.env?.VITE_FASTAPI_URL as string || 'http://127.0.0.1:11111';
  const injectedApiBase = ((import.meta.env?.VITE_FASTAPI_URL as string | undefined) || 'http://127.0.0.1:11111').trim() || defaultApiBase;
  const [apiBase, setApiBase] = useState<string>(injectedApiBase);

  const handleLogout = () => {
    logout();
    navigate('/auth/login');
  };

  useEffect(() => {
    let mounted = true;
    let t: any = null;
    const probeWS = () => {
      try {
        const wsUrl = apiBase.replace(/^http/i, 'ws').replace(/\/$/, '') + '/api/live_audio/ws';
        const ws = new WebSocket(wsUrl);
        let settled = false;
        const timer = setTimeout(() => {
          if (!settled) {
            try { ws.close(); } catch {}
            if (mounted) setWsOk(false);
          }
        }, 2000);
        ws.onopen = () => { try { ws.send(JSON.stringify({ type: 'ping' })); } catch {} };
        ws.onmessage = (ev) => {
          try {
            const m = JSON.parse(ev.data);
            if (m?.type === 'pong') {
              settled = true;
              clearTimeout(timer);
              if (mounted) setWsOk(true);
              try { ws.close(); } catch {}
            }
          } catch {}
        };
        ws.onclose = () => { clearTimeout(timer); };
        ws.onerror = () => {
          clearTimeout(timer);
          if (!settled && mounted) setWsOk(false);
        };
      } catch { if (mounted) setWsOk(false); }
    };
    const poll = async () => {
      try {
        const resp = await fetch(`${apiBase}/api/bootstrap/status`);
        const data = await resp.json();
        if (!mounted) return;
        setBootstrap(data || {});
        const ok = data && data.ffmpeg?.state === 'ok' && data.models?.state === 'ok';
        if (!data?.running && ok) {
          setTimeout(() => setShowBoot(false), 2000);
          return;
        }
      } catch {
        if (apiBase !== defaultApiBase) {
          setApiBase(defaultApiBase);
          setWsOk(null);
          return;
        }
      }
      t = setTimeout(poll, 1200);
    };
    poll();
    probeWS();
    return () => { mounted = false; if (t) clearTimeout(t); };
  }, [apiBase]);

  const runQuickSelfTest = async () => {
    setShowBoot(true);
    try {
      const r0 = await fetch(`${apiBase}/api/bootstrap/status`).catch(() => null);
      const d0 = r0 ? await r0.json().catch(() => null) : null;
      if (d0) setBootstrap(d0);
      const r1 = await fetch(`${apiBase}/api/live_audio/health`).catch(() => null);
      const d1 = r1 ? await r1.json().catch(() => null) : null;
      if (d1 && bootstrap) {
        setBootstrap({
          ...bootstrap,
          models: { state: d1?.success ? 'ok' : 'missing', model_present: !!d1?.assets?.model_present, vad_present: !!d1?.assets?.vad_present },
          suggestions: d1?.suggestions || bootstrap?.suggestions || [],
        });
      }
      try {
        const wsUrl = apiBase.replace(/^http/i, 'ws').replace(/\/$/, '') + '/api/live_audio/ws';
        const ws = new WebSocket(wsUrl);
        let settled = false;
        const timer = setTimeout(() => {
          if (!settled) {
            try { ws.close(); } catch {}
            setWsOk(false);
          }
        }, 2000);
        ws.onopen = () => { try { ws.send(JSON.stringify({ type: 'ping' })); } catch {} };
        ws.onmessage = (ev) => {
          try {
            const m = JSON.parse(ev.data);
            if (m?.type === 'pong') {
              settled = true;
              clearTimeout(timer);
              setWsOk(true);
              try { ws.close(); } catch {}
            }
          } catch {}
        };
        ws.onclose = () => { clearTimeout(timer); };
        ws.onerror = () => { clearTimeout(timer); if (!settled) setWsOk(false); };
      } catch {
        if (apiBase !== defaultApiBase) {
          setApiBase(defaultApiBase);
          return;
        }
        setWsOk(false);
      }
    } catch {
      if (apiBase !== defaultApiBase) {
        setApiBase(defaultApiBase);
      }
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-gray-50 to-slate-100 flex">
      {/* 侧边栏 */}
      <aside className="w-64 bg-white/80 backdrop-blur-sm border-r border-gray-100 flex flex-col p-5 h-screen sticky top-0">
        {/* Logo 区域 */}
        <div className="text-xl font-semibold text-gray-900 mb-8 flex items-center gap-3 flex-shrink-0 px-2">
          <div className="h-9 w-9 rounded-xl bg-gradient-to-br from-rose-100 to-orange-100 flex items-center justify-center">
            <img src={logoUrl} alt="TalkingCat" className="h-7 w-7 rounded-lg" />
          </div>
          <span className="leading-none tracking-tight">提猫直播助手</span>
        </div>

        {/* 导航 */}
        <nav className="flex-1 space-y-1 overflow-y-auto pr-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-4 py-2.5 rounded-xl transition-all duration-200 ${
                    isActive
                      ? 'text-white shadow-md'
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                  }`
                }
                style={({ isActive }) => isActive ? { background: 'var(--theme-gradient)' } : {}}
              >
                <Icon size={18} />
                <span className="font-medium">{item.label}</span>
              </NavLink>
            );
          })}
        </nav>

        {/* 底部区域 */}
        <div className="mt-4 pt-4 border-t border-gray-100 flex-shrink-0">
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium text-gray-500 hover:text-red-600 hover:bg-red-50 transition-all duration-200"
          >
            <LogOut size={18} />
            退出登录
          </button>
        </div>
      </aside>

      {/* 主内容区 */}
      <main className="flex-1 flex flex-col pr-4">
        {/* 顶部栏 */}
        <header className="flex justify-between items-center px-8 py-6">
          <div>
            <div className="text-lg font-semibold text-gray-900">
              欢迎回来，{(user as any)?.nickname || (user as any)?.email || '主播'}
            </div>
            <div className="text-sm text-gray-500">祝你直播顺利</div>
          </div>
          <div className="flex items-center gap-4">
            <NavLink
              to="/pay/subscription"
              className="px-5 py-2.5 text-white rounded-xl hover:shadow-lg transition-all duration-200 text-sm font-medium"
              style={{ background: 'var(--theme-gradient)' }}
            >
              订阅服务
            </NavLink>
            <ThemeToggle />
          </div>
        </header>

        {/* 启动状态提示 */}
        {showBoot && (
          <div className="mx-8 -mt-2 mb-4 rounded-xl border border-amber-200/50 bg-amber-50/80 backdrop-blur-sm px-4 py-3 text-sm text-amber-800 flex items-center justify-between">
            <div className="flex items-center gap-3">
              {(bootstrap?.running || wsOk === null) ? (
                <Loader2 size={16} className="animate-spin" />
              ) : (
                <span className="w-2 h-2 rounded-full bg-amber-500" />
              )}
              <span>
                {bootstrap?.running ? '正在准备运行所需资源…' : '资源检查完成'}
                {bootstrap?.models ? ` (模型: ${bootstrap.models.model_present ? 'OK' : '缺失'} · VAD: ${bootstrap.models.vad_present ? 'OK' : '缺失'})` : ''}
                {wsOk != null ? ` · WS: ${wsOk ? '可用' : '不可用'}` : ' · 正在检测 WS'}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <button className="timao-outline-btn text-xs px-3 py-1.5" onClick={runQuickSelfTest}>立即自检</button>
              {Array.isArray(bootstrap?.suggestions) && bootstrap.suggestions.length ? (
                <div className="text-xs text-gray-500 mr-2">
                  {bootstrap.suggestions.join('；')}
                </div>
              ) : null}
              {bootstrap?.paths?.model_dir ? (
                <button className="timao-outline-btn text-xs px-3 py-1.5" onClick={() => { try { (window as any).electronAPI?.openPath(bootstrap.paths.model_dir); } catch {} }}>打开模型目录</button>
              ) : null}
            </div>
          </div>
        )}

        {/* 内容区域 */}
        <section className="flex-1 px-8 pb-12">
          <Outlet />
        </section>
      </main>
    </div>
  );
};

export default MainLayout;
