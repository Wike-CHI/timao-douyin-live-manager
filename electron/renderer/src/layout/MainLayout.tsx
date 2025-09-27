import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import ThemeToggle from '../components/ThemeToggle';
import useAuthStore from '../store/useAuthStore';
import logoUrl from '../assets/logo.jpg';

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

  const handleLogout = () => {
    logout();
    navigate('/auth/login');
  };

  // 新增：余额与钱包入口
  const { balance } = useAuthStore();
  const goWallet = () => navigate('/pay/wallet');

  // 资源准备提示（启动后短暂轮询）
  useEffect(() => {
    let mounted = true;
    let t: any = null;
    const base = (import.meta.env?.VITE_FASTAPI_URL as string | undefined) || 'http://127.0.0.1:8007';
    // quick WS probe (one-shot)
    const probeWS = () => {
      try {
        const wsUrl = base.replace(/^http/i, 'ws').replace(/\/$/, '') + '/api/live_audio/ws';
        const ws = new WebSocket(wsUrl);
        const timer = setTimeout(() => { try { ws.close(); } catch {} if (mounted) setWsOk(false); }, 2000);
        ws.onopen = () => { try { ws.send(JSON.stringify({ type: 'ping' })); } catch {} };
        ws.onmessage = (ev) => { try { const m = JSON.parse(ev.data); if (m?.type === 'pong' && mounted) { setWsOk(true); } } catch {} };
        ws.onclose = () => { clearTimeout(timer); };
        ws.onerror = () => { clearTimeout(timer); if (mounted) setWsOk(false); };
      } catch { if (mounted) setWsOk(false); }
    };
    const poll = async () => {
      try {
        const resp = await fetch(`${base}/api/bootstrap/status`);
        const data = await resp.json();
        if (!mounted) return;
        setBootstrap(data || {});
        // 隐藏条件：非运行状态且 ffmpeg/models 就绪
        const ok = data && data.ffmpeg?.state === 'ok' && data.models?.state === 'ok';
        if (!data?.running && ok) {
          setTimeout(() => setShowBoot(false), 2000);
          return;
        }
      } catch {}
      t = setTimeout(poll, 1200);
    };
    poll();
    probeWS();
    return () => { mounted = false; if (t) clearTimeout(t); };
  }, []);

  // 立即自检（前端触发一次性检查：bootstrap状态 + WS ping + 模型健康）
  const runQuickSelfTest = async () => {
    const base = (import.meta.env?.VITE_FASTAPI_URL as string | undefined) || 'http://127.0.0.1:8007';
    setShowBoot(true);
    try {
      // refresh bootstrap status
      const r0 = await fetch(`${base}/api/bootstrap/status`).catch(() => null);
      const d0 = r0 ? await r0.json().catch(() => null) : null;
      if (d0) setBootstrap(d0);
      // model/VAD health
      const r1 = await fetch(`${base}/api/live_audio/health`).catch(() => null);
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
        const wsUrl = base.replace(/^http/i, 'ws').replace(/\/$/, '') + '/api/live_audio/ws';
        const ws = new WebSocket(wsUrl);
        const timer = setTimeout(() => { try { ws.close(); } catch {} setWsOk(false); }, 2000);
        ws.onopen = () => { try { ws.send(JSON.stringify({ type: 'ping' })); } catch {} };
        ws.onmessage = (ev) => { try { const m = JSON.parse(ev.data); if (m?.type === 'pong') { setWsOk(true); } } catch {} };
        ws.onclose = () => { clearTimeout(timer); };
        ws.onerror = () => { clearTimeout(timer); setWsOk(false); };
      } catch { setWsOk(false); }
    } catch {}
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
              欢迎回来，{user?.nickname || user?.email || '提猫主播'}！
            </div>
            <div className="text-sm timao-support-text">祝你今晚直播顺利喵～</div>
          </div>
          <div className="flex items-center gap-4">
            {/* 新增：余额展示 */}
            <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-purple-50/50 text-purple-700 shadow-sm">
              <span>💰</span>
              <span className="text-sm">余额</span>
              <span className="font-semibold">{(Number(balance ?? 0)).toFixed(2)}</span>
            </div>
            {/* 新增：钱包入口 */}
            <button
              onClick={goWallet}
              className="timao-primary-btn px-4 py-2"
              title="进入钱包充值"
            >
              打开钱包
            </button>
            <ThemeToggle />
          </div>
        </header>
        {/* 顶部资源提示条 */}
        {showBoot && (
          <div className="mx-8 -mt-2 mb-4 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span>🧩</span>
              <span>
                {bootstrap?.running ? '正在准备运行所需资源…' : '资源检查完成'}
                {bootstrap?.models ? `（模型: ${bootstrap.models.model_present ? 'OK' : '缺失'} · VAD: ${bootstrap.models.vad_present ? 'OK' : '缺失'}）` : ''}
                {wsOk != null ? ` · WS: ${wsOk ? '可用' : '不可用'}` : ''}
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
