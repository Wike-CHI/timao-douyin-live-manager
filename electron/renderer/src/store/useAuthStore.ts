import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface UserInfo {
  id: number;  // 修改为number类型，与后端保持一致
  username: string;
  email: string;
  nickname?: string;
  avatar_url?: string;
  role: string;
  status: string;
  email_verified: boolean;
  phone_verified: boolean;
  created_at: string; // 日期时间在JSON中会转换为字符串
}

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

const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      refreshToken: null,
      isPaid: false,
      isAuthenticated: false,
      rememberMe: true,
      setAuth: ({ user, token, refreshToken, isPaid = false }) =>
        set({ user, token, refreshToken, isPaid, isAuthenticated: true }),
      clearAuth: () =>
        set({ user: null, token: null, refreshToken: null, isPaid: false, isAuthenticated: false }),
      logout: () =>
        set({ user: null, token: null, refreshToken: null, isPaid: false, isAuthenticated: false }),
      setPaid: (value: boolean) => set({ isPaid: value }),
      setRememberMe: (value: boolean) => set({ rememberMe: value }),
    }),
    {
      name: 'timao-auth',
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