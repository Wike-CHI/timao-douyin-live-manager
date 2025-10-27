import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import ThemeToggle from '../components/ThemeToggle';
import useAuthStore from '../store/useAuthStore';
import logoUrl from '../assets/logo.jpg';
import type { UserInfo } from '../services/auth'; // 导入UserInfo类型

const navItems = [
  { to: '/dashboard', label: '总览', icon: '📊' },
  { to: '/live', label: '直播控制台', icon: '🎤' },
  { to: '/reports', label: '直播报告', icon: '📑' },
  { to: '/tools', label: '工具', icon: '🧰' },
  { to: '/about', label: '关于', icon: 'ℹ️' },
];

const MainLayout = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const [bootstrap, setBootstrap] = useState<any>(null);
  const [showBoot, setShowBoot] = useState<boolean>(true);
  const [wsOk, setWsOk] = useState<boolean | null>(null);
  const defaultApiBase = 'http://127.0.0.1:10090';
  const injectedApiBase = ((import.meta.env?.VITE_FASTAPI_URL as string | undefined) || '').trim() || defaultApiBase;
  const [apiBase, setApiBase] = useState<string>(injectedApiBase);

  const handleLogout = () => {
    logout();
    navigate('/auth/login');
  };

  // 资源准备提示（启动后短暂轮询）
  useEffect(() => {
    let mounted = true;
    let t: any = null;
    // quick WS probe (one-shot)
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
        // 隐藏条件：非运行状态且 ffmpeg/models 就绪
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

  // 立即自检（前端触发一次性检查：bootstrap状态 + WS ping + 模型健康）
  const runQuickSelfTest = async () => {
    setShowBoot(true);
    try {
      // refresh bootstrap status
      const r0 = await fetch(`${apiBase}/api/bootstrap/status`).catch(() => null);
      const d0 = r0 ? await r0.json().catch(() => null) : null;
      if (d0) setBootstrap(d0);
      // model/VAD health
      const r1 = await fetch(`${apiBase}/api/live_audio/health`).catch(() => null);
      const d1 = r1 ? await r1.json().catch(() => null) : null;
      if (d1 && bootstrap) {
        setBootstrap({
          ...bootstrap,
          models: { state: d1?.success ? 'ok' : 'missing', model_present: !!d1?.assets?.model_present, vad_present: !!d1?.assets?.vad_present },
          suggestions: d1?.suggestions || bootstrap?.suggestions || [],
        });
      }
      // WS probe
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
      <aside className="w-64 timao-card flex flex-col p-6 mr-4">
        <div className="text-2xl font-semibold text-purple-500 mb-8 flex items-center gap-3">
          <img src={logoUrl} alt="TalkingCat" className="h-8 w-8 rounded-lg ring-2 ring-purple-300 shadow" />
          <span className="leading-none">提猫直播助手 · TalkingCat</span>
        </div>
        <nav className="flex-1 space-y-2">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-150 ${
                  isActive
                    ? 'bg-purple-100/70 text-purple-600 shadow'
                    : 'text-slate-500 hover:bg-purple-50/60'
                }`
              }
            >
              <span>{item.icon}</span>
              <span className="font-medium">{item.label}</span>
            </NavLink>
          ))}
        </nav>
        <button onClick={handleLogout} className="mt-6 text-sm timao-support-text hover:text-purple-500">
          退出登录
        </button>
      </aside>
      <main className="flex-1 flex flex-col pr-4">
        <header className="flex justify-between items-center px-8 py-6">
          <div>
            <div className="text-lg font-semibold text-slate-700">
              欢迎回来，{(user as UserInfo)?.nickname || (user as UserInfo)?.email || '提猫主播'}！
            </div>
            <div className="text-sm timao-support-text">祝你今晚直播顺利喵～</div>
          </div>
          <div className="flex items-center gap-4">
            {/* 订阅服务按钮已隐藏 */}
            <ThemeToggle />
          </div>
        </header>
        {/* 顶部资源提示条 */}
        {showBoot && (
          <div className="mx-8 -mt-2 mb-4 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="relative flex items-center justify-center">
                {(bootstrap?.running || wsOk === null) ? (
                  <span className="inline-block w-3.5 h-3.5 border-2 border-amber-300 border-t-transparent rounded-full animate-spin" />
                ) : (
                  <span>🧩</span>
                )}
              </span>
              <span>
                {bootstrap?.running ? '正在准备运行所需资源…' : '资源检查完成'}
                {bootstrap?.models ? `（模型: ${bootstrap.models.model_present ? 'OK' : '缺失'} · VAD: ${bootstrap.models.vad_present ? 'OK' : '缺失'}）` : ''}
                {wsOk != null ? ` · WS: ${wsOk ? '可用' : '不可用'}` : ' · 正在检测 WS'}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <button className="timao-outline-btn text-[10px] px-2 py-0.5" onClick={runQuickSelfTest}>立即自检</button>
              {Array.isArray(bootstrap?.suggestions) && bootstrap.suggestions.length ? (
                <div className="text-xs timao-support-text mr-2">
                  {bootstrap.suggestions.join('；')}
                </div>
              ) : null}
              {/* 快捷打开目录（如果已知） */}
              {bootstrap?.paths?.model_dir ? (
                <button className="timao-outline-btn text-[10px] px-2 py-0.5" onClick={() => { try { (window as any).electronAPI?.openPath(bootstrap.paths.model_dir); } catch {} }}>打开模型目录</button>
              ) : null}
              {bootstrap?.paths?.vad_dir ? (
                <button className="timao-outline-btn text-[10px] px-2 py-0.5" onClick={() => { try { (window as any).electronAPI?.openPath(bootstrap.paths.vad_dir); } catch {} }}>打开VAD目录</button>
              ) : null}
              {bootstrap?.paths?.ffmpeg_dir ? (
                <button className="timao-outline-btn text-[10px] px-2 py-0.5" onClick={() => { try { (window as any).electronAPI?.openPath(bootstrap.paths.ffmpeg_dir); } catch {} }}>打开FFmpeg目录</button>
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