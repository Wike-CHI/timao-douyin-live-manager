# 直播模式组件

> **创建日期**: 2025-11-16  
> **状态**: Phase 1 完成 ✅  
> **审查人**: 叶维哲

---

## 📋 功能概述

提供直播控制台的双模式支持：
- **全功能模式**: 完整的四宫格布局（现有功能）
- **直播模式**: 极简悬浮窗，最小化干扰

---

## 🗂️ 文件结构

```
electron/renderer/src/
├── store/
│   └── useLiveModeStore.ts        # 模式管理Store
├── components/
│   └── live-mode/
│       ├── index.ts                # 组件导出
│       ├── FloatingWindow.tsx      # 悬浮窗主组件
│       └── README.md               # 本文档
└── pages/dashboard/
    └── LiveConsolePage.tsx         # 已集成模式切换
```

---

## 🚀 Phase 1 完成内容

### ✅ 1.1 模式管理Store (useLiveModeStore)

**功能**:
- 管理当前模式（全功能/直播）
- 管理悬浮窗显示状态
- 管理悬浮窗位置（带边界检查）
- 位置持久化到LocalStorage

**使用示例**:
```typescript
import { useLiveModeStore } from '@/store/useLiveModeStore';

function MyComponent() {
  const { 
    currentMode, 
    floatingVisible,
    switchToLiveMode, 
    switchToFullMode,
    toggleFloating,
    updatePosition 
  } = useLiveModeStore();
  
  return (
    <div>
      <p>当前模式: {currentMode}</p>
      <button onClick={switchToLiveMode}>切换到直播模式</button>
      <button onClick={toggleFloating}>显示/隐藏悬浮窗</button>
    </div>
  );
}
```

### ✅ 1.2 悬浮窗基础组件 (FloatingWindow)

**功能**:
- 固定定位，可拖拽移动
- 显示三种类型信息（AI分析、话术、数据统计）
- Tab切换
- 基础样式（半透明背景、圆角、阴影）

**Props接口**:
```typescript
interface FloatingWindowProps {
  onClose: () => void;  // 关闭回调
}
```

**使用示例**:
```typescript
import { FloatingWindow } from '@/components/live-mode';

function MyPage() {
  const [visible, setVisible] = useState(true);
  
  return (
    <div>
      {visible && (
        <FloatingWindow onClose={() => setVisible(false)} />
      )}
    </div>
  );
}
```

### ✅ 1.3 集成到LiveConsolePage

**修改内容**:
1. 导入FloatingWindow组件和useLiveModeStore
2. 在顶部控制栏添加"直播模式"切换按钮（仅运行中显示）
3. 条件渲染悬浮窗（根据floatingVisible状态）

**效果**:
- 点击"直播模式"按钮显示悬浮窗
- 悬浮窗右上角可切换回全功能模式
- 悬浮窗右上角可关闭

---

## 🎨 组件结构

### FloatingWindow 结构

```
┌──────────────────────────────────┐
│  [标题] 📊 提猫直播助手  [⇄] [×]  │  ← 标题栏（可拖拽）
├──────────────────────────────────┤
│                                  │
│    [Tab内容显示区域]              │  ← 主内容区
│    - AI分析                       │
│    - 话术建议                     │
│    - 数据统计                     │
│                                  │
├──────────────────────────────────┤
│  [🤖 AI] [💬 话术] [📈 数据]      │  ← Tab切换栏
└──────────────────────────────────┘

尺寸: 320px × 240px (最小高度)
位置: 固定定位，可拖拽
样式: 半透明背景，毛玻璃效果
```

---

## 🔧 技术实现

### 状态管理

使用Zustand + persist中间件：

```typescript
// Store结构
{
  currentMode: 'full' | 'live',
  floatingVisible: boolean,
  floatingPosition: { x: number, y: number },
  
  // 持久化配置
  persist: {
    name: 'live-mode-storage',
    partialize: (state) => ({ 
      floatingPosition: state.floatingPosition 
    })
  }
}
```

### 拖拽实现

使用原生MouseEvent API：

```typescript
// 1. mousedown - 记录拖拽起始点
// 2. mousemove - 计算新位置（带边界限制）
// 3. mouseup   - 保存位置到store
```

### 边界检查

```typescript
// 限制在屏幕内
const maxX = window.innerWidth - windowWidth;
const maxY = window.innerHeight - windowHeight;

newX = Math.max(0, Math.min(newX, maxX));
newY = Math.max(0, Math.min(newY, maxY));
```

---

## ✅ 验收标准

### 功能验收

- [x] Store可以创建和访问
- [x] 状态切换正常（full ↔ live）
- [x] LocalStorage持久化工作
- [x] TypeScript类型检查通过
- [x] 组件可以渲染
- [x] 显示在正确位置
- [x] 基础样式正确
- [x] 可以显示/隐藏
- [x] 切换按钮显示正确
- [x] 不影响现有功能

### 代码质量

- [x] 无ESLint错误
- [x] 无TypeScript类型错误
- [x] 变量命名清晰
- [x] 代码注释完整
- [x] 符合项目规范

---

## 🔜 下一步（Phase 2）

### 待实现功能

1. **完善拖拽功能**
   - 优化拖拽性能
   - 添加拖拽边界检查
   
2. **边缘吸附**
   - 释放鼠标时自动吸附到边缘
   - 平滑过渡动画
   
3. **响应式适配**
   - 监听窗口resize
   - 自动调整位置

---

## 📚 参考文档

- [直播控制台双模式设计文档](../../../docs/产品使用手册/直播控制台双模式设计文档.md)
- [悬浮窗设计代码实现文档](../../../docs/架构设计与规划/悬浮窗设计代码实现文档.md)

