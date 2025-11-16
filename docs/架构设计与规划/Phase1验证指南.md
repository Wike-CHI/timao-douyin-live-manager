# Phase 1 功能验证指南

> **创建日期**: 2025-11-16  
> **用途**: 快速验证Phase 1实现的功能是否正常工作

---

## 🎯 验证目标

确保以下功能正常：
- ✅ 模式切换按钮显示
- ✅ 悬浮窗可以显示/隐藏
- ✅ 悬浮窗可以拖拽
- ✅ Tab可以切换
- ✅ 数据可以显示
- ✅ 位置可以持久化

---

## 🚀 启动应用

### 1. 启动后端服务

```bash
# 在项目根目录
cd server
python app.py
```

### 2. 启动前端开发服务

```bash
# 在项目根目录
cd electron/renderer
npm run dev
```

### 3. 启动Electron应用

```bash
# 在项目根目录
npm run electron
```

---

## ✅ 验证步骤

### 步骤1: 检查初始状态

**操作**: 打开应用，进入"直播控制台"页面

**预期结果**:
- ✅ 看到熟悉的四宫格布局（全功能模式）
- ✅ "直播模式"按钮**不显示**（因为服务未运行）
- ✅ 无任何悬浮窗显示

**如果失败**:
- 检查是否正确导入了useLiveModeStore
- 检查console是否有错误

---

### 步骤2: 启动直播转写服务

**操作**: 
1. 在输入框输入直播地址，例如：`https://live.douyin.com/123456`
2. 点击"开始转写"按钮
3. 等待服务启动成功

**预期结果**:
- ✅ 按钮状态变为"运行中"
- ✅ 看到"📱 直播模式"按钮出现在停止按钮右侧
- ✅ 按钮颜色为紫色边框（bg-purple-50 text-purple-600）

**如果失败**:
- 检查isRunning状态是否正确
- 检查currentMode是否为'full'
- 查看React DevTools中的useLiveModeStore状态

---

### 步骤3: 切换到直播模式

**操作**: 点击"📱 直播模式"按钮

**预期结果**:
- ✅ 出现悬浮窗（右下角附近）
- ✅ 悬浮窗标题为"📊 提猫直播助手"
- ✅ 悬浮窗有半透明背景和毛玻璃效果
- ✅ 默认显示AI分析Tab（🤖 AI高亮）
- ✅ "直播模式"按钮消失（因为currentMode变为'live'）

**如果失败**:
- 检查floatingVisible状态是否为true
- 检查FloatingWindow组件是否正确渲染
- 查看console错误信息

---

### 步骤4: 测试悬浮窗拖拽

**操作**: 
1. 鼠标放在悬浮窗标题栏（"📊 提猫直播助手"）
2. 按住鼠标左键
3. 拖动到屏幕其他位置
4. 释放鼠标

**预期结果**:
- ✅ 鼠标光标变为move/grabbing样式
- ✅ 悬浮窗跟随鼠标移动
- ✅ 不会拖出屏幕边界
- ✅ 释放后位置固定

**如果失败**:
- 检查handleMouseDown是否绑定正确
- 检查useEffect中的事件监听是否正常
- 查看console是否有拖拽相关错误

---

### 步骤5: 测试Tab切换

**操作**: 
1. 点击底部的"💬 话术"Tab
2. 点击底部的"📈 数据"Tab
3. 再点击"🤖 AI"Tab

**预期结果**:
- ✅ 每次点击后，对应Tab高亮（紫色背景）
- ✅ 内容区显示对应的内容
- ✅ AI Tab显示氛围评分和建议
- ✅ 话术Tab显示话术文本和复制按钮
- ✅ 数据Tab显示在线人数、礼物价值等

**如果失败**:
- 检查currentTab状态是否更新
- 检查条件渲染逻辑
- 查看数据是否正确从store获取

---

### 步骤6: 测试数据显示

**操作**: 等待直播间有数据（弹幕、礼物、AI分析等）

**预期结果**:
- ✅ AI Tab显示最新的AI分析结果
- ✅ 话术Tab显示最新的生成话术
- ✅ 数据Tab显示实时统计数据
- ✅ 数据为空时显示友好提示（📭 + 提示文字）

**如果失败**:
- 检查useLiveConsoleStore数据是否正常
- 检查useMemo依赖数组
- 查看数据提取逻辑

---

### 步骤7: 测试复制功能

**操作**: 
1. 切换到"话术"Tab
2. 点击"📋 复制话术"按钮

**预期结果**:
- ✅ 按钮文字变为"✓ 已复制"
- ✅ 按钮颜色变为绿色
- ✅ 2秒后自动恢复
- ✅ 剪贴板中有话术文本

**如果失败**:
- 检查navigator.clipboard API是否可用
- 检查copySuccess状态更新
- 尝试手动粘贴验证

---

### 步骤8: 测试切换回全功能模式

**操作**: 点击悬浮窗右上角的"⇄"按钮

**预期结果**:
- ✅ 四宫格界面重新显示
- ✅ currentMode变为'full'
- ✅ "直播模式"按钮重新出现
- ✅ 悬浮窗保持显示（不自动关闭）

**如果失败**:
- 检查switchToFullMode是否调用
- 检查条件渲染逻辑

---

### 步骤9: 测试关闭悬浮窗

**操作**: 点击悬浮窗右上角的"×"按钮

**预期结果**:
- ✅ 悬浮窗消失
- ✅ floatingVisible变为false
- ✅ 四宫格界面保持显示

**如果失败**:
- 检查toggleFloating是否调用
- 检查onClose回调绑定

---

### 步骤10: 测试位置持久化

**操作**: 
1. 拖拽悬浮窗到某个位置（例如左上角）
2. 关闭Electron应用
3. 重新打开应用
4. 启动服务并切换到直播模式

**预期结果**:
- ✅ 悬浮窗出现在上次关闭时的位置
- ✅ LocalStorage中有'live-mode-storage'键
- ✅ 数据格式正确

**如果失败**:
- 打开浏览器DevTools → Application → Local Storage
- 检查'live-mode-storage'键是否存在
- 检查persist配置

---

## 🔧 调试工具

### React DevTools

安装并打开React DevTools：

1. 找到组件树中的`FloatingWindow`
2. 查看Props和State
3. 查看useLiveModeStore的状态

### LocalStorage检查

在浏览器DevTools中：

```javascript
// 查看保存的位置
const saved = localStorage.getItem('live-mode-storage');
console.log(JSON.parse(saved));

// 输出示例：
// {
//   state: {
//     floatingPosition: { x: 100, y: 200 }
//   },
//   version: 0
// }
```

### Console日志

建议添加调试日志：

```typescript
// 在FloatingWindow.tsx中
useEffect(() => {
  console.log('悬浮窗位置:', position);
  console.log('拖拽状态:', isDragging);
}, [position, isDragging]);
```

---

## 🐛 常见问题排查

### 问题1: 悬浮窗不显示

**可能原因**:
- floatingVisible为false
- 组件渲染条件不满足
- z-index被覆盖

**解决方法**:
```typescript
// 检查状态
const { floatingVisible } = useLiveModeStore.getState();
console.log('悬浮窗可见:', floatingVisible);

// 强制显示
useLiveModeStore.getState().switchToLiveMode();
```

### 问题2: 拖拽不工作

**可能原因**:
- 事件监听未绑定
- 标题栏选择器错误
- useEffect依赖问题

**解决方法**:
```typescript
// 检查事件绑定
console.log('拖拽状态:', isDragging);

// 检查鼠标事件
const handleMouseDown = (e) => {
  console.log('鼠标按下:', e.clientX, e.clientY);
  // ...
};
```

### 问题3: 位置不持久化

**可能原因**:
- persist配置错误
- LocalStorage被禁用
- 浏览器隐私模式

**解决方法**:
```typescript
// 检查persist配置
// 在useLiveModeStore.ts中添加日志
partialize: (state) => {
  const result = { floatingPosition: state.floatingPosition };
  console.log('持久化数据:', result);
  return result;
}
```

### 问题4: 数据不显示

**可能原因**:
- useLiveConsoleStore数据为空
- useMemo依赖未更新
- 数据结构不匹配

**解决方法**:
```typescript
// 检查store数据
const { aiEvents, answerScripts } = useLiveConsoleStore.getState();
console.log('AI事件:', aiEvents);
console.log('话术列表:', answerScripts);
```

---

## 📋 验证清单

复制此清单进行验证：

```
Phase 1 功能验证清单：

□ 初始状态正确（全功能模式，无悬浮窗）
□ 启动服务后出现"直播模式"按钮
□ 点击按钮显示悬浮窗
□ 悬浮窗出现在正确位置（右下角）
□ 悬浮窗样式正确（半透明、圆角、阴影）
□ 可以拖拽移动悬浮窗
□ 拖拽不会超出屏幕边界
□ 可以切换三个Tab
□ AI Tab显示内容（有数据时）
□ 话术Tab显示内容（有数据时）
□ 数据Tab显示统计信息
□ 复制功能正常工作
□ 点击⇄可以切回全功能模式
□ 点击×可以关闭悬浮窗
□ 重启应用后位置保持

所有项目通过 = Phase 1 验收合格 ✅
```

---

## 🎓 给下一个开发者的提示

### 如何测试

```bash
# 1. 确保后端运行
cd server && python app.py

# 2. 启动前端开发服务
cd electron/renderer && npm run dev

# 3. 启动Electron
cd ../.. && npm run electron
```

### 如何调试

1. 打开Chrome DevTools (Ctrl+Shift+I)
2. 查看Console日志
3. 使用React DevTools查看组件状态
4. 检查LocalStorage数据

### 如何修改

- **修改悬浮窗样式**: `FloatingWindow.tsx` 中的inline styles
- **修改初始位置**: `useLiveModeStore.ts` 中的 `getDefaultPosition()`
- **修改持久化配置**: `useLiveModeStore.ts` 中的persist配置

---

**验证完成后，即可进入Phase 2！** 🚀

