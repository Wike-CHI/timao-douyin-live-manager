# 复盘报告前端展示功能

## 功能概述

实现了直播复盘报告的前端界面展示功能，用户可以在应用内查看 AI 生成的复盘报告，无需打开外部 HTML 文件。

## 核心改进

### 1. 后端改进

#### `server/app/services/live_report_service.py`
- **保存结构化数据**：在生成报告时，除了保存 `report.html`，还保存 `review_data.json` 文件
- **JSON 文件位置**：`artifacts/review_data.json`
- **数据结构**：
  ```json
  {
    "session_id": "...",
    "room_id": "...",
    "anchor_name": "...",
    "started_at": 1234567890000,
    "stopped_at": 1234567890000,
    "duration_seconds": 3600,
    "metrics": {...},
    "transcript": "完整转写文本...",
    "comments_count": 1234,
    "ai_summary": {
      "overall_score": 85,
      "performance_analysis": {...},
      "key_highlights": [...],
      "key_issues": [...],
      "improvement_suggestions": [...],
      "gemini_metadata": {...}
    },
    "transcript_chars": 12345,
    "segments_count": 4
  }
  ```

#### `server/app/api/live_report.py`
- **新增 API 接口**：`GET /api/report/live/review/{report_path:path}`
- **功能**：从历史报告的 HTML 路径加载对应的 `review_data.json`
- **参数**：`report_path` - 例如 `D:/project/.../artifacts/report.html`
- **返回**：
  ```json
  {
    "success": true,
    "message": "ok",
    "data": {
      "review_data": {...}
    }
  }
  ```
- **错误处理**：
  - 报告文件不存在：404
  - review_data.json 不存在（旧版本报告）：404
  - 其他错误：400

### 2. 前端改进

#### `electron/renderer/src/pages/dashboard/ReportsPage.tsx`

##### 新增功能
1. **查看复盘按钮**：
   - 在"片段与产物"区域，报告路径旁边添加了两个按钮：
     - "打开文件"：打开本地 HTML 文件（原功能）
     - "查看复盘"：在应用内查看复盘报告（**新功能**）

2. **viewReview 函数**：
   ```typescript
   const viewReview = async (reportPath: string) => {
     // 调用 /api/report/live/review/{encodedPath} 接口
     // 加载 review_data.json 数据
     // 更新 artifacts.review_data
     // 显示 ReviewReportPage 组件
   }
   ```

3. **自动展示**：
   - 生成报告后，如果有 `review_data`，自动显示复盘页面
   - 点击"查看复盘"按钮，也会显示复盘页面

#### `electron/renderer/src/pages/dashboard/ReviewReportPage.tsx`
- **已创建的完整 UI 组件**（前一版本已实现）
- **三个标签页**：
  1. 概览：AI 评分、整体评价、亮点、问题、建议
  2. 转写：完整直播转写文本
  3. 数据：直播指标（关注、进场、在线、点赞、礼物）
- **Gemini 元数据显示**：模型、Token 数、成本、耗时

## 使用流程

### 场景 1：新生成的报告
1. 录制直播并停止
2. 点击"生成报告"按钮
3. 等待 AI 分析完成（约 10-30 秒）
4. **自动跳转到复盘页面**，显示 AI 分析结果

### 场景 2：查看历史报告
1. 在"片段与产物"区域，找到之前生成的报告路径
2. 点击"**查看复盘**"按钮
3. 系统加载 `review_data.json` 数据
4. **跳转到复盘页面**，显示历史分析结果

### 场景 3：返回主页面
- 在复盘页面点击"关闭"按钮，返回主页面

## 测试步骤

### 1. 测试新生成的报告
```bash
# 启动应用
npm run dev

# 在前端执行：
# 1. 输入直播地址（例如：https://live.douyin.com/123456）
# 2. 点击"开始录制"
# 3. 等待一段时间（至少 1 分钟）
# 4. 点击"停止"
# 5. 点击"生成报告"
# 6. 等待 Gemini 分析完成
# 7. 应该自动显示复盘页面
```

### 2. 测试查看历史报告
```bash
# 前提：已有历史报告（包含 review_data.json）
# 例如：server/records/抖音/南栖77/2025-11-01/live_抖音_南栖77_1762009981/artifacts/

# 在前端执行：
# 1. 找到"片段与产物"区域的报告路径
# 2. 点击"查看复盘"按钮
# 3. 应该显示复盘页面，内容来自历史 review_data.json
```

### 3. 测试旧版本报告（无 review_data.json）
```bash
# 找到没有 review_data.json 的旧报告
# 点击"查看复盘"按钮
# 应该显示错误："复盘数据文件不存在，可能是旧版本报告"
```

## 文件结构

```
server/records/抖音/{anchor_name}/{date}/live_抖音_{anchor}_{timestamp}/
├── artifacts/
│   ├── comments.json          # 弹幕数据
│   ├── transcript.txt         # 完整转写
│   ├── report.html            # HTML 报告（旧方式，保留兼容）
│   └── review_data.json       # 结构化复盘数据（新增）
├── segment_00001.mp4          # 录制片段
├── segment_00002.mp4
└── ...
```

## 技术细节

### API 路径编码
- 前端：使用 `encodeURIComponent()` 编码文件路径
- 后端：FastAPI 的 `{report_path:path}` 自动解码

### 错误处理
- **报告不存在**：404 错误，提示用户
- **无 review_data.json**：404 错误，提示"可能是旧版本报告"
- **网络错误**：显示在错误提示区域

### 状态管理
- `artifacts.review_data`：当前复盘数据
- `showReview`：是否显示复盘页面
- `busy`：加载状态，防止重复点击

## 成本信息

每次生成复盘报告的成本：
- **Gemini 2.5 Flash**：约 $0.0001/次
- **对比 Qwen**：Qwen 用于实时分析（每 60 秒），成本约 ¥0.004/次

## 后续优化建议

1. **批量清理**：添加清理空目录的功能
2. **报告列表**：展示所有历史报告的列表，方便选择
3. **搜索功能**：按主播名、日期搜索历史报告
4. **导出功能**：导出复盘数据为 PDF 或 Markdown
5. **对比功能**：对比不同场次的复盘数据

## 兼容性

- ✅ 保留 HTML 文件生成，向后兼容
- ✅ 旧版本报告仍可通过"打开文件"查看 HTML
- ✅ 新版本报告同时支持 HTML 和应用内查看

## 提交信息

本次改动包括：
1. 后端：保存 `review_data.json`
2. 后端：新增 `/api/report/live/review/{report_path:path}` 接口
3. 前端：添加"查看复盘"按钮和 `viewReview` 函数
4. 前端：集成 `ReviewReportPage` 组件

准备提交命令：
```bash
git add server/app/services/live_report_service.py
git add server/app/api/live_report.py
git add electron/renderer/src/pages/dashboard/ReportsPage.tsx
git add REVIEW_DISPLAY_FEATURE.md
git commit -m "feat: 添加复盘报告前端展示功能，支持查看历史报告"
```
