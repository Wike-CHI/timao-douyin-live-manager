import React, { FormEvent, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { register } from '../../services/auth';
import TermsModal from '../../components/TermsModal';

const RegisterPage = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    nickname: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [agreeTerms, setAgreeTerms] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalType, setModalType] = useState<'terms' | 'privacy'>('terms');

  const handleChange = (key: string, value: string) => {
    setFormData((prev) => ({ ...prev, [key]: value }));
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(false);

    if (!agreeTerms) {
      setError('请先阅读并同意服务条款和隐私政策');
      setLoading(false);
      return;
    }

    if (formData.password !== formData.confirmPassword) {
      setError('两次输入的密码不一致');
      setLoading(false);
      return;
    }

    try {
      const response = await register({
        email: formData.email,
        password: formData.password,
        nickname: formData.nickname,
        username: formData.nickname || formData.email.split('@')[0],
      });
      if (response?.success) {
        setSuccess(true);
        setTimeout(() => navigate('/auth/login', { replace: true }), 1200);
      } else {
        setError('注册响应异常，请稍后重试');
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
    <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl shadow-gray-200/50 p-10 border border-gray-100">
      <h2 className="text-2xl font-semibold text-gray-900 mb-2">
        注册提猫账号
      </h2>
      <p className="text-sm text-gray-500 mb-6">注册后即可体验直播管理与 AI 助手功能。</p>
      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        <div>
          <label htmlFor="register-email" className="block text-sm font-medium text-gray-600 mb-2">
            邮箱
          </label>
          <input
            id="register-email"
            type="email"
            value={formData.email}
            onChange={(e) => handleChange('email', e.target.value)}
            className="timao-input"
            required
            autoComplete="email"
          />
        </div>
        <div>
          <label htmlFor="register-nickname" className="block text-sm font-medium text-gray-600 mb-2">
            昵称
          </label>
          <input
            id="register-nickname"
            value={formData.nickname}
            onChange={(e) => handleChange('nickname', e.target.value)}
            className="timao-input"
            placeholder="直播间昵称"
            required
            autoComplete="nickname"
          />
        </div>
        <div>
          <label htmlFor="register-password" className="block text-sm font-medium text-gray-600 mb-2">
            密码
          </label>
          <input
            id="register-password"
            type="password"
            value={formData.password}
            onChange={(e) => handleChange('password', e.target.value)}
            className="timao-input"
            required
            minLength={6}
            autoComplete="new-password"
          />
        </div>
        <div>
          <label htmlFor="register-confirm-password" className="block text-sm font-medium text-gray-600 mb-2">
            确认密码
          </label>
          <input
            id="register-confirm-password"
            type="password"
            value={formData.confirmPassword}
            onChange={(e) => handleChange('confirmPassword', e.target.value)}
            className="timao-input"
            required
            minLength={6}
            autoComplete="new-password"
          />
        </div>

        {/* 同意条款复选框 */}
        <label className="flex items-start gap-3 py-3 cursor-pointer group">
          <input
            id="agree-terms"
            type="checkbox"
            checked={agreeTerms}
            onChange={(e) => setAgreeTerms(e.target.checked)}
            className="mt-0.5 w-4 h-4 rounded border-gray-300 text-rose-500 focus:ring-rose-500 focus:ring-offset-0"
            required
          />
          <span className="text-sm text-gray-600 leading-relaxed">
            我已阅读并同意
            <button
              type="button"
              onClick={() => openTermsModal('terms')}
              className="text-rose-500 hover:text-rose-600 mx-1 transition-colors"
            >
              《服务条款》
            </button>
            和
            <button
              type="button"
              onClick={() => openTermsModal('privacy')}
              className="text-rose-500 hover:text-rose-600 mx-1 transition-colors"
            >
              《隐私政策》
            </button>
          </span>
        </label>

        {error && (
          <div className="text-sm text-red-600 bg-red-50 rounded-xl px-4 py-3 border border-red-100" role="alert">
            {error}
          </div>
        )}
        {success && (
          <div className="text-sm text-emerald-600 bg-emerald-50 rounded-xl px-4 py-3 border border-emerald-100" role="status">
            注册成功，即将跳转登录
          </div>
        )}
        <button
          type="submit"
          className="timao-primary-btn w-full flex items-center justify-center gap-2"
          disabled={loading || !agreeTerms}
        >
          {loading && (
            <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
          )}
          {loading ? '注册中...' : '注册'}
        </button>
      </form>
      <div className="text-sm text-gray-500 mt-6 text-center">
        已有账号？
        <Link className="text-rose-500 font-medium ml-2 hover:text-rose-600 transition-colors" to="/auth/login">
          立即登录
        </Link>
      </div>

      <TermsModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        type={modalType}
      />
    </div>
  );
};

export default RegisterPage;