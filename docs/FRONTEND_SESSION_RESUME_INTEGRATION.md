# 前端会话恢复功能集成说明

## 概述

已为前端添加完整的会话恢复功能，包括：
1. 页面加载时自动检查可恢复的会话
2. 显示恢复提示对话框
3. 一键恢复会话并重启所有服务
4. 忽略恢复选项（开始新会话）

## ✅ 已完成的功能

### 1. 统一会话管理服务 (`liveSession.ts`)
- **文件**: `electron/renderer/src/services/liveSession.ts`
- **功能**:
  - ✅ `getSessionStatus()` - 获取当前会话状态
  - ✅ `resumeSession()` - 恢复会话
  - ✅ `pauseSession()` - 暂停会话
  - ✅ `resumePausedSession()` - 恢复暂停的会话
  - ✅ TypeScript类型定义 (`LiveSessionState`, `SessionStatusResponse`)

### 2. 前端页面集成 (`LiveConsolePage.tsx`)
- **文件**: `electron/renderer/src/pages/dashboard/LiveConsolePage.tsx`
- **新增状态**:
  ```typescript
  const [sessionState, setSessionState] = useState<LiveSessionState | null>(null);
  const [showResumeDialog, setShowResumeDialog] = useState(false);
  const [resumingSession, setResumingSession] = useState(false);
  const sessionCheckedRef = useRef(false);
  ```

- **新增功能**:
  1. **自动检查可恢复会话** (`useEffect`):
     - 页面加载后1秒自动检查
     - 如果发现 `recording` 或 `paused` 状态的会话，显示恢复对话框
     - 使用 `sessionCheckedRef` 防止重复检查

  2. **恢复会话处理** (`handleResumeSession`):
     - 调用后端API恢复统一会话
     - 根据会话状态恢复各服务：
       - 录制服务：自动恢复（后端已处理）
       - 弹幕服务：如果 `douyin_relay_active` 且 `live_id` 存在，重启服务
       - 转写服务：如果 `audio_transcription_active` 且 `live_url` 存在，重启服务
       - AI分析服务：如果 `ai_analysis_active`，重启服务
     - 如果会话是暂停状态，调用 `resumePausedSession`
     - 更新 `liveInput` 显示恢复的直播间ID
     - 刷新所有状态

  3. **忽略恢复** (`handleIgnoreResume`):
     - 关闭对话框
     - 清除会话状态
     - 允许用户开始新会话

  4. **恢复对话框UI**:
     - 显示会话详细信息（直播间ID、Room ID、主播、状态、开始时间）
     - 显示活跃服务标签
     - 提供"恢复会话"和"忽略，开始新会话"两个选项

## 🔄 工作流程

### 应用启动流程
```
1. 页面加载
2. 延迟1秒后检查会话状态
3. 如果发现可恢复会话 → 显示对话框
4. 用户选择：
   - 恢复 → 恢复会话并重启所有服务
   - 忽略 → 关闭对话框，可以开始新会话
```

### 会话恢复流程
```
1. 用户点击"恢复会话"
2. 调用后端API恢复统一会话
3. 根据会话状态恢复各服务：
   - 录制服务：自动恢复（后端处理）
   - 弹幕服务：重启（如果之前活跃）
   - 转写服务：重启（如果之前活跃）
   - AI分析服务：重启（如果之前活跃）
4. 更新UI状态
5. 刷新所有状态
```

## 📊 API调用

### 获取会话状态
```typescript
const response = await getSessionStatus(FASTAPI_BASE_URL);
// response: { success: boolean, data?: { session: LiveSessionState | null } }
```

### 恢复会话
```typescript
const resumeResponse = await resumeSession(FASTAPI_BASE_URL);
// resumeResponse: { success: boolean, data?: { session: LiveSessionState } }
```

### 恢复暂停的会话
```typescript
const resumePausedResponse = await resumePausedSession(FASTAPI_BASE_URL);
```

## 🎨 UI组件

### 恢复对话框
- **位置**: 模态对话框，覆盖整个页面
- **内容**:
  - 会话基本信息（直播间ID、Room ID、主播）
  - 会话状态（录制中/已暂停）
  - 开始时间
  - 活跃服务标签（录制、转写、AI、弹幕）
  - 操作按钮（恢复会话/忽略）

### 样式
- 使用 `timao-primary-btn` 和 `timao-outline-btn` 样式类
- 响应式设计，适配不同屏幕尺寸
- 灰色背景区域显示会话详情

## 🔧 配置

### 延迟检查时间
```typescript
setTimeout(checkResumableSession, 1000); // 1秒延迟
```

### 会话状态检查
```typescript
if (session.status === 'recording' || session.status === 'paused') {
  // 显示恢复对话框
}
```

## 📝 注意事项

1. **重复检查防护**: 使用 `sessionCheckedRef` 防止重复检查
2. **错误处理**: 检查失败不影响正常使用
3. **服务恢复**: 各服务恢复失败只显示警告，不阻塞其他服务
4. **状态同步**: 恢复后自动刷新所有状态
5. **用户体验**: 恢复过程中显示加载状态，防止重复操作

## 🚀 下一步优化建议

1. **自动恢复选项**: 添加"自动恢复"设置，用户可以选择是否自动恢复
2. **会话列表**: 显示多个可恢复会话，允许用户选择
3. **恢复进度**: 显示各服务恢复进度
4. **错误重试**: 服务恢复失败时提供重试机制
5. **会话验证**: 恢复前验证直播间是否仍在直播

## 📚 相关文件

- `electron/renderer/src/services/liveSession.ts` - 统一会话管理服务
- `electron/renderer/src/pages/dashboard/LiveConsolePage.tsx` - 直播控制台页面
- `server/app/api/live_session.py` - 后端统一会话管理API
- `server/app/services/live_session_manager.py` - 后端统一会话管理器

