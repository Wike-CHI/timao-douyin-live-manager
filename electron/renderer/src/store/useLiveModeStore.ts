import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

/**
 * 双模式类型定义
 * - full: 全功能模式（四宫格布局）
 * - live: 直播模式（悬浮窗）
 */
export type LiveMode = 'full' | 'live';

/**
 * 悬浮窗位置信息
 */
export interface FloatingPosition {
  x: number;
  y: number;
}

/**
 * 直播模式Store状态接口
 */
interface LiveModeState {
  // ========== 状态 ==========
  
  /** 当前模式 */
  currentMode: LiveMode;
  
  /** 悬浮窗是否可见 */
  floatingVisible: boolean;
  
  /** 悬浮窗位置（持久化到LocalStorage） */
  floatingPosition: FloatingPosition;
  
  // ========== 操作方法 ==========
  
  /**
   * 切换到直播模式
   * - 显示悬浮窗
   * - 隐藏全功能界面（可选）
   */
  switchToLiveMode: () => void;
  
  /**
   * 切换到全功能模式
   * - 显示四宫格界面
   * - 悬浮窗保留（用户可手动关闭）
   */
  switchToFullMode: () => void;
  
  /**
   * 切换悬浮窗显示/隐藏
   */
  toggleFloating: () => void;
  
  /**
   * 更新悬浮窗位置
   * @param x - X坐标
   * @param y - Y坐标
   */
  updatePosition: (x: number, y: number) => void;
  
  /**
   * 重置到默认位置
   */
  resetPosition: () => void;
}

/**
 * 计算默认位置
 * 优先显示在右下角，距离边缘20px
 */
const getDefaultPosition = (): FloatingPosition => {
  if (typeof window === 'undefined') {
    return { x: 100, y: 100 };
  }
  
  const windowWidth = 320; // 悬浮窗宽度
  const windowHeight = 240; // 悬浮窗高度
  const margin = 20;
  
  return {
    x: window.innerWidth - windowWidth - margin,
    y: window.innerHeight - windowHeight - margin,
  };
};

/**
 * 直播模式状态管理Store
 * 
 * 功能：
 * - 管理全功能模式 ↔ 直播模式的切换
 * - 管理悬浮窗的显示状态和位置
 * - 持久化悬浮窗位置到LocalStorage
 * 
 * 使用示例：
 * ```tsx
 * const { currentMode, switchToLiveMode } = useLiveModeStore();
 * 
 * <button onClick={switchToLiveMode}>切换到直播模式</button>
 * ```
 */
export const useLiveModeStore = create<LiveModeState>()(
  persist(
    (set, get) => ({
      // ========== 初始状态 ==========
      currentMode: 'full',
      floatingVisible: false,
      floatingPosition: getDefaultPosition(),
      
      // ========== 操作实现 ==========
      
      switchToLiveMode: () => {
        set({
          currentMode: 'live',
          floatingVisible: true,
        });
      },
      
      switchToFullMode: () => {
        set({
          currentMode: 'full',
          // 保持悬浮窗可见，用户可手动关闭
        });
      },
      
      toggleFloating: () => {
        set((state) => ({
          floatingVisible: !state.floatingVisible,
        }));
      },
      
      updatePosition: (x: number, y: number) => {
        // 边界检查：确保位置在屏幕内
        const maxX = window.innerWidth - 320;
        const maxY = window.innerHeight - 240;
        
        const validX = Math.max(0, Math.min(x, maxX));
        const validY = Math.max(0, Math.min(y, maxY));
        
        set({
          floatingPosition: { x: validX, y: validY },
        });
      },
      
      resetPosition: () => {
        set({
          floatingPosition: getDefaultPosition(),
        });
      },
    }),
    {
      name: 'live-mode-storage', // LocalStorage key
      storage: createJSONStorage(() => localStorage),
      // 只持久化悬浮窗位置，其他状态不持久化
      partialize: (state) => ({
        floatingPosition: state.floatingPosition,
      }),
    }
  )
);

