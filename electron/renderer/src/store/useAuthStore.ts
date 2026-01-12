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
    (set, get) => ({
      user: null,
      token: null,
      refreshToken: null,
      isPaid: true,  // 本地化模式：默认已付费
      isAuthenticated: false,
      rememberMe: true,
      setAuth: ({ user, token, refreshToken, isPaid = false }) =>
        set({ user, token, refreshToken, isPaid, isAuthenticated: true }),
      clearAuth: () =>
        set({ user: null, token: null, refreshToken: null, isPaid: false, isAuthenticated: false }),
      logout: () => {
        // 清除所有状态
        set({ user: null, token: null, refreshToken: null, isPaid: false, isAuthenticated: false });
        // 清除持久化存储（根据 rememberMe 状态清除对应的存储）
        try {
          localStorage.removeItem('timao-auth');
          sessionStorage.removeItem('timao-auth');
        } catch (e) {
          console.warn('清除认证缓存失败:', e);
        }
      },
      setPaid: (value: boolean) => set({ isPaid: value }),
      setRememberMe: (value: boolean) => set({ rememberMe: value }),
    }),
    {
      name: 'timao-auth',
      // 根据 rememberMe 状态决定使用 localStorage 还是 sessionStorage
      getStorage: () => {
        // 创建自定义存储适配器
        return {
          getItem: (name: string): string | null => {
            // 先尝试从 localStorage 读取（长期登录）
            const localValue = localStorage.getItem(name);
            if (localValue) return localValue;
            
            // 再尝试从 sessionStorage 读取（短期登录）
            const sessionValue = sessionStorage.getItem(name);
            return sessionValue;
          },
          setItem: (name: string, value: string): void => {
            try {
              const state = JSON.parse(value);
              // 根据 rememberMe 决定存储位置
              if (state.state?.rememberMe !== false) {
                // 勾选"记住我"：使用 localStorage（持久化）
                localStorage.setItem(name, value);
                // 清除 sessionStorage 中的数据
                sessionStorage.removeItem(name);
              } else {
                // 未勾选"记住我"：使用 sessionStorage（关闭浏览器后清除）
                sessionStorage.setItem(name, value);
                // 清除 localStorage 中的数据
                localStorage.removeItem(name);
              }
            } catch (e) {
              // 解析失败，默认使用 localStorage
              localStorage.setItem(name, value);
            }
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