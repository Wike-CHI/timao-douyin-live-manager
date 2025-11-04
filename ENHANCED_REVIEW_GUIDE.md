# 增强版直播复盘功能指南

## 🎯 功能概述

本系统针对**"颜值暧昧"类主播**进行了增强，从单纯的数据统计升级为**内容质量深度分析**。

### 核心升级

1. **从"数据统计"到"内容质量"** 
   - 旧版：关注进场数、点赞数等指标
   - 新版：分析哪些话术触发了消费、关注、互动

2. **触发点识别**
   - 识别礼物事件前后30秒的主播话术
   - 识别关注事件前后30秒的互动内容
   - 找出弹幕峰值时段的话题
   - 标注置信度（0-1）

3. **可落地训练建议**
   - 提取可复制的话术模板
   - 给出3-5个训练要点（含行动项）
   - 识别高价值用户并建议跟进方法

---

## 📊 输出数据结构

### 1. 话题分析 (`content_topics`)

#### 主播话题 (`anchor_topics`)
```json
{
  "topic": "颜值互动",
  "time_range": "第5-10分钟",
  "key_quotes": [
    "宝宝们觉得我今天这个妆容怎么样",
    "有人说我像迪丽热巴吗"
  ],
  "emotion_tags": ["暧昧", "俏皮"],
  "quality_score": 4.2,
  "reason": "话题引发大量弹幕互动，情绪表达到位"
}
```

#### 观众话题 (`audience_topics`)
```json
{
  "topic": "求加微信",
  "time_range": "第15-20分钟",
  "sample_comments": [
    "主播能加个微信吗",
    "私聊怎么联系你",
    "怎么才能加到你"
  ],
  "frequency": 50,
  "sentiment": "正面"
}
```

#### 高频关键词 (`top_keywords`)
```json
["漂亮", "加微信", "唱歌", "可爱", "关注", "礼物", "福利", "宝宝", "喜欢", "666"]
```

---

### 2. 触发点分析 (`trigger_analysis`)

#### 消费触发点 (`consumption_triggers`)
```json
{
  "topic": "撒娇要礼物",
  "evidence": {
    "time": "第12分35秒",
    "transcript_quote": "宝宝们能不能送个小心心呀，人家今天好累哦",
    "gifts": [
      {"user": "用户A", "gift": "玫瑰花", "amount": 10, "timestamp": 1730012345},
      {"user": "用户B", "gift": "小心心", "amount": 1, "timestamp": 1730012347}
    ],
    "related_comments": [
      "送你了宝贝",
      "这么可爱必须送"
    ]
  },
  "confidence": 0.85,
  "analysis": "撒娇+疲劳营造+情感共鸣，触发用户保护欲和打赏意愿"
}
```

#### 关注触发点 (`follow_triggers`)
```json
{
  "topic": "福利引导",
  "evidence": {
    "time": "第5分20秒",
    "transcript_quote": "关注主播不迷路，私聊有惊喜哦",
    "follows": [
      {"user": "12345678", "timestamp": 1730012321},
      {"user": "87654321", "timestamp": 1730012325}
    ],
    "related_comments": [
      "什么惊喜",
      "已关注"
    ]
  },
  "confidence": 0.82,
  "analysis": "明确的价值交换提示（关注=惊喜），触发用户关注行为"
}
```

#### 互动峰值 (`engagement_peaks`)
```json
{
  "time_range": "第8-10分钟",
  "topic": "才艺展示（唱歌）",
  "metrics": {
    "comments_per_minute": 25,
    "likes_spike": 150,
    "entries_spike": 30
  },
  "trigger_content": "主播演唱《可可托海的牧羊人》",
  "confidence": 0.90
}
```

---

### 3. 高价值用户 (`high_value_users`)

```json
{
  "user_name": "用户A",
  "contribution": {
    "total_gifts": 5,
    "total_value": 500,
    "interaction_count": 15
  },
  "interaction_context": "在颜值互动和才艺展示时活跃，送礼集中在第10-15分钟",
  "follow_up_actions": [
    {
      "action": "私聊话术",
      "content": "谢谢宝贝今天的支持，你今天送的礼物我都看到了，感动哭了😭 以后多来看我哦",
      "timing": "直播结束后1小时内"
    },
    {
      "action": "专属权益",
      "content": "添加专属微信，备注'VIP用户'，提供每日私照福利"
    }
  ]
}
```

---

### 4. 可复制话术 (`replicable_scripts`)

```json
{
  "scenario": "开场暖场",
  "script": "宝宝们晚上好呀，今天你们的小可爱又来啦~ 想我了吗？",
  "why_works": "建立亲昵感，使用'小可爱'自称拉近距离，反问引导互动",
  "usage_frequency": "每场直播开场",
  "evidence": "本场开场3分钟内收获80条弹幕互动，关注转化率12%"
}
```

```json
{
  "scenario": "礼物感谢",
  "script": "谢谢{用户名}宝宝的{礼物名}，爱你么么哒~ 你今天是第一个送礼的，主播记住你了哦",
  "why_works": "个性化称呼+情感反馈+稀缺性暗示（第一个），强化送礼正反馈",
  "usage_frequency": "每次收到礼物立即使用",
  "evidence": "使用后30秒内触发连续3个礼物"
}
```

---

### 5. 训练要点 (`training_points`)

```json
{
  "category": "话术优化",
  "current_issue": "冷场次数过多（5次超过30秒无有效内容），导致流失率上升",
  "target_improvement": "减少冷场，保持内容连贯性",
  "action_items": [
    "准备10个备用话题（才艺、颜值、福利、故事），冷场时快速切换",
    "学习使用过渡话术（如'对了宝宝们...'、'说到这个...'）",
    "训练即兴应对能力，每日练习5分钟脱口秀"
  ],
  "priority": "高",
  "expected_impact": "减少50%冷场时间，提升15%留人率"
}
```

```json
{
  "category": "情绪表达",
  "current_issue": "情绪单一，缺乏起伏变化，观众容易疲劳",
  "target_improvement": "丰富情绪表达，增加感染力",
  "action_items": [
    "学习3种情绪切换：兴奋、撒娇、神秘（配合声音、表情、肢体）",
    "每10分钟制造一个情绪高潮点（如惊喜、感动、搞笑）",
    "观看优秀主播视频，模仿情绪表达技巧"
  ],
  "priority": "中",
  "expected_impact": "提升20%互动率，增强观众粘性"
}
```

---

## 🔧 技术实现

### 文件结构

```
server/
├── ai/
│   ├── gemini_adapter.py           # 原版适配器（保留）
│   └── gemini_adapter_enhanced.py  # 🆕 增强版适配器
└── app/
    └── services/
        └── live_report_service.py  # 🆕 已更新为调用增强版
```

### 核心逻辑

```python
# 1. 事件分类
events = _analyze_comment_events(comments)
# -> {chats, gifts, follows, likes, entries}

# 2. 构建内容分析提示词
prompt = _build_content_analysis_prompt(
    anchor_name, duration_seconds, transcript, events, metrics
)

# 3. 调用 Gemini 生成分析
result = adapter.generate_review(
    prompt, temperature=0.3, max_tokens=6000, response_format="json"
)

# 4. 解析 JSON 并补充元数据
report = adapter.parse_json_response(result["text"])
report["trend_charts"] = _generate_real_trend_charts(metrics, duration_seconds)
report["event_statistics"] = {...}
```

### 时间窗匹配算法

```python
# 礼物事件触发点识别
for gift_event in gift_events:
    gift_time = gift_event.get("timestamp", 0) / 1000  # 转为秒
    
    # 在转写中查找 ±30秒 的内容
    start_time = gift_time - 30
    end_time = gift_time + 30
    
    # 提取该时间段的转写文本
    related_transcript = extract_transcript_by_time(
        transcript, start_time, end_time
    )
    
    # 分析话术特征
    analyze_trigger_pattern(related_transcript, gift_event)
```

---

## 📈 使用流程

### 1. 录制直播

```bash
# 前端：点击"开始录制"
POST /api/live-report/start
{
  "live_url": "https://live.douyin.com/123456",
  "segment_minutes": 30
}
```

### 2. 停止录制

```bash
# 前端：点击"停止录制"
POST /api/live-report/stop
```

### 3. 生成复盘

```bash
# 前端：点击"生成报告"
POST /api/live-report/generate
```

### 4. 查看复盘结果

```bash
# 查看 artifacts/ai_summary.json
{
  "content_topics": {...},         # 话题分析
  "trigger_analysis": {...},       # 触发点分析
  "high_value_users": [...],       # 高价值用户
  "replicable_scripts": [...],     # 可复制话术
  "training_points": [...],        # 训练要点
  "event_statistics": {...}        # 事件统计
}
```

---

## ⚙️ 配置要求

### 环境变量

```bash
# .env 文件
AIHUBMIX_API_KEY=sk-your-api-key
AIHUBMIX_BASE_URL=https://aihubmix.com/v1
GEMINI_MODEL=gemini-2.5-flash-preview-09-2025
```

### 成本估算

- **输入**: ~10,000 tokens (转写 + 弹幕 + 事件)
- **输出**: ~4,000 tokens (详细分析)
- **成本**: ~$0.0015/次 (约 ¥0.01/次)

---

## 🎓 最佳实践

### 1. 数据准备

- **转写质量**: 确保音频清晰，SenseVoice 转写准确
- **事件完整性**: 完整收集弹幕、礼物、关注事件
- **时间同步**: 确保事件时间戳准确

### 2. 分析解读

- **关注触发点**: 重点看 `consumption_triggers` 和 `follow_triggers`
- **验证置信度**: 置信度 >0.8 的触发点可直接复用
- **话术模板化**: 将 `replicable_scripts` 整理成话术库

### 3. 运营落地

- **高价值用户**: 24小时内完成 `follow_up_actions`
- **训练要点**: 按优先级逐项落实 `training_points`
- **话术优化**: 每周更新话术库，淘汰低效话术

---

## 🐛 故障排除

### 问题1: JSON解析失败

**原因**: Gemini 输出格式不正确

**解决方案**:
1. 查看 `artifacts/ai_summary.error.txt`
2. 检查 `raw_response_preview` 字段
3. 调整 `temperature` 参数（降低到 0.2）

### 问题2: 触发点识别不准确

**原因**: 时间戳不准确或转写质量差

**解决方案**:
1. 检查弹幕/礼物事件的 `timestamp` 字段
2. 提升录音质量，减少背景噪音
3. 增加转写样本长度（提高到 20000 字）

### 问题3: 话题抽取过于笼统

**原因**: 转写内容不够丰富或 prompt 不够具体

**解决方案**:
1. 确保直播时长 >15 分钟
2. 在 prompt 中增加示例
3. 提高 `max_tokens` 到 8000

---

## 📚 参考文档

- [Gemini 2.5 Flash API 文档](https://ai.google.dev/docs)
- [AiHubMix 代理服务](https://aihubmix.com)
- [SenseVoice 语音转写](./AST_README.md)
- [直播录制方案](./直播全场录制与分析方案.md)

---

## 🔄 版本历史

### v2.0 - 2025-01-04
- 🆕 增强版复盘功能上线
- ✨ 新增话题分析、触发点识别
- ✨ 新增高价值用户识别
- ✨ 新增可复制话术和训练要点
- 🔧 优化 Gemini prompt，提升分析质量

### v1.0 - 2025-10-26
- 🎉 基础复盘功能上线
- 📊 支持数据统计和趋势分析

---

## 💬 反馈与建议

如有问题或建议，请联系开发团队或提交 Issue。
