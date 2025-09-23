import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import ThemeToggle from '../components/ThemeToggle';
import useAuthStore from '../store/useAuthStore';
import logoUrl from '../assets/logo.jpg';

const navItems = [
  { to: '/dashboard', label: '总览', icon: '📊' },
  { to: '/live', label: '直播控制台', icon: '🎤' },
  { to: '/reports', label: '直播报告', icon: '📑' },
  { to: '/about', label: '关于', icon: 'ℹ️' },
];

const MainLayout = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  const handleLogout = () => {
    logout();
    navigate('/auth/login');
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
            <ThemeToggle />
          </div>
        </header>
        <section className="flex-1 px-8 pb-12">
          <Outlet />
        </section>
      </main>
    </div>
  );
};

export default MainLayout;
