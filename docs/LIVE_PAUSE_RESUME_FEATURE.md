# 直播复盘暂停/继续功能实现说明

## 功能概述

实现了直播复盘的暂停/继续功能,支持以下场景:

1. **手动暂停/继续**: 用户可以随时暂停录制,稍后继续,数据无缝衔接
2. **意外退出恢复**: 主播不小心关闭软件时,会话状态自动保存,重新打开后可以恢复
3. **断点恢复**: 应用启动时自动检测未完成的会话,提示用户是否继续
4. **状态持久化**: 会话状态保存到磁盘,应用重启后不丢失

## 技术实现

### 后端改造 (Python/FastAPI)

#### 1. 扩展会话状态数据结构

**文件**: `server/app/services/live_report_service.py`

```python
@dataclass
class LiveReportStatus:
    # ... 原有字段
    # 🆕 新增字段
    status: str = "recording"  # recording / paused / stopped
    paused_at: Optional[int] = None
    resumed_at: Optional[int] = None
    pause_count: int = 0
```

#### 2. 实现会话状态持久化

**文件**: `server/app/services/live_report_service.py`

新增方法:
- `_get_session_state_path()`: 获取会话状态文件路径
- `_save_session_state()`: 保存会话状态到磁盘 (JSON)
- `_load_session_state()`: 从磁盘加载会话状态
- `_load_saved_comments()`: 加载保存的弹幕数据
- `_clear_session_state()`: 清除会话状态文件
- `get_resumable_session()`: 获取可恢复的会话

#### 3. 实现暂停/继续逻辑

**文件**: `server/app/services/live_report_service.py`

新增方法:
- `pause()`: 暂停录制
  - 停止 ffmpeg、URL刷新任务、健康监控、弹幕采集
  - 标记为 `paused` 状态
  - 增量保存弹幕到磁盘
  - 持久化会话状态
  
- `resume()`: 继续录制
  - 重新获取流地址 (可能已过期)
  - 重启 ffmpeg (输出到同一目录,文件自动递增序号)
  - 重启 URL刷新任务、健康监控、弹幕采集
  - 标记为 `recording` 状态
  - 持久化会话状态

- `_stop_recording_tasks()`: 通用的停止任务方法
  - 停止 URL 刷新任务
  - 停止健康监控任务
  - 停止 ffmpeg 进程
  - 停止弹幕采集

- `_save_comments_incremental()`: 增量保存弹幕
  - 暂停时保存当前已收集的弹幕
  - 继续时从上次位置接着收集

#### 4. 修改现有方法

**`stop()`**: 
- 调用 `_stop_recording_tasks()` 统一停止任务
- 标记为 `stopped` 状态
- 持久化会话状态

**`generate_report()`**:
- 生成报告后调用 `_clear_session_state()` 清除持久化文件
- 允许开始新的录制

#### 5. 添加 REST API 路由

**文件**: `server/app/api/live_report.py`

新增路由:
- `POST /api/report/live/pause`: 暂停录制
- `POST /api/report/live/resume`: 继续录制
- `GET /api/report/live/resumable`: 获取可恢复的会话

修改路由:
- `POST /api/report/live/stop`: 返回 `status` 字段

### 前端改造 (React/TypeScript)

#### 1. 添加 API 服务

**文件**: `electron/renderer/src/services/liveReport.ts`

新增函数:
- `pauseLiveReport()`: 调用暂停 API
- `resumeLiveReport()`: 调用继续 API
- `getResumableSession()`: 调用获取可恢复会话 API

#### 2. 状态管理

**文件**: `electron/renderer/src/pages/dashboard/ReportsPage.tsx`

新增状态:
- `showResumeDialog`: 是否显示恢复会话对话框
- `resumableSession`: 可恢复的会话数据
- `isPaused`: 是否处于暂停状态
- `isRecording`: 是否正在录制

#### 3. 事件处理

新增函数:
- `pause()`: 暂停录制并停止轮询
- `resume()`: 继续录制并重启轮询
- `resumeSession()`: 恢复会话
- `discardSession()`: 放弃恢复,清除会话

#### 4. UI 组件

**状态显示**:
- 🔴 录制中 (绿色)
- ⏸️ 已暂停 (黄色)
- 未开始 (灰色)

**按钮**:
- 🎬 **开始录制**: 新建录制会话
- ⏸️ **暂停**: 暂停录制 (仅在录制中显示)
- ▶️ **继续**: 继续录制 (仅在暂停时显示)
- ⏹️ **停止**: 永久停止录制
- ✨ **生成报告**: 生成复盘报告

**恢复会话对话框**:
- 显示会话信息 (主播、状态、片段数、弹幕数)
- **继续录制**: 恢复会话
- **放弃**: 清除会话

#### 5. 应用启动时检测

在 `useEffect` 中调用 `getResumableSession()`:
- 如果有可恢复的会话,显示对话框
- 用户可以选择继续或放弃

## 数据流程

### 暂停流程

```
用户点击"暂停"
  ↓
前端调用 pauseLiveReport()
  ↓
后端 pause() 方法
  ├── 停止 ffmpeg 进程
  ├── 停止 URL 刷新任务
  ├── 停止健康监控任务
  ├── 停止弹幕采集
  ├── 标记状态为 "paused"
  ├── 增量保存弹幕到磁盘
  └── 持久化会话状态到 .live_session_state.json
  ↓
前端停止轮询,显示"已暂停"状态
```

### 继续流程

```
用户点击"继续"
  ↓
前端调用 resumeLiveReport()
  ↓
后端 resume() 方法
  ├── 重新获取流地址
  ├── 检查直播间是否开播
  ├── 重启 ffmpeg (输出到同一目录)
  ├── 重启 URL 刷新任务
  ├── 重启健康监控任务
  ├── 重启弹幕采集
  ├── 标记状态为 "recording"
  └── 持久化会话状态
  ↓
前端重启轮询,显示"录制中"状态
```

### 恢复会话流程

```
应用启动
  ↓
前端调用 getResumableSession()
  ↓
后端 get_resumable_session()
  ├── 读取 .live_session_state.json
  ├── 检查 status 是否为 "recording" 或 "paused"
  └── 返回会话数据
  ↓
前端显示"恢复会话"对话框
  ↓
用户点击"继续录制"
  ↓
根据会话状态:
  ├── 暂停状态: 调用 resumeLiveReport()
  └── 录制状态: 直接刷新状态并启动轮询
```

## 文件结构

### 会话状态文件

**位置**: `records/.live_session_state.json`

**内容**:
```json
{
  "session": {
    "session_id": "live_douyin_anchor_1234567890",
    "live_url": "https://live.douyin.com/xxxxx",
    "room_id": "xxxxx",
    "anchor_name": "anchor",
    "status": "paused",
    "started_at": 1700000000000,
    "paused_at": 1700001000000,
    "pause_count": 1,
    "segments": [...],
    ...
  },
  "aggregates": {
    "follows": 10,
    "entries": 100,
    "peak_viewers": 50,
    "like_total": 200,
    "gifts": {...}
  },
  "comments_count": 150,
  "carry": "..."
}
```

### 弹幕文件

**位置**: `records/douyin/<主播名>/<日期>/<session_id>/artifacts/comments.jsonl`

**内容**: 每行一个 JSON 对象
```jsonl
{"type": "chat", "payload": {...}, "ts": 1700000000000}
{"type": "like", "payload": {...}, "ts": 1700000001000}
...
```

### 录制文件

**位置**: `records/douyin/<主播名>/<日期>/<session_id>/`

**文件**: `<主播名>_20240101_120000_001.mp4`, `..._002.mp4`, ...

**特点**:
- 暂停后继续录制,新的文件会自动递增序号
- 所有片段保存在同一目录
- 生成报告时会合并所有片段的数据

## 错误处理

### 后端错误

1. **暂停失败**:
   - 没有活跃会话: 返回 404
   - 状态不是 "recording": 返回 400 + 错误信息

2. **继续失败**:
   - 没有可恢复的会话: 返回 404
   - 状态不是 "paused": 返回 400
   - 直播间未开播: 返回 400
   - 重启失败: 保持暂停状态

### 前端错误

- 所有错误显示在页面顶部的红色提示框
- 失败时保持原有状态,允许重试

## 测试建议

### 1. 基本功能测试

- [ ] 开始录制 → 暂停 → 继续 → 停止 → 生成报告
- [ ] 检查所有片段文件是否生成
- [ ] 检查弹幕数据是否完整
- [ ] 检查报告是否包含所有数据

### 2. 断点恢复测试

- [ ] 开始录制 → 暂停 → 关闭应用 → 重新打开 → 继续
- [ ] 开始录制 → 强制关闭应用 → 重新打开 → 恢复
- [ ] 检查会话状态文件是否保存/恢复正确

### 3. 边界条件测试

- [ ] 暂停后直播间下播 → 尝试继续 (应提示未开播)
- [ ] 多次暂停/继续 → 检查 pause_count 是否正确
- [ ] 长时间暂停 (流 URL 过期) → 继续时重新获取
- [ ] 生成报告后 → 会话状态文件是否清除

### 4. 并发测试

- [ ] 快速点击暂停/继续按钮
- [ ] 暂停期间点击停止按钮
- [ ] 同时打开多个标签页 (应共享状态)

## 注意事项

1. **流 URL 过期**: 
   - 暂停时间过长 (>20分钟),流 URL 可能过期
   - 继续时会自动重新获取

2. **会话状态文件**:
   - 保存在 `records/` 根目录
   - 生成报告后自动清除
   - 仅保存最新的一个会话

3. **弹幕数据**:
   - 暂停时增量保存到磁盘
   - 继续时从内存中继续追加
   - 不会重复采集已保存的弹幕

4. **录制文件**:
   - 暂停后继续,新文件自动递增序号
   - 所有文件保存在同一目录
   - ffmpeg 使用 `-strftime 1` 确保文件名带时间戳

## 未来优化

1. **多会话管理**: 支持保存多个未完成的会话
2. **恢复选项**: 允许用户选择从哪个时间点恢复
3. **自动暂停**: 检测到直播间下播时自动暂停
4. **暂停提醒**: 长时间暂停时提醒用户
5. **云端同步**: 将会话状态同步到云端 (跨设备恢复)

## 相关文件

### 后端

- `server/app/services/live_report_service.py`: 核心业务逻辑
- `server/app/api/live_report.py`: REST API 路由

### 前端

- `electron/renderer/src/services/liveReport.ts`: API 服务
- `electron/renderer/src/pages/dashboard/ReportsPage.tsx`: UI 组件

### 文档

- `LIVE_PAUSE_RESUME_FEATURE.md`: 本文档
- `AGENTS.md`: 项目指南 (已更新)

## 版本记录

- **v1.0.0** (2024-01-XX): 初始实现
  - 暂停/继续功能
  - 会话状态持久化
  - 断点恢复
  - 恢复会话对话框
