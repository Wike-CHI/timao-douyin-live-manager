# 直播复盘功能使用指南

## 📖 功能说明

直播复盘功能使用 **Gemini 2.5 Flash** AI 模型，在直播结束后自动分析整场直播数据，生成详细的复盘报告，包括：

- 📊 **综合评分**（0-100分）
- ✨ **亮点时刻**（峰值、高价值互动等）
- ⚠️  **主要问题**（冷场、技术故障等）
- 📈 **表现分析**（互动、内容质量、转化潜力）
- 💡 **改进建议**（按优先级分类）

## 🚀 快速开始

### 1. 配置 API Key

在项目根目录的 `.env` 文件中添加：

```bash
# Gemini API（通过 AiHubMix 代理）
AIHUBMIX_API_KEY=sk-your-aihubmix-api-key
```

**获取 API Key**：
- 访问 [AiHubMix](https://aihubmix.com)
- 注册账号并生成 API Key
- 充值余额（建议至少 $5）

### 2. 安装依赖

```bash
pip install openai  # OpenAI SDK（用于调用 Gemini）
```

### 3. 测试连接

```bash
python tools/test_gemini.py
```

如果看到 `✅ 所有测试通过！`，说明配置成功。

### 4. 初始化数据库

```bash
python tools/init_database_quick.py
```

这将创建 `live_review_reports` 表。

## 📋 使用流程

### 方式一：自动生成（推荐）

1. **开始直播**
   - 前端点击"开始直播"
   - 后端创建 `LiveSession` 记录

2. **直播进行中**
   - 实时分析（星火/通义千问）每 60 秒运行一次
   - 弹幕、转写、事件数据持续保存到 `records/live_logs/`

3. **结束直播**
   - 前端点击"结束直播"
   - 调用 `POST /api/live/review/end_session`
   - 复盘报告自动生成（30-60秒）

4. **查看报告**
   - 调用 `GET /api/live/review/{session_id}`
   - 前端展示 Markdown 格式报告

### 方式二：手动生成

如果直播结束时未生成报告，可以手动补生成：

```bash
curl -X POST http://localhost:10090/api/live/review/generate \
  -H "Content-Type: application/json" \
  -d '{"session_id": 1, "force_regenerate": false}'
```

## 🔌 API 接口

### 1. 结束直播并生成复盘

```http
POST /api/live/review/end_session
Content-Type: application/json

{
  "session_id": 1,
  "generate_review": true
}
```

**响应**：
```json
{
  "success": true,
  "message": "直播已结束，复盘报告生成中（预计 30-60 秒）...",
  "data": {
    "session_id": 1,
    "room_id": "123456",
    "duration": 3600,
    "total_viewers": 1200,
    "peak_viewers": 350,
    "comment_count": 450,
    "gift_value": 188.5
  }
}
```

### 2. 查询复盘报告

```http
GET /api/live/review/{session_id}
```

**响应**：
```json
{
  "success": true,
  "data": {
    "id": 1,
    "session_id": 1,
    "status": "completed",
    "overall_score": 78,
    "performance_analysis": {
      "engagement": {
        "score": 85,
        "highlights": ["互动频繁", "回复及时"],
        "issues": ["中途冷场10分钟"]
      },
      "content_quality": {
        "score": 70,
        "highlights": ["产品讲解清晰"],
        "issues": ["话题重复"]
      },
      "conversion": {
        "score": 65,
        "signals": ["询价多但转化少"]
      }
    },
    "key_highlights": [
      "20:15 在线人数达到峰值 350 人",
      "20:32 收到单笔最大礼物 ¥188"
    ],
    "key_issues": [
      "20:25-20:35 网络波动导致卡顿",
      "话题切换过于突然"
    ],
    "improvement_suggestions": [
      {
        "priority": "high",
        "category": "互动技巧",
        "action": "增加观众提问环节",
        "expected_impact": "提升留存率"
      }
    ],
    "full_report_markdown": "# 📊 直播复盘报告\n\n...",
    "generated_at": "2025-01-01T20:30:00",
    "ai_model": "gemini-2.5-flash",
    "generation_cost": 0.001234,
    "generation_tokens": 3500,
    "generation_duration": 12.5
  }
}
```

### 3. 检查报告是否存在

```http
GET /api/live/review/session/{session_id}/exists
```

### 4. 获取最近报告列表

```http
GET /api/live/review/list/recent?limit=10
```

### 5. 删除报告

```http
DELETE /api/live/review/{report_id}
```

## 💰 成本估算

Gemini 2.5 Flash 定价（通过 AiHubMix）：
- **输入**: $0.075 / 1M tokens
- **输出**: $0.30 / 1M tokens

**单次复盘成本估算**：
- 小型直播（20分钟，100条弹幕）：约 $0.001 - $0.003
- 中型直播（60分钟，500条弹幕）：约 $0.005 - $0.010
- 大型直播（120分钟，2000条弹幕）：约 $0.020 - $0.050

**按月成本**：
- 每天 5 场直播 × 30 天 = 150 次复盘
- 平均成本: $0.01 × 150 = $1.5/月

## 🔍 调试

### 查看日志

```bash
# 后端日志
tail -f logs/app.log | grep -i gemini

# 或在 Windows PowerShell
Get-Content logs\app.log -Wait | Select-String "gemini"
```

### 常见问题

**Q: 报告生成失败怎么办？**
A: 
1. 检查 `AIHUBMIX_API_KEY` 是否配置正确
2. 运行 `python tools/test_gemini.py` 测试连接
3. 查看后端日志中的错误信息
4. 确认账户余额充足

**Q: 报告内容不完整？**
A: 
1. 确认直播数据已正确保存到 `records/live_logs/`
2. 检查 `LiveSession` 的 `comment_file` 和 `transcript_file` 字段
3. 手动触发重新生成：`force_regenerate: true`

**Q: 成本过高？**
A: 
1. 可以设置每日成本上限（后续功能）
2. 对于低价值直播可以选择不生成复盘
3. 将转写和弹幕数据做更激进的摘要

## 📚 相关文件

- **模型**: `server/app/models/live_review.py`
- **适配器**: `server/ai/gemini_adapter.py`
- **服务**: `server/app/services/live_review_service.py`
- **API**: `server/app/api/live_review.py`
- **测试**: `tools/test_gemini.py`
- **迁移**: `server/app/database/migrations/add_live_review_reports.py`

## 🎯 下一步

1. **前端集成**: 在 Electron 界面添加复盘报告展示页面
2. **数据导出**: 支持导出 PDF/图片分享
3. **历史对比**: 多场直播数据横向对比
4. **智能建议**: 基于历史复盘生成下次直播策略

---

*最后更新: 2025-01-01*
