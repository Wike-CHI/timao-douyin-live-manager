import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface UserInfo {
  id: string;
  email?: string;
  nickname?: string;
}

interface AuthState {
  user: UserInfo | null;
  token: string | null;
  isPaid: boolean;
  isAuthenticated: boolean;
  // 首次免费使用状态
  firstFreeUsed: boolean;
  setAuth: (payload: { user: UserInfo; token: string; isPaid?: boolean; firstFreeUsed?: boolean }) => void;
  clearAuth: () => void;
  logout: () => void;
  setPaid: (value: boolean) => void;
  setFirstFreeUsed: (value: boolean) => void;
}

const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isPaid: false,
      isAuthenticated: false,
      firstFreeUsed: false,
      setAuth: ({ user, token, isPaid = false, firstFreeUsed = false }) =>
        set({ user, token, isPaid, isAuthenticated: true, firstFreeUsed }),
      clearAuth: () =>
        set({ user: null, token: null, isPaid: false, isAuthenticated: false, firstFreeUsed: false }),
      logout: () =>
        set({ user: null, token: null, isPaid: false, isAuthenticated: false, firstFreeUsed: false }),
      setPaid: (value: boolean) => set({ isPaid: value }),
      setFirstFreeUsed: (value: boolean) => set({ firstFreeUsed: value }),
    }),
    {
      name: 'timao-auth',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isPaid: state.isPaid,
        isAuthenticated: state.isAuthenticated,
        firstFreeUsed: state.firstFreeUsed,
      }),
    }
  )
);

export default useAuthStore;
