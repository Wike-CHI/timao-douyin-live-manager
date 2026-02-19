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
    <div className="timao-card p-10">
      <h2 className="text-2xl font-semibold text-gray-900 mb-2">
        欢迎回来
      </h2>
      <p className="text-sm timao-support-text mb-6">使用已注册账号登录，体验 AI 直播助手。</p>
      <form onSubmit={handleSubmit} className="space-y-5" noValidate>
        <div className="relative" ref={dropdownRef}>
          <label htmlFor="login-email" className="block text-sm font-medium timao-support-text mb-2">
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
                className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-orange-500 transition-colors"
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
            <div className="absolute z-10 w-full mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg max-h-60 overflow-y-auto">
              {savedAccounts.map((account) => (
                <div
                  key={account.email}
                  onClick={() => handleSelectAccount(account)}
                  className="flex items-center justify-between px-4 py-3 hover:bg-orange-50 dark:hover:bg-orange-900/20 cursor-pointer transition-colors border-b border-gray-100 dark:border-gray-700 last:border-b-0"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 rounded-full bg-orange-100 dark:bg-orange-900/30 flex items-center justify-center text-orange-600 dark:text-orange-400 text-sm font-medium">
                        {(account.nickname || account.email)[0].toUpperCase()}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                          {account.nickname || account.email.split('@')[0]}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                          {account.email}
                        </p>
                      </div>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={(e) => handleDeleteAccount(account.email, e)}
                    className="ml-2 p-1 text-gray-400 hover:text-red-500 transition-colors"
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
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <input
              id="save-password"
              type="checkbox"
              checked={savePassword}
              onChange={(e) => setSavePassword(e.target.checked)}
              className="h-4 w-4 text-orange-600 focus:ring-orange-500 border-gray-300 rounded"
            />
            <label htmlFor="save-password" className="ml-2 block text-sm timao-support-text">
              保存密码
            </label>
          </div>
          <div className="flex items-center">
            <input
              id="remember-me"
              type="checkbox"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
              className="h-4 w-4 text-orange-600 focus:ring-orange-500 border-gray-300 rounded"
            />
            <label htmlFor="remember-me" className="ml-2 block text-sm timao-support-text">
              记住登录
            </label>
          </div>
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
        <Link className="text-orange-500 font-semibold ml-2" to="/auth/register">
          立即注册
        </Link>
      </div>
      
      {/* 服务条款和隐私政策链接 */}
      <div className="text-xs text-gray-500 mt-4 text-center leading-relaxed">
        登录即表示您同意我们的
        <button 
          onClick={() => openTermsModal('terms')}
          className="text-orange-500 hover:text-orange-600 underline mx-1 font-medium"
        >
          服务条款
        </button>
        和
        <button 
          onClick={() => openTermsModal('privacy')}
          className="text-orange-500 hover:text-orange-600 underline mx-1 font-medium"
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