import { Outlet, Link, useLocation } from 'react-router-dom';
import ThemeToggle from '../components/ThemeToggle';

const AuthLayout = () => {
  const location = useLocation();
  const isLogin = location.pathname.includes('login');

  return (
    <div className="min-h-screen timao-surface flex items-stretch">
      <aside className="hidden md:flex flex-col justify-between w-96 p-10 timao-card relative">
        <div>
          <div className="text-2xl font-semibold text-gray-900 mb-4">提猫直播助手</div>
          <p className="text-gray-500 leading-relaxed">
            提升主播效率的桌面助手。实时弹幕洞察、AI 话术与冷场守护，一站式完成。
          </p>
        </div>
        <div className="text-sm text-gray-500">
          尚未拥有账号？
          {isLogin ? (
            <Link className="text-orange-500 font-medium ml-2" to="/auth/register">
              立即注册
            </Link>
          ) : (
            <Link className="text-orange-500 font-medium ml-2" to="/auth/login">
              返回登录
            </Link>
          )}
        </div>
      </aside>
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
