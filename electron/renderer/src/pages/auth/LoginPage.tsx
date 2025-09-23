import { FormEvent, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { login } from '../../services/auth';
import useAuthStore from '../../store/useAuthStore';

const LoginPage = () => {
  const navigate = useNavigate();
  const setAuth = useAuthStore((state) => state.setAuth);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await login({ email, password });
      if (response.success) {
        setAuth({ user: response.user, token: response.token, isPaid: response.isPaid });
        navigate('/pay/verify');
      }
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="timao-card p-10">
      <h2 className="text-2xl font-semibold text-purple-500 mb-2 flex items-center gap-2">
        <span>😺</span>
        欢迎回来
      </h2>
      <p className="text-sm timao-support-text mb-6">使用已注册账号登录，体验 AI 直播助手。</p>
      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label className="block text-sm font-medium timao-support-text mb-2">邮箱</label>
          <input
            type="email"
            className="timao-input"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="name@example.com"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium timao-support-text mb-2">密码</label>
          <input
            type="password"
            className="timao-input"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="请输入密码"
            required
          />
        </div>
        {error && <div className="text-sm text-red-500 bg-red-50 rounded-xl px-3 py-2">{error}</div>}
        <button type="submit" className="timao-primary-btn w-full" disabled={loading}>
          {loading ? '登录中...' : '登录'}
        </button>
      </form>
      <div className="text-sm timao-support-text mt-6">
        还没有账号？
        <Link className="text-purple-500 font-semibold ml-2" to="/auth/register">
          立即注册
        </Link>
      </div>
    </div>
  );
};

export default LoginPage;
