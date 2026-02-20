import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import useAuthStore from '../store/useAuthStore';

/**
 * 认证拦截器Hook（简化版 - 本地桌面应用模式）
 *
 * 不再进行token验证，本地模式始终已认证
 */
const useAuthInterceptor = () => {
  const navigate = useNavigate();
  const { isAuthenticated, token, clearAuth } = useAuthStore();

  // 本地模式：不进行任何认证检查
  useEffect(() => {
    // 空操作，保持hook结构兼容
  }, []);
};

export default useAuthInterceptor;
