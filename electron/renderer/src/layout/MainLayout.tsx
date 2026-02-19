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
    <div className="min-h-screen timao-surface flex">
      <aside className="w-64 timao-card flex flex-col p-6 mr-4 h-screen sticky top-0">
        <div className="text-xl font-semibold text-gray-900 mb-8 flex items-center gap-3 flex-shrink-0">
          <img src={logoUrl} alt="TalkingCat" className="h-8 w-8 rounded-lg" />
          <span className="leading-none">提猫直播助手</span>
        </div>

        <nav className="flex-1 space-y-1 overflow-y-auto pr-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-4 py-2.5 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-gray-100 text-gray-900'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  }`
                }
              >
                <Icon size={18} />
                <span className="font-medium">{item.label}</span>
              </NavLink>
            );
          })}
        </nav>

        <div className="mt-4 pt-4 border-t border-gray-200 flex-shrink-0">
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium text-red-600 hover:bg-red-50 transition-colors"
          >
            <LogOut size={18} />
            退出登录
          </button>
        </div>
      </aside>

      <main className="flex-1 flex flex-col pr-4">
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
              className="px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors text-sm font-medium"
            >
              订阅服务
            </NavLink>
            <ThemeToggle />
          </div>
        </header>

        {showBoot && (
          <div className="mx-8 -mt-2 mb-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800 flex items-center justify-between">
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
              <button className="timao-outline-btn text-xs px-2 py-1" onClick={runQuickSelfTest}>立即自检</button>
              {Array.isArray(bootstrap?.suggestions) && bootstrap.suggestions.length ? (
                <div className="text-xs text-gray-500 mr-2">
                  {bootstrap.suggestions.join('；')}
                </div>
              ) : null}
              {bootstrap?.paths?.model_dir ? (
                <button className="timao-outline-btn text-xs px-2 py-1" onClick={() => { try { (window as any).electronAPI?.openPath(bootstrap.paths.model_dir); } catch {} }}>打开模型目录</button>
              ) : null}
            </div>
          </div>
        )}

        <section className="flex-1 px-8 pb-12">
          <Outlet />
        </section>
      </main>
    </div>
  );
};

export default MainLayout;
