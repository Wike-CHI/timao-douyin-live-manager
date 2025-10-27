import React, { FormEvent, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { login, type LoginResponse } from '../../services/auth';
import useAuthStore from '../../store/useAuthStore';
import TermsModal from '../../components/TermsModal';

const LoginPage = () => {
  const navigate = useNavigate();
  const { setAuth, setFirstFreeUsed } = useAuthStore();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalType, setModalType] = useState<'terms' | 'privacy'>('terms');

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response: LoginResponse = await login({ email, password });
      if (response.success) {
        // 写入认证状态
        setAuth({
          user: response.user,
          token: response.token,
          isPaid: response.isPaid,
          firstFreeUsed: response.firstFreeUsed
        });

        // 写入首次免费使用状态
        if (typeof response.firstFreeUsed === 'boolean') {
          setFirstFreeUsed(response.firstFreeUsed);
        }

        // 根据订阅状态决定跳转
        const canEnter = !response.firstFreeUsed;
        navigate(canEnter ? '/dashboard' : '/pay/subscription');
      }
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const openTermsModal = (type: 'terms' | 'privacy') => {
    setModalType(type);
    setModalOpen(true);
  };

  return (
    <div className="timao-card p-10">
      <h2 className="text-2xl font-semibold text-purple-500 mb-2 flex items-center gap-2">
        <span>😺</span>
        欢迎回来
      </h2>
      <p className="text-sm timao-support-text mb-6">使用已注册账号登录，体验 AI 直播助手。</p>
      <form onSubmit={handleSubmit} className="space-y-5" noValidate>
        <div>
          <label htmlFor="login-email" className="block text-sm font-medium timao-support-text mb-2">
            邮箱
          </label>
          <input
            id="login-email"
            type="email"
            className="timao-input"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="name@example.com"
            required
            autoComplete="email"
          />
        </div>
        <div>
          <label htmlFor="login-password" className="block text-sm font-medium timao-support-text mb-2">
            密码
          </label>
          <input
            id="login-password"
            type="password"
            className="timao-input"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="请输入密码"
            required
            autoComplete="current-password"
          />
        </div>
        {error && (
          <div className="text-sm text-red-500 bg-red-50 rounded-xl px-3 py-2" role="alert">
            {error}
          </div>
        )}
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
      
      {/* 服务条款和隐私政策链接 */}
      <div className="text-xs text-gray-500 mt-4 text-center leading-relaxed">
        登录即表示您同意我们的
        <button 
          onClick={() => openTermsModal('terms')}
          className="text-purple-500 hover:text-purple-600 underline mx-1 font-medium"
        >
          服务条款
        </button>
        和
        <button 
          onClick={() => openTermsModal('privacy')}
          className="text-purple-500 hover:text-purple-600 underline mx-1 font-medium"
        >
          隐私政策
        </button>
      </div>
      
      <TermsModal 
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        type={modalType}
      />
    </div>
  );
};

export default LoginPage;