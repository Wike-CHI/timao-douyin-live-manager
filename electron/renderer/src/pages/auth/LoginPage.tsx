import React, { FormEvent, useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { login, type LoginResponse } from '../../services/auth';
import useAuthStore from '../../store/useAuthStore';
import useAccountStore from '../../store/useAccountStore';
import { useLiveConsoleStore } from '../../store/useLiveConsoleStore';
import { cleanupLiveData } from '../../utils/dataCleanup';
import TermsModal from '../../components/TermsModal';

const LoginPage = () => {
  const navigate = useNavigate();
  const { setAuth, rememberMe, setRememberMe } = useAuthStore();
  const { saveAccount, getSortedAccounts, removeAccount } = useAccountStore();
  const { clearAllData } = useLiveConsoleStore();
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalType, setModalType] = useState<'terms' | 'privacy'>('terms');
  const [showAccountDropdown, setShowAccountDropdown] = useState(false);
  const [savePassword, setSavePassword] = useState(true);  // 是否保存密码
  
  const dropdownRef = useRef<HTMLDivElement>(null);
  const savedAccounts = getSortedAccounts();

  // 初始化：自动填充最近使用的账号
  useEffect(() => {
    const recentAccount = useAccountStore.getState().getRecentAccount();
    if (recentAccount && savePassword) {
      setEmail(recentAccount.email);
      setPassword(recentAccount.password);
    }
  }, []);

  // 点击外部关闭下拉框
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowAccountDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response: LoginResponse = await login({ 
        email, 
        password,
        remember_me: rememberMe  // 传递"记住我"状态
      });
      if (response.success) {
        // 🧹 清理旧用户的直播控制台数据，防止数据残留
        console.log('🧹 正在清理旧的直播控制台数据...');
        
        // 1. 清理 Zustand store 中的数据
        clearAllData();
        
        // 2. 清理 storage 中的临时数据
        cleanupLiveData();
        
        // 登录成功后保存账号密码
        if (savePassword) {
          saveAccount(email, password, response.user.nickname || response.user.username);
        }
        
        // 写入认证状态
        setAuth({
          user: response.user,
          token: response.token,
          refreshToken: response.refresh_token,
          isPaid: response.isPaid
        });

        console.log('✅ 登录成功，数据已清理');
        
        // 登录成功后总是跳转到主页（对未付费用户更友好）
        navigate('/dashboard', { replace: true });
      }
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  // 选择已保存的账号
  const handleSelectAccount = (account: typeof savedAccounts[0]) => {
    setEmail(account.email);
    setPassword(account.password);
    setShowAccountDropdown(false);
  };

  // 删除已保存的账号
  const handleDeleteAccount = (email: string, event: React.MouseEvent) => {
    event.stopPropagation();
    removeAccount(email);
  };

  const openTermsModal = (type: 'terms' | 'privacy') => {
    setModalType(type);
    setModalOpen(true);
  };

  return (
    <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl shadow-gray-200/50 p-10 border border-gray-100">
      <h2 className="text-2xl font-semibold text-gray-900 mb-2">
        欢迎回来
      </h2>
      <p className="text-sm text-gray-500 mb-6">使用已注册账号登录，体验 AI 直播助手。</p>
      <form onSubmit={handleSubmit} className="space-y-5" noValidate>
        <div className="relative" ref={dropdownRef}>
          <label htmlFor="login-email" className="block text-sm font-medium text-gray-600 mb-2">
            邮箱
            {savedAccounts.length > 0 && (
              <span className="text-xs text-gray-400 ml-2">
                ({savedAccounts.length} 个已保存账号)
              </span>
            )}
          </label>
          <div className="relative">
            <input
              id="login-email"
              type="email"
              className="timao-input pr-10"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              onFocus={() => savedAccounts.length > 0 && setShowAccountDropdown(true)}
              placeholder="name@example.com"
              required
              autoComplete="email"
            />
            {savedAccounts.length > 0 && (
              <button
                type="button"
                onClick={() => setShowAccountDropdown(!showAccountDropdown)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-rose-500 transition-colors"
                title="选择已保存的账号"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
            )}
          </div>

          {/* 账号下拉列表 */}
          {showAccountDropdown && savedAccounts.length > 0 && (
            <div className="absolute z-10 w-full mt-2 bg-white border border-gray-100 rounded-xl shadow-xl max-h-60 overflow-y-auto">
              {savedAccounts.map((account) => (
                <div
                  key={account.email}
                  onClick={() => handleSelectAccount(account)}
                  className="flex items-center justify-between px-4 py-3 hover:bg-rose-50 cursor-pointer transition-colors border-b border-gray-50 last:border-b-0"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-full bg-gradient-to-br from-rose-100 to-orange-100 flex items-center justify-center text-rose-600 text-sm font-medium">
                        {(account.nickname || account.email)[0].toUpperCase()}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {account.nickname || account.email.split('@')[0]}
                        </p>
                        <p className="text-xs text-gray-400 truncate">
                          {account.email}
                        </p>
                      </div>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={(e) => handleDeleteAccount(account.email, e)}
                    className="ml-2 p-1.5 text-gray-300 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                    title="删除此账号"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
        <div>
          <label htmlFor="login-password" className="block text-sm font-medium text-gray-600 mb-2">
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
        <div className="flex items-center justify-between pt-1">
          <label className="flex items-center gap-2 cursor-pointer group">
            <input
              id="save-password"
              type="checkbox"
              checked={savePassword}
              onChange={(e) => setSavePassword(e.target.checked)}
              className="w-4 h-4 rounded border-gray-300 text-rose-500 focus:ring-rose-500 focus:ring-offset-0"
            />
            <span className="text-sm text-gray-600 group-hover:text-gray-900 transition-colors">保存密码</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer group">
            <input
              id="remember-me"
              type="checkbox"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
              className="w-4 h-4 rounded border-gray-300 text-rose-500 focus:ring-rose-500 focus:ring-offset-0"
            />
            <span className="text-sm text-gray-600 group-hover:text-gray-900 transition-colors">记住登录</span>
          </label>
        </div>
        {error && (
          <div className="text-sm text-red-600 bg-red-50 rounded-xl px-4 py-3 border border-red-100" role="alert">
            {error}
          </div>
        )}
        <button
          type="submit"
          className="timao-primary-btn w-full flex items-center justify-center gap-2"
          disabled={loading}
        >
          {loading && (
            <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
          )}
          {loading ? '登录中...' : '登录'}
        </button>
      </form>
      <div className="text-sm text-gray-500 mt-6 text-center">
        还没有账号？
        <Link className="text-rose-500 font-medium ml-2 hover:text-rose-600 transition-colors" to="/auth/register">
          立即注册
        </Link>
      </div>

      {/* 服务条款和隐私政策链接 */}
      <div className="text-xs text-gray-400 mt-5 text-center leading-relaxed">
        登录即表示您同意我们的
        <button
          onClick={() => openTermsModal('terms')}
          className="text-rose-500 hover:text-rose-600 mx-1 transition-colors"
        >
          服务条款
        </button>
        和
        <button
          onClick={() => openTermsModal('privacy')}
          className="text-rose-500 hover:text-rose-600 mx-1 transition-colors"
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