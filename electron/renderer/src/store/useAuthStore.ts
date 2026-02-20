import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface UserInfo {
  id: string;
  username: string;
  email: string;
  nickname?: string;
  avatar_url?: string;
  role: string;
  status: string;
  email_verified: boolean;
  phone_verified: boolean;
  created_at: string;
}

/**
 * 认证状态管理（简化版 - 本地桌面应用模式）
 *
 * 默认已认证，使用本地用户身份
 */
interface AuthState {
  user: UserInfo | null;
  token: string | null;
  refreshToken: string | null;
  isPaid: boolean;
  isAuthenticated: boolean;
  rememberMe: boolean;
  setAuth: (payload: { user: UserInfo; token: string; refreshToken?: string; isPaid?: boolean }) => void;
  clearAuth: () => void;
  logout: () => void;
  setPaid: (value: boolean) => void;
  setRememberMe: (value: boolean) => void;
}

// 默认本地用户
const DEFAULT_LOCAL_USER: UserInfo = {
  id: 'local_user',
  username: 'local_user',
  email: 'local@localhost',
  nickname: '本地用户',
  role: 'user',
  status: 'active',
  email_verified: true,
  phone_verified: false,
  created_at: new Date().toISOString(),
};

const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // 默认已认证（本地桌面应用模式）
      user: DEFAULT_LOCAL_USER,
      token: 'local_token',
      refreshToken: null,
      isPaid: true,  // 本地应用默认已付费
      isAuthenticated: true,  // 默认已认证
      rememberMe: true,
      setAuth: ({ user, token, refreshToken, isPaid = false }) =>
        set({ user, token, refreshToken, isPaid, isAuthenticated: true }),
      clearAuth: () =>
        // 本地模式不清除认证状态
        set({ user: DEFAULT_LOCAL_USER, token: 'local_token', refreshToken: null, isPaid: true, isAuthenticated: true }),
      logout: () => {
        // 本地模式保持认证状态
        set({ user: DEFAULT_LOCAL_USER, token: 'local_token', refreshToken: null, isPaid: true, isAuthenticated: true });
      },
      setPaid: (value: boolean) => set({ isPaid: true }),  // 本地模式始终为已付费
      setRememberMe: (value: boolean) => set({ rememberMe: value }),
    }),
    {
      name: 'timao-auth',
      getStorage: () => {
        return {
          getItem: (name: string): string | null => {
            const localValue = localStorage.getItem(name);
            if (localValue) return localValue;
            const sessionValue = sessionStorage.getItem(name);
            return sessionValue;
          },
          setItem: (name: string, value: string): void => {
            localStorage.setItem(name, value);
          },
          removeItem: (name: string): void => {
            localStorage.removeItem(name);
            sessionStorage.removeItem(name);
          },
        };
      },
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        refreshToken: state.refreshToken,
        isPaid: state.isPaid,
        isAuthenticated: state.isAuthenticated,
        rememberMe: state.rememberMe,
      }),
    }
  )
);

export default useAuthStore;
