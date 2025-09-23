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
  // 钱包相关
  balance: number;
  firstFreeUsed: boolean;
  setAuth: (payload: { user: UserInfo; token: string; isPaid?: boolean; balance?: number; firstFreeUsed?: boolean }) => void;
  clearAuth: () => void;
  logout: () => void;
  setPaid: (value: boolean) => void;
  setBalance: (value: number) => void;
  setFirstFreeUsed: (value: boolean) => void;
}

const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isPaid: false,
      isAuthenticated: false,
      balance: 0,
      firstFreeUsed: false,
      setAuth: ({ user, token, isPaid = false, balance = 0, firstFreeUsed = false }) =>
        set({ user, token, isPaid, isAuthenticated: true, balance, firstFreeUsed }),
      clearAuth: () =>
        set({ user: null, token: null, isPaid: false, isAuthenticated: false, balance: 0, firstFreeUsed: false }),
      logout: () =>
        set({ user: null, token: null, isPaid: false, isAuthenticated: false, balance: 0, firstFreeUsed: false }),
      setPaid: (value: boolean) => set({ isPaid: value }),
      setBalance: (value: number) => set({ balance: value }),
      setFirstFreeUsed: (value: boolean) => set({ firstFreeUsed: value }),
    }),
    {
      name: 'timao-auth',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isPaid: state.isPaid,
        isAuthenticated: state.isAuthenticated,
        balance: state.balance,
        firstFreeUsed: state.firstFreeUsed,
      }),
    }
  )
);

export default useAuthStore;
