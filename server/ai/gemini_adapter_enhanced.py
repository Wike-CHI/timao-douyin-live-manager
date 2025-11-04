# -*- coding: utf-8 -*-
"""
Gemini AI 增强适配器 - 专注于"颜值暧昧"类直播的内容质量复盘

在原有 gemini_adapter.py 基础上增强，重点分析：
1. 话题抽取与时间序列分析
2. 触发点识别（消费/关注/互动的触发话题）
3. 高价值用户识别与运营建议
4. 可复制话术与训练要点
"""

import json
import logging
from typing import Dict, Any, List, Optional
from .gemini_adapter import GeminiAdapter, get_gemini_adapter, _generate_real_trend_charts

logger = logging.getLogger(__name__)


def _split_transcript_into_time_windows(
    transcript_data,
    duration_seconds: int,
    window_size: int = 30
) -> List[Dict[str, Any]]:
    """将转写按时间窗切分，支持精确定位
    
    Args:
        transcript_data: 带时间戳的分段列表或纯文本字符串
        duration_seconds: 直播总时长
        window_size: 时间窗大小（秒），默认30秒
    
    Returns:
        时间窗列表，每个窗口包含 start_time, end_time, text
    """
    windows = []
    
    # 情况1：带时间戳的分段数据（推荐）
    if isinstance(transcript_data, list) and transcript_data:
        for segment in transcript_data:
            seg_start = segment.get("start_time", 0)
            seg_end = segment.get("end_time", seg_start + 1800)
            seg_text = segment.get("text", "")
            
            if not seg_text.strip():
                continue
            
            # 按句子切分（中文句号、问号、感叹号）
            import re
            sentences = re.split(r'[。！？\n]+', seg_text)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            if not sentences:
                continue
            
            # 计算分段时长
            seg_duration = seg_end - seg_start
            
            # 将句子均匀分布到时间段内
            num_sentences = len(sentences)
            avg_sentence_duration = seg_duration / num_sentences if num_sentences > 0 else seg_duration
            
            current_time = seg_start
            current_window_text = []
            window_start = current_time
            
            for i, sentence in enumerate(sentences):
                sentence_end = current_time + avg_sentence_duration
                current_window_text.append(sentence)
                
                # 当累积到30秒或最后一句时，保存窗口
                if (sentence_end - window_start >= window_size) or (i == num_sentences - 1):
                    windows.append({
                        "start_time": int(window_start),
                        "end_time": int(min(sentence_end, seg_end)),
                        "text": "。".join(current_window_text) + "。"
                    })
                    current_window_text = []
                    window_start = sentence_end
                
                current_time = sentence_end
    
    # 情况2：纯文本（降级方案）
    elif isinstance(transcript_data, str):
        # 简单按字符数均匀切分
        text = transcript_data
        total_chars = len(text)
        if total_chars == 0:
            return windows
        
        chars_per_second = total_chars / duration_seconds if duration_seconds > 0 else total_chars
        window_chars = int(chars_per_second * window_size)
        
        current_pos = 0
        current_time = 0
        
        while current_pos < total_chars:
            end_pos = min(current_pos + window_chars, total_chars)
            window_text = text[current_pos:end_pos].strip()
            
            if window_text:
                windows.append({
                    "start_time": current_time,
                    "end_time": current_time + window_size,
                    "text": window_text
                })
            
            current_pos = end_pos
            current_time += window_size
    
    return windows


def _format_seconds(seconds: int) -> str:
    """格式化秒数为 MM:SS 或 HH:MM:SS"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


def _match_events_to_time_windows(
    events: List[Dict],
    windows: List[Dict],
    time_window_seconds: int = 30
) -> Dict[str, List[Dict]]:
    """将事件（礼物/关注）匹配到对应的时间窗
    
    Args:
        events: 事件列表（包含 timestamp 字段，毫秒）
        windows: 时间窗列表
        time_window_seconds: 匹配窗口大小（秒）
    
    Returns:
        匹配结果字典
    """
    matched = {}
    
    for event in events:
        timestamp_ms = event.get("timestamp", 0)
        if not timestamp_ms:
            continue
        
        # 转换为秒
        event_time = timestamp_ms / 1000 if timestamp_ms > 1e10 else timestamp_ms
        
        # 查找前后30秒内的时间窗
        for window in windows:
            window_start = window["start_time"]
            window_end = window["end_time"]
            
            # 事件在窗口内或窗口的±30秒范围内
            if (window_start - time_window_seconds <= event_time <= window_end + time_window_seconds):
                window_key = f"{window_start}-{window_end}"
                if window_key not in matched:
                    matched[window_key] = {
                        "window": window,
                        "events": []
                    }
                matched[window_key]["events"].append(event)
    
    return matched


def _analyze_comment_events(comments: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """分析弹幕事件，分类为聊天、礼物、关注等
    
    Args:
        comments: 弹幕列表
    
    Returns:
        分类后的事件字典
    """
    gift_events = []
    follow_events = []
    chat_comments = []
    like_events = []
    entry_events = []
    
    for comment in comments:
        if not isinstance(comment, dict):
            continue
            
        event_type = comment.get("type", "comment")
        
        # 礼物事件
        if event_type == "gift" or "gift" in comment or "gift_name" in comment:
            gift_events.append(comment)
        # 关注事件
        elif event_type in ["follow", "social"]:
            follow_events.append(comment)
        # 点赞事件
        elif event_type == "like":
            like_events.append(comment)
        # 进场事件
        elif event_type in ["member", "entry"]:
            entry_events.append(comment)
        # 普通弹幕
        else:
            chat_comments.append(comment)
    
    return {
        "gifts": gift_events,
        "follows": follow_events,
        "chats": chat_comments,
        "likes": like_events,
        "entries": entry_events
    }


def _build_content_analysis_prompt(
    anchor_name: str,
    duration_seconds: int,
    transcript_data,  # 🔄 支持 List[Dict] 或 str
    events: Dict[str, List],
    metrics: Dict[str, Any]
) -> str:
    """构建专注于内容质量的分析提示词
    
    Args:
        anchor_name: 主播名称
        duration_seconds: 直播时长
        transcript_data: 带时间戳的分段列表或纯文本
        events: 分类后的事件
        metrics: 直播数据
    
    Returns:
        完整的提示词
    """
    duration_minutes = duration_seconds // 60
    
    # 🆕 将转写切分为时间窗（每30秒）
    time_windows = _split_transcript_into_time_windows(
        transcript_data, 
        duration_seconds, 
        window_size=30
    )
    
    logger.info(f"📊 转写切分完成 - {len(time_windows)} 个时间窗（每30秒）")
    
    # 🆕 匹配礼物和关注事件到时间窗
    gift_matches = _match_events_to_time_windows(events["gifts"], time_windows, time_window_seconds=30)
    follow_matches = _match_events_to_time_windows(events["follows"], time_windows, time_window_seconds=30)
    
    logger.info(
        f"🎯 事件匹配完成 - 礼物触发点: {len(gift_matches)}, 关注触发点: {len(follow_matches)}"
    )
    
    # 🆕 格式化带时间戳的转写文本（限制展示数量）
    max_windows_to_show = min(100, len(time_windows))  # 最多展示100个窗口
    transcript_with_timestamps = "\n\n".join([
        f"[{_format_seconds(w['start_time'])} - {_format_seconds(w['end_time'])}]\n{w['text']}"
        for w in time_windows[:max_windows_to_show]
    ])
    
    if len(time_windows) > max_windows_to_show:
        transcript_with_timestamps += f"\n\n...（省略 {len(time_windows) - max_windows_to_show} 个时间窗）"
    
    # 🆕 格式化触发点证据（展示匹配到事件的时间窗）
    trigger_evidence = []
    
    # 礼物触发点
    for window_key, match_data in list(gift_matches.items())[:10]:  # 最多展示10个
        window = match_data["window"]
        events_list = match_data["events"]
        trigger_evidence.append({
            "type": "gift",
            "time": f"{_format_seconds(window['start_time'])} - {_format_seconds(window['end_time'])}",
            "transcript": window["text"][:200],  # 截取前200字
            "events": [
                {
                    "user": e.get("user", "未知"),
                    "gift": e.get("gift_name", e.get("gift", "未知礼物")),
                    "count": e.get("count", 1)
                }
                for e in events_list[:5]  # 最多展示5个事件
            ]
        })
    
    # 关注触发点
    for window_key, match_data in list(follow_matches.items())[:10]:
        window = match_data["window"]
        events_list = match_data["events"]
        trigger_evidence.append({
            "type": "follow",
            "time": f"{_format_seconds(window['start_time'])} - {_format_seconds(window['end_time'])}",
            "transcript": window["text"][:200],
            "events": [
                {"user": e.get("user", "未知")}
                for e in events_list[:5]
            ]
        })
    
    # 限制弹幕和事件数量
    chat_preview = events["chats"][:200] if len(events["chats"]) > 200 else events["chats"]
    
    prompt = f"""你是一个专注于直播复盘与话术训练的自动化复盘AI。目标受众为"颜值暧昧"类主播，复盘重点是"内容质量"（不是单纯的数据），并识别哪些话题/台词触发了关注/消费/点赞/评论。

## 📊 输入数据

### 基础信息
- **主播**: {anchor_name}
- **时长**: {duration_minutes} 分钟 ({_format_seconds(duration_seconds)})
- **数据量**: 转写 {len(time_windows)} 个时间窗, 弹幕 {len(events['chats'])} 条, 礼物 {len(events['gifts'])} 个, 关注 {len(events['follows'])} 次

### 数据概览
```json
{json.dumps(metrics, ensure_ascii=False, indent=2)}
```

### 🎤 语音转写（带时间戳，每30秒一个时间窗）
{transcript_with_timestamps}

### 🎯 触发点证据（礼物/关注事件对应的话术）
以下是匹配到事件的时间窗及主播话术：

{json.dumps(trigger_evidence, ensure_ascii=False, indent=2)}

### 💬 弹幕样本（前50条）
{json.dumps(chat_preview[:50], ensure_ascii=False, indent=2)}

---

## 🎯 分析任务

你的核心任务是**识别触发消费/关注的话题钩子**。请严格基于上述"触发点证据"进行分析。

输出JSON格式报告：

{{
  "overall_score": 85,
  
  "performance_analysis": {{
    "overall_assessment": "整体表现概述（包含具体数据）",
    "content_quality": {{"score": 80, "comments": "内容质量分析（引用具体话术）"}},
    "engagement": {{"score": 85, "comments": "互动表现分析（引用具体数据）"}},
    "conversion_potential": {{"score": 75, "comments": "转化潜力分析"}}
  }},
  
  "content_topics": {{
    "anchor_topics": [
      {{
        "topic": "话题标题",
        "time_range": "第X-Y分钟",
        "key_quotes": ["台词1", "台词2"],
        "emotion_tags": ["暧昧", "俏皮"],
        "quality_score": 4.2,
        "reason": "评分理由"
      }}
    ],
    "audience_topics": [
      {{
        "topic": "观众关注点",
        "time_range": "第X-Y分钟",
        "sample_comments": ["弹幕1", "弹幕2"],
        "frequency": 50,
        "sentiment": "正面"
      }}
    ],
    "top_keywords": ["关键词1", "关键词2", "关键词3"]
  }},
  
  "trigger_analysis": {{
    "consumption_triggers": [
      {{
        "topic": "触发消费的话题/台词",
        "evidence": {{
          "time": "12:30 - 13:00",
          "transcript_quote": "主播说的具体话术（从触发点证据中原文引用）",
          "gifts": [{{"user": "用户昵称", "gift": "小心心", "count": 5}}],
          "related_comments": ["好美啊", "给姐姐刷礼物"]
        }},
        "confidence": 0.85,
        "analysis": "为什么这个话术触发了消费？分析情绪、语气、时机等因素"
      }}
    ],
    "follow_triggers": [
      {{
        "topic": "触发关注的话题/台词",
        "evidence": {{
          "time": "05:15 - 05:45",
          "transcript_quote": "主播话术原文",
          "follows": [{{"user": "用户昵称"}}],
          "related_comments": ["关注了"]
        }},
        "confidence": 0.82,
        "analysis": "分析为什么触发关注（价值承诺、情感连接等）"
      }}
    ],
    "engagement_peaks": [
      {{
        "time_range": "第8-10分钟",
        "topic": "高互动话题",
        "metrics": {{"comments_per_minute": 15, "likes_spike": 80}},
        "trigger_content": "触发内容（引用话术原文）",
        "confidence": 0.90
      }}
    ]
  }},
  
  "high_value_users": [
    {{
      "user_name": "用户昵称",
      "contribution": {{"total_gifts": 5, "total_value": 500}},
      "interaction_context": "在 05:30-06:00（某某话题）时活跃，送了XX礼物",
      "follow_up_actions": [
        {{"action": "私聊话术", "content": "具体话术（感谢+价值承诺）", "timing": "直播后1小时内"}},
        {{"action": "专属权益", "content": "专属微信/粉丝群/福利"}}
      ]
    }}
  ],
  
  "replicable_scripts": [
    {{
      "scenario": "使用场景（如：礼物引导、关注引导、气氛调动）",
      "script": "可复制话术模板（原文引用）",
      "why_works": "为什么有效（情绪表达、价值交换、稀缺性、时机把握）",
      "usage_frequency": "建议频率（如：每10分钟1次）",
      "evidence": "来自本场 12:30-13:00 的证据（必须标注时间）"
    }}
  ],
  
  "training_points": [
    {{
      "category": "训练类别",
      "current_issue": "当前问题",
      "target_improvement": "目标改进",
      "action_items": ["行动1", "行动2"],
      "priority": "高",
      "expected_impact": "预期效果"
    }}
  ],
  
  "key_highlights": [
    "具体亮点1（包含数据和话术）",
    "具体亮点2",
    "具体亮点3"
  ],
  
  "key_issues": [
    "具体问题1（包含数据和分析）",
    "具体问题2",
    "具体问题3"
  ],
  
  "improvement_suggestions": [
    "可执行建议1（包含具体方法和预期效果）",
    "可执行建议2",
    "可执行建议3"
  ],
  
  "notes": "数据缺失说明"
}}

---

## 🔑 核心分析要求

### 1. **精确时间定位**（最重要）
- ✅ 必须引用"触发点证据"中的具体时间（如：12:30-13:00）
- ✅ 必须引用证据中的主播话术原文
- ❌ 不要猜测或编造时间点

### 2. **触发点分析**（核心任务）
- 对于每个礼物/关注事件，在"触发点证据"中找到对应时间窗的话术
- 识别话术的共同特征：情绪（撒娇/暧昧/可怜）、语气、时机、内容
- **置信度评估标准**：
  - 0.9-1.0: 多个事件在同一话术后触发，模式明确
  - 0.7-0.89: 事件与话术有明显关联
  - 0.5-0.69: 关联较弱，可能是巧合
  - <0.5: 不要输出

### 3. **可复制话术提取**
- 从"触发点证据"中提取有效话术（原文引用）
- 说明为什么有效（情绪表达、价值交换、稀缺性等）
- 给出使用场景和频率建议
- **必须包含证据来源的时间**

### 4. **高价值用户识别**
- 统计送礼最多的用户（Top 3-5）
- 分析他们在哪些时间窗活跃（引用具体时间）
- 给出具体的跟进话术和权益设计

### 5. **训练要点**
- 基于发现的问题给出训练建议
- 每个训练点包含：问题、目标、行动项（≤3条）
- 按优先级排序（高/中/低）

---

## ⚠️ 注意事项

1. **只分析提供的数据**：不要凭空编造事件或用户
2. **精确引用时间**：必须使用"触发点证据"中的时间格式（MM:SS - MM:SS）
3. **原文引用话术**：从转写中引用原文，不要改写或美化
4. **置信度标注**：所有触发点必须标注置信度（0-1），低于0.5不输出
5. **JSON格式**：只输出纯JSON，不要markdown标记（```json）

现在开始输出JSON："""
    
    return prompt


def generate_enhanced_review_report(review_data: Dict[str, Any]) -> Dict[str, Any]:
    """生成增强版直播复盘报告（专注于内容质量和触发点分析）
    
    Args:
        review_data: 复盘数据（同原版）
    
    Returns:
        增强版复盘报告
    """
    adapter = get_gemini_adapter()
    
    if not adapter.is_available():
        raise RuntimeError("Gemini 服务不可用，请检查 AIHUBMIX_API_KEY 配置")
    
    # 提取数据
    transcript = review_data.get("transcript", "")
    comments = review_data.get("comments", [])
    anchor_name = review_data.get("anchor_name", "主播")
    metrics = review_data.get("metrics", {})
    duration_seconds = int(review_data.get("duration_seconds", 0))
    viewer_snapshots = review_data.get("viewer_snapshots", [])
    
    # 🆕 分析事件
    events = _analyze_comment_events(comments)
    
    logger.info(
        f"📊 数据分类完成 - "
        f"弹幕: {len(events['chats'])}, "
        f"礼物: {len(events['gifts'])}, "
        f"关注: {len(events['follows'])}, "
        f"点赞: {len(events['likes'])}, "
        f"进场: {len(events['entries'])}"
    )
    
    # 🆕 生成趋势图
    trend_charts = _generate_real_trend_charts(metrics, duration_seconds)
    
    # 🆕 构建内容质量分析提示词
    prompt = _build_content_analysis_prompt(
        anchor_name=anchor_name,
        duration_seconds=duration_seconds,
        transcript_data=transcript,  # 🔧 修正参数名
        events=events,
        metrics=metrics
    )
    
    # 调用 Gemini
    logger.info(f"🚀 开始调用 Gemini 生成增强版复盘报告...")
    logger.info(f"📝 转写长度: {len(transcript)} 字符")
    
    result = adapter.generate_review(
        prompt=prompt,
        temperature=0.3,
        max_tokens=6000,  # 增加token限制，支持更详细的分析
        response_format="json"
    )
    
    if not result:
        raise RuntimeError("Gemini API 调用失败")
    
    logger.info(f"✅ Gemini 响应成功 - 长度: {len(result['text'])} 字符")
    
    # 解析 JSON
    report_data = adapter.parse_json_response(result["text"])
    
    if not report_data:
        # 降级方案
        logger.warning("⚠️ JSON解析失败，使用降级方案")
        report_data = {
            "overall_score": 0,
            "performance_analysis": {
                "overall_assessment": "AI分析失败，JSON解析错误",
                "content_quality": {"score": 0, "comments": "解析失败"},
                "engagement": {"score": 0, "comments": "解析失败"},
                "conversion_potential": {"score": 0, "comments": "解析失败"}
            },
            "content_topics": {
                "anchor_topics": [],
                "audience_topics": [],
                "top_keywords": []
            },
            "trigger_analysis": {
                "consumption_triggers": [],
                "follow_triggers": [],
                "engagement_peaks": []
            },
            "high_value_users": [],
            "replicable_scripts": [],
            "training_points": [],
            "key_highlights": ["AI分析遇到问题"],
            "key_issues": ["JSON解析失败"],
            "improvement_suggestions": ["请重试"],
            "error": "JSON解析失败",
            "raw_response_preview": result["text"][:1000]
        }
    
    # 补充元数据
    report_data["ai_model"] = adapter.model
    report_data["generation_cost"] = result["cost"]
    report_data["generation_tokens"] = result["usage"]["total_tokens"]
    report_data["generation_duration"] = result["duration"]
    report_data["trend_charts"] = trend_charts
    
    # 🆕 补充事件统计
    report_data["event_statistics"] = {
        "total_chats": len(events["chats"]),
        "total_gifts": len(events["gifts"]),
        "total_follows": len(events["follows"]),
        "total_likes": len(events["likes"]),
        "total_entries": len(events["entries"])
    }
    
    logger.info(
        f"✅ 增强版复盘完成 - "
        f"评分: {report_data.get('overall_score', 0)}/100, "
        f"成本: ${result['cost']:.6f}, "
        f"耗时: {result['duration']:.2f}s"
    )
    
    return report_data
