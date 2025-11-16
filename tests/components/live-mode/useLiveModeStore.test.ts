/**
 * useLiveModeStore 单元测试
 * 
 * 测试范围：
 * - Store初始状态
 * - 模式切换功能
 * - 悬浮窗显示/隐藏
 * - 位置更新和持久化
 */

import { renderHook, act } from '@testing-library/react';
import { useLiveModeStore } from '../../../electron/renderer/src/store/useLiveModeStore';

describe('useLiveModeStore', () => {
  beforeEach(() => {
    // 清理LocalStorage
    localStorage.clear();
  });
  
  describe('初始状态', () => {
    it('应该有正确的初始值', () => {
      const { result } = renderHook(() => useLiveModeStore());
      
      expect(result.current.currentMode).toBe('full');
      expect(result.current.floatingVisible).toBe(false);
      expect(result.current.floatingPosition).toMatchObject({
        x: expect.any(Number),
        y: expect.any(Number),
      });
    });
  });
  
  describe('模式切换', () => {
    it('switchToLiveMode应该切换到直播模式并显示悬浮窗', () => {
      const { result } = renderHook(() => useLiveModeStore());
      
      act(() => {
        result.current.switchToLiveMode();
      });
      
      expect(result.current.currentMode).toBe('live');
      expect(result.current.floatingVisible).toBe(true);
    });
    
    it('switchToFullMode应该切换到全功能模式', () => {
      const { result } = renderHook(() => useLiveModeStore());
      
      // 先切换到直播模式
      act(() => {
        result.current.switchToLiveMode();
      });
      
      // 再切换回全功能模式
      act(() => {
        result.current.switchToFullMode();
      });
      
      expect(result.current.currentMode).toBe('full');
      // 悬浮窗保持可见（用户可手动关闭）
    });
    
    it('toggleFloating应该切换悬浮窗显示状态', () => {
      const { result } = renderHook(() => useLiveModeStore());
      
      const initialVisible = result.current.floatingVisible;
      
      act(() => {
        result.current.toggleFloating();
      });
      
      expect(result.current.floatingVisible).toBe(!initialVisible);
      
      act(() => {
        result.current.toggleFloating();
      });
      
      expect(result.current.floatingVisible).toBe(initialVisible);
    });
  });
  
  describe('位置管理', () => {
    it('updatePosition应该更新悬浮窗位置', () => {
      const { result } = renderHook(() => useLiveModeStore());
      
      // 模拟窗口尺寸
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 1920,
      });
      Object.defineProperty(window, 'innerHeight', {
        writable: true,
        configurable: true,
        value: 1080,
      });
      
      act(() => {
        result.current.updatePosition(100, 200);
      });
      
      expect(result.current.floatingPosition).toEqual({ x: 100, y: 200 });
    });
    
    it('updatePosition应该限制位置在屏幕内', () => {
      const { result } = renderHook(() => useLiveModeStore());
      
      // 模拟窗口尺寸
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 1920,
      });
      Object.defineProperty(window, 'innerHeight', {
        writable: true,
        configurable: true,
        value: 1080,
      });
      
      // 尝试设置超出边界的位置
      act(() => {
        result.current.updatePosition(-100, -100);
      });
      
      // 应该被限制到0,0
      expect(result.current.floatingPosition.x).toBeGreaterThanOrEqual(0);
      expect(result.current.floatingPosition.y).toBeGreaterThanOrEqual(0);
      
      // 尝试设置超出右下边界的位置
      act(() => {
        result.current.updatePosition(5000, 5000);
      });
      
      // 应该被限制在屏幕内
      expect(result.current.floatingPosition.x).toBeLessThanOrEqual(1920 - 320);
      expect(result.current.floatingPosition.y).toBeLessThanOrEqual(1080 - 240);
    });
    
    it('resetPosition应该重置到默认位置', () => {
      const { result } = renderHook(() => useLiveModeStore());
      
      // 先移动到某个位置
      act(() => {
        result.current.updatePosition(100, 100);
      });
      
      // 重置
      act(() => {
        result.current.resetPosition();
      });
      
      // 应该回到默认位置（右下角附近）
      expect(result.current.floatingPosition).toMatchObject({
        x: expect.any(Number),
        y: expect.any(Number),
      });
    });
  });
  
  describe('位置持久化', () => {
    it('应该持久化悬浮窗位置到LocalStorage', () => {
      const { result } = renderHook(() => useLiveModeStore());
      
      act(() => {
        result.current.updatePosition(150, 250);
      });
      
      // 检查LocalStorage
      const saved = localStorage.getItem('live-mode-storage');
      expect(saved).toBeTruthy();
      
      if (saved) {
        const parsed = JSON.parse(saved);
        expect(parsed.state.floatingPosition).toEqual({ x: 150, y: 250 });
      }
    });
    
    it('应该从LocalStorage恢复位置', () => {
      // 预设LocalStorage数据
      const savedData = {
        state: {
          floatingPosition: { x: 300, y: 400 },
        },
        version: 0,
      };
      localStorage.setItem('live-mode-storage', JSON.stringify(savedData));
      
      // 创建新的hook实例
      const { result } = renderHook(() => useLiveModeStore());
      
      // 应该恢复保存的位置
      expect(result.current.floatingPosition).toEqual({ x: 300, y: 400 });
    });
  });
});

