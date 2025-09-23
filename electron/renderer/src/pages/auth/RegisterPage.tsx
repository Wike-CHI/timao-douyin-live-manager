import { FormEvent, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { register } from '../../services/auth';

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

  const handleChange = (key: string, value: string) => {
    setFormData((prev) => ({ ...prev, [key]: value }));
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(false);

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
      });
      if (response.success) {
        setSuccess(true);
        setTimeout(() => navigate('/auth/login', { replace: true }), 1200);
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
        <span>🐾</span>
        注册提猫账号
      </h2>
      <p className="text-sm timao-support-text mb-6">注册后即可体验直播管理与 AI 助手功能。</p>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium timao-support-text mb-2">邮箱</label>
          <input
            type="email"
            value={formData.email}
            onChange={(e) => handleChange('email', e.target.value)}
            className="timao-input"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium timao-support-text mb-2">昵称</label>
          <input
            value={formData.nickname}
            onChange={(e) => handleChange('nickname', e.target.value)}
            className="timao-input"
            placeholder="直播间昵称"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium timao-support-text mb-2">密码</label>
          <input
            type="password"
            value={formData.password}
            onChange={(e) => handleChange('password', e.target.value)}
            className="timao-input"
            required
            minLength={6}
          />
        </div>
        <div>
          <label className="block text-sm font-medium timao-support-text mb-2">确认密码</label>
          <input
            type="password"
            value={formData.confirmPassword}
            onChange={(e) => handleChange('confirmPassword', e.target.value)}
            className="timao-input"
            required
            minLength={6}
          />
        </div>
        {error && <div className="text-sm text-red-500 bg-red-50 rounded-xl px-3 py-2">{error}</div>}
        {success && <div className="text-sm text-green-500 bg-green-50 rounded-xl px-3 py-2">注册成功，即将跳转登录</div>}
        <button type="submit" className="timao-primary-btn w-full" disabled={loading}>
          {loading ? '注册中...' : '注册'}
        </button>
      </form>
      <div className="text-sm timao-support-text mt-6">
        已有账号？
        <Link className="text-purple-500 font-semibold ml-2" to="/auth/login">
          立即登录
        </Link>
      </div>
    </div>
  );
};

export default RegisterPage;
