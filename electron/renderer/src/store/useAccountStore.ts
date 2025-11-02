import { create } from 'zustand';
import { persist } from 'zustand/middleware';

/**
 * 已保存的账号信息
 */
export interface SavedAccount {
  email: string;
  password: string;  // 简单加密存储
  lastUsed: number;  // 最后使用时间戳
  nickname?: string;  // 昵称（用于显示）
}

interface AccountState {
  savedAccounts: SavedAccount[];
  
  /**
   * 添加或更新账号
   */
  saveAccount: (email: string, password: string, nickname?: string) => void;
  
  /**
   * 删除账号
   */
  removeAccount: (email: string) => void;
  
  /**
   * 获取最近使用的账号
   */
  getRecentAccount: () => SavedAccount | null;
  
  /**
   * 获取所有账号（按最后使用时间排序）
   */
  getSortedAccounts: () => SavedAccount[];
  
  /**
   * 清除所有保存的账号
   */
  clearAllAccounts: () => void;
}

/**
 * 简单的 Base64 编码（用于混淆密码，不是真正的加密）
 * 注意：这不是安全的加密方式，仅用于防止明文存储
 */
const encodePassword = (password: string): string => {
  try {
    return btoa(unescape(encodeURIComponent(password)));
  } catch (e) {
    console.error('密码编码失败:', e);
    return password;
  }
};

const decodePassword = (encoded: string): string => {
  try {
    return decodeURIComponent(escape(atob(encoded)));
  } catch (e) {
    console.error('密码解码失败:', e);
    return encoded;
  }
};

const useAccountStore = create<AccountState>()(
  persist(
    (set, get) => ({
      savedAccounts: [],
      
      saveAccount: (email: string, password: string, nickname?: string) => {
        const accounts = get().savedAccounts;
        const existingIndex = accounts.findIndex(acc => acc.email === email);
        
        const newAccount: SavedAccount = {
          email,
          password: encodePassword(password),
          lastUsed: Date.now(),
          nickname,
        };
        
        if (existingIndex >= 0) {
          // 更新现有账号
          const updatedAccounts = [...accounts];
          updatedAccounts[existingIndex] = newAccount;
          set({ savedAccounts: updatedAccounts });
        } else {
          // 添加新账号
          set({ savedAccounts: [...accounts, newAccount] });
        }
      },
      
      removeAccount: (email: string) => {
        set(state => ({
          savedAccounts: state.savedAccounts.filter(acc => acc.email !== email),
        }));
      },
      
      getRecentAccount: () => {
        const accounts = get().savedAccounts;
        if (accounts.length === 0) return null;
        
        // 返回最近使用的账号
        const sorted = [...accounts].sort((a, b) => b.lastUsed - a.lastUsed);
        const recent = sorted[0];
        
        return {
          ...recent,
          password: decodePassword(recent.password),
        };
      },
      
      getSortedAccounts: () => {
        const accounts = get().savedAccounts;
        // 按最后使用时间排序
        return [...accounts]
          .sort((a, b) => b.lastUsed - a.lastUsed)
          .map(acc => ({
            ...acc,
            password: decodePassword(acc.password),
          }));
      },
      
      clearAllAccounts: () => {
        set({ savedAccounts: [] });
      },
    }),
    {
      name: 'timao-saved-accounts',
      // 始终使用 localStorage，即使退出登录也保留账号
    }
  )
);

export default useAccountStore;
