# 统一直播会话管理系统

## 概述

本系统实现了统一的直播会话管理，将整场直播的所有服务（录制、转写、AI、弹幕）绑定在一个session中，提供统一的状态持久化和恢复机制。

## 核心特性

### 1. 统一会话标识
- 所有服务共享同一个 `session_id`
- 格式：`live_{platform}_{anchor}_{date}_{timestamp}`
- 确保同一场直播的所有数据都在同一个会话中

### 2. 状态持久化
- 会话状态自动保存到 `records/.live_session_state.json`
- 支持应用重启后恢复会话
- 所有数据按 session 存储到 `records/sessions/{session_id}/`

### 3. 日期/时间检查
- 防止连接到昨天的旧会话
- 自动拒绝超过24小时未更新的会话
- 确保只恢复当天的有效会话

### 4. 服务统一管理
- ✅ 直播录制服务（LiveReportService）
- ✅ 抖音弹幕服务（DouyinWebRelay）
- 🔄 语音转写服务（LiveAudioStreamService）- 待集成
- 🔄 AI分析服务（AILiveAnalyzer）- 待集成

## 文件结构

```
records/
├── .live_session_state.json          # 当前会话状态（持久化）
└── sessions/                          # 按session组织的所有数据
    └── live_douyin_主播名_20250104_1234567890/
        ├── artifacts/                 # 弹幕、转写等数据
        │   ├── comments.jsonl
        │   └── transcript.txt
        └── *.mp4                      # 录制视频文件
```

## API 端点

### 获取会话状态
```
GET /api/live_session/status
```

### 恢复会话
```
POST /api/live_session/resume
```

### 暂停会话
```
POST /api/live_session/pause
```

### 恢复暂停的会话
```
POST /api/live_session/resume_paused
```

## 已完成的集成

### 1. LiveSessionManager ✅
- 创建了统一的会话管理器
- 实现了会话创建、恢复、暂停、停止功能
- 添加了日期/时间验证机制
- 实现了状态持久化

### 2. DouyinWebRelay ✅
- 添加了 `session_id` 字段到 `RelayStatus`
- `start()` 方法支持传入 `session_id`
- 弹幕数据按 session 存储到 `sessions/{session_id}/artifacts/comments.jsonl`

### 3. LiveReportService ✅
- 集成统一会话管理器
- 使用统一的 `session_id` 创建会话
- 数据存储到统一的会话目录
- `stop()` 方法更新统一会话状态

## 待完成的集成

### 1. LiveAudioStreamService 🔄
- [ ] 在 `start()` 方法中接收并使用统一 `session_id`
- [ ] 转写数据存储到 `sessions/{session_id}/artifacts/transcript.txt`
- [ ] 更新统一会话状态（`audio_transcription_active`）

### 2. AILiveAnalyzer 🔄
- [ ] 在 `start()` 方法中接收并使用统一 `session_id`
- [ ] AI分析结果存储到 `sessions/{session_id}/artifacts/ai_analysis.jsonl`
- [ ] 更新统一会话状态（`ai_analysis_active`）

### 3. 前端集成 🔄
- [ ] 应用启动时自动检查并恢复会话
- [ ] 显示会话状态和恢复提示
- [ ] 支持手动恢复、暂停、继续会话

### 4. 会话恢复逻辑 🔄
- [ ] 在服务启动时自动调用 `resume_session()`
- [ ] 恢复所有服务的状态（录制、转写、AI、弹幕）
- [ ] 验证 room_id 一致性

## 使用示例

### 创建新会话
```python
from server.app.services.live_session_manager import get_session_manager

session_mgr = get_session_manager()
session = await session_mgr.create_session(
    live_url="https://live.douyin.com/191495446158",
    live_id="191495446158",
    anchor_name="主播名",
    platform_key="douyin"
)
```

### 恢复会话
```python
session = await session_mgr.resume_session()
if session:
    print(f"已恢复会话: {session.session_id}")
    # 恢复所有服务的状态...
```

### 更新会话状态
```python
await session_mgr.update_session(
    room_id="7568875803245595418",
    recording_active=True,
    douyin_relay_active=True
)
```

## 注意事项

1. **日期检查**：系统会自动拒绝非当天的会话，确保不会连接到旧直播
2. **room_id一致性**：恢复会话时需要验证 room_id 是否匹配当前直播间
3. **数据存储**：所有数据都存储在 `records/sessions/{session_id}/` 目录下
4. **状态同步**：各服务需要主动更新统一会话状态

## 下一步计划

1. 完成 LiveAudioStreamService 和 AILiveAnalyzer 的集成
2. 实现自动会话恢复机制
3. 添加前端UI支持会话恢复
4. 实现会话数据的完整备份和恢复

