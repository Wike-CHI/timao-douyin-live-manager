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
  setAuth: (payload: { user: UserInfo; token: string; isPaid: boolean }) => void;
  clearAuth: () => void;
  logout: () => void;
  setPaid: (value: boolean) => void;
}

const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isPaid: false,
      isAuthenticated: false,
      setAuth: ({ user, token, isPaid }) =>
        set({ user, token, isPaid, isAuthenticated: true }),
      clearAuth: () =>
        set({ user: null, token: null, isPaid: false, isAuthenticated: false }),
      logout: () =>
        set({ user: null, token: null, isPaid: false, isAuthenticated: false }),
      setPaid: (value: boolean) => set({ isPaid: value }),
    }),
    {
      name: 'timao-auth',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isPaid: state.isPaid,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

export default useAuthStore;
