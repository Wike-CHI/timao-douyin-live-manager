import { Outlet, Link, useLocation } from 'react-router-dom';
import ThemeToggle from '../components/ThemeToggle';

const AuthLayout = () => {
  const location = useLocation();
  const isLogin = location.pathname.includes('login');

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-gray-50 to-slate-100 flex items-stretch">
      {/* 左侧品牌区域 - 中性渐变背景 */}
      <aside className="hidden md:flex flex-col justify-between w-96 p-10 relative overflow-hidden">
        {/* 柔和渐变背景 */}
        <div className="absolute inset-0 bg-gradient-to-br from-slate-100 via-gray-50 to-slate-50" />
        <div className="absolute top-0 right-0 w-64 h-64 bg-slate-200/30 rounded-full blur-3xl" />
        <div className="absolute bottom-0 left-0 w-48 h-48 bg-gray-200/40 rounded-full blur-2xl" />

        {/* 内容 */}
        <div className="relative z-10">
          <div className="text-2xl font-semibold text-gray-900 mb-4 tracking-tight">
            提猫直播助手
          </div>
          <p className="text-gray-600 leading-relaxed text-[15px]">
            提升主播效率的桌面助手。实时弹幕洞察、AI 话术与冷场守护，一站式完成。
          </p>
        </div>
        <div className="relative z-10 text-sm text-gray-600">
          {isLogin ? (
            <>
              尚未拥有账号？
              <Link
                className="font-medium ml-2 transition-colors"
                style={{ color: 'var(--accent-main)' }}
                to="/auth/register"
              >
                立即注册
              </Link>
            </>
          ) : (
            <>
              已有账号？
              <Link
                className="font-medium ml-2 transition-colors"
                style={{ color: 'var(--accent-main)' }}
                to="/auth/login"
              >
                返回登录
              </Link>
            </>
          )}
        </div>
      </aside>

      {/* 右侧表单区域 */}
      <main className="flex-1 flex flex-col">
        <header className="flex justify-end p-6">
          <ThemeToggle />
        </header>
        <section className="flex-1 flex items-center justify-center p-6">
          <div className="w-full max-w-md">
            <Outlet />
          </div>
        </section>
      </main>
    </div>
  );
};

export default AuthLayout;
