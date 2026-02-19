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
    <div className="timao-card p-10">
      <h2 className="text-2xl font-semibold text-gray-900 mb-2">
        注册提猫账号
      </h2>
      <p className="text-sm timao-support-text mb-6">注册后即可体验直播管理与 AI 助手功能。</p>
      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        <div>
          <label htmlFor="register-email" className="block text-sm font-medium timao-support-text mb-2">
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
          <label htmlFor="register-nickname" className="block text-sm font-medium timao-support-text mb-2">
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
          <label htmlFor="register-password" className="block text-sm font-medium timao-support-text mb-2">
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
          <label htmlFor="register-confirm-password" className="block text-sm font-medium timao-support-text mb-2">
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
        <div className="flex items-start space-x-3 py-3">
          <input
            id="agree-terms"
            type="checkbox"
            checked={agreeTerms}
            onChange={(e) => setAgreeTerms(e.target.checked)}
            className="mt-1 w-4 h-4 text-orange-600 bg-gray-100 border-gray-300 rounded focus:ring-orange-500 focus:ring-2"
            required
          />
          <label htmlFor="agree-terms" className="text-sm text-gray-700 leading-relaxed">
            我已阅读并同意
            <button 
              type="button"
              onClick={() => openTermsModal('terms')}
              className="text-orange-500 hover:text-purple-600 underline mx-1 font-medium"
            >
              《服务条款》
            </button>
            和
            <button 
              type="button"
              onClick={() => openTermsModal('privacy')}
              className="text-orange-500 hover:text-purple-600 underline mx-1 font-medium"
            >
              《隐私政策》
            </button>
          </label>
        </div>
        
        {error && (
          <div className="text-sm text-red-500 bg-red-50 rounded-xl px-3 py-2" role="alert">
            {error}
          </div>
        )}
        {success && (
          <div className="text-sm text-green-500 bg-green-50 rounded-xl px-3 py-2" role="status">
            注册成功，即将跳转登录
          </div>
        )}
        <button type="submit" className="timao-primary-btn w-full" disabled={loading || !agreeTerms}>
          {loading ? '注册中...' : '注册'}
        </button>
      </form>
      <div className="text-sm timao-support-text mt-6">
        已有账号？
        <Link className="text-orange-500 font-semibold ml-2" to="/auth/login">
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